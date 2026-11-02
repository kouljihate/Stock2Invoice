"""FastAPI application factory shared by every service.

One call wires: health endpoint, Mongo indexes, the outbox relay thread, the
RabbitMQ topology + consumer thread, and a clean shutdown. Services provide
routers and (optionally) a consumer handler.
"""

import logging
import threading
import time
from contextlib import asynccontextmanager

import pika
from fastapi import FastAPI

from .config import get_settings
from .db import ensure_indexes, ping
from .messaging import OutboxRelay, Rabbit

logger = logging.getLogger(__name__)


def probe_broker(rabbit: Rabbit) -> bool:
    params = pika.URLParameters(rabbit.settings.rabbitmq_url)
    params.socket_timeout = 3
    params.blocked_connection_timeout = 3
    try:
        conn = pika.BlockingConnection(params)
        conn.close()
        return True
    except Exception:
        return False


def create_service(name, *, title, binding_keys=('#',), consumer=None,
                   indexes=None, routers=(), on_startup=None):
    """Build the FastAPI app for service ``name``.

    ``consumer`` — optional ``handler(event)`` consumed from ``<name>.events``
    ``indexes``  — mapping passed to :func:`si_common.db.ensure_indexes`
    ``routers``  — (router, prefix) pairs
    ``on_startup`` — extra sync callable run at boot (seeding, etc.)
    """
    state = {'ready': False}
    rabbit = Rabbit(name)
    relay = OutboxRelay(name, rabbit)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        def _boot():
            if indexes:
                ensure_indexes(name, indexes)
            if on_startup:
                try:
                    on_startup()
                except Exception:
                    logger.exception('Startup hook failed for %s', name)
            try:
                rabbit.declare_topology(binding_keys)
                relay.start()
                state['ready'] = True
                if consumer:
                    rabbit.consume(consumer)   # blocks until shutdown
            except Exception:
                logger.exception('%s bootstrap failed', name)
                state['ready'] = False

        thread = threading.Thread(target=_boot, name=f'{name}-boot', daemon=True)
        thread.start()

        # Give the boot thread a brief head start so a quick /health right
        # after start-up reflects the real state, without blocking forever.
        for _ in range(50):
            if state['ready']:
                break
            time.sleep(0.1)

        yield

        relay.stop()
        rabbit.close()

    app = FastAPI(title=title, version='1.0.0', lifespan=lifespan)

    for router, prefix in routers:
        app.include_router(router, prefix=prefix)

    @app.get('/health')
    def health():
        ready = state['ready']
        mongo_ok = ping(name)
        broker_ok = ready and probe_broker(rabbit)
        status = 'ok' if (mongo_ok and broker_ok) else 'degraded'
        return {'status': status, 'service': name,
                'mongo': mongo_ok, 'rabbit': broker_ok}

    return app

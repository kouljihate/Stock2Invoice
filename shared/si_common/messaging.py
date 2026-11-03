"""RabbitMQ primitives shared by every service.

Design (see README-ARCHITECTURE):

* ``domain.events`` — topic exchange; every domain event is published here
  with its event type as the routing key (``sales.order.confirmed``).
* ``commands`` — direct exchange reserved for imperative cross-service
  commands (``stock.deduct``, ``stock.receive``).
* ``dead.letters`` — every service has its own DLQ bound from here.

Reliability model:

* Publishers wait for broker confirms.
* Services write domain events into a Mongo ``outbox`` collection; a relay
  thread publishes them and stamps ``published_at`` (at-least-once).
* Consumers ack manually, deduplicate on ``event_id`` (unique index), and on
  failure move the message through a per-queue TTL retry ladder
  (5s -> 30s -> 300s) before parking it on the service DLQ.

pika connections are not thread-safe, so channels are kept per-thread in a
``threading.local`` and re-established after broker hiccups.
"""

import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone

import pika
from pika.exceptions import UnroutableError

from .config import get_settings

logger = logging.getLogger(__name__)

EXCHANGE_EVENTS = 'domain.events'
EXCHANGE_COMMANDS = 'commands'
EXCHANGE_DLX = 'dead.letters'

# (queue suffix, message TTL in ms) — first failure waits 5s, then 30s, 5m.
RETRY_LADDER = (('5s', 5000), ('30s', 30000), ('300s', 300000))


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def new_event(event_type, *, company_id=None, payload=None, source=None,
              actor_user_id=None, correlation_id=None):
    """Build the envelope every service publishes."""
    return {
        'event_id': uuid.uuid4().hex,
        'type': event_type,
        'source': source,
        'occurred_at': utcnow(),
        'company_id': str(company_id) if company_id else None,
        'actor': {'user_id': str(actor_user_id) if actor_user_id else None},
        'correlation_id': correlation_id,
        'payload': payload or {},
    }


class Rabbit:
    """Thread-safe wrapper around pika blocking connections for one service."""

    def __init__(self, service_name):
        self.service_name = service_name
        self.settings = get_settings(service_name)
        self._binding_keys = ('#',)
        self._local = threading.local()
        self._closed = False

    def _reset(self):
        """Drop cached connection/channel so the next use reconnects."""
        try:
            conn = getattr(self._local, 'conn', None)
            if conn is not None and conn.is_open:
                conn.close()
        except Exception:
            pass
        self._local.conn = None
        self._local.channel = None

    # -- connections --------------------------------------------------------
    def _connection(self):
        conn = getattr(self._local, 'conn', None)
        if conn is not None and conn.is_open:
            return conn
        last_error = None
        for attempt in range(1, self.settings.rabbit_connect_retries + 1):
            try:
                conn = pika.BlockingConnection(
                    pika.URLParameters(self.settings.rabbitmq_url))
                self._local.conn = conn
                return conn
            except Exception as exc:  # broker not up yet / network blip
                last_error = exc
                if attempt == 1:
                    logger.warning('RabbitMQ connect attempt %d failed: %s',
                                   attempt, exc)
                time.sleep(self.settings.rabbit_retry_seconds)
        raise RuntimeError(f'RabbitMQ unreachable: {last_error}')

    def channel(self):
        conn = self._connection()
        chan = getattr(self._local, 'channel', None)
        if chan is not None and chan.is_open and chan.connection.is_open:
            return chan
        chan = conn.channel()
        # NOTE: this is a method call. A previous version assigned
        # `chan.confirm_delivery = True`, which merely shadowed the method
        # and left confirms disabled (silent event loss on broker failure).
        chan.confirm_delivery()
        self._local.channel = chan
        return chan

    def close(self):
        self._closed = True
        conn = getattr(self._local, 'conn', None)
        try:
            if conn is not None and conn.is_open:
                conn.close()
        except Exception:
            pass
        self._local.conn = None
        self._local.channel = None

    # -- topology -----------------------------------------------------------
    def declare_topology(self, binding_keys=('#',)):
        """Declare this service's exchanges, work queue, retry ladder and DLQ."""
        self._binding_keys = tuple(binding_keys)
        chan = self.channel()
        chan.exchange_declare(EXCHANGE_EVENTS, 'topic', durable=True)
        chan.exchange_declare(EXCHANGE_COMMANDS, 'direct', durable=True)
        chan.exchange_declare(EXCHANGE_DLX, 'direct', durable=True)

        work_queue = f'{self.service_name}.events'
        chan.queue_declare(work_queue, durable=True)
        for key in binding_keys:
            chan.queue_bind(work_queue, EXCHANGE_EVENTS, routing_key=key)

        for suffix, ttl in RETRY_LADDER:
            retry_queue = f'{work_queue}.retry.{suffix}'
            chan.queue_declare(retry_queue, durable=True, arguments={
                'x-message-ttl': ttl,
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': work_queue,
            })

        dlq = f'{work_queue}.dlq'
        chan.queue_declare(dlq, durable=True)
        chan.queue_bind(dlq, EXCHANGE_DLX, routing_key=self.service_name)
        logger.info('Topology ready for %s (bindings=%s)',
                    self.service_name, list(binding_keys))

    # -- publishing ---------------------------------------------------------
    def publish(self, routing_key, message, exchange=EXCHANGE_EVENTS):
        body = json.dumps(message, default=str).encode('utf-8')
        last_error = None
        # NOTE on pika semantics (BlockingChannel.basic_publish always
        # returns None): with confirms enabled, success is "no exception".
        # An unroutable mandatory message raises UnroutableError, a broker
        # nack raises NackError, and transport problems raise connection
        # errors. Never test the return value -- it is always None.
        for attempt in (1, 2):
            try:
                self.channel().basic_publish(
                    exchange=exchange, routing_key=routing_key, body=body,
                    properties=pika.BasicProperties(
                        content_type='application/json',
                        delivery_mode=2,  # persistent
                        message_id=message.get('event_id'),
                    ),
                    mandatory=True,
                )
                return True   # broker acked (confirms are on)
            except UnroutableError:
                raise   # deterministic: no retry can route this key
            except Exception as exc:
                last_error = exc
                logger.warning('Publish %s failed (attempt %d): %s',
                               routing_key, attempt, exc)
                self._reset()   # force reconnect on retry
        logger.error('Dropping event %s after retries: %s', routing_key, last_error)
        return False

    def send_command(self, routing_key, message):
        return self.publish(routing_key, message, exchange=EXCHANGE_COMMANDS)

    # -- consuming ----------------------------------------------------------
    def consume(self, handler, queue=None):
        """Consume ``<service>.events`` forever with retry ladder + DLQ.

        ``handler(event_dict)`` is called once per *new* event id. Raising
        routes the message through the retry ladder; returning normally acks.
        """
        work_queue = queue or f'{self.service_name}.events'
        processed = _ProcessedStore(self.service_name)

        def _on_message(chan, method, properties, body):
            attempts = _retry_count(properties)
            try:
                event = json.loads(body.decode('utf-8'))
            except Exception:
                logger.exception('Malformed message on %s -> DLQ', work_queue)
                self._park(chan, method, body, 'malformed')
                return
            event_id = (event.get('event_id')
                        or properties.message_id
                        or uuid.uuid4().hex)
            if processed.seen(event_id):
                chan.basic_ack(delivery_tag=method.delivery_tag)
                return
            try:
                handler(event)
            except Exception:
                logger.exception('Handler failed for %s (%s)', event.get('type'), event_id)
                if attempts >= len(RETRY_LADDER):
                    logger.error('Exhausted retries for %s -> DLQ', event.get('type'))
                    self._park(chan, method, body, event.get('type') or 'unknown')
                    return
                suffix = RETRY_LADDER[attempts][0]
                chan.basic_publish(
                    exchange='', routing_key=f'{work_queue}.retry.{suffix}',
                    body=body, properties=properties)
                chan.basic_ack(delivery_tag=method.delivery_tag)
                return
            processed.mark(event_id)
            chan.basic_ack(delivery_tag=method.delivery_tag)

        def _on_cancel(*_args):
            raise pika.exceptions.ConnectionClosedByBroker

        # A broker restart used to kill consumption forever (the exception
        # escaped start_consuming and the boot thread died). Reconnect with
        # capped backoff instead; redelivered messages are deduplicated on
        # event_id by _ProcessedStore, so at-least-once stays safe.
        delay = 2.0
        while not self._closed:
            try:
                self.declare_topology(self._binding_keys)
                chan = self.channel()
                chan.basic_qos(prefetch_count=16)
                chan.basic_consume(work_queue, _on_message, auto_ack=False)
                logger.info('%s consuming %s', self.service_name, work_queue)
                delay = 2.0
                chan.start_consuming()
                return   # clean stop (broker cancelled us and we are closed)
            except KeyboardInterrupt:
                try:
                    chan.stop_consuming()
                except Exception:
                    pass
                return
            except Exception as exc:
                if self._closed:
                    return
                logger.warning('%s consumer lost (%s); retrying in %.0fs',
                               self.service_name, exc, delay)
                self._reset()
                time.sleep(delay)
                delay = min(delay * 2, 60.0)

    def _park(self, chan, method, body, reason):
        try:
            self.publish(f'{self.service_name}',
                         {'dead_lettered_reason': str(reason),
                          'original': _safe_body(body)},
                         exchange=EXCHANGE_DLX)
            chan.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            logger.exception('Failed to park dead letter')
            chan.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def _retry_count(properties):
    """How many times this message has already been through the ladder."""
    headers = properties.headers or {}
    count = 0
    for entry in headers.get('x-death', []) or []:
        count = max(count, int(entry.get('count', 0)))
    return count


def _safe_body(body):
    try:
        return json.loads(body.decode('utf-8'))
    except Exception:
        return body.decode('utf-8', 'replace')[:2000]


class _ProcessedStore:
    """At-least-once -> effectively-once: one row per handled event id."""

    def __init__(self, service_name):
        from .db import get_db
        self._coll = get_db(service_name)['processed_events']
        try:
            self._coll.create_index('processed_at', expireAfterSeconds=30 * 24 * 3600)
        except Exception:
            pass

    def seen(self, event_id):
        return self._coll.find_one({'_id': event_id}, {'_id': 1}) is not None

    def mark(self, event_id):
        try:
            self._coll.insert_one({'_id': event_id, 'processed_at': datetime.now(timezone.utc)})
        except Exception:  # duplicate key: another worker got there first
            pass


class OutboxRelay:
    """Polls each service's ``outbox`` and publishes pending events with
    confirms, stamping ``published_at``. Started as a daemon thread."""

    def __init__(self, service_name, rabbit: Rabbit):
        self.service_name = service_name
        self.rabbit = rabbit
        self.settings = get_settings(service_name)
        from .db import get_db
        self._coll = get_db(service_name)['outbox']
        try:
            self._coll.create_index([('published_at', 1), ('created_at', 1)])
        except Exception:
            pass
        self._thread = None
        self._stop = threading.Event()

    def start(self):
        self._thread = threading.Thread(target=self._run, name=f'{self.service_name}-outbox', daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def drain_once(self):
        """Publish everything currently pending. Returns count published."""
        published = 0
        for row in self._coll.find({'published_at': None}).sort('created_at', 1).limit(100):
            try:
                ok = self.rabbit.publish(row.get('routing_key'),
                                         row.get('event'))
            except UnroutableError as exc:
                # Deterministic poison: no binding will ever match this key.
                # Count it down and then stop retrying (row stays as evidence).
                fails = int(row.get('poison_attempts') or 0) + 1
                update = {'$set': {'poison_attempts': fails,
                                   'last_error': str(exc)[:300]}}
                if fails >= 5:
                    logger.error('Parking poison event %s after %d tries',
                                 row.get('routing_key'), fails)
                    update['$set']['published_at'] = datetime.now(timezone.utc)
                    update['$set']['dead'] = True
                self._coll.update_one({'_id': row['_id']}, update)
                continue  # broker is fine: keep draining the rest
            if not ok:
                break  # transient/infra problem: retry all on next poll
            self._coll.update_one(
                {'_id': row['_id']},
                {'$set': {'published_at': datetime.now(timezone.utc)},
                 '$inc': {'attempts': 1}})
            published += 1
        return published

    def _run(self):
        while not self._stop.is_set():
            try:
                if self.drain_once() == 0:
                    self._stop.wait(self.settings.outbox_poll_seconds)
            except Exception:
                logger.exception('Outbox relay error')
                self._stop.wait(1.0)


def emit(db, event, routing_key=None):
    """Transactional outbox write: caller performs its domain write first (or
    in the same logical step), then enqueues the event here."""
    db['outbox'].insert_one({
        '_id': event['event_id'],
        'routing_key': routing_key or event['type'],
        'event': event,
        'created_at': datetime.now(timezone.utc),
        'published_at': None,
        'attempts': 0,
    })
    return event['event_id']

"""RabbitMQ monitoring via the broker's HTTP management API.

The BFF only needs read-only metrics for the admin dashboard, so this talks
to the management plugin (default :15672) instead of opening an AMQP channel.
The endpoint and credentials are derived from RABBITMQ_URL / RABBITMQ_MGMT_URL
so the same code works locally and inside docker compose.
"""

import base64
import json
import logging
import os
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

_TIMEOUT = 2


def _management_config():
    """Return ``(base_url, username, password)`` for the management API."""
    user, password = 'guest', 'guest'
    host, port = 'localhost', 15672

    amqp = os.getenv('RABBITMQ_URL', '')
    if amqp:
        parsed = urllib.parse.urlparse(amqp)
        if parsed.hostname:
            host = parsed.hostname
        if parsed.username:
            user = parsed.username
            password = parsed.password or password

    explicit = os.getenv('RABBITMQ_MGMT_URL', '')
    if explicit:
        parsed = urllib.parse.urlparse(explicit)
        if parsed.hostname:
            host = parsed.hostname
        if parsed.port:
            port = parsed.port
        if parsed.username:
            user = parsed.username
            password = parsed.password or password

    return f'http://{host}:{port}', user, password


def _get_json(path):
    base, user, password = _management_config()
    req = urllib.request.Request(base + path)
    token = base64.b64encode(f'{user}:{password}'.encode('utf-8')).decode('ascii')
    req.add_header('Authorization', f'Basic {token}')
    req.add_header('Accept', 'application/json')
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode('utf-8'))


def get_overview():
    """Broker health snapshot for the dashboard.

    Always returns a dict; ``ok`` is False when the broker is unreachable so
    the widget can render an "offline" state instead of raising.
    """
    try:
        overview = _get_json('/api/overview')
    except Exception as exc:  # noqa: BLE001 - any transport failure means "down"
        logger.warning('RabbitMQ management API unreachable: %s', exc)
        return {'ok': False, 'error': str(exc)[:160]}

    object_totals = overview.get('object_totals') or {}
    queue_totals = overview.get('queue_totals') or {}
    nodes = overview.get('nodes') or []
    alarms = overview.get('alarms') or []

    return {
        'ok': True,
        'version': overview.get('rabbitmq_version', '-'),
        'cluster': overview.get('cluster_name', '-'),
        'queues': object_totals.get('queues', 0),
        'connections': object_totals.get('connections', 0),
        'channels': object_totals.get('channels', 0),
        'consumers': object_totals.get('consumers', 0),
        'messages': queue_totals.get('messages', 0),
        'messages_ready': queue_totals.get('messages_ready', 0),
        'messages_unacked': queue_totals.get('messages_unacknowledged', 0),
        'nodes': len(nodes) if isinstance(nodes, list) else 0,
        'alarms': len(alarms) if isinstance(alarms, list) else 0,
    }


def get_top_queues(limit=5):
    """Busiest queues by message count (empty list when unreachable)."""
    try:
        queues = _get_json('/api/queues')
    except Exception as exc:  # noqa: BLE001
        logger.warning('RabbitMQ queue listing failed: %s', exc)
        return []
    if not isinstance(queues, list):
        return []

    queues.sort(key=lambda q: q.get('messages', 0) or 0, reverse=True)
    return [{
        'name': q.get('name', '-'),
        'vhost': q.get('vhost', '/'),
        'messages': q.get('messages', 0) or 0,
        'consumers': q.get('consumers', 0) or 0,
        'state': q.get('state', '-'),
    } for q in queues[:limit]]

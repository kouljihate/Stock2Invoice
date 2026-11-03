"""HTTP transport from the BFF to the domain services.

Every internal call forwards the browser's access token (header or cookie)
so the far service sees the same identity, roles and tenant the monolith's
in-process code saw. CLI commands with no browser session pass
``service=True`` to authenticate with the shared internal key instead.

These modules are the ``app/core/models`` and ``app/core/services`` of the
old monolith with the same class/method signatures, reimplemented over REST
so blueprints and templates stay untouched.
"""

import logging
import os

import requests
from flask import has_request_context, request

logger = logging.getLogger(__name__)

_DEFAULTS = {
    'identity': 'http://localhost:8001',
    'inventory': 'http://localhost:8002',
    'sales': 'http://localhost:8003',
    'procurement': 'http://localhost:8004',
    'workers': 'http://localhost:8005',
}

SERVICE_URLS = {
    name: os.getenv(f'{name.upper()}_URL', default)
    for name, default in _DEFAULTS.items()
}

INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', 'si-internal-dev-key')
HTTP_TIMEOUT = float(os.getenv('HTTP_TIMEOUT_SECONDS', '10'))

_session = requests.Session()

# Transient-error resilience: services restart on redeploy, and without
# retries that single refused connection / 503 becomes a user-facing 500.
# Retries apply to connect/read errors and to 502/503/504 on idempotent
# methods; POST/PATCH are never retried on status (not idempotent).
try:
    from urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter

    _retry = Retry(
        total=2, connect=2, read=2, backoff_factor=0.2,
        status_forcelist=(502, 503, 504),
    )
    _adapter = HTTPAdapter(max_retries=_retry,
                           pool_connections=10, pool_maxsize=20)
    _session.mount('http://', _adapter)
    _session.mount('https://', _adapter)
except Exception:  # pragma: no cover - urllib3 always ships with requests
    logger.warning('HTTP retry adapter unavailable; calls run without retries')


class ApiError(Exception):
    """A domain service returned an error status (or was unreachable)."""

    def __init__(self, service, status, detail):
        super().__init__(f'{service} {status}: {detail}')
        self.service = service
        self.status = status
        self.detail = detail or ''

    @property
    def not_found(self):
        return self.status == 404


def bearer_token():
    """The caller's access token, wherever flask-jwt-extended put it."""
    if not has_request_context():
        return None
    header = request.headers.get('Authorization', '')
    if header.lower().startswith('bearer '):
        return header[7:].strip()
    for location in ('access_token_cookie', 'access_token'):
        token = request.cookies.get(location)
        if token:
            return token
    return None


def call(service, method, path, *, json=None, params=None, service_key=False,
         timeout=None, expect_bytes=False):
    base = SERVICE_URLS[service].rstrip('/')
    url = f'{base}/{path.lstrip("/")}'
    headers = {'Accept': 'application/json'}
    token = bearer_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if service_key:
        headers['X-Service-Key'] = INTERNAL_API_KEY

    try:
        resp = _session.request(method, url, json=json, params=params,
                                headers=headers,
                                timeout=timeout or HTTP_TIMEOUT)
    except requests.RequestException as exc:
        logger.error('Service call failed: %s %s: %s', method, url, exc)
        raise ApiError(service, 0, f'{service} is unreachable') from exc

    if resp.status_code >= 400:
        raise ApiError(service, resp.status_code, _detail(resp))
    if expect_bytes:
        return resp.content
    if resp.status_code == 204 or not resp.content:
        return None
    try:
        return resp.json()
    except ValueError:
        return resp.text


def _detail(resp):
    try:
        body = resp.json()
        if isinstance(body, dict):
            return str(body.get('detail') or body.get('error') or body)
        return str(body)
    except ValueError:
        return (resp.text or '')[:500]


def get(service, path, **kwargs):
    return call(service, 'GET', path, **kwargs)


def post(service, path, **kwargs):
    return call(service, 'POST', path, **kwargs)


def patch(service, path, **kwargs):
    return call(service, 'PATCH', path, **kwargs)


def delete(service, path, **kwargs):
    return call(service, 'DELETE', path, **kwargs)


def or_none(fn, *args, **kwargs):
    """Run a call, mapping 404 to ``None`` (mirrors ``find_by_*`` semantics)."""
    try:
        return fn(*args, **kwargs)
    except ApiError as exc:
        if exc.not_found:
            return None
        raise


def as_bool(fn, *args, **kwargs):
    """Run a call, mapping 404 to ``False`` (mirrors ``delete`` semantics)."""
    try:
        return fn(*args, **kwargs) is not None
    except ApiError as exc:
        if exc.not_found:
            return False
        raise

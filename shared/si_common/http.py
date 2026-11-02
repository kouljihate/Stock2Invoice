"""Synchronous HTTP calls between services (``requests``-based).

Identity tokens are forwarded verbatim so the far service sees the same
tenant/roles; background calls with no browser session use the shared
``X-Service-Key``.
"""

import logging

import requests

from .config import get_settings

logger = logging.getLogger(__name__)

_URL_ATTR = {
    'identity': 'identity_url',
    'inventory': 'inventory_url',
    'sales': 'sales_url',
    'procurement': 'procurement_url',
    'workers': 'workers_url',
}


class ServiceCallError(Exception):
    def __init__(self, service, status, detail):
        super().__init__(f'{service} returned {status}: {detail}')
        self.service = service
        self.status = status
        self.detail = detail


def base_url(service_name: str) -> str:
    settings = get_settings('')
    return getattr(settings, _URL_ATTR[service_name])


def call(service_name, path, method='GET', *, json=None, params=None,
         identity=None, service_key=False, timeout=None):
    settings = get_settings('')
    url = f'{base_url(service_name).rstrip("/")}/{path.lstrip("/")}'
    headers = {'Accept': 'application/json'}
    token = getattr(identity, 'token', None) if identity is not None else None
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if service_key:
        headers['X-Service-Key'] = settings.internal_api_key
    try:
        resp = requests.request(method, url, json=json, params=params,
                                headers=headers,
                                timeout=timeout or settings.http_timeout_seconds)
    except requests.RequestException as exc:
        logger.error('Call to %s failed: %s', url, exc)
        raise ServiceCallError(service_name, 0, str(exc)) from exc
    if resp.status_code >= 400:
        detail = _detail(resp)
        raise ServiceCallError(service_name, resp.status_code, detail)
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
            return body.get('detail') or body.get('error') or str(body)
        return str(body)
    except ValueError:
        return (resp.text or '')[:500]

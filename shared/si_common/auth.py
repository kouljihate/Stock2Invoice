"""FastAPI security dependencies: who is calling, and under which tenant.

The BFF mints the JWT exactly as the monolith did (HS256, ``sub`` = user id,
``company_id`` / ``role_names`` additional claims) and forwards it as
``Authorization: Bearer`` on every internal call, so the browser's session is
the single source of truth end-to-end. Service-to-service calls that carry no
browser identity (worker -> identity lookups) authenticate with the shared
``X-Service-Key`` instead.
"""

from dataclasses import dataclass, field

import jwt as pyjwt
from fastapi import Depends, Header, HTTPException, Request

from .config import get_settings


@dataclass(frozen=True)
class Identity:
    user_id: str
    company_id: str | None = None
    roles: list = field(default_factory=list)
    name: str = ''
    email: str = ''
    # Raw access token, so service-to-service calls can forward the caller's
    # session instead of escalating to the shared service key.
    token: str | None = None

    @property
    def is_platform_admin(self) -> bool:
        return 'Admin' in (self.roles or [])

    @property
    def has_company(self) -> bool:
        return bool(self.company_id)


def decode_token(token: str, service_name: str) -> dict | None:
    settings = get_settings(service_name)
    try:
        return pyjwt.decode(token, settings.jwt_secret,
                            algorithms=[settings.jwt_algorithm])
    except Exception:
        return None


def identity_from_claims(claims: dict, token: str | None = None) -> Identity:
    return Identity(
        user_id=str(claims.get('sub', '')),
        company_id=claims.get('company_id'),
        roles=list(claims.get('role_names') or []),
        name=claims.get('user_name') or '',
        email=claims.get('user_email') or '',
        token=token,
    )


def _bearer(request: Request) -> str | None:
    header = request.headers.get('Authorization', '')
    if header.lower().startswith('bearer '):
        return header[7:].strip()
    return None


def get_identity(request: Request, service_name: str) -> Identity | None:
    token = _bearer(request)
    if not token:
        return None
    claims = decode_token(token, service_name)
    if not claims:
        return None
    return identity_from_claims(claims, token=token)


def make_require_identity(service_name: str):
    """Factory so each service binds its own name without boilerplate."""
    def require_identity(request: Request) -> Identity:
        identity = get_identity(request, service_name)
        if identity is None or not identity.user_id:
            raise HTTPException(status_code=401, detail='Missing or invalid access token')
        return identity
    return require_identity


def make_require_company(service_name: str):
    require_identity = make_require_identity(service_name)

    def require_company(identity: Identity = Depends(require_identity)) -> Identity:
        if not identity.has_company:
            raise HTTPException(status_code=403, detail='Account is not linked to a company')
        return identity
    return require_company


def make_require_admin(service_name: str):
    require_identity = make_require_identity(service_name)

    def require_admin(identity: Identity = Depends(require_identity)) -> Identity:
        if not identity.is_platform_admin:
            raise HTTPException(status_code=403, detail='Platform administrator only')
        return identity
    return require_admin


def make_require_service(service_name: str):
    """``X-Service-Key`` gate for internal endpoints used service-to-service
    (no browser session exists for a background worker)."""
    def require_service(x_service_key: str = Header(default='')) -> bool:
        expected = get_settings(service_name).internal_api_key
        if not expected or x_service_key != expected:
            raise HTTPException(status_code=403, detail='Service key required')
        return True
    return require_service

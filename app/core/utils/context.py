"""Request-scoped identity, resolved from the database.

Everything that decides *who* the caller is and *which tenant* they belong to
goes through this module. The values are cached on ``g`` for the duration of
one request, so a route can call them freely.

Why not read the JWT claims? A token is minted at login and is then stale for
its whole lifetime (up to 24h in docker-compose): a user moved to another
company, a demoted Admin or a role change would keep the old rights until the
token expired. The central ``before_request`` gate already loads the user from
Mongo on every request, so resolving identity here costs no extra query and
keeps the tenant boundary and the RBAC gate on the same, fresh data.
"""

import logging

from flask import g, has_request_context
from flask_jwt_extended import get_jwt_identity

logger = logging.getLogger(__name__)


def current_user():
    """The acting user's document, loaded once per request. ``None`` if there
    is no valid identity or the account no longer exists."""
    if not has_request_context():
        return None
    if 'ctx_user' in g:
        return g.ctx_user
    user = None
    try:
        identity = get_jwt_identity()
    except Exception:
        identity = None
    if identity:
        from app.core.models.user_model import UserModel
        try:
            user = UserModel.find_by_id(identity)
        except Exception:
            logger.exception('Could not load user %s', identity)
            user = None
    g.ctx_user = user
    return user


def current_company_id():
    """String id of the acting user's company, or ``None``.

    Always derived from the user document (never from token claims) so a
    company change takes effect on the very next request.
    """
    if not has_request_context():
        return None
    if 'ctx_company_id' in g:
        return g.ctx_company_id
    user = current_user()
    company_id = user.get('company_id') if user else None
    value = str(company_id) if company_id else None
    g.ctx_company_id = value
    return value


def is_super_admin():
    """True when the acting user currently holds the platform Admin profile."""
    user = current_user()
    return bool(user and 'Admin' in (user.get('roles') or []))

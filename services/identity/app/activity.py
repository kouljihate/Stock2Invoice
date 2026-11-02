"""Activity/domain events published by identity-service."""

from si_common.events import activity, emit_event

from . import repos


def _emit(event_type, *, company_id=None, user_id=None, act=None, payload=None):
    return emit_event(
        repos.users.db, event_type,
        source='identity',
        company_id=company_id,
        actor_user_id=user_id,
        activity=act,
        payload=payload,
    )


def session_login(user):
    uid = str(user['_id'])
    return _emit('identity.session.login', company_id=user.get('company_id'),
                 user_id=uid,
                 act=activity('session', uid, user.get('email', ''), 'login'),
                 payload={'email': user.get('email', '')})


def session_logout(user):
    uid = str(user['_id'])
    return _emit('identity.session.logout', company_id=user.get('company_id'),
                 user_id=uid,
                 act=activity('session', uid, user.get('email', ''), 'logout'),
                 payload={'email': user.get('email', '')})


def user_created(user):
    return _emit('identity.user.created',
                 company_id=user.get('company_id'),
                 user_id=str(user['_id']),
                 payload={'id': str(user['_id']),
                          'email': user.get('email'),
                          'roles': user.get('roles', [])})


def company_created(company, *, activity_action=None, user_name=None):
    """Domain event always; an activity-log row only when the caller passes an
    action (the profile wizard records 'setup' — the moment a tenant comes
    into existence; ordinary admin creation never logged an activity)."""
    cid = str(company['_id'])
    act = None
    if activity_action:
        act = activity('company', cid, company.get('name', ''), activity_action)
        if user_name:
            act['user_name'] = user_name
    return _emit(f'identity.company.{activity_action or "created"}',
                 company_id=cid, user_id=company.get('created_by'),
                 act=act,
                 payload={'id': cid, 'name': company.get('name'),
                          'action': activity_action or 'created'})

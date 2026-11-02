"""Auth endpoints: credential verification, registration, session events,
and the CLI operations (super-admin minting, role promotion)."""

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_identity, make_require_service
from si_common.ids import oid
from si_common.rbac import ROLE_DEFINITIONS

from .. import activity, repos, security, serialize

router = APIRouter(tags=['auth'])

require_identity = make_require_identity('identity')
require_service = make_require_service('identity')


@router.post('/authenticate')
def authenticate(credentials: dict = Body(...)):
    email = (credentials.get('email') or '').strip().lower()
    password = credentials.get('password') or ''
    user = repos.users.find_one({'email': email})
    if not user or not security.check_password(user.get('password', ''), password):
        raise HTTPException(status_code=401, detail='Invalid email or password.')
    activity.session_login(user)
    return serialize.user_out(user)


@router.post('/register')
def register(body: dict = Body(...)):
    email = (body.get('email') or '').strip().lower()
    password = body.get('password') or ''
    if not email or not password:
        raise HTTPException(status_code=422, detail='Email and password are required.')
    if repos.users.find_one({'email': email}):
        raise HTTPException(status_code=409, detail='Email already registered.')
    data = {
        'name': (body.get('name') or '').strip(),
        'email': email,
        'password': security.hash_password(password),
        'roles': ['Customer'],
    }
    if body.get('company_id'):
        data['company_id'] = oid(body['company_id'])
    user_id = repos.users.create(data)
    created = repos.users.find_by_id(user_id)
    activity.user_created(created)
    return {'id': user_id}


@router.post('/logout')
def logout(identity: Identity = Depends(require_identity)):
    user = repos.users.find_by_id(identity.user_id)
    if user:
        activity.session_logout(user)
    return {'ok': True}


# --- CLI operations (invoked by the BFF's flask commands over internal HTTP) ---

@router.post('/internal/create-super-admin', dependencies=[Depends(require_service)])
def create_super_admin(body: dict = Body(...)):
    email = (body.get('email') or '').strip().lower()
    password = body.get('password') or ''
    if repos.users.find_one({'email': email}):
        return {'error': f'User "{email}" already exists.'}
    if repos.users.count({'roles': 'Admin'}):
        return {'error': 'an Admin account already exists. This application '
                         'allows exactly one Admin profile.'}
    user_id = repos.users.create({
        'name': body.get('name') or 'Super Admin',
        'email': email,
        'password': security.hash_password(password),
        'roles': ['Admin'],
    })
    activity.user_created(repos.users.find_by_id(user_id))
    return {'ok': True, 'email': email}


@router.post('/internal/promote', dependencies=[Depends(require_service)])
def promote(body: dict = Body(...)):
    email = (body.get('email') or '').strip().lower()
    role = body.get('role') or ''
    if role not in ROLE_DEFINITIONS:
        return {'error': f'unknown role "{role}". Choose one of: '
                         f'{", ".join(ROLE_DEFINITIONS)}'}
    user = repos.users.find_one({'email': email})
    if not user:
        return {'error': f'no user with email "{email}".'}
    if role == 'Admin':
        others = repos.users.count({'roles': 'Admin',
                                    '_id': {'$ne': user['_id']}})
        if others:
            return {'error': 'another account already holds the Admin profile. '
                             'Exactly one is allowed; demote it first.'}
    repos.users.update(str(user['_id']), {'roles': [role]}, touch_updated=True)
    return {'ok': True, 'role': role}

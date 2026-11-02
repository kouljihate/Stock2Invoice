"""User CRUD and lookups. Password hashes never leave this service."""

from fastapi import APIRouter, Body, HTTPException, Query

from si_common.ids import oid

from .. import activity, repos, security, serialize

router = APIRouter(tags=['users'])


def _query(search=None, email=None, company_id=None):
    query = {}
    if email:
        query['email'] = email
    if company_id:
        query['company_id'] = oid(company_id)
    if search:
        import re
        regex = {'$regex': re.escape(search), '$options': 'i'}
        query['$or'] = [{'name': regex}, {'email': regex}]
    return query


def _coerce(filters: dict) -> dict:
    """Client filters carry ids as strings; this collection stores ObjectIds."""
    out = dict(filters or {})
    if out.get('company_id'):
        out['company_id'] = oid(out['company_id'])
    if out.get('_id'):
        out['_id'] = oid(out['_id'])
    return out


@router.get('')
def list_users(search: str | None = None, email: str | None = None,
               company_id: str | None = None):
    docs, _ = repos.users.find_all(1, 10_000, _query(search, email, company_id))
    return {'items': [serialize.user_out(u) for u in docs]}


@router.get('/count')
def count_users(filters: str | None = Query(default=None)):
    import json
    query = {}
    if filters:
        try:
            query = json.loads(filters)
        except ValueError:
            query = {}
    return {'count': repos.users.count(_coerce(query))}


@router.get('/count-admins')
def count_admins(exclude_id: str | None = None):
    query = {'roles': 'Admin'}
    if exclude_id:
        query['_id'] = {'$ne': oid(exclude_id)}
    return {'count': repos.users.count(query)}


@router.get('/id/{user_id}')
def get_user(user_id: str):
    doc = repos.users.find_by_id(user_id)
    if not doc:
        raise HTTPException(status_code=404, detail='User not found.')
    return serialize.user_out(doc)


@router.post('')
def create_user(body: dict = Body(...)):
    data = dict(body)
    if data.get('password'):
        data['password'] = security.hash_password(data['password'])
    if data.get('company_id'):
        data['company_id'] = oid(data['company_id'])
    data.setdefault('roles', [])
    user_id = repos.users.create(data)
    activity.user_created(repos.users.find_by_id(user_id))
    return {'id': user_id}


@router.patch('/{user_id}')
def update_user(user_id: str, body: dict = Body(...)):
    data = dict(body)
    if data.get('password'):
        data['password'] = security.hash_password(data['password'])
    if 'company_id' in data:
        data['company_id'] = oid(data['company_id'])
    if not repos.users.update(user_id, data, touch_updated=True):
        raise HTTPException(status_code=404, detail='User not found.')
    return {'ok': True}


@router.delete('/{user_id}')
def delete_user(user_id: str):
    if not repos.users.delete(user_id):
        raise HTTPException(status_code=404, detail='User not found.')
    return {'ok': True}

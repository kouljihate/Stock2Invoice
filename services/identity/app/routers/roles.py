"""Role lookups — the catalogue the BFF's user-management screens render."""

from fastapi import APIRouter, HTTPException

from .. import repos, serialize

router = APIRouter(tags=['roles'])


@router.get('')
def list_roles():
    docs = repos.roles.find_all()
    docs.sort(key=lambda r: (r.get('name') or '').lower())
    return {'items': [serialize.role_out(r) for r in docs]}


@router.get('/name/{name}')
def get_role(name: str):
    doc = repos.roles.find_one({'_id': name.lower()})
    if not doc:
        raise HTTPException(status_code=404, detail='Role not found.')
    return serialize.role_out(doc)

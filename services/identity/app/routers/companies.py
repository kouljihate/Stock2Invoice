"""Company CRUD + the first-login setup wizard endpoint."""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_identity

from .. import activity, repos, serialize

router = APIRouter(tags=['companies'])

require_identity = make_require_identity('identity')


@router.get('')
def list_companies():
    docs = repos.companies.find_all_unpaginated()
    docs.sort(key=lambda c: (c.get('name') or '').lower())
    return {'items': [serialize.company_out(c) for c in docs]}


@router.get('/count')
def count_companies():
    return {'count': repos.companies.count()}


@router.get('/id/{company_id}')
def get_company(company_id: str):
    doc = repos.companies.find_by_id(company_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Company not found.')
    return serialize.company_out(doc)


@router.get('/slug/{slug}')
def get_company_by_slug(slug: str):
    doc = repos.companies.find_one({'slug': slug})
    if not doc:
        raise HTTPException(status_code=404, detail='Company not found.')
    return serialize.company_out(doc)


@router.post('')
def create_company(body: dict = Body(...)):
    data = dict(body)
    company_id = repos.companies.create(data)
    doc = repos.companies.find_by_id(company_id)
    activity.company_created(doc)
    return {'id': company_id}


@router.post('/setup')
def setup_company(body: dict = Body(...),
                  identity: Identity = Depends(require_identity)):
    """First-login wizard: the moment a PME tenant comes into existence."""
    data = dict(body)
    data['created_by'] = identity.user_id
    company_id = repos.companies.create(data)
    doc = repos.companies.find_by_id(company_id)
    user = repos.users.find_by_id(identity.user_id)
    activity.company_created(doc, activity_action='setup',
                             user_name=(user or {}).get('name', ''))
    return {'id': company_id}


@router.patch('/{company_id}')
def update_company(company_id: str, body: dict = Body(...)):
    if not repos.companies.update(company_id, dict(body)):
        raise HTTPException(status_code=404, detail='Company not found.')
    return {'ok': True}


@router.delete('/{company_id}')
def delete_company(company_id: str):
    if not repos.companies.delete(company_id):
        raise HTTPException(status_code=404, detail='Company not found.')
    return {'ok': True}

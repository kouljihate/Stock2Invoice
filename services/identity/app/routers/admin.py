"""Platform-admin statistics + internal operations.

The admin dashboard renders cross-collection aggregates; each service
exposes the slice it owns and the BFF merges them. identity owns companies,
users and role breakdowns.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_admin, make_require_service

from .. import repos, seed, serialize

router = APIRouter(tags=['admin'])

require_admin = make_require_admin('identity')
require_service = make_require_service('identity')


@router.get('/admin/stats')
def admin_stats(_: Identity = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    user_counts = {}
    for row in repos.users.aggregate([{'$group': {'_id': '$company_id', 'n': {'$sum': 1}}}]):
        if row['_id'] is not None:
            user_counts[str(row['_id'])] = row['n']

    growth = list(repos.companies.aggregate([
        {'$match': {'created_at': {'$gte': thirty_days_ago}}},
        {'$group': {'_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}},
                    'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}},
    ]))

    role_rows = list(repos.users.aggregate([
        {'$unwind': '$roles'},
        {'$group': {'_id': '$roles', 'count': {'$sum': 1}}},
    ]))

    return {
        'counters': {'user_count': user_counts},
        'company_growth': [{'day': g['_id'], 'count': g['count']} for g in growth],
        'user_roles': {r['_id'] or 'Unknown': r['count'] for r in role_rows},
        'collection_stats': {
            'companies': repos.companies.count(),
            'users': repos.users.count(),
            'roles': repos.roles.count(),
        },
    }


@router.get('/internal/users/{user_id}', dependencies=[Depends(require_service)])
def user_brief(user_id: str):
    """Name/email resolution for background workers (no browser session)."""
    doc = repos.users.find_by_id(user_id)
    return serialize.user_brief(doc) or {'id': user_id, 'name': '', 'email': ''}


@router.post('/internal/bootstrap', dependencies=[Depends(require_service)])
def bootstrap():
    return seed.bootstrap()

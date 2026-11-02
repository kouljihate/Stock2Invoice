"""Repositories + index definitions owned by identity-service."""

from si_common.crud import Repository
from si_common.db import ensure_indexes

users = Repository('identity', 'users')
companies = Repository('identity', 'companies')
roles = Repository('identity', 'roles')

# Ported from the monolith's bootstrap.INDEXES — only the collections this
# service owns. Products/invoices/... indexes are ensured by their owners.
INDEXES = {
    'users': [
        ([('email', 1)], {'unique': True, 'name': 'uniq_users_email'}),
        ([('company_id', 1)], {'name': 'users_company'}),
        ([('roles', 1)], {'name': 'users_roles'}),
    ],
    'companies': [
        ([('name', 1)], {'name': 'companies_name'}),
    ],
}


def ensure_all():
    return ensure_indexes('identity', INDEXES)

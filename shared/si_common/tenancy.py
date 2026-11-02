"""Tenant scoping helpers — the microservice port of ``tenant_filter``.

Every service derives the acting company from the *token*, never from a
client-supplied field, so a forged filter cannot widen a query across
tenants.
"""

from .ids import tenant_filter


def scoped(identity, filters=None, *, allow_unscoped=False):
    """Merge tenant scoping into a query filter.

    * company user  -> pinned to their company
    * platform Admin on an unscoped endpoint -> sees everything
    * anyone else on a tenant endpoint -> matches nothing (never everything)
    """
    query = dict(filters or {})
    company_id = getattr(identity, 'company_id', None)
    if company_id:
        query.update(tenant_filter(company_id))
    elif not allow_unscoped:
        query.update(tenant_filter(None))
    return query


def company_or_forbid(identity) -> str:
    if not getattr(identity, 'company_id', None):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail='Account is not linked to a company')
    return identity.company_id

"""ObjectId helpers and JSON-safe document shaping.

Mirrors ``app/core/utils/helpers.oid`` and the ``to_dict`` conventions the
templates already expect: ids become strings, datetimes become ISO strings,
and a malformed id matches *nothing* rather than everything.
"""

from datetime import date, datetime, timezone

from bson import ObjectId


def oid(val):
    if val is None or val == '':
        return None
    if isinstance(val, ObjectId):
        return val
    try:
        return ObjectId(str(val))
    except Exception:
        return None


def tenant_filter(cid, field='company_id'):
    """A query that only ever matches one tenant's documents.

    When ``cid`` is missing or unusable the result matches nothing: a caller
    with no company must never see another tenant's rows.
    """
    value = oid(cid)
    if value is None:
        return {field: {'$in': []}}
    return {field: value}


def iso(value):
    """ISO-8601 string for datetime/date, passthrough for str, else None."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return str(value)


def as_str(value):
    return str(value) if value is not None else None


def now():
    return datetime.now(timezone.utc)


def jsonable(value):
    """Recursively convert Mongo types into JSON-safe values."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return iso(value)
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value

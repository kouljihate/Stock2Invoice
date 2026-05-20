def oid(val):
    from bson.objectid import ObjectId
    if val is None:
        return None
    try:
        return ObjectId(val) if isinstance(val, str) else val
    except Exception:
        return None


def paginate(page, per_page):
    try:
        page = max(int(page), 1)
    except (ValueError, TypeError):
        page = 1
    try:
        per_page = min(max(int(per_page), 1), 100)
    except (ValueError, TypeError):
        per_page = 20
    return page, per_page

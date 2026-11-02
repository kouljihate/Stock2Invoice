"""Generic Mongo repository — the port of the per-model CRUD layer.

Each service instantiates one per collection; routers shape documents to
their public dict form with the service's own ``to_dict``.
"""

from bson import ObjectId

from .db import get_db
from .ids import now


class Repository:
    def __init__(self, service_name: str, collection: str):
        self.service_name = service_name
        self.collection = collection
        self.db = get_db(service_name)
        self.coll = self.db[collection]

    # -- writes -------------------------------------------------------------
    def create(self, data: dict) -> str:
        data = dict(data)
        data.setdefault('created_at', now())
        result = self.coll.insert_one(data)
        return str(result.inserted_id)

    def update(self, entity_id, data: dict, *, touch_updated: bool = False) -> bool:
        """``$set`` the payload; only identity-service stamps ``updated_at``
        (mirrors the monolith's per-model behaviour)."""
        payload = dict(data)
        if touch_updated:
            payload['updated_at'] = now()
        result = self.coll.update_one({'_id': _oid(entity_id)}, {'$set': payload})
        return result.matched_count > 0

    def delete(self, entity_id) -> bool:
        result = self.coll.delete_one({'_id': _oid(entity_id)})
        return result.deleted_count > 0

    # -- reads --------------------------------------------------------------
    def find_by_id(self, entity_id, filters=None):
        query = {'_id': _oid(entity_id)}
        if filters:
            query.update(filters)
        return self.coll.find_one(query)

    def find_one(self, query: dict):
        return self.coll.find_one(query)

    def find_all(self, page=1, per_page=20, filters=None, sort=('created_at', -1)):
        query = filters or {}
        total = self.coll.count_documents(query)
        cursor = self.coll.find(query)
        if sort:
            cursor = cursor.sort(*sort) if isinstance(sort, tuple) else cursor.sort(sort)
        docs = list(cursor.skip((page - 1) * per_page).limit(per_page))
        return docs, total

    def find_all_unpaginated(self, filters=None):
        return list(self.coll.find(filters or {}))

    def count(self, filters=None) -> int:
        return self.coll.count_documents(filters or {})

    def recent(self, limit=10, filters=None):
        query = filters or {}
        return list(self.coll.find(query).sort('created_at', -1).limit(limit))

    def aggregate(self, pipeline):
        return list(self.coll.aggregate(pipeline))

    def insert_event_row(self, row: dict) -> str:
        return self.create(row)


def _oid(value):
    if isinstance(value, ObjectId) or value is None:
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None

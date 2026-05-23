from datetime import datetime, timezone
from app.extensions.db import mongo


class EventModel:
    collection = 'events'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[EventModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def count(filters=None):
        return mongo.db[EventModel.collection].count_documents(filters or {})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[EventModel.collection].count_documents(query)
        cursor = mongo.db[EventModel.collection].find(query) \
            .sort('created_at', -1) \
            .skip((page - 1) * per_page) \
            .limit(per_page)
        return list(cursor), total

    @staticmethod
    def to_dict(ev):
        return {
            'id': str(ev['_id']),
            'company_id': str(ev.get('company_id')) if ev.get('company_id') else None,
            'entity_type': ev.get('entity_type', ''),
            'entity_id': ev.get('entity_id', ''),
            'entity_number': ev.get('entity_number', ''),
            'action': ev.get('action', ''),
            'changes': ev.get('changes', {}),
            'user_id': str(ev.get('user_id')) if ev.get('user_id') else None,
            'user_name': ev.get('user_name', ''),
            'created_at': ev.get('created_at').isoformat() if ev.get('created_at') else None,
        }

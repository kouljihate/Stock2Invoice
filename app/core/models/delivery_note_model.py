from datetime import datetime, timezone
from app.extensions.db import mongo


class DeliveryNoteModel:
    collection = 'delivery_notes'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[DeliveryNoteModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(dn_id):
        from bson.objectid import ObjectId
        return mongo.db[DeliveryNoteModel.collection].find_one({'_id': ObjectId(dn_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[DeliveryNoteModel.collection].count_documents(query)
        cursor = mongo.db[DeliveryNoteModel.collection].find(query).sort('created_at', -1).skip((page - 1) * per_page).limit(per_page)
        return list(cursor), total

    @staticmethod
    def count(filters=None):
        return mongo.db[DeliveryNoteModel.collection].count_documents(filters or {})

    @staticmethod
    def delete(dn_id):
        from bson.objectid import ObjectId
        mongo.db[DeliveryNoteModel.collection].delete_one({'_id': ObjectId(dn_id)})

    @staticmethod
    def to_dict(dn):
        return {
            'id': str(dn['_id']),
            'dn_number': dn.get('dn_number'),
            'order_id': str(dn.get('order_id')) if dn.get('order_id') else None,
            'order_number': dn.get('order_number', ''),
            'customer_name': dn.get('customer_name', ''),
            'items': dn.get('items', []),
            'notes': dn.get('notes', ''),
            'company_id': str(dn.get('company_id')) if dn.get('company_id') else None,
            'created_by': str(dn.get('created_by')) if dn.get('created_by') else None,
            'created_at': dn.get('created_at').isoformat() if dn.get('created_at') else None,
        }
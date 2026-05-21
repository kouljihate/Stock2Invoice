from datetime import datetime, timezone
from app.extensions.db import mongo


class SupplierModel:
    collection = 'suppliers'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[SupplierModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(supplier_id):
        from bson.objectid import ObjectId
        return mongo.db[SupplierModel.collection].find_one({'_id': ObjectId(supplier_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[SupplierModel.collection].count_documents(query)
        cursor = mongo.db[SupplierModel.collection].find(query).sort('name', 1).skip((page - 1) * per_page).limit(per_page)
        return list(cursor), total

    @staticmethod
    def find_all_unpaginated(filters=None):
        return list(mongo.db[SupplierModel.collection].find(filters or {}).sort('name', 1))

    @staticmethod
    def update(supplier_id, data):
        from bson.objectid import ObjectId
        mongo.db[SupplierModel.collection].update_one({'_id': ObjectId(supplier_id)}, {'$set': data})

    @staticmethod
    def delete(supplier_id):
        from bson.objectid import ObjectId
        mongo.db[SupplierModel.collection].delete_one({'_id': ObjectId(supplier_id)})

    @staticmethod
    def count(filters=None):
        return mongo.db[SupplierModel.collection].count_documents(filters or {})

    @staticmethod
    def to_dict(s):
        return {
            'id': str(s['_id']),
            'name': s.get('name'),
            'contact_name': s.get('contact_name', ''),
            'email': s.get('email', ''),
            'phone': s.get('phone', ''),
            'address': s.get('address', ''),
            'city': s.get('city', ''),
            'ice': s.get('ice', ''),
            'rc': s.get('rc', ''),
            'payment_terms': s.get('payment_terms', ''),
            'company_id': str(s.get('company_id')) if s.get('company_id') else None,
            'created_at': s.get('created_at').isoformat() if s.get('created_at') else None,
        }
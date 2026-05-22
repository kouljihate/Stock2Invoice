from datetime import datetime, timezone
from app.extensions.db import mongo


class CustomerModel:
    collection = 'customers'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[CustomerModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(customer_id):
        from bson.objectid import ObjectId
        return mongo.db[CustomerModel.collection].find_one({'_id': ObjectId(customer_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[CustomerModel.collection].count_documents(query)
        cursor = mongo.db[CustomerModel.collection].find(query).sort('name', 1).skip((page - 1) * per_page).limit(per_page)
        return list(cursor), total

    @staticmethod
    def find_all_unpaginated(filters=None):
        return list(mongo.db[CustomerModel.collection].find(filters or {}).sort('name', 1))

    @staticmethod
    def update(customer_id, data):
        from bson.objectid import ObjectId
        mongo.db[CustomerModel.collection].update_one({'_id': ObjectId(customer_id)}, {'$set': data})

    @staticmethod
    def delete(customer_id):
        from bson.objectid import ObjectId
        mongo.db[CustomerModel.collection].delete_one({'_id': ObjectId(customer_id)})

    @staticmethod
    def count(filters=None):
        return mongo.db[CustomerModel.collection].count_documents(filters or {})

    @staticmethod
    def to_dict(c):
        return {
            'id': str(c['_id']),
            'type': c.get('type', 'prive'),
            'name': c.get('name'),
            'contact': c.get('contact', ''),
            'email': c.get('email', ''),
            'phone': c.get('phone', ''),
            'address': c.get('address', ''),
            'city': c.get('city', ''),
            'paiement_terms': c.get('paiement_terms', ''),
            'ICE': c.get('ICE', ''),
            'RC': c.get('RC', ''),
            'company_id': str(c.get('company_id')) if c.get('company_id') else None,
            'created_at': c.get('created_at').isoformat() if c.get('created_at') else None,
        }

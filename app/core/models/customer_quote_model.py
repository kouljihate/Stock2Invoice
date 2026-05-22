from datetime import datetime, timezone
from app.extensions.db import mongo


class CustomerQuoteModel:
    collection = 'customer_quotes'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[CustomerQuoteModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(quote_id):
        from bson.objectid import ObjectId
        return mongo.db[CustomerQuoteModel.collection].find_one({'_id': ObjectId(quote_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[CustomerQuoteModel.collection].count_documents(query)
        cursor = mongo.db[CustomerQuoteModel.collection].find(query).sort('created_at', -1).skip((page - 1) * per_page).limit(per_page)
        return list(cursor), total

    @staticmethod
    def update(quote_id, data):
        from bson.objectid import ObjectId
        mongo.db[CustomerQuoteModel.collection].update_one({'_id': ObjectId(quote_id)}, {'$set': data})

    @staticmethod
    def count(filters=None):
        return mongo.db[CustomerQuoteModel.collection].count_documents(filters or {})

    @staticmethod
    def delete(quote_id):
        from bson.objectid import ObjectId
        mongo.db[CustomerQuoteModel.collection].delete_one({'_id': ObjectId(quote_id)})

    @staticmethod
    def to_dict(q):
        return {
            'id': str(q['_id']),
            'quote_number': q.get('quote_number'),
            'customer_name': q.get('customer_name'),
            'customer_email': q.get('customer_email', ''),
            'customer_address': q.get('customer_address', ''),
            'items': q.get('items', []),
            'subtotal': float(q.get('subtotal', 0)),
            'discount_percent': float(q.get('discount_percent', 0)),
            'discount_amount': float(q.get('discount_amount', 0)),
            'tax_percent': float(q.get('tax_percent', 0)),
            'tax_amount': float(q.get('tax_amount', 0)),
            'total': float(q.get('total', 0)),
            'status': q.get('status', 'draft'),
            'valid_until': q.get('valid_until').isoformat() if q.get('valid_until') else None,
            'notes': q.get('notes', ''),
            'company_id': str(q.get('company_id')) if q.get('company_id') else None,
            'created_by': str(q.get('created_by')) if q.get('created_by') else None,
            'created_at': q.get('created_at').isoformat() if q.get('created_at') else None,
            'generated_order_id': str(q.get('generated_order_id')) if q.get('generated_order_id') else None,
            'generated_order_number': q.get('generated_order_number'),
        }
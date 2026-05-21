from datetime import datetime, timezone
from app.extensions.db import mongo


class PaymentModel:
    collection = 'payments'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[PaymentModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(payment_id):
        from bson.objectid import ObjectId
        return mongo.db[PaymentModel.collection].find_one({'_id': ObjectId(payment_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[PaymentModel.collection].count_documents(query)
        cursor = mongo.db[PaymentModel.collection].find(query).sort('created_at', -1).skip((page - 1) * per_page).limit(per_page)
        return list(cursor), total

    @staticmethod
    def update(payment_id, data):
        from bson.objectid import ObjectId
        mongo.db[PaymentModel.collection].update_one({'_id': ObjectId(payment_id)}, {'$set': data})

    @staticmethod
    def count(filters=None):
        return mongo.db[PaymentModel.collection].count_documents(filters or {})

    @staticmethod
    def to_dict(p):
        return {
            'id': str(p['_id']),
            'payment_number': p.get('payment_number'),
            'supplier_id': str(p.get('supplier_id')) if p.get('supplier_id') else None,
            'supplier_name': p.get('supplier_name', ''),
            'invoice_id': str(p.get('invoice_id')) if p.get('invoice_id') else None,
            'invoice_number': p.get('invoice_number', ''),
            'amount': float(p.get('amount', 0)),
            'payment_date': p.get('payment_date').isoformat() if p.get('payment_date') else None,
            'payment_method': p.get('payment_method', ''),
            'reference': p.get('reference', ''),
            'notes': p.get('notes', ''),
            'status': p.get('status', 'pending'),
            'company_id': str(p.get('company_id')) if p.get('company_id') else None,
            'created_by': str(p.get('created_by')) if p.get('created_by') else None,
            'created_at': p.get('created_at').isoformat() if p.get('created_at') else None,
        }
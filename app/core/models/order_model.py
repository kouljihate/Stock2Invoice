from datetime import datetime, timezone
from app.extensions.db import mongo


class OrderModel:
    collection = 'orders'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[OrderModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(order_id):
        from bson.objectid import ObjectId
        return mongo.db[OrderModel.collection].find_one({'_id': ObjectId(order_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[OrderModel.collection].count_documents(query)
        cursor = mongo.db[OrderModel.collection].find(query) \
            .sort('created_at', -1) \
            .skip((page - 1) * per_page) \
            .limit(per_page)
        return list(cursor), total

    @staticmethod
    def update(order_id, data):
        from bson.objectid import ObjectId
        mongo.db[OrderModel.collection].update_one(
            {'_id': ObjectId(order_id)},
            {'$set': data},
        )

    @staticmethod
    def count(filters=None):
        return mongo.db[OrderModel.collection].count_documents(filters or {})

    @staticmethod
    def recent(limit=5, filters=None):
        query = filters or {}
        cursor = mongo.db[OrderModel.collection].find(query).sort('created_at', -1).limit(limit)
        return list(cursor)

    @staticmethod
    def delete(order_id):
        from bson.objectid import ObjectId
        mongo.db[OrderModel.collection].delete_one({'_id': ObjectId(order_id)})

    @staticmethod
    def to_dict(order):
        return {
            'id': str(order['_id']),
            'order_number': order.get('order_number'),
            'customer_name': order.get('customer_name'),
            'contact_name': order.get('contact_name', ''),
            'contact_email': order.get('contact_email', ''),
            'customer_address': order.get('customer_address', ''),
            'items': order.get('items', []),
            'subtotal': float(order.get('subtotal', 0)),
            'discount_percent': float(order.get('discount_percent', 0)),
            'discount_amount': float(order.get('discount_amount', 0)),
            'tax_percent': float(order.get('tax_percent', 0)),
            'tax_amount': float(order.get('tax_amount', 0)),
            'total': float(order.get('total', 0)),
            'status': order.get('status', 'pending'),
            'notes': order.get('notes', ''),
            'generated_invoice_id': str(order.get('generated_invoice_id')) if order.get('generated_invoice_id') else None,
            'generated_invoice_number': order.get('generated_invoice_number'),
            'company_id': str(order.get('company_id')) if order.get('company_id') else None,
            'created_by': str(order.get('created_by')) if order.get('created_by') else None,
            'created_at': order.get('created_at').isoformat() if order.get('created_at') else None,
        }

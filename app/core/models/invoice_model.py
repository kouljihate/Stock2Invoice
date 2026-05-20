from datetime import datetime, timezone
from app.extensions.db import mongo


class InvoiceModel:
    collection = 'invoices'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[InvoiceModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(invoice_id):
        from bson.objectid import ObjectId
        return mongo.db[InvoiceModel.collection].find_one({'_id': ObjectId(invoice_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[InvoiceModel.collection].count_documents(query)
        cursor = mongo.db[InvoiceModel.collection].find(query) \
            .sort('created_at', -1) \
            .skip((page - 1) * per_page) \
            .limit(per_page)
        return list(cursor), total

    @staticmethod
    def find_all_unpaginated(filters=None):
        query = filters or {}
        return list(mongo.db[InvoiceModel.collection].find(query))

    @staticmethod
    def update(invoice_id, data):
        from bson.objectid import ObjectId
        mongo.db[InvoiceModel.collection].update_one(
            {'_id': ObjectId(invoice_id)},
            {'$set': data},
        )

    @staticmethod
    def delete(invoice_id):
        from bson.objectid import ObjectId
        mongo.db[InvoiceModel.collection].delete_one({'_id': ObjectId(invoice_id)})

    @staticmethod
    def get_next_sequence():
        result = mongo.db.counters.find_one_and_update(
            {'_id': 'invoice_number'},
            {'$inc': {'seq': 1}},
            upsert=True,
            return_document=True,
        )
        return result['seq']

    @staticmethod
    def count(filters=None):
        return mongo.db[InvoiceModel.collection].count_documents(filters or {})

    @staticmethod
    def recent(limit=5, filters=None):
        query = filters or {}
        cursor = mongo.db[InvoiceModel.collection].find(query).sort('created_at', -1).limit(limit)
        return list(cursor)

    @staticmethod
    def to_dict(inv):
        return {
            'id': str(inv['_id']),
            'invoice_number': inv.get('invoice_number'),
            'customer_name': inv.get('customer_name'),
            'customer_email': inv.get('customer_email', ''),
            'customer_address': inv.get('customer_address', ''),
            'invoice_date': inv.get('invoice_date').isoformat() if inv.get('invoice_date') else None,
            'due_date': inv.get('due_date').isoformat() if inv.get('due_date') else None,
            'items': inv.get('items', []),
            'subtotal': float(inv.get('subtotal', 0)),
            'discount_percent': float(inv.get('discount_percent', 0)),
            'discount_amount': float(inv.get('discount_amount', 0)),
            'tax_percent': float(inv.get('tax_percent', 0)),
            'tax_amount': float(inv.get('tax_amount', 0)),
            'total': float(inv.get('total', 0)),
            'status': inv.get('status', 'draft'),
            'notes': inv.get('notes', ''),
            'company_id': str(inv.get('company_id')) if inv.get('company_id') else None,
            'created_by': str(inv.get('created_by')) if inv.get('created_by') else None,
            'created_at': inv.get('created_at').isoformat() if inv.get('created_at') else None,
        }

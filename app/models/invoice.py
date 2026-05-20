from datetime import datetime, timezone


class InvoiceModel:
    collection = 'invoices'

    @staticmethod
    def create(data):
        from app.extensions import mongo
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[InvoiceModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(invoice_id):
        from app.extensions import mongo
        from bson.objectid import ObjectId
        return mongo.db[InvoiceModel.collection].find_one({'_id': ObjectId(invoice_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        from app.extensions import mongo
        query = filters or {}
        total = mongo.db[InvoiceModel.collection].count_documents(query)
        cursor = mongo.db[InvoiceModel.collection].find(query) \
            .sort('created_at', -1) \
            .skip((page - 1) * per_page) \
            .limit(per_page)
        items = list(cursor)
        return items, total

    @staticmethod
    def update(invoice_id, data):
        from app.extensions import mongo
        from bson.objectid import ObjectId
        mongo.db[InvoiceModel.collection].update_one(
            {'_id': ObjectId(invoice_id)},
            {'$set': data}
        )

    @staticmethod
    def get_next_sequence():
        from app.extensions import mongo
        result = mongo.db.counters.find_one_and_update(
            {'_id': 'invoice_number'},
            {'$inc': {'seq': 1}},
            upsert=True,
            return_document=True,
        )
        return result['seq']

    @staticmethod
    def to_dict(inv):
        return {
            'id': str(inv['_id']),
            'invoice_number': inv.get('invoice_number'),
            'customer_name': inv.get('customer_name'),
            'customer_email': inv.get('customer_email', ''),
            'items': inv.get('items', []),
            'subtotal': float(inv.get('subtotal', 0)),
            'tax': float(inv.get('tax', 0)),
            'total': float(inv.get('total', 0)),
            'status': inv.get('status', 'draft'),
            'notes': inv.get('notes', ''),
            'created_by': str(inv.get('created_by')) if inv.get('created_by') else None,
            'created_at': inv.get('created_at').isoformat() if inv.get('created_at') else None,
        }

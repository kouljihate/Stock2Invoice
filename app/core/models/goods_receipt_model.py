from datetime import datetime, timezone
from app.extensions.db import mongo


class GoodsReceiptModel:
    collection = 'goods_receipts'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[GoodsReceiptModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(gr_id):
        from bson.objectid import ObjectId
        return mongo.db[GoodsReceiptModel.collection].find_one({'_id': ObjectId(gr_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[GoodsReceiptModel.collection].count_documents(query)
        cursor = mongo.db[GoodsReceiptModel.collection].find(query).sort('created_at', -1).skip((page - 1) * per_page).limit(per_page)
        return list(cursor), total

    @staticmethod
    def count(filters=None):
        return mongo.db[GoodsReceiptModel.collection].count_documents(filters or {})

    @staticmethod
    def update(gr_id, data):
        from bson.objectid import ObjectId
        mongo.db[GoodsReceiptModel.collection].update_one({'_id': ObjectId(gr_id)}, {'$set': data})

    @staticmethod
    def delete(gr_id):
        from bson.objectid import ObjectId
        mongo.db[GoodsReceiptModel.collection].delete_one({'_id': ObjectId(gr_id)})

    @staticmethod
    def to_dict(gr):
        return {
            'id': str(gr['_id']),
            'receipt_number': gr.get('receipt_number'),
            'po_id': str(gr.get('po_id')) if gr.get('po_id') else None,
            'po_number': gr.get('po_number', ''),
            'supplier_id': str(gr.get('supplier_id')) if gr.get('supplier_id') else None,
            'supplier_name': gr.get('supplier_name', ''),
            'items': gr.get('items', []),
            'notes': gr.get('notes', ''),
            'status': gr.get('status', 'waiting'),
            'company_id': str(gr.get('company_id')) if gr.get('company_id') else None,
            'created_by': str(gr.get('created_by')) if gr.get('created_by') else None,
            'created_at': gr.get('created_at').isoformat() if gr.get('created_at') else None,
        }
from datetime import datetime, timezone
from app.extensions.db import mongo


class PurchaseOrderModel:
    collection = 'purchase_orders'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[PurchaseOrderModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(po_id):
        from bson.objectid import ObjectId
        return mongo.db[PurchaseOrderModel.collection].find_one({'_id': ObjectId(po_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[PurchaseOrderModel.collection].count_documents(query)
        cursor = mongo.db[PurchaseOrderModel.collection].find(query).sort('created_at', -1).skip((page - 1) * per_page).limit(per_page)
        return list(cursor), total

    @staticmethod
    def update(po_id, data):
        from bson.objectid import ObjectId
        mongo.db[PurchaseOrderModel.collection].update_one({'_id': ObjectId(po_id)}, {'$set': data})

    @staticmethod
    def count(filters=None):
        return mongo.db[PurchaseOrderModel.collection].count_documents(filters or {})

    @staticmethod
    def to_dict(po):
        return {
            'id': str(po['_id']),
            'po_number': po.get('po_number'),
            'supplier_id': str(po.get('supplier_id')) if po.get('supplier_id') else None,
            'supplier_name': po.get('supplier_name', ''),
            'items': po.get('items', []),
            'subtotal': float(po.get('subtotal', 0)),
            'discount_percent': float(po.get('discount_percent', 0)),
            'discount_amount': float(po.get('discount_amount', 0)),
            'tax_percent': float(po.get('tax_percent', 0)),
            'tax_amount': float(po.get('tax_amount', 0)),
            'total': float(po.get('total', 0)),
            'status': po.get('status', 'draft'),
            'notes': po.get('notes', ''),
            'company_id': str(po.get('company_id')) if po.get('company_id') else None,
            'created_by': str(po.get('created_by')) if po.get('created_by') else None,
            'created_at': po.get('created_at').isoformat() if po.get('created_at') else None,
        }
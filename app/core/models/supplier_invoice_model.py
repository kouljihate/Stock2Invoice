from datetime import datetime, timezone
from app.extensions.db import mongo


class SupplierInvoiceModel:
    collection = 'supplier_invoices'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[SupplierInvoiceModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(inv_id):
        from bson.objectid import ObjectId
        return mongo.db[SupplierInvoiceModel.collection].find_one({'_id': ObjectId(inv_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[SupplierInvoiceModel.collection].count_documents(query)
        cursor = mongo.db[SupplierInvoiceModel.collection].find(query).sort('created_at', -1).skip((page - 1) * per_page).limit(per_page)
        return list(cursor), total

    @staticmethod
    def update(inv_id, data):
        from bson.objectid import ObjectId
        mongo.db[SupplierInvoiceModel.collection].update_one({'_id': ObjectId(inv_id)}, {'$set': data})

    @staticmethod
    def count(filters=None):
        return mongo.db[SupplierInvoiceModel.collection].count_documents(filters or {})

    @staticmethod
    def to_dict(inv):
        return {
            'id': str(inv['_id']),
            'invoice_number': inv.get('invoice_number'),
            'supplier_id': str(inv.get('supplier_id')) if inv.get('supplier_id') else None,
            'supplier_name': inv.get('supplier_name', ''),
            'po_id': str(inv.get('po_id')) if inv.get('po_id') else None,
            'po_number': inv.get('po_number', ''),
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
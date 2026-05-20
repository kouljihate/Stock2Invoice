from datetime import datetime, timezone
from app.extensions.db import mongo


class StockMovementModel:
    collection = 'stock_movements'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[StockMovementModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[StockMovementModel.collection].count_documents(query)
        cursor = mongo.db[StockMovementModel.collection].find(query) \
            .sort('created_at', -1) \
            .skip((page - 1) * per_page) \
            .limit(per_page)
        return list(cursor), total

    @staticmethod
    def recent(limit=10, filters=None):
        query = filters or {}
        cursor = mongo.db[StockMovementModel.collection].find(query).sort('created_at', -1).limit(limit)
        return list(cursor)

    @staticmethod
    def to_dict(mv):
        return {
            'id': str(mv['_id']),
            'product_id': str(mv.get('product_id')),
            'product_name': mv.get('product_name', ''),
            'sku': mv.get('sku', ''),
            'type': mv.get('type'),
            'quantity': mv.get('quantity', 0),
            'quantity_before': mv.get('quantity_before', 0),
            'quantity_after': mv.get('quantity_after', 0),
            'reason': mv.get('reason', ''),
            'reference': mv.get('reference', ''),
            'company_id': str(mv.get('company_id')) if mv.get('company_id') else None,
            'created_by': str(mv.get('created_by')) if mv.get('created_by') else None,
            'created_at': mv.get('created_at').isoformat() if mv.get('created_at') else None,
        }

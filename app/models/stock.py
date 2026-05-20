from datetime import datetime, timezone


class StockModel:
    collection = 'stocks'

    @staticmethod
    def create(data):
        from app.extensions import mongo
        data['created_at'] = datetime.now(timezone.utc)
        data['updated_at'] = datetime.now(timezone.utc)
        result = mongo.db[StockModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(stock_id):
        from app.extensions import mongo
        from bson.objectid import ObjectId
        return mongo.db[StockModel.collection].find_one({'_id': ObjectId(stock_id)})

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        from app.extensions import mongo
        query = filters or {}
        total = mongo.db[StockModel.collection].count_documents(query)
        cursor = mongo.db[StockModel.collection].find(query) \
            .sort('created_at', -1) \
            .skip((page - 1) * per_page) \
            .limit(per_page)
        items = list(cursor)
        return items, total

    @staticmethod
    def update(stock_id, data):
        from app.extensions import mongo
        from bson.objectid import ObjectId
        data['updated_at'] = datetime.now(timezone.utc)
        mongo.db[StockModel.collection].update_one(
            {'_id': ObjectId(stock_id)},
            {'$set': data}
        )

    @staticmethod
    def delete(stock_id):
        from app.extensions import mongo
        from bson.objectid import ObjectId
        mongo.db[StockModel.collection].delete_one({'_id': ObjectId(stock_id)})

    @staticmethod
    def to_dict(item):
        return {
            'id': str(item['_id']),
            'name': item.get('name'),
            'sku': item.get('sku'),
            'description': item.get('description', ''),
            'quantity': item.get('quantity', 0),
            'unit_price': float(item.get('unit_price', 0)),
            'category': item.get('category', ''),
            'created_at': item.get('created_at').isoformat() if item.get('created_at') else None,
            'updated_at': item.get('updated_at').isoformat() if item.get('updated_at') else None,
        }

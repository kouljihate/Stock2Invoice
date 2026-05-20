from datetime import datetime, timezone
from app.extensions.db import mongo


class ProductModel:
    collection = 'products'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        data['updated_at'] = datetime.now(timezone.utc)
        result = mongo.db[ProductModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(product_id):
        from bson.objectid import ObjectId
        return mongo.db[ProductModel.collection].find_one({'_id': ObjectId(product_id)})

    @staticmethod
    def find_by_sku(sku, company_id=None):
        query = {'sku': sku}
        if company_id:
            from bson.objectid import ObjectId
            query['company_id'] = ObjectId(company_id)
        return mongo.db[ProductModel.collection].find_one(query)

    @staticmethod
    def find_all(page=1, per_page=20, filters=None):
        query = filters or {}
        total = mongo.db[ProductModel.collection].count_documents(query)
        cursor = mongo.db[ProductModel.collection].find(query) \
            .sort('created_at', -1) \
            .skip((page - 1) * per_page) \
            .limit(per_page)
        return list(cursor), total

    @staticmethod
    def find_all_unpaginated(filters=None):
        query = filters or {}
        return list(mongo.db[ProductModel.collection].find(query))

    @staticmethod
    def update(product_id, data):
        from bson.objectid import ObjectId
        data['updated_at'] = datetime.now(timezone.utc)
        mongo.db[ProductModel.collection].update_one(
            {'_id': ObjectId(product_id)},
            {'$set': data},
        )

    @staticmethod
    def delete(product_id):
        from bson.objectid import ObjectId
        mongo.db[ProductModel.collection].delete_one({'_id': ObjectId(product_id)})

    @staticmethod
    def count(filters=None):
        return mongo.db[ProductModel.collection].count_documents(filters or {})

    @staticmethod
    def aggregate(pipeline):
        return list(mongo.db[ProductModel.collection].aggregate(pipeline))

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
            'tax_rate': float(item.get('tax_rate', 0)),
            'low_stock_threshold': int(item.get('low_stock_threshold', 5)),
            'company_id': str(item.get('company_id')) if item.get('company_id') else None,
            'created_at': item.get('created_at').isoformat() if item.get('created_at') else None,
            'updated_at': item.get('updated_at').isoformat() if item.get('updated_at') else None,
        }

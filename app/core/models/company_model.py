from datetime import datetime, timezone
from app.extensions.db import mongo


class CompanyModel:
    collection = 'companies'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        result = mongo.db[CompanyModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(company_id):
        from bson.objectid import ObjectId
        return mongo.db[CompanyModel.collection].find_one({'_id': ObjectId(company_id)})

    @staticmethod
    def find_by_slug(slug):
        return mongo.db[CompanyModel.collection].find_one({'slug': slug})

    @staticmethod
    def find_all():
        cursor = mongo.db[CompanyModel.collection].find().sort('name', 1)
        return list(cursor)

    @staticmethod
    def count():
        return mongo.db[CompanyModel.collection].count_documents({})

    @staticmethod
    def to_dict(c):
        return {
            'id': str(c['_id']),
            'name': c.get('name'),
            'slug': c.get('slug'),
            'created_at': c.get('created_at').isoformat() if c.get('created_at') else None,
        }

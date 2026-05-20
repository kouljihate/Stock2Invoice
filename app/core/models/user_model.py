from datetime import datetime, timezone
from app.extensions.db import mongo


class UserModel:
    collection = 'users'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        data['updated_at'] = datetime.now(timezone.utc)
        result = mongo.db[UserModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_email(email, company_id=None):
        query = {'email': email}
        if company_id:
            from bson.objectid import ObjectId
            query['company_id'] = ObjectId(company_id)
        return mongo.db[UserModel.collection].find_one(query)

    @staticmethod
    def find_by_id(user_id):
        from bson.objectid import ObjectId
        return mongo.db[UserModel.collection].find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def update(user_id, data):
        from bson.objectid import ObjectId
        data['updated_at'] = datetime.now(timezone.utc)
        mongo.db[UserModel.collection].update_one(
            {'_id': ObjectId(user_id)},
            {'$set': data},
        )

    @staticmethod
    def count(filters=None):
        return mongo.db[UserModel.collection].count_documents(filters or {})

    @staticmethod
    def find_by_company(company_id):
        from bson.objectid import ObjectId
        return list(mongo.db[UserModel.collection].find({'company_id': ObjectId(company_id)}))

    @staticmethod
    def to_dict(user):
        return {
            'id': str(user['_id']),
            'name': user.get('name'),
            'email': user.get('email'),
            'role': user.get('role', 'user'),
            'company_id': str(user.get('company_id')) if user.get('company_id') else None,
            'created_at': user.get('created_at').isoformat() if user.get('created_at') else None,
        }

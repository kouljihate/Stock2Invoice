from app.extensions.db import mongo
from datetime import datetime, timezone


class PermissionModel:
    collection = 'permissions'

    @staticmethod
    def create(data):
        data['created_at'] = datetime.now(timezone.utc)
        data['updated_at'] = datetime.now(timezone.utc)
        result = mongo.db[PermissionModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_name(name):
        return mongo.db[PermissionModel.collection].find_one({'name': name})

    @staticmethod
    def find_all():
        return list(mongo.db[PermissionModel.collection].find().sort('name', 1))

    @staticmethod
    def update(permission_id, data):
        from bson.objectid import ObjectId
        data['updated_at'] = datetime.now(timezone.utc)
        mongo.db[PermissionModel.collection].update_one(
            {'_id': ObjectId(permission_id)},
            {'$set': data},
        )

    @staticmethod
    def delete(permission_id):
        from bson.objectid import ObjectId
        mongo.db[PermissionModel.collection].delete_one({'_id': ObjectId(permission_id)})

    @staticmethod
    def to_dict(permission):
        return {
            'id': str(permission['_id']),
            'name': permission.get('name'),
            'description': permission.get('description'),
            'created_at': permission.get('created_at').isoformat() if permission.get('created_at') else None,
            'updated_at': permission.get('updated_at').isoformat() if permission.get('updated_at') else None,
        }
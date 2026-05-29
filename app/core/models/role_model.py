from app.extensions.db import mongo
from datetime import datetime, timezone


class RoleModel:
    collection = 'roles'

    @staticmethod
    def create(data):
        name = data.get('name', '')
        data['_id'] = name.lower()
        data['created_at'] = datetime.now(timezone.utc)
        data['updated_at'] = datetime.now(timezone.utc)
        result = mongo.db[RoleModel.collection].insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_name(name):
        return mongo.db[RoleModel.collection].find_one({'_id': name.lower()})

    @staticmethod
    def find_all():
        return list(mongo.db[RoleModel.collection].find().sort('name', 1))

    @staticmethod
    def update(role_name, data):
        data['updated_at'] = datetime.now(timezone.utc)
        mongo.db[RoleModel.collection].update_one(
            {'_id': role_name.lower()},
            {'$set': data},
        )

    @staticmethod
    def delete(role_name):
        mongo.db[RoleModel.collection].delete_one({'_id': role_name.lower()})

    @staticmethod
    def to_dict(role):
        return {
            'id': role['_id'],
            'name': role.get('name'),
            'description': role.get('description'),
            'permissions': role.get('permissions', []),
            'created_at': role.get('created_at').isoformat() if role.get('created_at') else None,
            'updated_at': role.get('updated_at').isoformat() if role.get('updated_at') else None,
        }

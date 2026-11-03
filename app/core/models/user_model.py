from datetime import datetime, timezone
from app.extensions.db import mongo
from app.core.utils.permissions import get_effective_permissions, has_permission


class UserModel:
    collection = 'users'

    @staticmethod
    def create(data):
        # Set default values for new fields if not provided
        if 'roles' not in data:
            data['roles'] = []  # Will be set to default role after roles are created
            
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
    def count_admins(exclude_id=None):
        """Number of accounts holding the single platform 'Admin' profile."""
        query = {'roles': 'Admin'}
        if exclude_id:
            from bson.objectid import ObjectId
            query['_id'] = {'$ne': ObjectId(exclude_id)}
        return mongo.db[UserModel.collection].count_documents(query)

    @staticmethod
    def find_by_company(company_id):
        from bson.objectid import ObjectId
        return list(mongo.db[UserModel.collection].find({'company_id': ObjectId(company_id)}))

    @staticmethod
    def find_all(search=None):
        query = {}
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}},
            ]
        return list(mongo.db[UserModel.collection].find(query).sort('created_at', -1))

    @staticmethod
    def _role_permissions(role_names):
        """Effective permissions for a set of role names.

        Cached on the request when there is one: list views call ``to_dict``
        once per row, which would otherwise repeat the same roles query N
        times per render.
        """
        if not role_names:
            return []
        cache_key = tuple(sorted(role_names))
        from flask import has_request_context, g
        if has_request_context():
            cache = getattr(g, '_role_perm_cache', None)
            if cache is None:
                cache = {}
                g._role_perm_cache = cache
            if cache_key in cache:
                return cache[cache_key]
        roles = list(mongo.db['roles'].find(
            {'_id': {'$in': [n.lower() for n in role_names]}}))
        permissions = []
        for role in roles:
            perms = role.get('permissions', [])
            if perms:
                permissions.extend(perms)
        if has_request_context():
            cache[cache_key] = permissions
        return permissions

    @staticmethod
    def to_dict(user):
        # Get roles and permissions
        role_names = user.get('roles', [])
        effective_permissions = get_effective_permissions(
            UserModel._role_permissions(role_names))

        return {
            'id': str(user['_id']),
            'name': user.get('name'),
            'email': user.get('email'),
            'roles': role_names,
            'role_names': role_names,
            'permissions': effective_permissions,
            'company_id': str(user.get('company_id')) if user.get('company_id') else None,
            'primary_font_size': user.get('primary_font_size', 'medium'),
            'arabic_font_size': user.get('arabic_font_size', 'medium'),
            'created_at': user.get('created_at').isoformat() if user.get('created_at') else None,
        }

    @staticmethod
    def has_perm(user, permission):
        if not user:
            return False
        if isinstance(user, dict):
            role_names = user.get('roles', [])
        else:
            role_names = getattr(user, 'roles', [])
        if not role_names:
            return False
        return has_permission(UserModel._role_permissions(role_names), permission)

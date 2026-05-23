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
    def update(company_id, data):
        from bson.objectid import ObjectId
        mongo.db[CompanyModel.collection].update_one(
            {'_id': ObjectId(company_id)},
            {'$set': data},
        )

    @staticmethod
    def delete(company_id):
        from bson.objectid import ObjectId
        mongo.db[CompanyModel.collection].delete_one({'_id': ObjectId(company_id)})

    @staticmethod
    def to_dict(c):
        return {
            'id': str(c['_id']),
            'name': c.get('name'),
            'slug': c.get('slug'),
            'logo': c.get('logo'),
            'address': c.get('address'),
            'city': c.get('city'),
            'phone': c.get('phone'),
            'email': c.get('email'),
            'contact_name': c.get('contact_name'),
            'ice': c.get('ice'),
            'rc': c.get('rc'),
            'if_tax': c.get('if_tax'),
            'cnss': c.get('cnss'),
            'patente': c.get('patente'),
            'rib': c.get('rib', ''),
            'tp': c.get('tp', c.get('patente', '')),
            'website': c.get('website'),
            'invoice_template': c.get('invoice_template', {}),
            'created_at': c.get('created_at').isoformat() if c.get('created_at') else None,
        }

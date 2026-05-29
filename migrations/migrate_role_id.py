from app import create_app
from app.extensions.db import mongo

app = create_app()
with app.app_context():
    roles = list(mongo.db.roles.find({}))
    for role in roles:
        old_id = role['_id']
        name = role.get('name', '')
        new_id = name.lower()
        if str(old_id) != new_id:
            role['_id'] = new_id
            mongo.db.roles.insert_one(role)
            from bson.objectid import ObjectId
            mongo.db.roles.delete_one({'_id': ObjectId(old_id)})
            print(f'Migrated: {old_id} -> {new_id} ({name})')
        else:
            print(f'Skipped {name} (_id already correct)')

    print('\nVerification:')
    for r in mongo.db.roles.find({}, {'_id': 1, 'name': 1, 'permissions': 1}):
        print(f'  _id={r["_id"]}, name={r["name"]}, perms={r["permissions"]}')

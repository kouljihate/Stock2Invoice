from app import create_app
from app.extensions.db import mongo

app = create_app()
with app.app_context():
    mongo.db.users.update_one({'email': 'admin@si.ma'}, {'$set': {'roles': ['Admin']}})
    mongo.db.users.update_one({'email': 'kouljihate@gmail.com'}, {'$set': {'roles': ['Manager']}})
    mongo.db.users.update_many({'email': {'$regex': '^admin_'}}, {'$set': {'roles': ['Manager']}})
    mongo.db.users.update_many({'email': {'$regex': '@test.ma$'}}, {'$set': {'roles': ['Manager']}})
    print('Done')
    for u in mongo.db.users.find({}, {'email': 1, 'roles': 1}):
        print(f'{u["email"]}: {u["roles"]}')

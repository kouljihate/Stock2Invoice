from app import create_app
from app.extensions.db import mongo
from datetime import datetime, timezone

app = create_app()
with app.app_context():
    # Add new permissions
    new_perms = ['eshop.administration', 'eshop.link']
    for perm_name in new_perms:
        existing = mongo.db.permissions.find_one({'name': perm_name})
        if not existing:
            mongo.db.permissions.insert_one({
                'name': perm_name,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
            })
            print(f'Created permission: {perm_name}')

    # Update Admin (already has '*', but add eshop permits explicitly too)
    admin_role = mongo.db.roles.find_one({'name': 'Admin'})
    if admin_role:
        perms = admin_role.get('permissions', [])
        if '*' not in perms:
            perms.extend(new_perms)
            mongo.db.roles.update_one({'name': 'Admin'}, {'$set': {'permissions': perms}})
            print('Updated Admin role')

    # Update Manager
    manager_role = mongo.db.roles.find_one({'name': 'Manager'})
    if manager_role:
        perms = manager_role.get('permissions', [])
        for p in new_perms:
            if p not in perms:
                perms.append(p)
        mongo.db.roles.update_one({'name': 'Manager'}, {'$set': {'permissions': perms}})
        print('Updated Manager role')

    # Update Cashier
    cashier_role = mongo.db.roles.find_one({'name': 'Cashier'})
    if cashier_role:
        perms = cashier_role.get('permissions', [])
        if 'eshop.link' not in perms:
            perms.append('eshop.link')
        mongo.db.roles.update_one({'name': 'Cashier'}, {'$set': {'permissions': perms}})
        print('Updated Cashier role')

    # Update Customer
    customer_role = mongo.db.roles.find_one({'name': 'Customer'})
    if customer_role:
        perms = customer_role.get('permissions', [])
        if 'eshop.link' not in perms:
            perms.append('eshop.link')
        mongo.db.roles.update_one({'name': 'Customer'}, {'$set': {'permissions': perms}})
        print('Updated Customer role')

    print('Done')
    for r in mongo.db.roles.find({}, {'name': 1, 'permissions': 1}):
        print(f'{r["name"]}: {r["permissions"]}')

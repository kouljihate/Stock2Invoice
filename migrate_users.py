from app import create_app
from app.extensions.db import mongo

app = create_app()
with app.app_context():
    # Update all existing users to have the new fields
    users = mongo.db.users.find({})
    updated_count = 0
    
    for user in users:
        update_data = {}
        
        # Ensure role is a list
        if 'role' not in user or not isinstance(user['role'], list):
            if user.get('role') == 'super_admin':
                update_data['role'] = ['super_admin']
            elif user.get('role') == 'company_admin':
                update_data['role'] = ['company_admin']
            else:
                update_data['role'] = ['user']
        
        # Ensure access is a list with default values
        if 'access' not in user or not isinstance(user['access'], list):
            if user.get('role') == 'super_admin' or (isinstance(user.get('role'), list) and 'super_admin' in user.get('role', [])):
                update_data['access'] = ['P2P', 'Q2C', 'EShop', 'Full']
            elif user.get('role') == 'company_admin' or (isinstance(user.get('role'), list) and 'company_admin' in user.get('role', [])):
                update_data['access'] = ['P2P', 'Q2C', 'EShop']
            else:
                update_data['access'] = ['Guest']
        
        # Special case for allchemwater@gmail.com - should only see Q2C and General
        if user.get('email') == 'allchemwater@gmail.com':
            update_data['role'] = ['user']
            update_data['access'] = ['Q2C', 'Guest']
        
        if update_data:
            mongo.db.users.update_one(
                {'_id': user['_id']},
                {'$set': update_data}
            )
            updated_count += 1
            print('Updated user:', user.get('email'), 'with role:', update_data.get('role', user.get('role')), 'and access:', update_data.get('access', user.get('access')))
    
    print('Total users updated:', updated_count)
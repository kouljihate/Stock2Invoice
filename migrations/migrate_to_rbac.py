from app import create_app
from app.extensions.db import mongo
from app.core.models.permission_model import PermissionModel
from app.core.models.role_model import RoleModel
from app.core.models.user_model import UserModel
from bson.objectid import ObjectId
from datetime import datetime, timezone

app = create_app()
with app.app_context():
    print("Starting migration to RBAC...")
    
    # 1. Create permissions
    permissions_data = [
        # Product permissions
        {'name': 'product.view', 'description': 'View products'},
        {'name': 'product.edit', 'description': 'Edit products'},
        {'name': 'product.create', 'description': 'Create products'},
        {'name': 'product.delete', 'description': 'Delete products'},
        
        # Order permissions
        {'name': 'order.view', 'description': 'View orders'},
        {'name': 'order.edit', 'description': 'Edit orders'},
        {'name': 'order.create', 'description': 'Create orders'},
        {'name': 'order.delete', 'description': 'Delete orders'},
        
        # Invoice permissions
        {'name': 'invoice.view', 'description': 'View invoices'},
        {'name': 'invoice.edit', 'description': 'Edit invoices'},
        {'name': 'invoice.create', 'description': 'Create invoices'},
        {'name': 'invoice.delete', 'description': 'Delete invoices'},
        
        # Stock permissions
        {'name': 'stock.view', 'description': 'View stock'},
        {'name': 'stock.edit', 'description': 'Edit stock'},
        {'name': 'stock.adjust', 'description': 'Adjust stock levels'},
        
        # Service permissions
        {'name': 'service.view', 'description': 'View services'},
        {'name': 'service.edit', 'description': 'Edit services'},
        {'name': 'service.create', 'description': 'Create services'},
        {'name': 'service.delete', 'description': 'Delete services'},
        
        # Settings permissions
        {'name': 'settings.view', 'description': 'View settings'},
        {'name': 'settings.edit', 'description': 'Edit settings'},
        
        # Additional permissions
        {'name': 'user.view', 'description': 'View users'},
        {'name': 'user.edit', 'description': 'Edit users'},
        {'name': 'user.create', 'description': 'Create users'},
        {'name': 'user.delete', 'description': 'Delete users'},
    ]
    
    permission_ids = {}
    for perm_data in permissions_data:
        existing = PermissionModel.find_by_name(perm_data['name'])
        if not existing:
            perm_id = PermissionModel.create(perm_data)
            permission_ids[perm_data['name']] = perm_id
            print(f"Created permission: {perm_data['name']}")
        else:
            permission_ids[perm_data['name']] = str(existing['_id'])
            print(f"Permission already exists: {perm_data['name']}")
    
    # 2. Create roles with permissions
    roles_data = [
        {
            'name': 'Admin',
            'description': 'System administrator with full access',
            'permissions': list(permission_ids.values())  # All permissions
        },
        {
            'name': 'Manager',
            'description': 'Manager with access to most business operations',
            'permissions': [
                permission_ids['product.view'], permission_ids['product.edit'], permission_ids['product.create'],
                permission_ids['order.view'], permission_ids['order.edit'], permission_ids['order.create'],
                permission_ids['invoice.view'], permission_ids['invoice.edit'], permission_ids['invoice.create'],
                permission_ids['stock.view'], permission_ids['stock.edit'], permission_ids['stock.adjust'],
                permission_ids['service.view'], permission_ids['service.edit'], permission_ids['service.create'],
                permission_ids['settings.view']
            ]
        },
        {
            'name': 'Cashier',
            'description': 'Cashier focused on sales and payments',
            'permissions': [
                permission_ids['product.view'],
                permission_ids['order.view'], permission_ids['order.create'],
                permission_ids['invoice.view'], permission_ids['invoice.create'],
                # Assuming we have payment permissions - add if needed
                permission_ids['service.view'], permission_ids['service.create']
            ]
        },
        {
            'name': 'Technician',
            'description': 'Technician handling products and services',
            'permissions': [
                permission_ids['product.view'], permission_ids['product.edit'],
                permission_ids['stock.view'], permission_ids['stock.adjust'],
                permission_ids['service.view'], permission_ids['service.edit']
            ]
        },
        {
            'name': 'Customer',
            'description': 'Customer with limited access to view own data',
            'permissions': [
                permission_ids['product.view'],
                permission_ids['order.view'],  # In a real system, this would be restricted to own orders
                permission_ids['invoice.view'],  # Restricted to own invoices
                permission_ids['service.view']
            ]
        }
    ]
    
    role_ids = {}
    for role_data in roles_data:
        # Convert permission names to ObjectIds
        perm_object_ids = [ObjectId(pid) for pid in role_data['permissions']]
        role_data['permissions'] = perm_object_ids
        
        existing = RoleModel.find_by_name(role_data['name'])
        if not existing:
            role_id = RoleModel.create(role_data)
            role_ids[role_data['name']] = role_id
            print(f"Created role: {role_data['name']}")
        else:
            # Update existing role with permissions
            RoleModel.update(str(existing['_id']), {'permissions': perm_object_ids})
            role_ids[role_data['name']] = str(existing['_id'])
            print(f"Role already exists, updated permissions: {role_data['name']}")
    
    # 3. Update existing users
    users = mongo.db.users.find({})
    updated_count = 0
    
    for user in users:
        update_data = {}
        
        # Determine role based on existing role and access
        role_name = 'Customer'  # Default role
        
        # Check if user has super_admin role or Full access
        user_role = user.get('role')
        user_access = user.get('access', [])
        
        # Handle both string and list formats for backward compatibility
        if isinstance(user_role, str):
            user_role = [user_role] if user_role else []
        if not isinstance(user_access, list):
            user_access = []
            
        # Map old roles/access to new roles
        if 'super_admin' in user_role or 'Full' in user_access:
            role_name = 'Admin'
        elif 'company_admin' in user_role or ('P2P' in user_access and 'Q2C' in user_access and 'EShop' in user_access):
            role_name = 'Manager'
        elif 'user' in user_role:
            role_name = 'Customer'  # Default for regular users
        else:
            role_name = 'Customer'  # Default fallback
            
        # Get the role ObjectId
        role_object_id = ObjectId(role_ids[role_name])
        update_data['role_ids'] = [role_object_id]
        
        # Remove old fields (optional, but clean)
        update_data['$unset'] = {'role': '', 'access': ''}
        
        # Update the user
        if update_data:
            mongo.db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'role_ids': [role_object_id]}, '$unset': {'role': '', 'access': ''}}
            )
            updated_count += 1
            print(f'Updated user: {user.get("email")} -> role: {role_name}')
    
    print(f'Total users updated: {updated_count}')
    print('Migration to RBAC completed!')
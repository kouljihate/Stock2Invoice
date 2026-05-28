from app import create_app
from app.extensions.db import mongo
from datetime import datetime, timezone

app = create_app()
with app.app_context():
    print("Starting RBAC v2 migration...")

    # 1. Clear old permissions and roles
    mongo.db.permissions.delete_many({})
    mongo.db.roles.delete_many({})

    # 2. Create new permissions
    all_permissions = [
        'product.view', 'product.create', 'product.edit', 'product.delete', 'product.price_edit',
        'order.view', 'order.create', 'order.edit', 'order.cancel', 'order.view_own',
        'invoice.view', 'invoice.create', 'invoice.refund', 'invoice.view_own',
        'stock.view', 'stock.adjust', 'stock.transfer', 'stock.audit',
        'service.view', 'service.create', 'service.schedule', 'service.close',
        'user.view', 'user.manage', 'role.manage', 'settings.update',
    ]

    for perm_name in all_permissions:
        mongo.db.permissions.insert_one({
            'name': perm_name,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
        })
    print(f"Created {len(all_permissions)} permissions")

    # 3. Create roles with permissions (using wildcards)
    roles_data = [
        {
            'name': 'Admin',
            'description': 'Full system access',
            'permissions': ['*'],
        },
        {
            'name': 'Manager',
            'description': 'Manages day-to-day operations',
            'permissions': [
                'product.view', 'product.create', 'product.edit', 'product.delete', 'product.price_edit',
                'order.*',
                'invoice.*',
                'stock.view', 'stock.adjust', 'stock.transfer',
                'service.view', 'service.create', 'service.schedule',
                'user.view', 'user.manage',
                'settings.update',
            ],
        },
        {
            'name': 'Cashier',
            'description': 'Handles sales and payments',
            'permissions': [
                'product.view',
                'order.*',
                'invoice.*',
                'stock.view',
                'service.view', 'service.create',
            ],
        },
        {
            'name': 'Technician',
            'description': 'Performs service interventions',
            'permissions': [
                'product.view',
                'order.view',
                'stock.view', 'stock.adjust',
                'service.*',
            ],
        },
        {
            'name': 'Customer',
            'description': 'Can browse products and place orders',
            'permissions': [
                'product.view',
                'order.create', 'order.view_own',
                'invoice.view_own',
            ],
        },
    ]

    for role_data in roles_data:
        mongo.db.roles.insert_one({
            'name': role_data['name'],
            'description': role_data['description'],
            'permissions': role_data['permissions'],
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
        })
        print(f"Created role: {role_data['name']}")

    # 4. Update existing users to use 'roles' array with role name strings
    users = mongo.db.users.find({})
    updated_count = 0
    for user in users:
        # Try to get old role_ids or role field to determine new roles
        old_role_ids = user.get('role_ids') or []
        old_role = user.get('role') or ''
        old_access = user.get('access') or []

        # Determine new roles based on old data
        new_roles = ['Customer']  # Default

        if isinstance(old_role, list) and len(old_role) > 0:
            old_role = old_role[0] if old_role else ''
        if not isinstance(old_role, str):
            old_role = ''

        if old_role == 'super_admin' or 'Full' in (old_access if isinstance(old_access, list) else []):
            new_roles = ['Admin']
        elif old_role == 'company_admin' or ('P2P' in (old_access if isinstance(old_access, list) else []) and 'Q2C' in (old_access if isinstance(old_access, list) else [])):
            new_roles = ['Manager']
        elif old_role == 'user':
            new_roles = ['Customer']
        elif old_role == 'guest':
            new_roles = ['Customer']

        # If user has allchemwater email, give Customer role (which only has limited perms)
        if user.get('email') == 'allchemwater@gmail.com':
            new_roles = ['Customer']

        # Update user: set roles, remove old fields
        mongo.db.users.update_one(
            {'_id': user['_id']},
            {
                '$set': {'roles': new_roles},
                '$unset': {'role_ids': '', 'role': '', 'access': '', 'role_names': ''},
            }
        )
        updated_count += 1
        print(f"Updated user: {user.get('email')} -> roles: {new_roles}")

    print(f"Total users updated: {updated_count}")
    print("RBAC v2 migration completed!")

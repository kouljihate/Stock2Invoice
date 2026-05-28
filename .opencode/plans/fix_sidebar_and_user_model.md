# Fix Sidebar Template Syntax Error and User Model Updates

## Issues to Fix

1. **Sidebar Template Syntax Error**: Duplicate closing tags in sidebar.html causing Jinja2 template syntax error
2. **User Model Updates**: Add role and access fields to support flexible permissions
3. **Sidebar Logic Update**: Replace hardcoded email check with role/access based logic
4. **Admin Forms Update**: Update user creation/edit forms to handle role/access as checkboxes
5. **Data Migration**: Update existing users with appropriate role/access values

## Detailed Fixes

### 1. Fix Sidebar Template Syntax Error
Remove the duplicate closing tags at the end of sidebar.html (lines 170-175) that are causing the Jinja2 syntax error.

### 2. Update UserModel
- Add default values for role (list) and access (list) fields in create() method
- Update to_dict() method to return the new fields
- Role options: ['super_admin', 'company_admin', 'user', 'guest']
- Access options: ['P2P', 'Q2C', 'EShop', 'Full', 'Guest']

### 3. Update Sidebar Logic
Replace the hardcoded email check for 'allchemwater@gmail.com' with logic that checks user's role and access fields:
- If user has 'Q2C' in access AND does NOT have 'P2P' or 'EShop' in access, show only Q2C and General modules
- Otherwise, show all modules based on standard permissions

### 4. Update Admin Forms
- Modify admin/edit_user.html to use checkboxes for role and access fields
- Add validation to ensure at least one role and one access level is selected
- Update the edit_user route in admin/routes.py to handle checkbox arrays

### 5. Data Migration
Create and run a script to update existing users:
- Super admins: role=['super_admin'], access=['P2P', 'Q2C', 'EShop', 'Full']
- Company admins: role=['company_admin'], access=['P2P', 'Q2C', 'EShop']
- Regular users: role=['user'], access=['Guest']
- For user 'allchemwater@gmail.com': role=['user'], access=['Q2C', 'Guest']

## Implementation Steps

1. Fix sidebar.html template syntax by removing duplicate tags
2. Update UserModel.py with new fields and default values
3. Update admin/routes.py to handle checkbox arrays for role/access
4. Update admin/edit_user.html to use checkboxes
5. Create and run migration script to update existing users
6. Test login with allchemwater@gmail.com to verify they only see Q2C and General modules
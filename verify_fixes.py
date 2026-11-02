"""Verification harness for the security fixes.

Uses the Flask test client so no server or credentials are needed; the acting
user is established with a signed access cookie produced by the app itself.
Any temporary database change is restored at the end.
"""

import re
import sys
from datetime import datetime, timezone

from bson.objectid import ObjectId
from flask import make_response
from flask_jwt_extended import create_access_token, set_access_cookies

from app import app
from app.extensions.db import bcrypt, mongo

results = []


def check(name, ok, detail=''):
    results.append((ok, name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}{'  -> ' + detail if detail else ''}")


def cookies_for(identity, role_names, company_id=None):
    """Signed access + csrf cookies for ``identity``, exactly as login sets them."""
    claims = {'role_names': role_names, 'user_name': 'Verify', 'user_email': 'v@x'}
    if company_id:
        claims['company_id'] = str(company_id)
    with app.app_context():
        token = create_access_token(identity=identity, additional_claims=claims)
        resp = make_response()
        set_access_cookies(resp, token)
        jar = {}
        for header in resp.headers.getlist('Set-Cookie'):
            m = re.match(r'([^=]+)=([^;]*)', header)
            if m:
                jar[m.group(1)] = m.group(2)
    return jar


def client_with(jar):
    c = app.test_client()
    for k, v in jar.items():
        try:
            c.set_cookie(k, v)
        except TypeError:  # older Flask signature
            c.set_cookie('localhost', k, v)
    return c


HTML = {'Accept': 'text/html,application/xhtml+xml'}

# --------------------------------------------------------------------------
# Save state we may temporarily change
# --------------------------------------------------------------------------
users = mongo.db['users']
admin_doc = users.find_one({'email': 'admin@stc.ma'})
member_doc = users.find_one({'email': 'kouljihate@gmail.com'})
original_member_company = member_doc.get('company_id')
admin_hash_before = admin_doc['password']

# --------------------------------------------------------------------------
# A. Unauthenticated
# --------------------------------------------------------------------------
c = app.test_client()

r = c.get('/web/invoices/', headers=HTML)
check('anonymous deep link redirects to login', r.status_code == 302 and '/web/auth/login' in r.headers.get('Location', ''), f'{r.status_code} {r.headers.get("Location")}')

r = c.get('/web/auth/register', headers=HTML)
check('public registration is disabled', r.status_code == 302 and '/web/auth/login' in r.headers.get('Location', ''), f'{r.status_code} {r.headers.get("Location")}')

r = c.post('/web/auth/login', data={'reset_admin_password': '1', 'email': 'admin@si.ma'}, headers=HTML)
after = users.find_one({'email': 'admin@stc.ma'})['password']
r2 = c.post('/web/auth/login', data={'reset_admin_password': '1', 'email': admin_doc['email']}, headers=HTML)
after2 = users.find_one({'email': admin_doc['email']})['password']
check('admin password-reset backdoor is gone',
      after == admin_hash_before and after2 == admin_hash_before
      and 'admin123' not in r2.get_data(as_text=True),
      'password hash unchanged, no reset confirmation in response')

r = c.get('/definitely/not/a/route', headers=HTML)
body = r.get_data(as_text=True)
check('404 page is generic', r.status_code == 404 and 'SCRIPT:' not in body and 'Traceback' not in body)

# --------------------------------------------------------------------------
# B. Super admin (no company)
# --------------------------------------------------------------------------
admin_jar = cookies_for(str(admin_doc['_id']), ['Admin'])
ac = client_with(admin_jar)

r = ac.get('/admin/', headers=HTML)
check('super admin reaches /admin', r.status_code == 200, str(r.status_code))

r = ac.get('/web/invoices/', headers=HTML)
check('company-less account is refused tenant routes',
      r.status_code == 302 and '/web/dashboard/' in r.headers.get('Location', ''),
      f'{r.status_code} {r.headers.get("Location")}')

r = ac.get('/web/dashboard/', headers=HTML)
check('company-less account still sees its dashboard', r.status_code == 200, str(r.status_code))

# --------------------------------------------------------------------------
# C. Ordinary user, bound to a company
# --------------------------------------------------------------------------
company_id = ObjectId()
users.update_one({'_id': member_doc['_id']}, {'$set': {'company_id': company_id}})
member_jar = cookies_for(str(member_doc['_id']), ['Customer'], company_id)
mc = client_with(member_jar)

r = mc.get('/web/invoices/', headers=HTML)
check('tenant-scoped list renders for a company user', r.status_code == 200, str(r.status_code))

r = mc.get('/web/stock/', headers=HTML)
check('stock list renders for a company user', r.status_code == 200, str(r.status_code))

# Cross-tenant: an invoice belonging to a different company must not load
other_company = ObjectId()
inv_id = mongo.db['invoices'].insert_one({
    'invoice_number': 'IV-VERIFY-DELETE-ME',
    'customer_name': 'Verification Fixture',
    'items': [], 'subtotal': 0, 'total': 0, 'status': 'draft',
    'company_id': other_company, 'created_at': datetime.now(timezone.utc),
}).inserted_id
r = mc.get(f'/web/invoices/{inv_id}', headers=HTML)
check('invoice from another company is not readable', r.status_code == 302,
      f'{r.status_code} -> {r.headers.get("Location")}')
mongo.db['invoices'].delete_one({'_id': inv_id})

r = mc.get('/admin/', headers=HTML)
check('non-admin is rejected from /admin', r.status_code == 403, str(r.status_code))

# A valid CSRF token on both, so a 403 can only come from the permission gate.
csrf_m = member_jar.get('csrf_access_token')
r = mc.post('/web/users/create', data={'email': 'x@y.z', 'password': 'aaaa1111', 'name': 'X', 'csrf_token': csrf_m}, headers=HTML)
check('permission gate blocks user.manage for Customer', r.status_code == 403, str(r.status_code))

r = mc.post(f'/web/users/{member_doc["_id"]}/set-role', data={'role': 'user', 'csrf_token': csrf_m}, headers=HTML)
check('permission gate blocks set-role for Customer', r.status_code == 403, str(r.status_code))

# D. 500 page must not leak internals
r = mc.get('/web/invoices/not-a-valid-objectid', headers=HTML)
body = r.get_data(as_text=True)
check('500 page does not leak script/line details',
      r.status_code == 500 and 'SCRIPT:' not in body and 'FUNCTION:' not in body and 'Traceback' not in body,
      f'status={r.status_code}')

# E. CSRF — using an endpoint this role *is* allowed to reach, so a 403 can
# only come from the CSRF gate and never from the permission gate.
CSRF_FORM = {'name': 'CSRF-VERIFY-DELETE-ME', 'email': 'not-a-valid-email'}
r = mc.post('/web/customers/create', data=dict(CSRF_FORM), headers=HTML)
body = r.get_data(as_text=True)
check('cookie-authenticated POST without CSRF token is rejected',
      r.status_code == 403 and 'token' in body.lower(),
      f'status={r.status_code}')

csrf = member_jar.get('csrf_access_token')
r = mc.post('/web/customers/create', data=dict(CSRF_FORM, csrf_token=csrf), headers=HTML)
check('POST with the CSRF token passes the CSRF gate',
      r.status_code not in (400, 401, 403), f'status={r.status_code}')

mongo.db['customers'].delete_many({'name': 'CSRF-VERIFY-DELETE-ME'})

# --------------------------------------------------------------------------
# G. Profiles & first-login onboarding (Admin / PME-Admin)
# --------------------------------------------------------------------------
from app.core.utils.bootstrap import ROLE_DEFINITIONS

check('both profiles exist in the role seed',
      'Admin' in ROLE_DEFINITIONS and 'PME-Admin' in ROLE_DEFINITIONS,
      ', '.join(ROLE_DEFINITIONS))

pme_role = mongo.db['roles'].find_one({'_id': 'pme-admin'})
check('PME-Admin role written to the database with tenant permissions',
      pme_role is not None and pme_role.get('permissions')
      and 'general.companies' not in pme_role['permissions'],
      f"{len(pme_role.get('permissions', [])) if pme_role else 0} permissions")

# A fresh company-less PME-Admin, exactly as the admin panel creates one.
temp_pme_email = 'verify-pme@localhost'
users.delete_one({'email': temp_pme_email})
from app.extensions.db import bcrypt as _bcrypt
pme_id = users.insert_one({
    'name': 'Verify PME', 'email': temp_pme_email,
    'password': _bcrypt.generate_password_hash('TempPass123!').decode('utf-8'),
    'roles': ['PME-Admin'], 'created_at': datetime.now(timezone.utc),
}).inserted_id

# The single-Admin guards need at least one Admin in the database.
made_admin = None
if not users.count_documents({'roles': 'Admin'}):
    made_admin = users.insert_one({
        'name': 'Verify Admin', 'email': 'verify-admin@localhost',
        'password': _bcrypt.generate_password_hash('TempPass123!').decode('utf-8'),
        'roles': ['Admin'], 'created_at': datetime.now(timezone.utc),
    }).inserted_id

runner = app.test_cli_runner()
res = runner.invoke(args=['promote', temp_pme_email, 'Admin'])
admins_before = users.count_documents({'roles': 'Admin'})
check('promote refuses to create a second Admin',
      'Exactly one Admin' in res.output and admins_before == 1,
      (res.output or '').strip()[:70])

res = runner.invoke(args=['create-super-admin', 'verify-second@localhost', 'TempPass123!'])
check('create-super-admin refuses when an Admin exists',
      'ERROR' in res.output and 'already exists' in res.output,
      (res.output or '').strip()[:70])

pme_jar = cookies_for(str(pme_id), ['PME-Admin'])
pc = client_with(pme_jar)

r = pc.get('/web/dashboard/', headers=HTML)
check('company-less PME-Admin is sent to first-login setup',
      r.status_code == 302 and '/web/profile/setup' in r.headers.get('Location', ''),
      f'{r.status_code} -> {r.headers.get("Location")}')

r = pc.get('/web/stock/', headers=HTML)
check('tenant routes divert to setup, not to an empty store',
      r.status_code == 302 and '/web/profile/setup' in r.headers.get('Location', ''),
      f'{r.status_code} -> {r.headers.get("Location")}')

r = pc.get('/web/profile/setup', headers=HTML)
check('setup wizard renders', r.status_code == 200, str(r.status_code))

r = pc.post('/web/profile/setup', data={
    'name': 'Verify PME Owner', 'phone': '+212600000001',
    'company_name': 'VERIFY PME SETUP',
    'address': '1 Rue de la Verification', 'city': 'Casablanca',
    'company_phone': '+212500000001', 'company_email': 'owner@localhost',
    'contact_name': '', 'website': '', 'ice': '', 'rc': '', 'if_tax': '',
    'cnss': '', 'patente': '', 'csrf_token': pme_jar.get('csrf_access_token'),
}, headers=HTML)
check('wizard completes and redirects to the dashboard',
      r.status_code == 302 and '/web/dashboard' in r.headers.get('Location', ''),
      f'{r.status_code} -> {r.headers.get("Location")}')

pme_after = users.find_one({'_id': pme_id})
company = (mongo.db['companies'].find_one({'_id': pme_after['company_id']})
           if pme_after.get('company_id') else None)
check('company created and linked to the PME-Admin',
      company is not None and company.get('name') == 'VERIFY PME SETUP'
      and company.get('slug'),
      company.get('name') if company else 'no company')

r = pc.get('/web/stock/', headers=HTML)
check('after setup the tenant area opens for the owner',
      r.status_code == 200, str(r.status_code))

r = pc.get('/web/profile/setup', headers=HTML)
check('setup never re-runs once complete',
      r.status_code == 302 and '/web/profile/setup' not in r.headers.get('Location', ''),
      f'{r.status_code} -> {r.headers.get("Location")}')

# The admin panel must not be able to mint a second Admin either.
r = ac.post(f'/admin/users/{pme_id}/edit',
            data={'name': 'Verify PME', 'email': temp_pme_email,
                  'roles': ['Admin'],
                  'csrf_token': admin_jar.get('csrf_access_token')},
            headers=HTML)
check('admin panel refuses to grant the Admin profile to a second user',
      users.find_one({'_id': pme_id})['roles'] == ['PME-Admin'],
      f'status={r.status_code}, roles={users.find_one({"_id": pme_id})["roles"]}')

# Clean up everything this section created.
if company:
    mongo.db['events'].delete_many({'company_id': company['_id']})
    mongo.db['companies'].delete_one({'_id': company['_id']})
users.delete_one({'_id': pme_id})
if made_admin:
    users.delete_one({'_id': made_admin})
users.delete_one({'email': 'verify-second@localhost'})

# --------------------------------------------------------------------------
# Restore
# --------------------------------------------------------------------------
restore = ({'$set': {'company_id': original_member_company}}
           if original_member_company
           else {'$unset': {'company_id': ''}})
users.update_one({'_id': member_doc['_id']}, restore)
mongo.db['products'].delete_one({'sku': 'VERIFY-SKU'})
mongo.db['customers'].delete_many({'name': 'CSRF-VERIFY-DELETE-ME'})

# --------------------------------------------------------------------------
# F. Login throttling (last: it consumes the in-process bucket)
# --------------------------------------------------------------------------
from app.core.utils.rate_limit import reset_limits
reset_limits()
tc = app.test_client()
statuses = []
for i in range(12):
    r = tc.post('/web/auth/login', data={'email': 'nobody@example.com', 'password': 'wrong'}, headers=HTML)
    statuses.append(r.status_code)
throttled = any('Too many attempts' in tc.get('/web/auth/login', headers=HTML).get_data(as_text=True)
                for _ in [0])
# the throttle flashes on the POST response itself
r = tc.post('/web/auth/login', data={'email': 'nobody@example.com', 'password': 'wrong'}, headers=HTML)
check('login attempts are rate limited',
      'Too many attempts' in r.get_data(as_text=True) or statuses[-1] == 429,
      f'statuses seen: {statuses}')

failed = [name for ok, name, _ in results if not ok]
print()
print(f'{len(results) - len(failed)}/{len(results)} checks passed')
if failed:
    print('FAILED:', failed)
    sys.exit(1)

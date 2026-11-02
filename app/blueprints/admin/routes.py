import logging
import os
import re
from uuid import uuid4
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, abort
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.core.models.company_model import CompanyModel
from app.core.models.user_model import UserModel
from app.core.models.role_model import RoleModel
from app.core.services.auth_service import AuthService
from app.core.services.rabbitmq_service import get_overview, get_top_queues
from app.extensions.db import mongo
from functools import wraps

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _save_logo(file):
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return None
    filename = f'{uuid4().hex}.{ext}'
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'logos')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return filename

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, template_folder='../templates')


def super_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        role_names = claims.get('role_names', [])
        if 'Admin' not in role_names:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


@admin_bp.route('/')
@jwt_required()
@super_admin_required
def index():
    from bson.objectid import ObjectId
    from app.core.models.event_model import EventModel
    from datetime import datetime, timezone, timedelta

    user = _get_user()
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)

    companies = CompanyModel.find_all()

    # One grouped query per collection instead of one count per company per
    # collection: 6 queries total rather than 6 x N (+ N for users).
    def _counts_by_company(collection):
        counts = {}
        for row in mongo.db[collection].aggregate([
            {'$group': {'_id': '$company_id', 'n': {'$sum': 1}}},
        ]):
            if row['_id'] is not None:
                counts[str(row['_id'])] = row['n']
        return counts

    counters = {
        'user_count': _counts_by_company('users'),
        'product_count': _counts_by_company('products'),
        'order_count': _counts_by_company('orders'),
        'invoice_count': _counts_by_company('invoices'),
        'movement_count': _counts_by_company('stock_movements'),
        'po_count': _counts_by_company('purchase_orders'),
    }

    company_list = []
    for c in companies:
        d = CompanyModel.to_dict(c)
        for key, counts in counters.items():
            d[key] = counts.get(d['id'], 0)
        company_list.append(d)

    total_companies = len(company_list)
    total_users = sum(c['user_count'] for c in company_list)
    total_activities = EventModel.count()
    today_activities = EventModel.count({'created_at': {'$gte': today_start}})
    today_movements = mongo.db['stock_movements'].count_documents({'created_at': {'$gte': today_start}})
    today_ops = today_activities + today_movements

    company_growth = list(mongo.db['companies'].aggregate([
        {'$match': {'created_at': {'$gte': thirty_days_ago}}},
        {'$group': {'_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}}, 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}},
    ]))
    growth_labels = [g['_id'] for g in company_growth]
    growth_data = [g['count'] for g in company_growth]
    growth_max = max(growth_data) if growth_data else 1
    # Guard both denominators: a single data point (or a single company in
    # the window) would otherwise divide by zero.
    growth_len = max(len(growth_data), 2)
    growth_points = ' '.join(
        f'{int(i * 200 / (growth_len - 1))},{int(32 - (v / growth_max * 28))}'
        for i, v in enumerate(growth_data)
    ) if growth_data else ''
    growth_fill = f'0,32 {growth_points} 200,32' if growth_points else ''

    user_roles = list(mongo.db['users'].aggregate([
        {'$unwind': '$roles'},
        {'$group': {'_id': '$roles', 'count': {'$sum': 1}}},
    ]))
    role_breakdown = {r['_id'] or 'Unknown': r['count'] for r in user_roles}
    max_role_count = max(role_breakdown.values()) if role_breakdown else 1

    active_user_ids = set()
    recent_user_events = mongo.db['events'].find(
        {'created_at': {'$gte': today_start}, 'user_id': {'$ne': None}},
        {'user_id': 1}
    )
    for ev in recent_user_events:
        if ev.get('user_id'):
            active_user_ids.add(str(ev['user_id']))

    events_raw, _ = EventModel.find_all(page=1, per_page=20)
    recent_events = [EventModel.to_dict(ev) for ev in events_raw]

    critical_events = [e for e in recent_events if e['action'] in ('delete',) or 'failed' in e.get('entity_type', '').lower() or 'alert' in e.get('entity_type', '').lower()]

    collection_stats = {}
    for col in ['companies', 'users', 'products', 'orders', 'invoices', 'stock_movements', 'purchase_orders', 'supplier_invoices', 'customer_quotes', 'delivery_notes']:
        collection_stats[col] = mongo.db[col].count_documents({})

    db_usage_30d = list(mongo.db['events'].aggregate([
        {'$match': {'created_at': {'$gte': thirty_days_ago}}},
        {'$group': {'_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}}, 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}},
    ]))
    db_labels = [d['_id'] for d in db_usage_30d]
    db_data = [d['count'] for d in db_usage_30d]

    # RabbitMQ monitor widget. This blueprint is Admin-only
    # (@super_admin_required), so the block is never exposed to other roles.
    rabbitmq = get_overview()
    rabbitmq_queues = get_top_queues() if rabbitmq.get('ok') else []

    return render_template('admin/index.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           rabbitmq=rabbitmq,
                           rabbitmq_queues=rabbitmq_queues,
                           companies=company_list,
                           total_companies=total_companies,
                           total_users=total_users,
                           total_activities=total_activities,
                           today_activities=today_activities,
                           today_movements=today_movements,
                           today_ops=today_ops,
                           recent_events=recent_events,
                           critical_events=critical_events[:5],
                           growth_labels=growth_labels,
                           growth_data=growth_data,
                           growth_points=growth_points,
                           growth_fill=growth_fill,
                           role_breakdown=role_breakdown,
                           max_role_count=max_role_count,
                           active_users=len(active_user_ids),
                           collection_stats=collection_stats,
                           db_labels=db_labels,
                           db_data=db_data)


@admin_bp.route('/companies')
@jwt_required()
@super_admin_required
def companies():
    from bson.objectid import ObjectId
    user = _get_user()
    companies_raw = CompanyModel.find_all()

    company_list = []
    grand = {'users': 0, 'products': 0, 'orders': 0, 'invoices': 0, 'movements': 0}
    for c in companies_raw:
        cid = ObjectId(c['_id'])
        d = CompanyModel.to_dict(c)
        d['user_count'] = UserModel.count({'company_id': cid})
        d['product_count'] = mongo.db['products'].count_documents({'company_id': cid})
        d['order_count'] = mongo.db['orders'].count_documents({'company_id': cid})
        d['invoice_count'] = mongo.db['invoices'].count_documents({'company_id': cid})
        d['movement_count'] = mongo.db['stock_movements'].count_documents({'company_id': cid})
        d['total_revenue'] = 0
        invoices_cursor = mongo.db['invoices'].find({'company_id': cid, 'status': 'paid'})
        for inv in invoices_cursor:
            d['total_revenue'] += float(inv.get('total', 0))
        company_list.append(d)
        grand['users'] += d['user_count']
        grand['products'] += d['product_count']
        grand['orders'] += d['order_count']
        grand['invoices'] += d['invoice_count']
        grand['movements'] += d['movement_count']

    return render_template('admin/companies.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           companies=company_list, grand=grand)


@admin_bp.route('/companies/create', methods=['GET', 'POST'])
@jwt_required()
@super_admin_required
def create_company():
    user = _get_user()
    if request.method == 'GET':
        return render_template('admin/create_company.html', mode='web',
                               user=UserModel.to_dict(user) if user else None)

    company_name = (request.form.get('company_name') or '').strip()
    admin_email = (request.form.get('admin_email') or '').strip().lower()
    admin_password = request.form.get('admin_password', '')
    admin_name = (request.form.get('admin_name') or '').strip()

    errors = []
    if not company_name:
        errors.append('Company name is required.')
    if not admin_email:
        errors.append('Admin email is required.')
    if len(admin_password) < 8:
        errors.append('Password must be at least 8 characters.')

    existing_company = CompanyModel.find_by_slug(company_name.lower().replace(' ', '-'))
    if existing_company:
        errors.append('A company with this name already exists.')

    existing_user = UserModel.find_by_email(admin_email)
    if existing_user:
        errors.append('Email already registered.')

    logo = request.files.get('logo')
    logo_filename = _save_logo(logo)

    if errors:
        for e in errors:
            flash(e, 'danger')
        return render_template('admin/create_company.html', mode='web',
                               user=UserModel.to_dict(user) if user else None)

    from bson.objectid import ObjectId
    company_data = {
        'name': company_name,
        'slug': company_name.lower().replace(' ', '-'),
        'logo': logo_filename,
        'address': (request.form.get('address') or '').strip(),
        'city': (request.form.get('city') or '').strip(),
        'phone': (request.form.get('phone') or '').strip(),
        'email': (request.form.get('contact_email') or '').strip(),
        'contact_name': (request.form.get('contact_name') or '').strip(),
        'ice': (request.form.get('ice') or '').strip(),
        'rc': (request.form.get('rc') or '').strip(),
        'if_tax': (request.form.get('if_tax') or '').strip(),
        'cnss': (request.form.get('cnss') or '').strip(),
        'patente': (request.form.get('patente') or '').strip(),
        'website': (request.form.get('website') or '').strip(),
        'invoice_template': {
            'primary_color': '#1a73e8',
            'secondary_color': '#6c757d',
            'accent_color': '#0d6efd',
            'font_family': "'Comfortaa', sans-serif",
            'show_logo': True,
            'show_legal_ids': True,
            'show_rib': True,
            'header_text': '',
            'footer_text': '',
            'payment_terms': '',
            'signature_name': '',
            'signature_title': '',
        },
    }
    company_id = CompanyModel.create(company_data)

    from app.extensions.db import bcrypt
    hashed = bcrypt.generate_password_hash(admin_password).decode('utf-8')
    user_data = {
        'name': admin_name or company_name + ' Admin',
        'email': admin_email,
        'password': hashed,
        'roles': ['Manager'],
        'company_id': ObjectId(company_id),
    }
    UserModel.create(user_data)

    logger.info('Company created: %s (id=%s) with admin %s', company_name, company_id, admin_email)
    flash(f'Company "{company_name}" created with admin account ({admin_email}).', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/companies/<company_id>/users')
@jwt_required()
@super_admin_required
def company_users(company_id):
    from bson.objectid import ObjectId
    user = _get_user()
    company = CompanyModel.find_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('admin.index'))

    users = UserModel.find_by_company(company_id)
    return render_template('admin/company_users.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           company=CompanyModel.to_dict(company),
                           users=[UserModel.to_dict(u) for u in users])


@admin_bp.route('/companies/<company_id>')
@jwt_required()
@super_admin_required
def company_detail(company_id):
    from bson.objectid import ObjectId
    user = _get_user()
    company = CompanyModel.find_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('admin.index'))

    cid = ObjectId(company_id)
    users = UserModel.find_by_company(company_id)
    product_count = mongo.db['products'].count_documents({'company_id': cid})
    order_count = mongo.db['orders'].count_documents({'company_id': cid})
    invoice_count = mongo.db['invoices'].count_documents({'company_id': cid})
    movement_count = mongo.db['stock_movements'].count_documents({'company_id': cid})

    products_raw = mongo.db['products'].find({'company_id': cid}).sort('created_at', -1).limit(50)
    products = [{
        'id': str(p['_id']), 'name': p.get('name'), 'sku': p.get('sku'),
        'quantity': p.get('quantity', 0), 'price': float(p.get('price', 0)),
        'category': p.get('category', ''), 'stock_value': float(p.get('quantity', 0)) * float(p.get('price', 0)),
    } for p in products_raw]

    orders_raw = mongo.db['orders'].find({'company_id': cid}).sort('created_at', -1).limit(50)
    orders = [{
        'id': str(o['_id']), 'order_number': o.get('order_number'),
        'customer_name': o.get('customer_name'), 'total': float(o.get('total', 0)),
        'status': o.get('status', 'pending'),
        'created_at': o.get('created_at').isoformat()[:10] if o.get('created_at') else '',
    } for o in orders_raw]

    invoices_raw = mongo.db['invoices'].find({'company_id': cid}).sort('created_at', -1).limit(50)
    invoices = [{
        'id': str(inv['_id']), 'invoice_number': inv.get('invoice_number'),
        'customer_name': inv.get('customer_name'), 'total': float(inv.get('total', 0)),
        'status': inv.get('status', 'draft'),
        'created_at': inv.get('created_at').isoformat()[:10] if inv.get('created_at') else '',
    } for inv in invoices_raw]

    return render_template('admin/company_detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           company=CompanyModel.to_dict(company),
                           users=[UserModel.to_dict(u) for u in users],
                           stats={
                               'product_count': product_count,
                               'order_count': order_count,
                               'invoice_count': invoice_count,
                               'movement_count': movement_count,
                           },
                           products=products, orders=orders, invoices=invoices)


@admin_bp.route('/companies/<company_id>/edit', methods=['GET', 'POST'])
@jwt_required()
@super_admin_required
def edit_company(company_id):
    from bson.objectid import ObjectId
    user = _get_user()
    company = CompanyModel.find_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('admin.index'))

    if request.method == 'GET':
        return render_template('admin/edit_company.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               company=CompanyModel.to_dict(company))

    company_name = (request.form.get('company_name') or '').strip()
    if not company_name:
        flash('Company name is required.', 'danger')
        return render_template('admin/edit_company.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               company=CompanyModel.to_dict(company))

    new_slug = company_name.lower().replace(' ', '-')
    existing = CompanyModel.find_by_slug(new_slug)
    if existing and str(existing['_id']) != company_id:
        flash('A company with this name already exists.', 'danger')
        return render_template('admin/edit_company.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               company=CompanyModel.to_dict(company))

    update_data = {
        'name': company_name,
        'slug': new_slug,
        'address': (request.form.get('address') or '').strip(),
        'city': (request.form.get('city') or '').strip(),
        'phone': (request.form.get('phone') or '').strip(),
        'email': (request.form.get('contact_email') or '').strip(),
        'contact_name': (request.form.get('contact_name') or '').strip(),
        'ice': (request.form.get('ice') or '').strip(),
        'rc': (request.form.get('rc') or '').strip(),
        'if_tax': (request.form.get('if_tax') or '').strip(),
        'cnss': (request.form.get('cnss') or '').strip(),
        'patente': (request.form.get('patente') or '').strip(),
        'website': (request.form.get('website') or '').strip(),
        'invoice_template': {
            'primary_color': (request.form.get('inv_primary_color') or '').strip(),
            'secondary_color': (request.form.get('inv_secondary_color') or '').strip(),
            'accent_color': (request.form.get('inv_accent_color') or '').strip(),
            'font_family': (request.form.get('inv_font_family') or '').strip(),
            'show_logo': request.form.get('inv_show_logo') == '1',
            'show_legal_ids': request.form.get('inv_show_legal_ids') == '1',
            'show_rib': request.form.get('inv_show_rib') == '1',
            'header_text': (request.form.get('inv_header_text') or '').strip(),
            'footer_text': (request.form.get('inv_footer_text') or '').strip(),
            'payment_terms': (request.form.get('inv_payment_terms') or '').strip(),
            'signature_name': (request.form.get('inv_signature_name') or '').strip(),
            'signature_title': (request.form.get('inv_signature_title') or '').strip(),
        },
    }

    logo = request.files.get('logo')
    if logo and logo.filename:
        logo_filename = _save_logo(logo)
        if logo_filename:
            update_data['logo'] = logo_filename

    CompanyModel.update(company_id, update_data)
    logger.info('Company updated: %s (id=%s)', company_name, company_id)
    flash(f'Company "{company_name}" updated.', 'success')
    return redirect(url_for('admin.company_detail', company_id=company_id))


@admin_bp.route('/companies/<company_id>/delete', methods=['POST'])
@jwt_required()
@super_admin_required
def delete_company(company_id):
    company = CompanyModel.find_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('admin.index'))

    CompanyModel.delete(company_id)
    logger.warning('Company deleted: %s (id=%s)', company.get('name'), company_id)
    flash(f'Company "{company.get("name")}" deleted.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/companies/<company_id>/add-user', methods=['GET', 'POST'])
@jwt_required()
@super_admin_required
def add_user(company_id):
    from bson.objectid import ObjectId
    user = _get_user()
    company = CompanyModel.find_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('admin.index'))

    if request.method == 'GET':
        # Fetch all roles to display in the form
        roles = RoleModel.find_all()
        return render_template('admin/create_user.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               company=CompanyModel.to_dict(company) if company else None,
                               roles=[RoleModel.to_dict(r) for r in roles])

    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password', '')
    name = (request.form.get('name') or '').strip()
    roles = request.form.getlist('roles')  # Get list of selected role names

    errors = []
    if not email:
        errors.append('Email is required.')
    if len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if not roles:
        errors.append('At least one role must be selected.')
    if 'Admin' in roles:
        errors.append('The Admin profile belongs to the single platform administrator '
                      'and cannot be assigned here.')

    existing_user = UserModel.find_by_email(email)
    if existing_user:
        errors.append('Email already registered.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('admin.company_detail', company_id=company_id))

    from app.extensions.db import bcrypt
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    user_data = {
        'name': name or email.split('@')[0],
        'email': email,
        'password': hashed,
        'roles': roles,
        'company_id': ObjectId(company_id),
    }
    UserModel.create(user_data)

    logger.info('User %s added to company %s (roles=%s)', email, company.get('name'), roles)
    flash(f'User "{email}" added to company.', 'success')
    return redirect(url_for('admin.company_detail', company_id=company_id))


@admin_bp.route('/users/<user_id>/set-role', methods=['POST'])
@jwt_required()
@super_admin_required
def set_user_role(user_id):
    user = UserModel.find_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.index'))

    user_dict = UserModel.to_dict(user)
    if 'Admin' in user_dict.get('role_names', []):
        flash('Cannot change admin role.', 'danger')
        return redirect(url_for('admin.index'))

    new_role_name = request.form.get('role', '')
    if new_role_name not in ('user', 'company_admin'):
        flash('Invalid role.', 'danger')
    else:
        # Map old role names to RBAC role names: the company-owner profile is
        # PME-Admin, the ordinary member profile is Customer.
        target_role = 'Customer' if new_role_name == 'user' else 'PME-Admin'
        role = RoleModel.find_by_name(target_role)
        if role:
            UserModel.update(user_id, {'roles': [target_role]})
            logger.info('User %s role changed to %s', user.get('email'), target_role)
            flash(f'User role updated to {target_role}.', 'success')
        else:
            flash(f'Role "{target_role}" not found.', 'danger')

    company_id = str(user['company_id']) if user.get('company_id') else None
    if company_id:
        return redirect(url_for('admin.company_detail', company_id=company_id))
    return redirect(url_for('admin.index'))


@admin_bp.route('/users')
@jwt_required()
@super_admin_required
def list_users():
    from bson.objectid import ObjectId
    user = _get_user()
    search = (request.args.get('search') or '').strip()

    users_raw = UserModel.find_all(search=search if search else None)
    all_users = []
    for u in users_raw:
        d = UserModel.to_dict(u)
        if d['company_id']:
            comp = CompanyModel.find_by_id(d['company_id'])
            d['company_name'] = comp.get('name', '—') if comp else '—'
        else:
            d['company_name'] = '—'
        all_users.append(d)

    total = len(all_users)

    return render_template('admin/users.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           users=all_users,
                           total=total, search=search)


@admin_bp.route('/users/create-pme-admin', methods=['GET', 'POST'])
@jwt_required()
@super_admin_required
def create_pme_admin():
    """Create a PME-Admin account that has no company yet.

    The platform Admin manages every other user profile; the PME-Admin
    registers his own personal and company details on his first login
    (``web_profile.setup``), which is what gives him his own stock and
    customer data space.
    """
    user = _get_user()

    if request.method == 'GET':
        return render_template('admin/create_pme_admin.html', mode='web',
                               user=UserModel.to_dict(user) if user else None)

    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password', '')
    name = (request.form.get('name') or '').strip()

    errors = []
    if not name:
        errors.append('Name is required.')
    if not email or '@' not in email:
        errors.append('A valid email is required.')
    if len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if UserModel.find_by_email(email):
        errors.append('Email already registered.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return render_template('admin/create_pme_admin.html', mode='web',
                               user=UserModel.to_dict(user) if user else None)

    from app.extensions.db import bcrypt
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    UserModel.create({
        'name': name,
        'email': email,
        'password': hashed,
        'roles': ['PME-Admin'],
        # Deliberately no company_id: the first login collects it.
    })
    logger.info('PME-Admin account created: %s', email)
    flash(f'PME-Admin "{email}" created. He will register his company on first login.', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@jwt_required()
@super_admin_required
def edit_user(user_id):
    user = _get_user()
    target = UserModel.find_by_id(user_id)
    if not target:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.list_users'))

    # Check if trying to edit another admin (current user can edit themselves)
    target_dict = UserModel.to_dict(target)
    current_user_id = get_jwt_identity()
    if 'Admin' in target_dict.get('role_names', []) and str(target['_id']) != current_user_id:
        flash('Cannot edit admin accounts.', 'danger')
        return redirect(url_for('admin.list_users'))

    if request.method == 'GET':
        # Fetch all roles to display in the form
        roles_list = RoleModel.find_all()
        return render_template('admin/edit_user.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               target=target_dict,
                               roles=[RoleModel.to_dict(r) for r in roles_list])

    name = (request.form.get('name') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    roles = request.form.getlist('roles')  # Get list of selected role names

    errors = []
    if not name:
        errors.append('Name is required.')
    if not email:
        errors.append('Email is required.')

    # Validate roles - must have at least one
    if not roles:
        errors.append('At least one role must be selected.')
    if 'Admin' in roles and 'Admin' not in target_dict.get('role_names', []):
        errors.append('Exactly one Admin account is allowed; this user cannot be made an Admin.')
    if 'Admin' in target_dict.get('role_names', []) and 'Admin' not in roles:
        errors.append('The Admin profile cannot be removed — it is the only platform administrator.')

    existing = UserModel.find_by_email(email)
    if existing and str(existing['_id']) != user_id:
        errors.append('Email already in use.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return render_template('admin/edit_user.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               target=target_dict,
                               roles=[RoleModel.to_dict(r) for r in RoleModel.find_all()])

    update_data = {
        'name': name,
        'email': email,
        'roles': roles
    }
    UserModel.update(user_id, update_data)
    logger.info('User updated: %s (id=%s)', email, user_id)
    flash('User details updated.', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/<user_id>/reset-password', methods=['POST'])
@jwt_required()
@super_admin_required
def reset_password(user_id):
    target = UserModel.find_by_id(user_id)
    if not target:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.list_users'))

    target_dict = UserModel.to_dict(target)
    if 'Admin' in target_dict.get('role_names', []):
        flash('Cannot reset password for admin via UI.', 'danger')
        return redirect(url_for('admin.list_users'))

    new_password = request.form.get('new_password', '')
    if len(new_password) < 8:
        flash('Password must be at least 8 characters.', 'danger')
        company_id = str(target['company_id']) if target.get('company_id') else None
        return redirect(url_for('admin.edit_user', user_id=user_id) if not company_id else url_for('admin.company_detail', company_id=company_id))

    from app.extensions.db import bcrypt
    hashed = bcrypt.generate_password_hash(new_password).decode('utf-8')
    UserModel.update(user_id, {'password': hashed})
    logger.info('Password reset for user %s', target.get('email'))
    flash('Password reset successful.', 'success')

    company_id = str(target['company_id']) if target.get('company_id') else None
    if company_id:
        return redirect(url_for('admin.company_detail', company_id=company_id))
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@jwt_required()
@super_admin_required
def delete_user(user_id):
    target = UserModel.find_by_id(user_id)
    if not target:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.list_users'))

    target_dict = UserModel.to_dict(target)
    if 'Admin' in target_dict.get('role_names', []):
        flash('Cannot delete admin account.', 'danger')
        return redirect(url_for('admin.list_users'))

    company_id = str(target['company_id']) if target.get('company_id') else None
    from bson.objectid import ObjectId
    mongo.db['users'].delete_one({'_id': ObjectId(user_id)})
    logger.warning('User deleted: %s (id=%s)', target.get('email'), user_id)
    flash(f'User "{target.get("email")}" deleted.', 'success')

    if company_id:
        return redirect(url_for('admin.company_detail', company_id=company_id))
    return redirect(url_for('admin.list_users'))

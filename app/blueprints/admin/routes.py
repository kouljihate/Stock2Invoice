import logging
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.core.models.company_model import CompanyModel
from app.core.models.user_model import UserModel
from app.core.services.auth_service import AuthService
from app.extensions.db import mongo
from functools import wraps

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, template_folder='../templates')


def super_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'super_admin':
            flash('Super admin access required.', 'danger')
            return redirect(url_for('web_auth.login'))
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
    companies = CompanyModel.find_all()
    user = _get_user()

    company_list = []
    for c in companies:
        d = CompanyModel.to_dict(c)
        d['user_count'] = UserModel.count({'company_id': ObjectId(d['id'])})
        company_list.append(d)

    total_companies = len(company_list)
    total_users = sum(c['user_count'] for c in company_list)

    return render_template('admin/index.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           companies=company_list,
                           total_companies=total_companies,
                           total_users=total_users)


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

    if errors:
        for e in errors:
            flash(e, 'danger')
        return render_template('admin/create_company.html', mode='web',
                               user=UserModel.to_dict(user) if user else None)

    from bson.objectid import ObjectId
    company_data = {
        'name': company_name,
        'slug': company_name.lower().replace(' ', '-'),
    }
    company_id = CompanyModel.create(company_data)

    from app.extensions.db import bcrypt
    hashed = bcrypt.generate_password_hash(admin_password).decode('utf-8')
    user_data = {
        'name': admin_name or company_name + ' Admin',
        'email': admin_email,
        'password': hashed,
        'role': 'company_admin',
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

    return render_template('admin/company_detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           company=CompanyModel.to_dict(company),
                           users=[UserModel.to_dict(u) for u in users],
                           stats={
                               'product_count': product_count,
                               'order_count': order_count,
                               'invoice_count': invoice_count,
                               'movement_count': movement_count,
                           })


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

    CompanyModel.update(company_id, {'name': company_name, 'slug': new_slug})
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


@admin_bp.route('/companies/<company_id>/add-user', methods=['POST'])
@jwt_required()
@super_admin_required
def add_user(company_id):
    from bson.objectid import ObjectId
    user = _get_user()
    company = CompanyModel.find_by_id(company_id)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('admin.index'))

    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password', '')
    name = (request.form.get('name') or '').strip()
    role = request.form.get('role', 'user')

    errors = []
    if not email:
        errors.append('Email is required.')
    if len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if role not in ('user', 'company_admin'):
        errors.append('Invalid role.')

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
        'role': role,
        'company_id': ObjectId(company_id),
    }
    UserModel.create(user_data)

    logger.info('User %s added to company %s (role=%s)', email, company.get('name'), role)
    flash(f'User "{email}" added to company.', 'success')
    return redirect(url_for('admin.company_detail', company_id=company_id))

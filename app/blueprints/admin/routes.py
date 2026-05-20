import logging
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.core.models.company_model import CompanyModel
from app.core.models.user_model import UserModel
from app.core.services.auth_service import AuthService
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
    companies = CompanyModel.find_all()
    user = _get_user()
    return render_template('admin/index.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           companies=companies)


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

    users = list(UserModel.collection.find({'company_id': ObjectId(company_id)}))
    return render_template('admin/company_users.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           company=CompanyModel.to_dict(company),
                           users=[UserModel.to_dict(u) for u in users])

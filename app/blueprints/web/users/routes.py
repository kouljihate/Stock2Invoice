import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app.core.models.user_model import UserModel
from app.core.models.company_model import CompanyModel
from app.core.utils.helpers import oid

logger = logging.getLogger(__name__)
web_users_bp = Blueprint('web_users', __name__, template_folder='../../../templates')


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


def _company_admin_required(user):
    if not user:
        return False
    role = user.get('role', '')
    return role in ('company_admin', 'super_admin')


@web_users_bp.route('')
@jwt_required()
def list_users():
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('web_auth.login'))

    cid = _company_id()
    if not cid:
        flash('No company assigned.', 'danger')
        return redirect(url_for('web_dashboard.index'))

    users = UserModel.find_by_company(cid)
    company = CompanyModel.find_by_id(cid)

    return render_template('web/users/list.html', mode='web',
                           user=UserModel.to_dict(user),
                           users=[UserModel.to_dict(u) for u in users],
                           company=company)


@web_users_bp.route('/create', methods=['POST'])
@jwt_required()
def create_user():
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)
    if not _company_admin_required(user):
        flash('Permission denied.', 'danger')
        return redirect(url_for('web_users.list_users'))

    cid = _company_id()
    if not cid:
        flash('No company assigned.', 'danger')
        return redirect(url_for('web_dashboard.index'))

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
    if not name:
        errors.append('Name is required.')

    existing = UserModel.find_by_email(email)
    if existing:
        errors.append('Email already registered.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('web_users.list_users'))

    from app.extensions.db import bcrypt
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    from bson.objectid import ObjectId
    UserModel.create({
        'name': name,
        'email': email,
        'password': hashed,
        'role': role,
        'company_id': ObjectId(cid),
    })

    logger.info('User %s added to company %s (role=%s)', email, cid, role)
    flash(f'User "{email}" created.', 'success')
    return redirect(url_for('web_users.list_users'))


@web_users_bp.route('/<user_id>/set-role', methods=['POST'])
@jwt_required()
def set_role(user_id):
    current_user = UserModel.find_by_id(get_jwt_identity())
    if not _company_admin_required(current_user):
        flash('Permission denied.', 'danger')
        return redirect(url_for('web_users.list_users'))

    cid = _company_id()
    target = UserModel.find_by_id(user_id)
    if not target:
        flash('User not found.', 'danger')
        return redirect(url_for('web_users.list_users'))

    if str(target.get('company_id', '')) != str(cid):
        flash('Cannot manage users from other companies.', 'danger')
        return redirect(url_for('web_users.list_users'))

    if target.get('role') == 'super_admin':
        flash('Cannot change super admin role.', 'danger')
        return redirect(url_for('web_users.list_users'))

    new_role = request.form.get('role', '')
    if new_role not in ('user', 'company_admin'):
        flash('Invalid role.', 'danger')
    else:
        UserModel.update(user_id, {'role': new_role})
        logger.info('User %s role changed to %s', target.get('email'), new_role)
        flash(f'User role updated to {new_role}.', 'success')

    return redirect(url_for('web_users.list_users'))

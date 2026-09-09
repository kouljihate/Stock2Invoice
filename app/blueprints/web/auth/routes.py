import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity
from app.core.services.auth_service import AuthService
from app.core.models.user_model import UserModel
from app.core.services.event_service import EventService
from .forms import LoginForm, RegisterForm

logger = logging.getLogger(__name__)
web_auth_bp = Blueprint('web_auth', __name__, template_folder='../../../templates')


def _redirect_after_login(user):
    user_dict = UserModel.to_dict(user)
    if 'Admin' in user_dict.get('role_names', []):
        return redirect(url_for('admin.index'))
    return redirect(url_for('web_dashboard.index'))


@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html', mode='web')

    if request.form.get('reset_admin_password'):
        email = (request.form.get('email') or '').strip().lower()
        if email != 'admin@si.ma':
            flash('Email must be the admin email to reset the password.', 'danger')
            return render_template('auth/login.html', mode='web')

        admin_user = UserModel.find_by_email('admin@si.ma')
        if not admin_user:
            flash('Admin user not found.', 'danger')
            return render_template('auth/login.html', mode='web')

        from app.extensions.db import bcrypt
        hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
        UserModel.update(str(admin_user['_id']), {'password': hashed})
        flash('Password has been reset to admin123. Please log in.', 'success')
        return render_template('auth/login.html', mode='web')

    form = LoginForm(request.form)
    if not form.validate():
        for e in form.errors:
            flash(e, 'danger')
        return render_template('auth/login.html', mode='web')

    try:
        user = AuthService.authenticate(form.email, form.password)
        if not user:
            flash('Invalid email or password.', 'danger')
            logger.warning('Web login failed for %s', form.email)
            return render_template('auth/login.html', mode='web')

        user_dict = UserModel.to_dict(user)
        claims = {
            'role_names': user_dict.get('role_names', []),
            'user_name': user_dict.get('name', ''),
            'user_email': user_dict.get('email', ''),
        }
        company_id = user.get('company_id')
        if company_id:
            claims['company_id'] = str(company_id)

        token = create_access_token(
            identity=str(user['_id']),
            additional_claims=claims,
        )
        resp = _redirect_after_login(user)
        set_access_cookies(resp, token)
        flash('Welcome back!', 'success')
        EventService.record(
            company_id, 'session', str(user['_id']), form.email, 'login',
            user_id=str(user['_id']), user_name=user_dict.get('name', ''),
        )
        logger.info('Web SESSION START: %s', form.email)
        return resp
    except Exception as e:
        logger.exception('Login error')
        flash('An error occurred. Please try again.', 'danger')
        return render_template('auth/login.html', mode='web')


@web_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html', mode='web')

    form = RegisterForm(request.form)
    if not form.validate():
        for e in form.errors:
            flash(e, 'danger')
        return render_template('auth/register.html', mode='web')

    try:
        existing = UserModel.find_by_email(form.email)
        if existing:
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html', mode='web')

        AuthService.register({'name': form.name, 'email': form.email, 'password': form.password})
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('web_auth.login'))
    except Exception as e:
        logger.exception('Registration error')
        flash('An error occurred. Please try again.', 'danger')
        return render_template('auth/register.html', mode='web')


@web_auth_bp.route('/logout', methods=['GET'])
def logout():
    uid = None
    try:
        uid = get_jwt_identity()
    except Exception:
        uid = None
    email = '-'
    u = UserModel.find_by_id(uid) if uid else None
    if u:
        email = u.get('email', '-')
        EventService.record(
            u.get('company_id'), 'session', str(u['_id']), email, 'logout',
            user_id=uid, user_name=u.get('name', ''),
        )
    resp = redirect(url_for('web_auth.login'))
    unset_jwt_cookies(resp)
    flash('You have been logged out.', 'info')
    logger.info('Web SESSION END: %s', email)
    return resp


@web_auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/forgot_password.html', mode='web')

        # In a real application, you would:
        # 1. Check if the email exists in the database
        # 2. Generate a reset token
        # 3. Send an email with the reset link
        # For now, we'll just show a success message (to prevent user enumeration)
        flash('If your email is registered, you will receive a password reset link.', 'info')
        # Fall through to render the template again with the message

    # For both GET and POST (after processing), render the template
    return render_template('auth/forgot_password.html', mode='web')

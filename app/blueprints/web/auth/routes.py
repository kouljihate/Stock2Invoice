import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity
from app.core.services.auth_service import AuthService
from app.core.models.user_model import UserModel
from .forms import LoginForm, RegisterForm

logger = logging.getLogger(__name__)
web_auth_bp = Blueprint('web_auth', __name__, template_folder='../../../templates')


def _redirect_after_login(user):
    role = user.get('role', 'user')
    if role == 'super_admin':
        return redirect(url_for('admin.index'))
    return redirect(url_for('web_dashboard.index'))


@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
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

        claims = {
            'role': user.get('role', 'user'),
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
        logger.info('Web login success: %s', form.email)
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
    resp = redirect(url_for('web_auth.login'))
    unset_jwt_cookies(resp)
    flash('You have been logged out.', 'info')
    logger.info('Web logout')
    return resp


@web_auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('auth/forgot_password.html', mode='web')

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
    return redirect(url_for('web_auth.login'))

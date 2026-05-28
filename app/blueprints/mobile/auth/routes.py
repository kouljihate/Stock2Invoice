import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity
from app.core.services.auth_service import AuthService
from app.core.models.user_model import UserModel
from .forms import LoginForm, RegisterForm

logger = logging.getLogger(__name__)
mobile_auth_bp = Blueprint('mobile_auth', __name__, template_folder='../../../templates')


def _redirect_after_login(user):
    user_dict = UserModel.to_dict(user)
    if 'Admin' in user_dict.get('role_names', []):
        return redirect(url_for('admin.index'))
    return redirect(url_for('mobile_dashboard.index'))


@mobile_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html', mode='mobile')

    form = LoginForm(request.form)
    if not form.validate():
        for e in form.errors:
            flash(e, 'danger')
        return render_template('auth/login.html', mode='mobile')

    try:
        user = AuthService.authenticate(form.email, form.password)
        if not user:
            flash('Invalid email or password.', 'danger')
            logger.warning('Mobile login failed for %s', form.email)
            return render_template('auth/login.html', mode='mobile')

        user_dict = UserModel.to_dict(user)
        claims = {
            'role_names': user_dict.get('role_names', []),
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
        logger.info('Mobile login success: %s', form.email)
        return resp
    except Exception as e:
        logger.exception('Mobile login error')
        flash('An error occurred.', 'danger')
        return render_template('auth/login.html', mode='mobile')


@mobile_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html', mode='mobile')

    form = RegisterForm(request.form)
    if not form.validate():
        for e in form.errors:
            flash(e, 'danger')
        return render_template('auth/register.html', mode='mobile')

    try:
        existing = UserModel.find_by_email(form.email)
        if existing:
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html', mode='mobile')

        AuthService.register({'name': form.name, 'email': form.email, 'password': form.password})
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('mobile_auth.login'))
    except Exception as e:
        logger.exception('Mobile registration error')
        flash('An error occurred.', 'danger')
        return render_template('auth/register.html', mode='mobile')


@mobile_auth_bp.route('/logout', methods=['GET'])
def logout():
    resp = redirect(url_for('mobile_auth.login'))
    unset_jwt_cookies(resp)
    flash('You have been logged out.', 'info')
    logger.info('Mobile logout')
    return resp


@mobile_auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/forgot_password.html', mode='mobile')

        # In a real application, you would:
        # 1. Check if the email exists in the database
        # 2. Generate a reset token
        # 3. Send an email with the reset link
        # For now, we'll just show a success message (to prevent user enumeration)
        flash('If your email is registered, you will receive a password reset link.', 'info')
        # Fall through to render the template again with the message

    # For both GET and POST (after processing), render the template
    return render_template('auth/forgot_password.html', mode='mobile')

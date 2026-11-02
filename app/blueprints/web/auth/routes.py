import logging
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, abort
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity
from app.core.services.auth_service import AuthService
from app.core.models.user_model import UserModel
from app.core.services.event_service import EventService
from app.core.utils.rate_limit import check_rate_limit, client_ip
from .forms import LoginForm, RegisterForm

logger = logging.getLogger(__name__)
web_auth_bp = Blueprint('web_auth', __name__, template_folder='../../../templates')

REGISTER_LIMIT = 5
REGISTER_WINDOW = 3600


def _throttled(bucket, limit=None):
    """True when this client has exhausted its allowance for ``bucket``."""
    cfg = current_app.config
    return check_rate_limit(
        f'{bucket}:{client_ip()}',
        limit or cfg['AUTH_RATE_LIMIT'],
        cfg['AUTH_RATE_WINDOW'],
    )


def _redirect_after_login(user):
    user_dict = UserModel.to_dict(user)
    if 'Admin' in user_dict.get('role_names', []):
        return redirect(url_for('admin.index'))
    return redirect(url_for('web_dashboard.index'))


@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html', mode='web')

    if _throttled('login'):
        logger.warning('Login rate-limited for %s', client_ip())
        flash('Too many attempts. Please wait a few minutes and try again.', 'danger')
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
    except Exception:
        logger.exception('Login error')
        flash('An error occurred. Please try again.', 'danger')
        return render_template('auth/login.html', mode='web')


@web_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if not current_app.config['ALLOW_PUBLIC_REGISTRATION']:
        flash('Self-service registration is disabled on this instance.', 'info')
        return redirect(url_for('web_auth.login'))

    if request.method == 'GET':
        return render_template('auth/register.html', mode='web')

    if _throttled('register', REGISTER_LIMIT):
        logger.warning('Registration rate-limited for %s', client_ip())
        flash('Too many attempts. Please wait and try again.', 'danger')
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
    except Exception:
        logger.exception('Registration error')
        flash('An error occurred. Please try again.', 'danger')
        return render_template('auth/register.html', mode='web')


@web_auth_bp.route('/logout', methods=['POST'])
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
    # POST answers land back on the tabbed login page so the Login /
    # Reset Password tabs stay in one place; GET keeps the standalone page
    # for direct links and the mobile flow.
    def _reset_page():
        if request.method == 'POST':
            return render_template('auth/login.html', mode='web', active_tab='reset')
        return render_template('auth/forgot_password.html', mode='web')

    if request.method == 'POST':
        if _throttled('forgot', REGISTER_LIMIT):
            flash('Too many attempts. Please wait and try again.', 'danger')
            return _reset_page()

        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.', 'danger')
            return _reset_page()

        # Password resets are not self-service: no token is generated and no
        # mail is sent, so the response is identical whether or not the
        # address exists (prevents account enumeration).
        flash('If your email is registered, you will receive a password reset link.', 'info')

    return _reset_page()

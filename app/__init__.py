import click
import logging
from datetime import datetime
from flask import Flask, abort, g, request, redirect, url_for
from flask_cors import CORS

from .config import Config
from .extensions.db import mongo, bcrypt, jwt
from .extensions.logging import setup_logging, setup_request_logging
from .core.utils.error_handlers import register_error_handlers
from .core.utils.route_permissions import permission_for, TENANT_SCOPED_BLUEPRINTS

from .blueprints.web.auth.routes import web_auth_bp
from .blueprints.web.dashboard.routes import web_dashboard_bp
from .blueprints.web.stock.routes import web_stock_bp
from .blueprints.web.invoices.routes import web_invoices_bp
from .blueprints.web.orders.routes import web_orders_bp

from .blueprints.web.suppliers.routes import web_suppliers_bp
from .blueprints.web.purchase_orders.routes import web_purchase_orders_bp
from .blueprints.web.goods_receipt.routes import web_goods_receipt_bp
from .blueprints.web.supplier_invoices.routes import web_supplier_invoices_bp
from .blueprints.web.payments.routes import web_payments_bp

from .blueprints.web.customer_quotes.routes import web_customer_quotes_bp
from .blueprints.web.delivery_notes.routes import web_delivery_notes_bp
from .blueprints.web.customers.routes import web_customers_bp
from .blueprints.web.events.routes import web_events_bp
from .blueprints.web.users.routes import web_users_bp
from .blueprints.web.profile.routes import web_profile_bp

from .blueprints.eshop.routes import eshop_bp

from .blueprints.mobile.auth.routes import mobile_auth_bp
from .blueprints.mobile.dashboard.routes import mobile_dashboard_bp
from .blueprints.mobile.stock.routes import mobile_stock_bp
from .blueprints.mobile.invoices.routes import mobile_invoices_bp
from .blueprints.mobile.orders.routes import mobile_orders_bp

from .blueprints.admin.routes import admin_bp
from .version import VERSION, BUILD_DATE
from .core.utils.i18n import (PAIR_BADGES, PAIR_COOKIE, PAIR_LABELS, arabic,
                              dual_markup, primary_lang, resolve_pair)
from .translations import _ as _translate


logger = logging.getLogger(__name__)

LANGS = {'en': 'English', 'ar': 'Arabic', 'fr': 'French'}

# Endpoints a company-less PME-Admin may still reach while the first-login
# setup is outstanding (finishing the setup, getting out, static assets).
SETUP_EXEMPT = frozenset({
    'web_profile.setup',
    'web_auth.login', 'web_auth.logout',
    'mobile_auth.login', 'mobile_auth.logout',
    'static', 'favicon', 'health', 'set_lang', 'set_lang_pair', 'index',
})


def _current_user():
    """The acting user for this request, loaded once and cached on ``g``.

    Delegates to :mod:`app.core.utils.context` — the single place that
    resolves identity from the database rather than from JWT claims.
    """
    from .core.utils.context import current_user
    return current_user()


def _current_company():
    """Company of the acting user, loaded once per request and cached on ``g``."""
    if 'rbac_company' in g:
        return g.rbac_company
    company = None
    user = _current_user()
    if user and user.get('company_id'):
        from .core.models.company_model import CompanyModel
        try:
            company = CompanyModel.find_by_id(str(user['company_id']))
        except Exception:
            logger.exception('Could not load company for user %s', user.get('_id'))
            company = None
    g.rbac_company = company
    return company


def create_app(config_class=Config):
    config_class.validate_secrets()

    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        from flask import render_template, url_for, request
        lang = request.cookies.get('lang', 'en')
        if lang not in LANGS:
            lang = 'en'
        return render_template('base/token_expired.html', current_lang=lang, _=lambda key: _translate(key, lang), version=VERSION, build_date=BUILD_DATE), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        from flask import request, redirect, url_for, jsonify
        if request.path.startswith('/web/') or request.path.startswith('/mobile/'):
            if request.path.endswith('/api/lookup') or request.is_json or request.accept_mimetypes.accept_json:
                return jsonify({'msg': str(reason)}), 401
            return redirect(url_for('web_auth.login'))
        return jsonify({'msg': str(reason)}), 401

    setup_logging(app)
    setup_request_logging(app)
    register_error_handlers(app)

    @app.before_request
    def enforce_permissions():
        """Central authorization gate.

        0. A PME-Admin who has never completed the first-login company setup
           is sent there before anything else.
        1. Tenant-scoped blueprints are refused outright for authenticated
           accounts that are not linked to a company, so no view there can be
           reached unscoped.
        2. Every endpoint that resolves to a permission is checked against the
           acting user's effective RBAC permissions.

        Runs before the view (and therefore before ``@jwt_required()``), so a
        missing or invalid token is left for the view to answer with the
        correct 401/redirect. Only a *present* identity is judged here.
        """
        endpoint = request.endpoint
        if not endpoint:
            return None

        user = _current_user()

        # First-login onboarding: the PME-Admin must register himself and his
        # company before he can use any part of the application. The platform
        # Admin never has a company and is never pushed through this.
        if (user is not None
                and not user.get('company_id')
                and 'PME-Admin' in (user.get('roles') or [])
                and 'Admin' not in (user.get('roles') or [])
                and endpoint not in SETUP_EXEMPT):
            logger.info('Onboarding redirect for PME-Admin %s', user.get('_id'))
            return redirect(url_for('web_profile.setup'))

        permission = permission_for(endpoint)
        blueprint = endpoint.split('.', 1)[0]
        needs_company = blueprint in TENANT_SCOPED_BLUEPRINTS
        if not permission and not needs_company:
            return None

        if user is None:
            return None

        if needs_company and not user.get('company_id'):
            logger.warning('Tenant denied %s: user %s has no company',
                           endpoint, user.get('_id'))
            message = 'Your account is not linked to a company yet.'
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                from flask import jsonify
                return jsonify({'error': message}), 403
            from flask import flash
            flash(message, 'warning')
            target = ('mobile_dashboard.index'
                      if request.path.startswith('/mobile/')
                      else 'web_dashboard.index')
            return redirect(url_for(target))

        from .core.models.user_model import UserModel
        if not UserModel.has_perm(user, permission):
            logger.warning('RBAC denied %s -> %s for user %s',
                           endpoint, permission, user.get('_id'))
            abort(403)
        return None

    # Idempotent: seed the RBAC roles and MongoDB indexes the code relies on.
    try:
        with app.app_context():
            from .core.utils.bootstrap import bootstrap
            bootstrap()
    except Exception:
        logger.exception('Boot-time bootstrap (roles/indexes) failed; '
                         'run `flask bootstrap` to retry')

    app.register_blueprint(web_auth_bp, url_prefix='/web/auth')
    app.register_blueprint(web_dashboard_bp, url_prefix='/web/dashboard')
    app.register_blueprint(web_stock_bp, url_prefix='/web/stock')
    app.register_blueprint(web_invoices_bp, url_prefix='/web/invoices')
    app.register_blueprint(web_orders_bp, url_prefix='/web/orders')

    app.register_blueprint(web_suppliers_bp, url_prefix='/web/suppliers')
    app.register_blueprint(web_purchase_orders_bp, url_prefix='/web/purchase-orders')
    app.register_blueprint(web_goods_receipt_bp, url_prefix='/web/goods-receipt')
    app.register_blueprint(web_supplier_invoices_bp, url_prefix='/web/supplier-invoices')
    app.register_blueprint(web_payments_bp, url_prefix='/web/payments')

    app.register_blueprint(web_customer_quotes_bp, url_prefix='/web/quotes')
    app.register_blueprint(web_delivery_notes_bp, url_prefix='/web/delivery-notes')
    app.register_blueprint(web_customers_bp, url_prefix='/web/customers')
    app.register_blueprint(web_events_bp, url_prefix='/web/events')
    app.register_blueprint(web_users_bp, url_prefix='/web/users')
    app.register_blueprint(web_profile_bp, url_prefix='/web/profile')

    app.register_blueprint(eshop_bp, url_prefix='/eshop')

    app.register_blueprint(mobile_auth_bp, url_prefix='/mobile/auth')
    app.register_blueprint(mobile_dashboard_bp, url_prefix='/mobile/dashboard')
    app.register_blueprint(mobile_stock_bp, url_prefix='/mobile/stock')
    app.register_blueprint(mobile_invoices_bp, url_prefix='/mobile/invoices')
    app.register_blueprint(mobile_orders_bp, url_prefix='/mobile/orders')

    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Every screen gets a stable page ID (login = 0.0) rendered in a badge and
    # explained by a dialog. Built after all blueprints so the registry always
    # matches the live url map.
    from .core.utils.page_registry import register as register_page_registry
    register_page_registry(app)

    @app.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory
        import os
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.svg', mimetype='image/vnd.microsoft.icon')

    @app.route('/lang/<lang>')
    def set_lang(lang):
        if lang in LANGS:
            resp = redirect(request.referrer or url_for('web_auth.login'))
            resp.set_cookie('lang', lang, max_age=365 * 24 * 3600)
            return resp
        return redirect(url_for('web_auth.login'))

    @app.route('/lang/pair/<pair>')
    def set_lang_pair(pair):
        """Switch the bilingual pair: Arabic/English or Arabic/French."""
        resp = redirect(request.referrer or url_for('web_auth.login'))
        resp.set_cookie(PAIR_COOKIE, resolve_pair(pair), max_age=365 * 24 * 3600)
        return resp

    @app.context_processor
    def inject_globals():
        # The interface is bilingual: text is shown in Arabic alongside the
        # primary language of the chosen pair. ``_()`` follows that primary
        # language (used where markup is not allowed, e.g. placeholders).
        pair = resolve_pair(request.cookies.get(PAIR_COOKIE))
        lang = primary_lang(pair)

        from .core.models.company_model import CompanyModel
        company_doc = _current_company()
        current_company = CompanyModel.to_dict(company_doc) if company_doc else None

        return {
            'current_lang': lang,
            'lang_pair': pair,
            'lang_pair_labels': PAIR_LABELS,
            'lang_pair_badges': PAIR_BADGES,
            'available_langs': LANGS,
            'version': VERSION,
            'build_date': BUILD_DATE,
            'current_company': current_company,
            'registration_enabled': app.config['ALLOW_PUBLIC_REGISTRATION'],
            'now': datetime.now(),
            '_': lambda key: _translate(key, lang),
            'dual': lambda key: dual_markup(key, lang),
            'arabic': arabic,
        }

    @app.cli.command('create-super-admin')
    @click.argument('email')
    @click.argument('password')
    @click.argument('name', default='Super Admin')
    def create_super_admin(email, password, name):
        from app.core.models.user_model import UserModel
        existing = UserModel.find_by_email(email)
        if existing:
            click.echo(f'ERROR: User "{email}" already exists.')
            return
        if UserModel.count_admins():
            click.echo('ERROR: an Admin account already exists. '
                       'This application allows exactly one Admin profile.')
            return
        from app.extensions.db import bcrypt
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        UserModel.create({
            'name': name,
            'email': email.strip().lower(),
            'password': hashed,
            'roles': ['Admin'],
        })
        click.echo(f'Super admin created: {email}')

    @app.cli.command('bootstrap')
    def bootstrap_command():
        """Seed RBAC roles and create the MongoDB indexes (idempotent)."""
        from app.core.utils.bootstrap import bootstrap
        result = bootstrap()
        click.echo(f"Roles written: {result['roles']}")
        click.echo(f"Indexes ensured: {len(result['indexes'])}")

    @app.cli.command('promote')
    @click.argument('email')
    @click.argument('role')
    def promote_command(email, role):
        """Set EMAIL's role to ROLE (Admin, PME-Admin, Manager or Customer)."""
        from app.core.models.user_model import UserModel
        from app.core.utils.bootstrap import ROLE_DEFINITIONS
        if role not in ROLE_DEFINITIONS:
            click.echo(f'ERROR: unknown role "{role}". '
                       f'Choose one of: {", ".join(ROLE_DEFINITIONS)}')
            return
        user = UserModel.find_by_email(email.strip().lower())
        if not user:
            click.echo(f'ERROR: no user with email "{email}".')
            return
        if role == 'Admin' and UserModel.count_admins(exclude_id=str(user['_id'])):
            click.echo('ERROR: another account already holds the Admin profile. '
                       'Exactly one Admin is allowed; demote it first.')
            return
        UserModel.update(str(user['_id']), {'roles': [role]})
        click.echo(f'{email} is now {role}')

    @app.route('/')
    def index():
        return '', 302, {'Location': '/web/auth/login'}

    @app.route('/api/health')
    def health():
        return {'status': 'ok'}

    return app


app = create_app()

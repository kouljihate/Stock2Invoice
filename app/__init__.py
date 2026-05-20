import click
from flask import Flask, request, redirect, url_for
from flask_cors import CORS

from .config import Config
from .extensions.db import mongo, bcrypt, jwt
from .extensions.logging import setup_logging
from .core.utils.error_handlers import register_error_handlers

from .blueprints.web.auth.routes import web_auth_bp
from .blueprints.web.dashboard.routes import web_dashboard_bp
from .blueprints.web.stock.routes import web_stock_bp
from .blueprints.web.invoices.routes import web_invoices_bp
from .blueprints.web.orders.routes import web_orders_bp

from .blueprints.mobile.auth.routes import mobile_auth_bp
from .blueprints.mobile.dashboard.routes import mobile_dashboard_bp
from .blueprints.mobile.stock.routes import mobile_stock_bp
from .blueprints.mobile.invoices.routes import mobile_invoices_bp
from .blueprints.mobile.orders.routes import mobile_orders_bp

from .blueprints.admin.routes import admin_bp
from .version import VERSION


LANGS = {'en': 'English', 'ar': 'Arabic', 'fr': 'French'}


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        from flask import render_template, url_for
        return render_template('base/token_expired.html'), 401

    setup_logging(app)
    register_error_handlers(app)

    app.register_blueprint(web_auth_bp, url_prefix='/web/auth')
    app.register_blueprint(web_dashboard_bp, url_prefix='/web/dashboard')
    app.register_blueprint(web_stock_bp, url_prefix='/web/stock')
    app.register_blueprint(web_invoices_bp, url_prefix='/web/invoices')
    app.register_blueprint(web_orders_bp, url_prefix='/web/orders')

    app.register_blueprint(mobile_auth_bp, url_prefix='/mobile/auth')
    app.register_blueprint(mobile_dashboard_bp, url_prefix='/mobile/dashboard')
    app.register_blueprint(mobile_stock_bp, url_prefix='/mobile/stock')
    app.register_blueprint(mobile_invoices_bp, url_prefix='/mobile/invoices')
    app.register_blueprint(mobile_orders_bp, url_prefix='/mobile/orders')

    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/lang/<lang>')
    def set_lang(lang):
        if lang in LANGS:
            resp = redirect(request.referrer or url_for('web_auth.login'))
            resp.set_cookie('lang', lang, max_age=365 * 24 * 3600)
            return resp
        return redirect(url_for('web_auth.login'))

    @app.context_processor
    def inject_globals():
        lang = request.cookies.get('lang', 'en')
        if lang not in LANGS:
            lang = 'en'

        current_company = None
        try:
            from flask_jwt_extended import get_jwt_identity
            identity = get_jwt_identity()
            if identity:
                from app.core.models.user_model import UserModel
                from app.core.models.company_model import CompanyModel
                u = UserModel.find_by_id(identity)
                if u and u.get('company_id'):
                    from bson.objectid import ObjectId
                    company = CompanyModel.find_by_id(str(u['company_id']))
                    if company:
                        current_company = CompanyModel.to_dict(company)
        except Exception:
            pass

        return {
            'current_lang': lang,
            'available_langs': LANGS,
            'version': VERSION,
            'current_company': current_company,
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
        from app.extensions.db import bcrypt
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        UserModel.create({
            'name': name,
            'email': email.strip().lower(),
            'password': hashed,
            'role': 'super_admin',
        })
        click.echo(f'Super admin created: {email}')

    @app.route('/')
    def index():
        return '', 302, {'Location': '/web/auth/login'}

    @app.route('/api/health')
    def health():
        return {'status': 'ok'}

    return app

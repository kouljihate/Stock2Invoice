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
        return {
            'current_lang': lang,
            'available_langs': LANGS,
            'version': VERSION,
        }

    @app.route('/')
    def index():
        return '', 302, {'Location': '/web/auth/login'}

    @app.route('/api/health')
    def health():
        return {'status': 'ok'}

    return app

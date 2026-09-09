import os
import logging
from time import perf_counter
from logging.handlers import RotatingFileHandler
from flask import has_request_context, request


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            name = getattr(request, 'user_name', '') or ''
            uid = getattr(request, 'user_id', None) or 'anonymous'
            record.user = f'{name} ({uid})' if name else str(uid)
            record.ip = request.remote_addr
        else:
            record.user = 'system'
            record.ip = '-'
        return super().format(record)


def setup_logging(app):
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    fmt = '%(asctime)s | %(levelname)-8s | %(user)s | %(ip)s | %(message)s'

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8',
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(RequestFormatter(fmt))

    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8',
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(RequestFormatter(fmt))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    app.logger.info('Logging initialised')


def setup_request_logging(app):
    """Log every action of a session (login -> logout).

    Attaches the JWT user to each request in before_request, then logs the
    completed request (method, path, status, duration) from after_request.
    Static assets, health checks, favicon, and CORS preflights are skipped.
    """

    skip_prefixes = ('/static/',)
    skip_exact = ('/favicon.ico', '/api/health')

    @app.before_request
    def _attach_user_context():
        request.user_id = None
        request.user_name = ''
        request.company_id = None
        request.start_time = perf_counter()
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity:
                request.user_id = str(identity)
                claims = get_jwt()
                request.company_id = claims.get('company_id')
                request.user_name = claims.get('user_name') or ''
        except Exception:
            pass

    @app.after_request
    def _log_action(response):
        try:
            if request.method == 'OPTIONS':
                return response
            path = request.path
            if path.startswith(skip_prefixes) or path in skip_exact:
                return response
            duration_ms = (perf_counter() - getattr(request, 'start_time', perf_counter())) * 1000
            user = getattr(request, 'user_id', None) or 'anonymous'
            app.logger.info('%s %s -> %s (%dms) [%s]', request.method, path,
                            response.status_code, duration_ms, user)
        except Exception:
            pass
        return response

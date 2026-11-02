import logging
from flask import render_template, jsonify, request
from flask_jwt_extended.exceptions import CSRFError as _CSRFError
from flask_jwt_extended import get_jwt_identity
from werkzeug.exceptions import HTTPException

from app.core.utils.helpers import error_context

logger = logging.getLogger(__name__)


def _get_mode():
    path = request.path
    if path.startswith('/mobile/'):
        return 'mobile'
    return 'web'


def _get_user_dict():
    try:
        from app.core.models.user_model import UserModel
        uid = get_jwt_identity()
        if uid:
            u = UserModel.find_by_id(uid)
            if u:
                return UserModel.to_dict(u)
    except Exception:
        pass
    return None


def register_error_handlers(app):
    """Render friendly error pages.

    The diagnostic detail from ``error_context`` (script, function, line,
    exception text) is written to the log only — it never reaches the client.
    """

    @app.errorhandler(_CSRFError)
    def csrf_rejected(e):
        """A missing/invalid CSRF token is a client problem, not a server error."""
        logger.warning('CSRF rejected on %s %s', request.method, request.path)
        if request.is_json or not request.accept_mimetypes.accept_html:
            return jsonify({'error': 'CSRF token missing or invalid'}), 403
        return render_template('base/error.html', code=403,
                               message='Your form token is missing or expired. '
                                       'Please refresh the page and try again.',
                               mode=_get_mode(), user=_get_user_dict()), 403

    @app.errorhandler(400)
    def bad_request(e):
        logger.warning('400 %s %s', request.path, str(e))
        if request.is_json:
            return jsonify({'error': 'Bad request'}), 400
        return render_template('base/error.html', code=400, message='Bad request.', mode=_get_mode(), user=_get_user_dict()), 400

    @app.errorhandler(401)
    def unauthorized(e):
        logger.warning('401 %s', request.path)
        if request.is_json:
            return jsonify({'error': 'Unauthorized'}), 401
        return render_template('base/error.html', code=401, message='Please log in to continue.', mode=_get_mode(), user=None), 401

    @app.errorhandler(403)
    def forbidden(e):
        logger.warning('403 %s', request.path)
        if request.is_json:
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('base/error.html', code=403, message='You do not have permission to view this page.', mode=_get_mode(), user=_get_user_dict()), 403

    @app.errorhandler(404)
    def not_found(e):
        logger.warning('404 %s', request.path)
        if request.is_json:
            return jsonify({'error': 'Not found'}), 404
        return render_template('base/error.html', code=404, message='Page not found.', mode=_get_mode(), user=_get_user_dict()), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception('500 %s', request.path)
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('base/error.html', code=500, message='Something went wrong.', mode=_get_mode(), user=_get_user_dict()), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        # Full detail goes to the log; the client gets a generic message.
        logger.error('Unhandled exception on %s -> %s', request.path, error_context(e), exc_info=True)
        if isinstance(e, HTTPException):
            # An HTTP error that had no dedicated handler (405, 415, ...).
            status = e.code or 500
            description = e.description or 'Request failed.'
            if request.is_json:
                return jsonify({'error': description}), status
            return render_template('base/error.html', code=status, message=description,
                                   mode=_get_mode(), user=_get_user_dict()), status
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('base/error.html', code=500,
                               message='Something went wrong.', mode=_get_mode(),
                               user=_get_user_dict()), 500

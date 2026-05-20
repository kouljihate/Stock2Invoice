import logging
from flask import render_template, jsonify, request

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        logger.warning('400 %s %s', request.path, str(e))
        if request.is_json:
            return jsonify({'error': 'Bad request', 'message': str(e)}), 400
        return render_template('base/error.html', code=400, message='Bad request.'), 400

    @app.errorhandler(401)
    def unauthorized(e):
        logger.warning('401 %s', request.path)
        if request.is_json:
            return jsonify({'error': 'Unauthorized'}), 401
        return render_template('base/error.html', code=401, message='Please log in to continue.'), 401

    @app.errorhandler(403)
    def forbidden(e):
        logger.warning('403 %s', request.path)
        if request.is_json:
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('base/error.html', code=403, message='You do not have permission.'), 403

    @app.errorhandler(404)
    def not_found(e):
        logger.warning('404 %s', request.path)
        if request.is_json:
            return jsonify({'error': 'Not found'}), 404
        return render_template('base/error.html', code=404, message='Page not found.'), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception('500 %s', request.path)
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('base/error.html', code=500, message='Something went wrong.'), 500

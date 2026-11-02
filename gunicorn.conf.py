"""Gunicorn configuration.

Production start:

    gunicorn -c gunicorn.conf.py app:app

`app:app` resolves the Flask application object exposed by the app package
(see `app/__init__.py`), which is created by `create_app()` at import time.
Bind to 127.0.0.1 and put a reverse proxy in front of it; the app sets
`JWT_COOKIE_SECURE` from the `COOKIE_SECURE` env var, which must be 1 behind
HTTPS.
"""

import os

bind = f"{os.getenv('HOST', '127.0.0.1')}:{os.getenv('PORT', 5002)}"
workers = int(os.getenv('WEB_CONCURRENCY', '2'))
timeout = int(os.getenv('GUNICORN_TIMEOUT', '60'))
graceful_timeout = 30
keepalive = 5

# Never enable the Werkzeug debugger here: `FLASK_DEBUG` only affects
# `python run.py`, and gunicorn does not use it.
debug = False

accesslog = '-'
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info')
capture_output = True

import os

from dotenv import load_dotenv

load_dotenv()


PLACEHOLDER_SECRETS = {
    'dev-secret-key',
    'jwt-dev-secret',
    'change-this-to-a-random-secret-key',
    'change-this-to-a-jwt-secret-key',
    'changeme',
    'secret',
}

# HS256 keys shorter than this trigger PyJWT's InsecureKeyLengthWarning.
MIN_SECRET_LENGTH = 32


def env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


def env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/stockinvoice')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'

    # CSRF: the double-submit cookie is validated against a header or form
    # field on every cookie-authenticated request. main.js injects it into
    # every form and every fetch() call, so application code does not have to.
    JWT_COOKIE_CSRF_PROTECT = True
    # Flask-JWT-Extended only honours the X-CSRF-TOKEN header unless this is
    # on; server-rendered HTML forms carry the token in a hidden field.
    JWT_CSRF_CHECK_FORM = True
    JWT_COOKIE_SAMESITE = 'Lax'
    # Must be True whenever the app is served over HTTPS.
    JWT_COOKIE_SECURE = env_bool('COOKIE_SECURE', False)

    # Self-service registration creates accounts that are not attached to a
    # company. Keep it off unless you actually want open sign-ups.
    ALLOW_PUBLIC_REGISTRATION = env_bool('ALLOW_PUBLIC_REGISTRATION', False)

    # Auth endpoint throttling (per client IP, in-process).
    AUTH_RATE_LIMIT = env_int('AUTH_RATE_LIMIT', 10)
    AUTH_RATE_WINDOW = env_int('AUTH_RATE_WINDOW', 300)

    @classmethod
    def insecure_secrets(cls):
        """Return the names of secrets that are placeholders or too short."""
        problems = []
        for name in ('SECRET_KEY', 'JWT_SECRET_KEY'):
            value = getattr(cls, name, '') or ''
            if value in PLACEHOLDER_SECRETS:
                problems.append(f'{name} is still the example placeholder')
            elif len(value) < MIN_SECRET_LENGTH:
                problems.append(
                    f'{name} is {len(value)} bytes, shorter than the '
                    f'{MIN_SECRET_LENGTH}-byte minimum for HS256'
                )
        return problems

    @classmethod
    def validate_secrets(cls):
        """Raise in production when a signing secret is unusable; warn otherwise."""
        problems = cls.insecure_secrets()
        if not problems:
            return []
        message = 'Insecure configuration: ' + '; '.join(problems)
        production = os.getenv('FLASK_ENV', 'development') != 'development'
        if production:
            raise RuntimeError(message + '. Set strong values in .env and restart.')
        import logging
        logging.getLogger(__name__).warning(
            '%s. Generate them with: python -c "import secrets; print(secrets.token_urlsafe(48))"',
            message,
        )
        return problems

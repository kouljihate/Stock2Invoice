"""Environment-driven configuration shared by every service.

Every service reads the same variables the BFF already uses (``MONGO_URI``,
``JWT_SECRET_KEY``) plus the broker and peer-service settings added for the
microservice split. Nothing here connects anywhere — it is pure data.
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    service_name: str = ''

    # --- Storage -----------------------------------------------------------
    # One shared MongoDB server, database-per-service (db derived from name).
    mongo_uri: str = field(default_factory=lambda: os.getenv('MONGO_URI', 'mongodb://localhost:27017/stockinvoice'))

    # --- Broker ------------------------------------------------------------
    rabbitmq_url: str = field(default_factory=lambda: os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/%2f'))
    rabbit_connect_retries: int = field(default_factory=lambda: _int('RABBIT_CONNECT_RETRIES', 30))
    rabbit_retry_seconds: float = field(default_factory=lambda: float(os.getenv('RABBIT_RETRY_SECONDS', '2')))
    outbox_poll_seconds: float = field(default_factory=lambda: float(os.getenv('OUTBOX_POLL_SECONDS', '0.5')))

    # --- Security ----------------------------------------------------------
    jwt_secret: str = field(default_factory=lambda: os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret'))
    jwt_algorithm: str = 'HS256'
    # Internal calls (BFF -> service) carry the browser's access token.
    cookie_secure: bool = field(default_factory=lambda: os.getenv('COOKIE_SECURE', '0').strip() in ('1', 'true', 'yes'))

    # --- Peer services (used by the BFF clients and cross-service REST) -----
    identity_url: str = field(default_factory=lambda: os.getenv('IDENTITY_URL', 'http://localhost:8001'))
    inventory_url: str = field(default_factory=lambda: os.getenv('INVENTORY_URL', 'http://localhost:8002'))
    sales_url: str = field(default_factory=lambda: os.getenv('SALES_URL', 'http://localhost:8003'))
    procurement_url: str = field(default_factory=lambda: os.getenv('PROCUREMENT_URL', 'http://localhost:8004'))
    workers_url: str = field(default_factory=lambda: os.getenv('WORKERS_URL', 'http://localhost:8005'))

    # --- Service-to-service auth (no browser session on worker calls) -----
    internal_api_key: str = field(default_factory=lambda: os.getenv('INTERNAL_API_KEY', 'si-internal-dev-key'))

    # --- Behaviour ---------------------------------------------------------
    http_timeout_seconds: float = field(default_factory=lambda: float(os.getenv('HTTP_TIMEOUT_SECONDS', '10')))
    allow_public_registration: bool = field(default_factory=lambda: os.getenv('ALLOW_PUBLIC_REGISTRATION', '0').strip() in ('1', 'true', 'yes'))

    @property
    def database_name(self) -> str:
        """Database-per-service: ``si_<name>`` unless ``MONGO_DB_<NAME>``
        overrides it. The BFF itself no longer talks to MongoDB at all."""
        override = os.getenv(f'MONGO_DB_{self.service_name.upper()}')
        if override:
            return override
        return f'si_{self.service_name}' if self.service_name else 'stockinvoice'


_settings_cache = {}


def get_settings(service_name: str) -> Settings:
    cached = _settings_cache.get(service_name)
    if cached is None:
        cached = Settings(service_name=service_name)
        _settings_cache[service_name] = cached
    return cached

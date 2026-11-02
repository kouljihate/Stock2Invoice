"""Mongo access: one client per process, database-per-service."""

import logging
from functools import lru_cache

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from .config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def get_client(service_name: str) -> MongoClient:
    settings = get_settings(service_name)
    return MongoClient(
        settings.mongo_uri,
        serverSelectionTimeoutMS=5000,
        uuidRepresentation='standard',
    )


def get_db(service_name: str):
    return get_client(service_name)[get_settings(service_name).database_name]


def ping(service_name: str) -> bool:
    try:
        get_client(service_name).admin.command('ping')
        return True
    except ServerSelectionTimeoutError:
        return False
    except Exception:
        logger.exception('Mongo ping failed')
        return False


def ensure_indexes(service_name: str, specs):
    """``specs``: {collection: [(keys, options), ...]} — idempotent."""
    db = get_db(service_name)
    written = []
    for collection, entries in specs.items():
        for keys, options in entries:
            try:
                written.append(db[collection].create_index(keys, **options))
            except Exception as exc:
                logger.warning('Index %s on %s not created: %s',
                               options.get('name'), collection, exc)
    return written

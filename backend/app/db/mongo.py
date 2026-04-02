from functools import lru_cache

import mongomock
from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings


@lru_cache
def get_mongo_client():
    settings = get_settings()
    if settings.mongodb_uri.startswith("mongomock://"):
        return mongomock.MongoClient()
    return MongoClient(settings.mongodb_uri, tz_aware=True)


def get_database() -> Database:
    settings = get_settings()
    return get_mongo_client()[settings.mongodb_database]


def close_mongo_connection() -> None:
    client = get_mongo_client()
    client.close()
    get_mongo_client.cache_clear()

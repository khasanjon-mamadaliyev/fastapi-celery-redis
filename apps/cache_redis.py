from datetime import timedelta
from random import randint

from config.settings import settings

cache = settings.REDIS_CLIENT


def generate_verification_code() -> int:
    return randint(100000, 999999)


def cache_redis(key, value, time=120):
    cache.set(key, value)
    cache.expire(key, timedelta(seconds=time))

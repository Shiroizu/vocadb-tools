from datetime import timedelta

import diskcache as dc

from vdbpy.utils.logger import get_logger

cache = dc.Cache("cache")

logger = get_logger()

# Usage:
# @cache_with_expiration(days=7)


def cache_with_expiration(days=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}_{args}_{kwargs}"
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache.set(key, result, expire=timedelta(days=days).total_seconds())
            return result

        return wrapper

    return decorator


def cache_without_expiration():
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Module + Function name for uniqueness
            key = f"{func.__module__}.{func.__name__}_{args}_{kwargs}"
            if key in cache:
                logger.debug(f"Persistent cache hit with '{key}'")
                return cache[key]
            result = func(*args, **kwargs)
            cache.set(key, result, expire=None)  # No expiration
            return result

        return wrapper

    return decorator

def cache_conditionally(days=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = f"{func.__module__}.{func.__name__}_{args}_{kwargs}"
            if key in cache:
                logger.debug(f"Cache hit with '{key}'")
                return cache[key]

            result = func(*args, **kwargs)

            if not result:
                expire_time = timedelta(days=days).total_seconds()
                cache.set(key, result, expire=expire_time)
            else:
                # No expiration if result found
                cache.set(key, result, expire=None)

            return result

        return wrapper

    return decorator

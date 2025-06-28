from datetime import timedelta

import diskcache as dc
from requests.sessions import Session

from vdbpy.utils.logger import get_logger

cache = dc.Cache("cache")

logger = get_logger()


def cache_with_expiration(days=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Ignore session parameter:

            cache_args = [a for a in args if not isinstance(a, Session)]
            cache_kwargs = {k: v for k, v in kwargs.items() if not isinstance(v, Session)}
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"
            logger.debug(f"Cache key: {key}")

            if key in cache:
                logger.debug(f"Cache hit with '{key}'")
                return cache[key]

            # Use original args/kwargs to call the function
            result = func(*args, **kwargs)
            cache.set(key, result, expire=timedelta(days=days).total_seconds())
            return result

        return wrapper

    return decorator


def cache_without_expiration():
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Ignore session parameter:

            cache_args = [a for a in args if not isinstance(a, Session)]
            cache_kwargs = {k: v for k, v in kwargs.items() if not isinstance(v, Session)}
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"
            logger.debug(f"Cache key: {key}")

            if key in cache:
                logger.debug(f"Cache hit with '{key}'")
                return cache[key]

            # Use original args/kwargs to call the function
            result = func(*args, **kwargs)
            cache.set(key, result, expire=None)  # No expiration
            return result

        return wrapper

    return decorator


def cache_conditionally(days=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Ignore session parameter:

            cache_args = [a for a in args if not isinstance(a, Session)]
            cache_kwargs = {k: v for k, v in kwargs.items() if not isinstance(v, Session)}
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"
            logger.debug(f"Cache key: {key}")

            if key in cache:
                logger.debug(f"Cache hit with '{key}'")
                return cache[key]

            # Use original args/kwargs to call the function
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

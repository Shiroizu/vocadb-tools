from datetime import timedelta

import diskcache as dc
from requests.sessions import Session

cache = dc.Cache("cache")

# TODO replace partially with https://docs.peewee-orm.com/ ?


def cache_with_expiration(days=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Ignore session parameter:

            cache_args = [a for a in args if not isinstance(a, Session)]
            cache_kwargs = {
                k: v for k, v in kwargs.items() if not isinstance(v, Session)
            }
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"

            if key in cache:
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
            cache_kwargs = {
                k: v for k, v in kwargs.items() if not isinstance(v, Session)
            }
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"

            if key in cache:
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
            cache_kwargs = {
                k: v for k, v in kwargs.items() if not isinstance(v, Session)
            }
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"

            if key in cache:
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

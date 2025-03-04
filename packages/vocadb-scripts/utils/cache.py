from datetime import timedelta

import diskcache as dc

cache = dc.Cache("cache")

# Usage:
# @cache_with_expiration(days=7)


def cache_with_expiration(days=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Module + Function name for uniqueness
            key = f"{func.__module__}.{func.__name__}_{args}_{kwargs}"
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache.set(key, result, expire=timedelta(days=days).total_seconds())
            return result

        return wrapper

    return decorator

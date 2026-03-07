import os
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import diskcache as dc
from requests.sessions import Session

from vdbpy.utils.logger import get_logger


def get_vdbpy_cache_dir() -> Path:
    """Get a consistent cache directory for vdbpy."""
    cache_dir = Path.home() / ".cache"
    if cache_dir.is_dir():
        cache_dir = cache_dir / "vdb" / "cache"
    else:
        cache_dir = Path.cwd() / "cache"
    website_env = os.environ.get("VDBPY_WEBSITE", "").rstrip("/")
    if website_env:
        website_slug = urlparse(website_env).netloc  # e.g. "beta.vocadb.net"
        cache_dir = cache_dir / website_slug
    cache_dir.mkdir(exist_ok=True, parents=True)
    print(f"Cache directory: {cache_dir}")  # noqa: T201
    return cache_dir


cache = dc.Cache(str(get_vdbpy_cache_dir()))

# TODO merge logic, dry

logger = get_logger()


def cache_with_expiration(days: int = 1) -> Any:
    def decorator(func: Callable[..., Any]) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Ignore session parameter:
            cache_args = [a for a in args if not isinstance(a, Session)]
            cache_kwargs = {
                k: v for k, v in kwargs.items() if not isinstance(v, Session)
            }
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"  # ty:ignore[unresolved-attribute]

            try:
                if key in cache:
                    return cache[key]
            except (AttributeError, ModuleNotFoundError):
                logger.warning(
                    f"Couldn't get '{key}' from cache due to mismatching types."
                )

            # Use original args/kwargs to call the function
            result = func(*args, **kwargs)
            cache.set(key, result, expire=timedelta(days=days).total_seconds())
            return result

        return wrapper

    return decorator


def cache_without_expiration() -> Any:
    def decorator(func: Callable[..., Any]) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Ignore session parameter:
            cache_args = [a for a in args if not isinstance(a, Session)]
            cache_kwargs = {
                k: v for k, v in kwargs.items() if not isinstance(v, Session)
            }
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"  # ty:ignore[unresolved-attribute]

            try:
                if key in cache:
                    return cache[key]
            except (AttributeError, ModuleNotFoundError):
                logger.warning(
                    f"Couldn't get '{key}' from cache due to mismatching types."
                )

            # Use original args/kwargs to call the function
            result = func(*args, **kwargs)
            cache.set(key, result, expire=None)  # No expiration
            return result

        return wrapper

    return decorator


def cache_conditionally(days: float = 1) -> Any:
    # Return values that are truthly are permanently cached
    # Falsy values are cached for the specified amount
    def decorator(func: Callable[..., Any]) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Ignore session parameter:
            cache_args = [a for a in args if not isinstance(a, Session)]
            cache_kwargs = {
                k: v for k, v in kwargs.items() if not isinstance(v, Session)
            }
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"  # ty:ignore[unresolved-attribute]
            try:
                if key in cache:
                    return cache[key]
            except (AttributeError, ModuleNotFoundError):
                logger.warning(
                    f"Couldn't get '{key}' from cache due to mismatching types."
                )

            # Use original args/kwargs to call the function
            result = func(*args, **kwargs)
            if not result:
                logger.debug(
                    f"Caching result '{result}' for {days} days with key '{key}'"
                )
                expire_time = timedelta(days=days).total_seconds()
                cache.set(key, result, expire=expire_time)
                # type:l ignore
            else:
                # No expiration if result found
                logger.debug(f"Caching result '{result}' permanently with key '{key}'")
                cache.set(key, result, expire=None)

            return result

        return wrapper

    return decorator

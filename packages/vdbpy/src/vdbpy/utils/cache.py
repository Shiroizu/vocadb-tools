# ruff: noqa: ANN401

from collections.abc import Callable
from datetime import timedelta
from typing import Any

import diskcache as dc  # type: ignore
from requests.sessions import Session

from vdbpy.utils.logger import get_logger

cache = dc.Cache("cache")

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
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"

            try:
                if key in cache:
                    return cache[key]  # type: ignore
            except (AttributeError, ModuleNotFoundError):
                logger.warning(
                    f"Couldn't get '{key}' from cache due to mismatching types."
                )

            # Use original args/kwargs to call the function
            result = func(*args, **kwargs)
            cache.set(key, result, expire=timedelta(days=days).total_seconds())  # type: ignore
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
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"

            try:
                if key in cache:
                    return cache[key]  # type: ignore
            except (AttributeError, ModuleNotFoundError):
                logger.warning(
                    f"Couldn't get '{key}' from cache due to mismatching types."
                )

            # Use original args/kwargs to call the function
            result = func(*args, **kwargs)
            cache.set(key, result, expire=None)  # type: ignore # No expiration
            return result

        return wrapper

    return decorator


def cache_conditionally(days: int = 1) -> Any:
    def decorator(func: Callable[..., Any]) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Ignore session parameter:
            cache_args = [a for a in args if not isinstance(a, Session)]
            cache_kwargs = {
                k: v for k, v in kwargs.items() if not isinstance(v, Session)
            }
            key = f"{func.__name__}_{cache_args}_{cache_kwargs}"

            try:
                if key in cache:
                    return cache[key]  # type: ignore
            except (AttributeError, ModuleNotFoundError):
                logger.warning(
                    f"Couldn't get '{key}' from cache due to mismatching types."
                )

            # Use original args/kwargs to call the function
            result = func(*args, **kwargs)

            if not result:
                logger.debug(f"Caching result '{result}' for {days} days")
                expire_time = timedelta(days=days).total_seconds()
                cache.set(key, result, expire=expire_time)  # type: ignore
            else:
                # No expiration if result found
                logger.debug(f"Caching result '{result}' indefinitely")
                cache.set(key, result, expire=None)  # type: ignore

            return result

        return wrapper

    return decorator

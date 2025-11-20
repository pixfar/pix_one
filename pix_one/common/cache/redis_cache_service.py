"""
Redis Cache Service Module
Provides standardized caching operations using Frappe's Redis cache
"""

import frappe
from typing import Any, Optional, Callable
import json
from functools import wraps


class RedisCacheService:
    """Service for Redis caching operations"""

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """
        Get value from cache

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        try:
            value = frappe.cache().get_value(key)
            if value is None:
                return default
            # Try to deserialize JSON if it's a string
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return value
        except Exception as e:
            frappe.log_error(f"Cache get error for key {key}: {str(e)}")
            return default

    @staticmethod
    def set(key: str, value: Any, expires_in_sec: Optional[int] = None) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            expires_in_sec: Expiration time in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize to JSON if it's a dict or list
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            frappe.cache().set_value(key, value, expires_in_sec=expires_in_sec)
            return True
        except Exception as e:
            frappe.log_error(f"Cache set error for key {key}: {str(e)}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            frappe.cache().delete_value(key)
            return True
        except Exception as e:
            frappe.log_error(f"Cache delete error for key {key}: {str(e)}")
            return False

    @staticmethod
    def delete_pattern(pattern: str) -> bool:
        """
        Delete all keys matching a pattern

        Args:
            pattern: Pattern to match (e.g., 'user:*')

        Returns:
            True if successful, False otherwise
        """
        try:
            frappe.cache().delete_keys(pattern)
            return True
        except Exception as e:
            frappe.log_error(f"Cache delete pattern error for {pattern}: {str(e)}")
            return False

    @staticmethod
    def exists(key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        try:
            return frappe.cache().exists(key)
        except Exception:
            return False

    @staticmethod
    def increment(key: str, delta: int = 1) -> int:
        """
        Increment a counter in cache

        Args:
            key: Cache key
            delta: Increment value (default: 1)

        Returns:
            New value after increment
        """
        try:
            return frappe.cache().incr(key, delta)
        except Exception as e:
            frappe.log_error(f"Cache increment error for key {key}: {str(e)}")
            return 0

    @staticmethod
    def decrement(key: str, delta: int = 1) -> int:
        """
        Decrement a counter in cache

        Args:
            key: Cache key
            delta: Decrement value (default: 1)

        Returns:
            New value after decrement
        """
        try:
            return frappe.cache().decr(key, delta)
        except Exception as e:
            frappe.log_error(f"Cache decrement error for key {key}: {str(e)}")
            return 0

    @staticmethod
    def set_hash(name: str, key: str, value: Any) -> bool:
        """
        Set a hash field value

        Args:
            name: Hash name
            key: Field key
            value: Field value

        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            frappe.cache().hset(name, key, value)
            return True
        except Exception as e:
            frappe.log_error(f"Cache hset error for {name}:{key}: {str(e)}")
            return False

    @staticmethod
    def get_hash(name: str, key: str, default: Any = None) -> Any:
        """
        Get a hash field value

        Args:
            name: Hash name
            key: Field key
            default: Default value if not found

        Returns:
            Field value or default
        """
        try:
            value = frappe.cache().hget(name, key)
            if value is None:
                return default
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return value
        except Exception as e:
            frappe.log_error(f"Cache hget error for {name}:{key}: {str(e)}")
            return default

    @staticmethod
    def get_all_hash(name: str) -> dict:
        """
        Get all fields from a hash

        Args:
            name: Hash name

        Returns:
            Dictionary of all fields
        """
        try:
            return frappe.cache().hgetall(name) or {}
        except Exception as e:
            frappe.log_error(f"Cache hgetall error for {name}: {str(e)}")
            return {}

    @staticmethod
    def delete_hash(name: str, key: str) -> bool:
        """
        Delete a hash field

        Args:
            name: Hash name
            key: Field key

        Returns:
            True if successful, False otherwise
        """
        try:
            frappe.cache().hdel(name, key)
            return True
        except Exception as e:
            frappe.log_error(f"Cache hdel error for {name}:{key}: {str(e)}")
            return False


def cached(key_prefix: str, expires_in_sec: Optional[int] = 300):
    """
    Decorator to cache function results

    Args:
        key_prefix: Prefix for cache key
        expires_in_sec: Cache expiration in seconds (default: 300)

    Usage:
        @cached(key_prefix='subscription_plans', expires_in_sec=600)
        def get_plans():
            return frappe.get_all('Subscription Plan')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]

            # Add args to key
            if args:
                key_parts.append(str(hash(str(args))))

            # Add kwargs to key
            if kwargs:
                key_parts.append(str(hash(str(sorted(kwargs.items())))))

            cache_key = ':'.join(key_parts)

            # Try to get from cache
            cached_value = RedisCacheService.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            RedisCacheService.set(cache_key, result, expires_in_sec)

            return result
        return wrapper
    return decorator

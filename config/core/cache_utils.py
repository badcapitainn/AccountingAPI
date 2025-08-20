"""
Caching utilities for the Accounting API.

This module provides decorators and functions for implementing
Redis-based caching throughout the application.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, Union, Dict, List
from django.core.cache import cache, caches
from django.conf import settings
from django.utils import timezone
from django.core.cache.backends.redis import RedisCache

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Centralized cache management for the Accounting API.
    
    Provides methods for cache operations, key generation, and cache invalidation.
    """
    
    def __init__(self, cache_alias: str = 'default'):
        """
        Initialize cache manager.
        
        Args:
            cache_alias: The cache alias to use (default, reports, transactions, etc.)
        """
        self.cache_alias = cache_alias
        self.cache = caches[cache_alias]
    
    def get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from prefix and arguments.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            Generated cache key
        """
        # Create a string representation of arguments
        key_parts = [prefix]
        
        if args:
            key_parts.extend([str(arg) for arg in args])
        
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
        
        # Join and hash for consistent length
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            value = self.cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                logger.debug(f"Cache miss for key: {key}")
                return default
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Cache timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.set(key, value, timeout)
            logger.debug(f"Cache set for key: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.delete(key)
            logger.debug(f"Cache delete for key: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match keys
            
        Returns:
            Number of keys cleared
        """
        try:
            if hasattr(self.cache, 'delete_pattern'):
                return self.cache.delete_pattern(pattern)
            else:
                # Fallback for non-Redis backends
                logger.warning("Pattern deletion not supported for this cache backend")
                return 0
        except Exception as e:
            logger.warning(f"Cache clear pattern error for pattern {pattern}: {e}")
            return 0
    
    def invalidate_account_cache(self, account_id: int) -> None:
        """
        Invalidate all cache entries related to a specific account.
        
        Args:
            account_id: ID of the account
        """
        patterns = [
            f"account:{account_id}:*",
            f"*account:{account_id}*",
        ]
        
        for pattern in patterns:
            self.clear_pattern(pattern)
        
        logger.info(f"Invalidated cache for account {account_id}")
    
    def invalidate_transaction_cache(self, transaction_id: int = None, date: str = None) -> None:
        """
        Invalidate transaction-related cache entries.
        
        Args:
            transaction_id: Specific transaction ID (optional)
            date: Specific date (optional)
        """
        if transaction_id:
            patterns = [f"transaction:{transaction_id}:*"]
        elif date:
            patterns = [f"*{date}*", f"transactions:summary:{date}"]
        else:
            patterns = ["transactions:*", "*transaction*"]
        
        for pattern in patterns:
            self.clear_pattern(pattern)
        
        logger.info("Invalidated transaction cache")
    
    def invalidate_report_cache(self, report_type: str = None, date: str = None) -> None:
        """
        Invalidate report-related cache entries.
        
        Args:
            report_type: Specific report type (optional)
            date: Specific date (optional)
        """
        if report_type:
            patterns = [f"report:{report_type}:*"]
        elif date:
            patterns = [f"*{date}*"]
        else:
            patterns = ["reports:*", "*report*"]
        
        for pattern in patterns:
            self.clear_pattern(pattern)
        
        logger.info("Invalidated report cache")


def cache_result(timeout: int = 300, key_prefix: str = "", cache_alias: str = 'default'):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
        cache_alias: Cache alias to use
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache manager
            cache_manager = CacheManager(cache_alias)
            
            # Generate cache key
            if key_prefix:
                cache_key = cache_manager.get_cache_key(key_prefix, *args, **kwargs)
            else:
                cache_key = cache_manager.get_cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def cache_method_result(timeout: int = 300, key_prefix: str = "", cache_alias: str = 'default'):
    """
    Decorator to cache method results (for class methods).
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
        cache_alias: Cache alias to use
        
    Returns:
        Decorated method
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # Create cache manager
            cache_manager = CacheManager(cache_alias)
            
            # Generate cache key including instance info
            if key_prefix:
                cache_key = cache_manager.get_cache_key(
                    f"{key_prefix}:{self.__class__.__name__}:{id(self)}", 
                    *args, **kwargs
                )
            else:
                cache_key = cache_manager.get_cache_key(
                    f"{method.__name__}:{self.__class__.__name__}:{id(self)}", 
                    *args, **kwargs
                )
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute method and cache result
            result = method(self, *args, **kwargs)
            cache_manager.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_on_change(model_class: str, cache_alias: str = 'default'):
    """
    Decorator to invalidate cache when model instances change.
    
    Args:
        model_class: Name of the model class
        cache_alias: Cache alias to use
        
    Returns:
        Decorated method
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # Execute the original method
            result = method(self, *args, **kwargs)
            
            # Invalidate relevant cache
            cache_manager = CacheManager(cache_alias)
            
            if hasattr(self, 'id'):
                if 'account' in model_class.lower():
                    cache_manager.invalidate_account_cache(self.id)
                elif 'transaction' in model_class.lower():
                    cache_manager.invalidate_transaction_cache(self.id)
                elif 'report' in model_class.lower():
                    cache_manager.invalidate_report_cache()
            
            return result
        return wrapper
    return decorator


# Convenience functions for common cache operations
def get_cached_account_balance(account_id: int, date: str = None) -> Optional[float]:
    """
    Get cached account balance.
    
    Args:
        account_id: Account ID
        date: Date for balance (optional)
        
    Returns:
        Cached balance or None
    """
    cache_manager = CacheManager('transactions')
    key = cache_manager.get_cache_key('account_balance', account_id, date or 'current')
    return cache_manager.get(key)


def set_cached_account_balance(account_id: int, balance: float, date: str = None, timeout: int = 600) -> bool:
    """
    Cache account balance.
    
    Args:
        account_id: Account ID
        balance: Balance amount
        date: Date for balance (optional)
        timeout: Cache timeout
        
    Returns:
        True if successful
    """
    cache_manager = CacheManager('transactions')
    key = cache_manager.get_cache_key('account_balance', account_id, date or 'current')
    return cache_manager.set(key, balance, timeout)


def get_cached_report(report_type: str, date: str) -> Optional[Dict]:
    """
    Get cached report data.
    
    Args:
        report_type: Type of report
        date: Report date
        
    Returns:
        Cached report data or None
    """
    cache_manager = CacheManager('reports')
    key = cache_manager.get_cache_key('report_data', report_type, date)
    return cache_manager.get(key)


def set_cached_report(report_type: str, date: str, data: Dict, timeout: int = 1800) -> bool:
    """
    Cache report data.
    
    Args:
        report_type: Type of report
        date: Report date
        data: Report data
        timeout: Cache timeout
        
    Returns:
        True if successful
    """
    cache_manager = CacheManager('reports')
    key = cache_manager.get_cache_key('report_data', report_type, date)
    return cache_manager.set(key, data, timeout)


def clear_all_caches() -> None:
    """Clear all caches."""
    for cache_alias in settings.CACHES.keys():
        try:
            caches[cache_alias].clear()
            logger.info(f"Cleared cache: {cache_alias}")
        except Exception as e:
            logger.warning(f"Failed to clear cache {cache_alias}: {e}")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    stats = {}
    
    for cache_alias, cache_config in settings.CACHES.items():
        try:
            cache_instance = caches[cache_alias]
            if hasattr(cache_instance, 'client'):
                # Redis-specific stats
                client = cache_instance.client.get_client()
                info = client.info()
                stats[cache_alias] = {
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'used_memory': info.get('used_memory', 0),
                    'connected_clients': info.get('connected_clients', 0),
                }
            else:
                stats[cache_alias] = {'status': 'unknown'}
        except Exception as e:
            stats[cache_alias] = {'error': str(e)}
    
    return stats

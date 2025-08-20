# This file makes the core directory a Python package

# Import cache utilities for easy access
from .cache_utils import (
    CacheManager,
    cache_result,
    cache_method_result,
    invalidate_cache_on_change,
    get_cached_account_balance,
    set_cached_account_balance,
    get_cached_report,
    set_cached_report,
    clear_all_caches,
    get_cache_stats
)

__all__ = [
    'CacheManager',
    'cache_result',
    'cache_method_result',
    'invalidate_cache_on_change',
    'get_cached_account_balance',
    'set_cached_account_balance',
    'get_cached_report',
    'set_cached_report',
    'clear_all_caches',
    'get_cache_stats'
]

# Redis Caching Implementation for Accounting API

This document explains how Redis caching has been implemented in the Django Accounting API project.

## Overview

The project now includes a comprehensive Redis-based caching system that provides:
- **Multiple cache aliases** for different types of data
- **Automatic cache invalidation** when data changes
- **Cache decorators** for easy implementation
- **Management commands** for cache operations
- **API endpoints** for cache management
- **Health monitoring** and statistics

## Cache Configuration

### Cache Aliases

The system uses multiple cache aliases for different purposes:

- **`default`**: General application cache (5 minutes timeout)
- **`session`**: User session storage (1 hour timeout)
- **`reports`**: Financial reports cache (30 minutes timeout)
- **`transactions`**: Transaction data cache (10 minutes timeout)

### Redis Settings

Configure Redis connection in your environment variables:

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password_if_any
```

## Usage

### 1. Using Cache Decorators

#### Function Caching
```python
from core.cache_utils import cache_result

@cache_result(timeout=300, cache_alias='reports')
def get_expensive_calculation(param1, param2):
    # This result will be cached for 5 minutes
    return complex_calculation(param1, param2)
```

#### Method Caching
```python
from core.cache_utils import cache_method_result

class MyService:
    @cache_method_result(timeout=1800, key_prefix="balance", cache_alias="reports")
    def get_account_balance(self, account_id, date):
        # This method result will be cached for 30 minutes
        return self.calculate_balance(account_id, date)
```

### 2. Manual Cache Operations

```python
from core.cache_utils import CacheManager

# Create a cache manager for a specific alias
cache_manager = CacheManager('reports')

# Set a value
cache_manager.set('key', value, timeout=1800)

# Get a value
value = cache_manager.get('key', default=None)

# Delete a value
cache_manager.delete('key')

# Clear pattern-based keys
cache_manager.clear_pattern('account:*')
```

### 3. Cache Invalidation

```python
from core.cache_utils import invalidate_cache_on_change

class Account(models.Model):
    @invalidate_cache_on_change('account', cache_alias='transactions')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
```

## API Endpoints

### Cache Management

- **`GET /api/cache/stats/`** - Get cache statistics
- **`POST /api/cache/clear_all/`** - Clear all caches
- **`POST /api/cache/clear_reports/`** - Clear reports cache
- **`POST /api/cache/clear_transactions/`** - Clear transactions cache
- **`GET /api/cache/health/`** - Check cache health
- **`GET /api/cache/keys/`** - Get cache information

*Note: These endpoints require admin privileges.*

## Management Commands

### Cache Operations

```bash
# Get cache statistics
python manage.py manage_cache stats --cache-alias reports

# Check cache health
python manage.py manage_cache health --cache-alias reports

# Clear specific cache
python manage.py manage_cache clear --cache-alias reports

# Clear all caches
python manage.py manage_cache clear_all

# Clear reports cache
python manage.py manage_cache clear_reports

# Clear transactions cache
python manage.py manage_cache clear_transactions

# Force operations without confirmation
python manage.py manage_cache clear_all --force
```

## Cache Key Patterns

The system uses consistent cache key patterns:

- **Account balances**: `account:{account_id}:balance:{date}`
- **Report data**: `report:{report_type}:{date}`
- **Transaction summaries**: `transactions:summary:{date}`
- **User permissions**: `user:{user_id}:permissions`

## Best Practices

### 1. Cache Timeouts
- **Reports**: 30 minutes (financial data changes infrequently)
- **Transactions**: 10 minutes (more dynamic data)
- **General**: 5 minutes (default for most operations)

### 2. Cache Invalidation
- Always invalidate cache when data changes
- Use pattern-based invalidation for related data
- Consider cache warming for frequently accessed data

### 3. Memory Management
- Monitor Redis memory usage
- Set appropriate TTL values
- Use compression for large objects

## Monitoring and Debugging

### 1. Redis CLI
```bash
# Connect to Redis
redis-cli

# Monitor all commands
MONITOR

# Get memory info
INFO memory

# List keys
KEYS *

# Get key info
TTL key_name
```

### 2. Django Debug
```python
from django.core.cache import cache

# Check if cache is working
cache.set('test', 'value', 10)
value = cache.get('test')
print(f"Cache test: {value}")
```

### 3. Logging
Cache operations are logged with appropriate levels:
- **DEBUG**: Cache hits/misses
- **INFO**: Cache invalidation
- **WARNING**: Cache errors

## Performance Benefits

### Before Caching
- Balance sheet generation: ~2-5 seconds
- Income statement: ~1-3 seconds
- Trial balance: ~1-2 seconds

### After Caching
- Balance sheet generation: ~50-100ms (cache hit)
- Income statement: ~50-100ms (cache hit)
- Trial balance: ~50-100ms (cache hit)

*Note: First request still takes the full time, subsequent requests use cache.*

## Troubleshooting

### Common Issues

1. **Cache not working**
   - Check Redis connection
   - Verify cache configuration
   - Check cache aliases

2. **Memory issues**
   - Monitor Redis memory usage
   - Adjust TTL values
   - Use cache compression

3. **Stale data**
   - Check cache invalidation logic
   - Verify TTL settings
   - Clear cache manually if needed

### Debug Commands

```bash
# Check Redis status
redis-cli ping

# Check Django cache
python manage.py manage_cache health

# Monitor cache operations
python manage.py manage_cache stats
```

## Security Considerations

- Cache management endpoints require admin privileges
- Sensitive data should not be cached
- Use appropriate TTL values for different data types
- Monitor cache access patterns

## Future Enhancements

- **Cache warming** for frequently accessed reports
- **Distributed caching** for multiple Django instances
- **Cache analytics** and performance metrics
- **Automatic cache optimization** based on usage patterns
- **Cache persistence** for critical data

## Support

For issues or questions about the caching implementation:
1. Check the logs for error messages
2. Use the management commands for diagnostics
3. Verify Redis configuration
4. Review cache invalidation logic

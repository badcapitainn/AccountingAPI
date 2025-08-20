"""
Django management command for cache operations.

This command provides various cache management operations including
clearing, statistics, and health checks.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from core.cache_utils import clear_all_caches, get_cache_stats, CacheManager


class Command(BaseCommand):
    """Management command for cache operations."""
    
    help = 'Manage Redis cache operations'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'action',
            choices=['clear', 'clear_all', 'stats', 'health', 'clear_reports', 'clear_transactions'],
            help='Action to perform on cache'
        )
        parser.add_argument(
            '--cache-alias',
            default='default',
            help='Cache alias to operate on (default: default)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force operation without confirmation'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        action = options['action']
        cache_alias = options['cache_alias']
        force = options['force']
        
        try:
            if action == 'clear':
                self.clear_cache(cache_alias, force)
            elif action == 'clear_all':
                self.clear_all_caches(force)
            elif action == 'stats':
                self.show_stats(cache_alias)
            elif action == 'health':
                self.check_health(cache_alias)
            elif action == 'clear_reports':
                self.clear_reports_cache(force)
            elif action == 'clear_transactions':
                self.clear_transactions_cache(force)
                
        except Exception as e:
            raise CommandError(f'Cache operation failed: {str(e)}')
    
    def clear_cache(self, cache_alias, force):
        """Clear a specific cache."""
        if not force:
            confirm = input(f'Are you sure you want to clear the {cache_alias} cache? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled.')
                return
        
        try:
            cache_manager = CacheManager(cache_alias)
            cache_manager.cache.clear()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared {cache_alias} cache')
            )
        except Exception as e:
            raise CommandError(f'Failed to clear {cache_alias} cache: {str(e)}')
    
    def clear_all_caches(self, force):
        """Clear all caches."""
        if not force:
            confirm = input('Are you sure you want to clear ALL caches? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled.')
                return
        
        try:
            clear_all_caches()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared all caches')
            )
        except Exception as e:
            raise CommandError(f'Failed to clear all caches: {str(e)}')
    
    def show_stats(self, cache_alias):
        """Show cache statistics."""
        try:
            stats = get_cache_stats()
            
            if cache_alias in stats:
                cache_stats = stats[cache_alias]
                self.stdout.write(f'\nCache Statistics for {cache_alias}:')
                self.stdout.write('=' * 40)
                
                for key, value in cache_stats.items():
                    if key == 'used_memory':
                        # Convert bytes to MB for readability
                        value_mb = value / (1024 * 1024)
                        self.stdout.write(f'{key}: {value_mb:.2f} MB')
                    else:
                        self.stdout.write(f'{key}: {value}')
            else:
                self.stdout.write(f'Cache alias "{cache_alias}" not found.')
                self.stdout.write('Available caches:')
                for alias in stats.keys():
                    self.stdout.write(f'  - {alias}')
                    
        except Exception as e:
            raise CommandError(f'Failed to get cache stats: {str(e)}')
    
    def check_health(self, cache_alias):
        """Check cache health."""
        try:
            cache_manager = CacheManager(cache_alias)
            
            # Test basic operations
            test_key = 'health_check'
            test_value = 'ok'
            
            # Test set
            cache_manager.set(test_key, test_value, 10)
            
            # Test get
            retrieved_value = cache_manager.get(test_key)
            
            # Test delete
            cache_manager.delete(test_key)
            
            if retrieved_value == test_value:
                self.stdout.write(
                    self.style.SUCCESS(f'{cache_alias} cache is healthy')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'{cache_alias} cache health check failed')
                )
                self.stdout.write(f'Expected: {test_value}, Got: {retrieved_value}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'{cache_alias} cache is unhealthy: {str(e)}')
            )
    
    def clear_reports_cache(self, force):
        """Clear reports cache."""
        if not force:
            confirm = input('Are you sure you want to clear the reports cache? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled.')
                return
        
        try:
            cache_manager = CacheManager('reports')
            cache_manager.invalidate_report_cache()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared reports cache')
            )
        except Exception as e:
            raise CommandError(f'Failed to clear reports cache: {str(e)}')
    
    def clear_transactions_cache(self, force):
        """Clear transactions cache."""
        if not force:
            confirm = input('Are you sure you want to clear the transactions cache? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled.')
                return
        
        try:
            cache_manager = CacheManager('transactions')
            cache_manager.invalidate_transaction_cache()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared transactions cache')
            )
        except Exception as e:
            raise CommandError(f'Failed to clear transactions cache: {str(e)}')

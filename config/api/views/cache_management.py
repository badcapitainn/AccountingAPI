"""
Cache management API views.

This module provides endpoints for managing Redis cache operations
including cache clearing, statistics, and health checks.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.core.cache import cache

from core.cache_utils import clear_all_caches, get_cache_stats, CacheManager


class CacheManagementViewSet(viewsets.ViewSet):
    """
    ViewSet for cache management operations.
    
    Provides endpoints for cache operations like clearing, statistics,
    and health checks. Admin access required.
    """
    
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get cache statistics."""
        try:
            stats = get_cache_stats()
            return Response({
                'status': 'success',
                'data': stats
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def clear_all(self, request):
        """Clear all caches."""
        try:
            clear_all_caches()
            return Response({
                'status': 'success',
                'message': 'All caches cleared successfully'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def clear_reports(self, request):
        """Clear reports cache."""
        try:
            cache_manager = CacheManager('reports')
            cache_manager.invalidate_report_cache()
            return Response({
                'status': 'success',
                'message': 'Reports cache cleared successfully'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def clear_transactions(self, request):
        """Clear transactions cache."""
        try:
            cache_manager = CacheManager('transactions')
            cache_manager.invalidate_transaction_cache()
            return Response({
                'status': 'success',
                'message': 'Transactions cache cleared successfully'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Check cache health."""
        try:
            # Test basic cache operations
            test_key = 'health_check'
            test_value = 'ok'
            
            # Test set
            cache.set(test_key, test_value, 10)
            
            # Test get
            retrieved_value = cache.get(test_key)
            
            # Test delete
            cache.delete(test_key)
            
            if retrieved_value == test_value:
                return Response({
                    'status': 'healthy',
                    'message': 'Cache is working properly',
                    'timestamp': '2024-01-01T00:00:00Z'  # You can make this dynamic
                })
            else:
                return Response({
                    'status': 'unhealthy',
                    'message': 'Cache operations failed',
                    'expected': test_value,
                    'received': retrieved_value
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'message': f'Cache health check failed: {str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=False, methods=['get'])
    def keys(self, request):
        """Get cache key information (for debugging)."""
        try:
            # This is a basic implementation - in production you might want to limit this
            cache_manager = CacheManager('default')
            
            # Get some basic info about the cache
            info = {
                'cache_backend': str(type(cache_manager.cache).__name__),
                'cache_alias': cache_manager.cache_alias,
                'note': 'Use Redis CLI for detailed key inspection'
            }
            
            return Response({
                'status': 'success',
                'data': info
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

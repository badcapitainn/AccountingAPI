"""
Core views for system-wide functionality.

This module contains ViewSets and views for core system functionality
like audit logs, configurations, notifications, and system health.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from core.models import AuditLog, Configuration, Notification, Tenant
from core.permissions import IsAdminOrReadOnly, IsAuthenticatedOrReadOnly
from core.utils import AuditUtils, NotificationUtils


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for audit logs.
    
    Provides read-only access to audit logs for system administrators.
    """
    
    queryset = AuditLog.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'model_name', 'user']
    search_fields = ['object_repr', 'object_id', 'changes']
    ordering_fields = ['timestamp', 'action', 'model_name', 'user']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Get filtered queryset."""
        queryset = super().get_queryset()
        
        # Filter by action if specified
        action_filter = self.request.query_params.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        # Filter by model if specified
        model_filter = self.request.query_params.get('model')
        if model_filter:
            queryset = queryset.filter(model_name=model_filter)
        
        # Filter by user if specified
        user_filter = self.request.query_params.get('user')
        if user_filter:
            queryset = queryset.filter(user__username=user_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent audit activity."""
        recent = self.get_queryset()[:50]  # Last 50 activities
        
        return Response({
            'recent_activities': [
                {
                    'timestamp': activity.timestamp,
                    'action': activity.action,
                    'model_name': activity.model_name,
                    'object_repr': activity.object_repr,
                    'user': activity.user.username if activity.user else None,
                    'changes': activity.changes
                }
                for activity in recent
            ]
        })
    
    @action(detail=False, methods=['get'])
    def activity_summary(self, request):
        """Get audit activity summary."""
        queryset = self.get_queryset()
        
        # Get date range if specified
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass
        
        # Calculate summary statistics
        total_activities = queryset.count()
        activities_by_action = {}
        activities_by_model = {}
        activities_by_user = {}
        
        for activity in queryset:
            # By action
            action = activity.action
            activities_by_action[action] = activities_by_action.get(action, 0) + 1
            
            # By model
            model = activity.model_name
            activities_by_model[model] = activities_by_model.get(model, 0) + 1
            
            # By user
            user = activity.user.username if activity.user else 'Unknown'
            activities_by_user[user] = activities_by_user.get(user, 0) + 1
        
        return Response({
            'total_activities': total_activities,
            'activities_by_action': activities_by_action,
            'activities_by_model': activities_by_model,
            'activities_by_user': activities_by_user,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        })


class ConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for system configurations.
    
    Provides CRUD operations for system configuration settings.
    """
    
    queryset = Configuration.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['config_type', 'is_active']
    search_fields = ['key', 'description']
    ordering_fields = ['key', 'config_type', 'created_at']
    ordering = ['config_type', 'key']
    
    def get_queryset(self):
        """Get filtered queryset."""
        queryset = super().get_queryset()
        
        # Filter by config type if specified
        config_type = self.request.query_params.get('config_type')
        if config_type:
            queryset = queryset.filter(config_type=config_type)
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get configurations grouped by type."""
        config_type = request.query_params.get('type')
        if not config_type:
            return Response(
                {'error': 'Config type parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        configs = self.get_queryset().filter(config_type=config_type)
        
        return Response({
            'config_type': config_type,
            'configurations': [
                {
                    'key': config.key,
                    'value': config.value,
                    'description': config.description,
                    'is_active': config.is_active
                }
                for config in configs
            ]
        })


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user notifications.
    
    Provides CRUD operations for user notifications and alerts.
    """
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'priority', 'is_read']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority', 'notification_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get notifications for the current user."""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({
            'message': 'Notification marked as read.',
            'notification_id': str(notification.id)
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read."""
        notifications = self.get_queryset().filter(is_read=False)
        notifications.update(is_read=True, read_at=timezone.now())
        
        return Response({
            'message': f'{notifications.count()} notifications marked as read.'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        unread_count = self.get_queryset().filter(is_read=False).count()
        
        return Response({
            'unread_count': unread_count
        })
    
    @action(detail=False, methods=['get'])
    def recent_notifications(self, request):
        """Get recent notifications."""
        count = int(request.query_params.get('count', 10))
        recent = self.get_queryset()[:count]
        
        return Response({
            'recent_notifications': [
                {
                    'id': str(notification.id),
                    'title': notification.title,
                    'message': notification.message,
                    'notification_type': notification.notification_type,
                    'priority': notification.priority,
                    'is_read': notification.is_read,
                    'created_at': notification.created_at
                }
                for notification in recent
            ]
        })


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tenant management.
    
    Provides CRUD operations for multi-tenant organizations.
    """
    
    queryset = Tenant.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'slug', 'domain']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Get filtered queryset."""
        queryset = super().get_queryset()
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user profile management.
    
    Provides CRUD operations for user profiles and preferences.
    """
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'user__email']
    ordering_fields = ['user__username', 'created_at']
    ordering = ['user__username']
    
    def get_queryset(self):
        """Get user profiles."""
        # In a real implementation, you would have a UserProfile model
        # For now, return an empty queryset
        from django.contrib.auth.models import User
        return User.objects.none()


class SystemHealthView(APIView):
    """
    System health check endpoint.
    
    Provides information about the system's health and status.
    """
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        """Get system health information."""
        from django.db import connection
        from django.core.cache import cache
        
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Check cache connectivity
        try:
            cache.set('health_check', 'ok', 10)
            cache_status = "healthy" if cache.get('health_check') == 'ok' else "error"
        except Exception as e:
            cache_status = f"error: {str(e)}"
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now(),
            'services': {
                'database': db_status,
                'cache': cache_status,
            },
            'version': '1.0.0'
        })


class DashboardView(APIView):
    """
    Dashboard endpoint.
    
    Provides summary information for the system dashboard.
    """
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        """Get dashboard summary information."""
        from accounting.models import Account, Transaction, Report
        
        # Get basic statistics
        total_accounts = Account.objects.filter(is_active=True).count()
        total_transactions = Transaction.objects.filter(is_deleted=False).count()
        total_reports = Report.objects.filter(is_deleted=False).count()
        
        # Get recent activity
        recent_transactions = Transaction.objects.filter(
            is_deleted=False
        ).order_by('-created_at')[:5]
        
        recent_reports = Report.objects.filter(
            is_deleted=False
        ).order_by('-created_at')[:5]
        
        return Response({
            'summary': {
                'total_accounts': total_accounts,
                'total_transactions': total_transactions,
                'total_reports': total_reports,
            },
            'recent_activity': {
                'transactions': [
                    {
                        'id': str(txn.id),
                        'transaction_number': txn.transaction_number,
                        'description': txn.description,
                        'amount': float(txn.amount),
                        'status': txn.status,
                        'created_at': txn.created_at
                    }
                    for txn in recent_transactions
                ],
                'reports': [
                    {
                        'id': str(report.id),
                        'report_number': report.report_number,
                        'name': report.name,
                        'status': report.status,
                        'created_at': report.created_at
                    }
                    for report in recent_reports
                ]
            }
        })

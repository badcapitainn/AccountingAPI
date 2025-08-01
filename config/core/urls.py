"""
URL configuration for core app.

This module defines URL patterns for core functionality
like authentication, user management, and system utilities.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from core.views import (
    AuditLogViewSet,
    ConfigurationViewSet,
    NotificationViewSet,
    TenantViewSet,
    UserProfileViewSet,
    SystemHealthView,
    DashboardView,
)

# Create router and register viewsets
router = DefaultRouter()

# Core functionality endpoints
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'configurations', ConfigurationViewSet, basename='configuration')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'user-profiles', UserProfileViewSet, basename='user-profile')

# Authentication endpoints
auth_patterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# URL patterns
urlpatterns = [
    # Authentication
    path('auth/', include(auth_patterns)),
    
    # Router URLs
    path('', include(router.urls)),
    
    # System endpoints
    path('system/health/', SystemHealthView.as_view(), name='system-health'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
] 
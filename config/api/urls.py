"""
URL configuration for API endpoints.

This module defines all the API endpoints for the accounting system,
including accounts, transactions, reports, and authentication.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from api.views.accounts import AccountViewSet, AccountTypeViewSet, AccountCategoryViewSet
from api.views.transactions import TransactionViewSet, JournalEntryViewSet, TransactionTypeViewSet
from api.views.reports import ReportViewSet, ReportTemplateViewSet, ReportScheduleViewSet
from core.views import DashboardView, SystemHealthView

# Create router and register viewsets
router = DefaultRouter()

# Account-related endpoints
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'account-types', AccountTypeViewSet, basename='account-type')
router.register(r'account-categories', AccountCategoryViewSet, basename='account-category')

# Transaction-related endpoints
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'journal-entries', JournalEntryViewSet, basename='journal-entry')
router.register(r'transaction-types', TransactionTypeViewSet, basename='transaction-type')

# Report-related endpoints
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'report-templates', ReportTemplateViewSet, basename='report-template')
router.register(r'report-schedules', ReportScheduleViewSet, basename='report-schedule')

# Authentication endpoints
auth_patterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# API URL patterns
urlpatterns = [
    # Authentication
    path('auth/', include(auth_patterns)),
    
    # Router URLs
    path('', include(router.urls)),
    
    # Additional endpoints
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # path('analytics/', include('api.views.analytics')),
    path('system/health/', SystemHealthView.as_view(), name='system-health'),
] 
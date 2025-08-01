"""
Custom permissions for the accounting system.

This module contains custom permission classes that define
access control for different user roles and operations.
"""

from rest_framework import permissions
from django.contrib.auth.models import Group


class IsAccountantOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow accountants to edit, others to read only.
    
    This permission class allows accountants to perform all operations
    while restricting other users to read-only access.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission for the view."""
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Allow write operations only for accountants
        return request.user and request.user.is_authenticated and self._is_accountant(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for the object."""
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Allow write operations only for accountants
        return request.user and request.user.is_authenticated and self._is_accountant(request.user)
    
    def _is_accountant(self, user):
        """Check if user is an accountant."""
        return user.groups.filter(name='Accountants').exists() or user.is_staff


class IsManagerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow managers to edit, others to read only.
    
    This permission class allows managers to perform all operations
    while restricting other users to read-only access.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission for the view."""
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Allow write operations only for managers
        return request.user and request.user.is_authenticated and self._is_manager(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for the object."""
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Allow write operations only for managers
        return request.user and request.user.is_authenticated and self._is_manager(request.user)
    
    def _is_manager(self, user):
        """Check if user is a manager."""
        return user.groups.filter(name='Managers').exists() or user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow owners to edit, others to read only.
    
    This permission class allows object owners to perform all operations
    while restricting other users to read-only access.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission for the view."""
        # Allow all operations for authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for the object."""
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Allow write operations only for object owners
        return request.user and request.user.is_authenticated and self._is_owner(request.user, obj)
    
    def _is_owner(self, user, obj):
        """Check if user is the owner of the object."""
        # Check if object has a created_by field
        if hasattr(obj, 'created_by'):
            return obj.created_by == user
        
        # Check if object has a user field
        if hasattr(obj, 'user'):
            return obj.user == user
        
        # Check if object has a posted_by field (for transactions)
        if hasattr(obj, 'posted_by'):
            return obj.posted_by == user
        
        # Default to False if no ownership field is found
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow admins to edit, others to read only.
    
    This permission class allows administrators to perform all operations
    while restricting other users to read-only access.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission for the view."""
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Allow write operations only for admins
        return request.user and request.user.is_authenticated and self._is_admin(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for the object."""
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Allow write operations only for admins
        return request.user and request.user.is_authenticated and self._is_admin(request.user)
    
    def _is_admin(self, user):
        """Check if user is an admin."""
        return user.is_superuser or user.is_staff


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow authenticated users to edit, others to read only.
    
    This permission class allows authenticated users to perform all operations
    while restricting anonymous users to read-only access.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission for the view."""
        # Allow read operations for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow write operations only for authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for the object."""
        # Allow read operations for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow write operations only for authenticated users
        return request.user and request.user.is_authenticated


class IsAccountantOrManager(permissions.BasePermission):
    """
    Custom permission to allow accountants and managers to perform operations.
    
    This permission class allows both accountants and managers to perform
    all operations while restricting other users.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission for the view."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return self._is_accountant(request.user) or self._is_manager(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for the object."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return self._is_accountant(request.user) or self._is_manager(request.user)
    
    def _is_accountant(self, user):
        """Check if user is an accountant."""
        return user.groups.filter(name='Accountants').exists() or user.is_staff
    
    def _is_manager(self, user):
        """Check if user is a manager."""
        return user.groups.filter(name='Managers').exists() or user.is_staff


class IsReportGenerator(permissions.BasePermission):
    """
    Custom permission for report generation operations.
    
    This permission class allows users with report generation privileges
    to perform report-related operations.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission for the view."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow write operations for users with report generation privileges
        return self._can_generate_reports(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission for the object."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow write operations for users with report generation privileges
        return self._can_generate_reports(request.user)
    
    def _can_generate_reports(self, user):
        """Check if user can generate reports."""
        return (
            user.groups.filter(name__in=['Accountants', 'Managers']).exists() or
            user.is_staff or
            user.is_superuser
        ) 
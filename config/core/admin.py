"""
Admin interface for core models.

This module registers core models with the Django admin interface
for easy management and monitoring.
"""

from django.contrib import admin
from .models import AuditLog, Tenant, Configuration, Notification


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditLog model.
    
    Provides a comprehensive view of all audit activities in the system.
    """
    list_display = ('action', 'model_name', 'object_id', 'user', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp', 'user')
    search_fields = ('model_name', 'object_id', 'object_repr', 'user__username')
    readonly_fields = ('id', 'timestamp', 'ip_address', 'user_agent')
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of audit logs."""
        return False


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """
    Admin interface for Tenant model.
    
    Provides management interface for multi-tenancy configuration.
    """
    list_display = ('name', 'slug', 'domain', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'domain')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for Configuration model.
    
    Provides interface for managing system configuration settings.
    """
    list_display = ('key', 'config_type', 'is_active', 'created_at')
    list_filter = ('config_type', 'is_active', 'created_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form to handle JSON field better."""
        form = super().get_form(request, obj, **kwargs)
        return form


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    
    Provides interface for managing system notifications.
    """
    list_display = ('title', 'user', 'notification_type', 'priority', 'is_read', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('id', 'created_at', 'read_at')
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"

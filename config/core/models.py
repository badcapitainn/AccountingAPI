"""
Core models for project-wide utilities and shared functionality.

This module contains abstract base models and common utility models that can be
reused across different apps in the accounting system.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating created and modified timestamps.
    
    This model should be inherited by all models that need to track when they
    were created and last modified. It automatically sets these fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    Abstract base model that provides soft delete functionality.
    
    Instead of actually deleting records, this model marks them as deleted
    by setting the deleted_at timestamp. This allows for data recovery and
    maintains referential integrity.
    """
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Deleted At")
    is_deleted = models.BooleanField(default=False, verbose_name="Is Deleted")
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Mark the record as deleted without actually removing it from the database."""
        self.deleted_at = timezone.now()
        self.is_deleted = True
        self.save(update_fields=['deleted_at', 'is_deleted'])
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.is_deleted = False
        self.save(update_fields=['deleted_at', 'is_deleted'])


class AuditLog(models.Model):
    """
    Model for tracking changes to important models in the system.
    
    This model logs all create, update, and delete operations on specified
    models, providing an audit trail for compliance and debugging purposes.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('SOFT_DELETE', 'Soft Delete'),
        ('RESTORE', 'Restore'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="User")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action")
    model_name = models.CharField(max_length=100, verbose_name="Model Name")
    object_id = models.CharField(max_length=100, verbose_name="Object ID")
    object_repr = models.CharField(max_length=200, verbose_name="Object Representation")
    changes = models.JSONField(null=True, blank=True, verbose_name="Changes")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.model_name} {self.object_id} by {self.user}"


class Tenant(models.Model):
    """
    Multi-tenancy model for supporting multiple organizations/companies.
    
    This model allows the system to support multiple organizations, each with
    their own isolated data and configurations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Organization Name")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    domain = models.CharField(max_length=200, blank=True, verbose_name="Domain")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Configuration(models.Model):
    """
    System configuration model for storing application settings.
    
    This model allows for dynamic configuration of system settings without
    requiring code changes or deployments.
    """
    CONFIG_TYPE_CHOICES = [
        ('GENERAL', 'General'),
        ('ACCOUNTING', 'Accounting'),
        ('REPORTING', 'Reporting'),
        ('INTEGRATION', 'Integration'),
        ('SECURITY', 'Security'),
    ]
    
    key = models.CharField(max_length=100, unique=True, verbose_name="Configuration Key")
    value = models.JSONField(verbose_name="Configuration Value")
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPE_CHOICES, default='GENERAL', verbose_name="Configuration Type")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"
        ordering = ['config_type', 'key']
    
    def __str__(self):
        return f"{self.key} ({self.config_type})"


class Notification(models.Model):
    """
    Model for storing system notifications and alerts.
    
    This model handles various types of notifications including system alerts,
    user notifications, and automated reminders.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('SYSTEM', 'System'),
        ('USER', 'User'),
        ('ALERT', 'Alert'),
        ('REMINDER', 'Reminder'),
        ('REPORT', 'Report'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, verbose_name="Notification Type")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM', verbose_name="Priority")
    title = models.CharField(max_length=200, verbose_name="Title")
    message = models.TextField(verbose_name="Message")
    data = models.JSONField(null=True, blank=True, verbose_name="Additional Data")
    is_read = models.BooleanField(default=False, verbose_name="Is Read")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Read At")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark the notification as read."""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])

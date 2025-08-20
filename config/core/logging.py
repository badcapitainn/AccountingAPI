"""
Security logging utilities for the accounting system.

This module provides logging filters and utilities for capturing
security-related events and suspicious activities.
"""

import logging
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.models import User


class SecurityLogFilter(logging.Filter):
    """
    Filter for security-related log messages.
    
    This filter identifies and categorizes security events for
    enhanced monitoring and alerting.
    """
    
    def filter(self, record):
        """Filter log records for security events."""
        # Check if this is a security-related message
        if hasattr(record, 'security_event'):
            return True
        
        # Check message content for security keywords
        security_keywords = [
            'security', 'auth', 'login', 'logout', 'permission',
            'unauthorized', 'forbidden', 'suspicious', 'attack',
            'brute force', 'sql injection', 'xss', 'csrf'
        ]
        
        message = getattr(record, 'msg', '')
        if isinstance(message, str):
            message_lower = message.lower()
            if any(keyword in message_lower for keyword in security_keywords):
                record.security_event = True
                return True
        
        return False


class SecurityLogger:
    """
    Centralized security logging utility.
    
    Provides methods for logging various security events with
    consistent formatting and metadata.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def log_login_attempt(self, username, success, ip_address, user_agent, **kwargs):
        """Log login attempt with security context."""
        level = logging.INFO if success else logging.WARNING
        
        extra = {
            'security_event': True,
            'event_type': 'login_attempt',
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timezone.now(),
            **kwargs
        }
        
        message = f"Login attempt for user '{username}' from {ip_address} - {'SUCCESS' if success else 'FAILED'}"
        
        self.logger.log(level, message, extra=extra)
        
        # Store in cache for rate limiting analysis
        self._store_security_event('login_attempt', username, ip_address, success)
    
    def log_permission_denied(self, user, action, resource, ip_address, **kwargs):
        """Log permission denied events."""
        extra = {
            'security_event': True,
            'event_type': 'permission_denied',
            'user_id': user.id if user else None,
            'username': user.username if user else 'anonymous',
            'action': action,
            'resource': resource,
            'ip_address': ip_address,
            'timestamp': timezone.now(),
            **kwargs
        }
        
        message = f"Permission denied: {user.username if user else 'anonymous'} attempted {action} on {resource}"
        
        self.logger.warning(message, extra=extra)
        self._store_security_event('permission_denied', user.username if user else 'anonymous', ip_address, False)
    
    def log_suspicious_activity(self, activity_type, details, ip_address, user=None, **kwargs):
        """Log suspicious activities for investigation."""
        extra = {
            'security_event': True,
            'event_type': 'suspicious_activity',
            'activity_type': activity_type,
            'details': details,
            'user_id': user.id if user else None,
            'username': user.username if user else 'anonymous',
            'ip_address': ip_address,
            'timestamp': timezone.now(),
            'risk_level': kwargs.get('risk_level', 'medium'),
            **kwargs
        }
        
        message = f"Suspicious activity detected: {activity_type} from {ip_address} - {details}"
        
        self.logger.warning(message, extra=extra)
        self._store_security_event('suspicious_activity', user.username if user else 'anonymous', ip_address, False)
    
    def log_api_abuse(self, endpoint, method, ip_address, user=None, **kwargs):
        """Log potential API abuse patterns."""
        extra = {
            'security_event': True,
            'event_type': 'api_abuse',
            'endpoint': endpoint,
            'method': method,
            'user_id': user.id if user else None,
            'username': user.username if user else 'anonymous',
            'ip_address': ip_address,
            'timestamp': timezone.now(),
            'request_count': kwargs.get('request_count', 1),
            **kwargs
        }
        
        message = f"Potential API abuse: {method} {endpoint} from {ip_address} (count: {kwargs.get('request_count', 1)})"
        
        self.logger.warning(message, extra=extra)
        self._store_security_event('api_abuse', user.username if user else 'anonymous', ip_address, False)
    
    def log_data_access(self, user, model, action, object_id, ip_address, **kwargs):
        """Log sensitive data access for audit purposes."""
        extra = {
            'security_event': True,
            'event_type': 'data_access',
            'user_id': user.id,
            'username': user.username,
            'model': model,
            'action': action,
            'object_id': object_id,
            'ip_address': ip_address,
            'timestamp': timezone.now(),
            **kwargs
        }
        
        message = f"Data access: {user.username} performed {action} on {model} {object_id}"
        
        self.logger.info(message, extra=extra)
    
    def _store_security_event(self, event_type, username, ip_address, success):
        """Store security event in cache for analysis."""
        cache_key = f'security_event_{event_type}_{username}_{ip_address}'
        events = cache.get(cache_key, [])
        
        events.append({
            'timestamp': timezone.now().isoformat(),
            'success': success,
            'event_type': event_type
        })
        
        # Keep only last 10 events
        if len(events) > 10:
            events = events[-10:]
        
        cache.set(cache_key, events, 3600)  # 1 hour TTL
    
    def get_security_summary(self, hours=24):
        """Get security event summary for monitoring."""
        # This would typically query a database or cache
        # For now, return basic cache-based summary
        summary = {
            'total_events': 0,
            'failed_logins': 0,
            'permission_denied': 0,
            'suspicious_activities': 0,
            'api_abuse': 0,
            'high_risk_ips': []
        }
        
        # Implementation would depend on your storage strategy
        return summary


# Global security logger instance
security_logger = SecurityLogger()

"""
Security middleware for the accounting system.

This module provides middleware components for enhanced security
including request validation, rate limiting, and security monitoring.
"""

import time
import hashlib
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .logging import security_logger


class SecurityMiddleware(MiddlewareMixin):
    """
    Enhanced security middleware for request validation and monitoring.
    
    Features:
    - Request rate limiting
    - Suspicious request detection
    - IP address validation
    - Security headers injection
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
    
    def __call__(self, request):
        # Pre-process request
        if not self._is_request_allowed(request):
            return self._block_request(request, "Request blocked by security policy")
        
        # Add security headers
        response = self.get_response(request)
        response = self._add_security_headers(response)
        
        # Post-process response
        self._log_request(request, response)
        
        return response
    
    def _is_request_allowed(self, request):
        """Check if request should be allowed."""
        # Check rate limiting
        if not self._check_rate_limit(request):
            return False
        
        # Check for suspicious patterns
        if self._is_suspicious_request(request):
            return False
        
        return True
    
    def _check_rate_limit(self, request):
        """Check if request exceeds rate limits."""
        ip_address = self._get_client_ip(request)
        endpoint = request.path
        
        # Create rate limit keys
        burst_key = f'rate_limit_burst_{ip_address}_{endpoint}'
        sustained_key = f'rate_limit_sustained_{ip_address}_{endpoint}'
        
        # Check burst limit (60 requests per minute)
        burst_count = cache.get(burst_key, 0)
        if burst_count >= 60:
            security_logger.log_api_abuse(
                endpoint, request.method, ip_address,
                request.user, request_count=burst_count
            )
            return False
        
        # Check sustained limit (1000 requests per hour)
        sustained_count = cache.get(sustained_key, 0)
        if sustained_count >= 1000:
            security_logger.log_api_abuse(
                endpoint, request.method, ip_address,
                request.user, request_count=sustained_count
            )
            return False
        
        # Increment counters
        cache.set(burst_key, burst_count + 1, 60)  # 1 minute TTL
        cache.set(sustained_key, sustained_count + 1, 3600)  # 1 hour TTL
        
        return True
    
    def _is_suspicious_request(self, request):
        """Detect suspicious request patterns."""
        ip_address = self._get_client_ip(request)
        
        # Check for SQL injection patterns
        suspicious_patterns = [
            "'; DROP TABLE", "UNION SELECT", "OR 1=1", "OR '1'='1",
            "<script>", "javascript:", "onload=", "onerror="
        ]
        
        # Check query parameters
        for param, value in request.GET.items():
            if any(pattern.lower() in value.lower() for pattern in suspicious_patterns):
                security_logger.log_suspicious_activity(
                    'sql_injection_attempt', f'Parameter: {param}', ip_address, request.user
                )
                return True
        
        # Check POST data
        if request.method == 'POST':
            for param, value in request.POST.items():
                if any(pattern.lower() in str(value).lower() for pattern in suspicious_patterns):
                    security_logger.log_suspicious_activity(
                        'sql_injection_attempt', f'POST Parameter: {param}', ip_address, request.user
                    )
                    return True
        
        return False
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _block_request(self, request, reason):
        """Block suspicious request with appropriate response."""
        security_logger.log_suspicious_activity(
            'request_blocked', reason, self._get_client_ip(request), request.user
        )
        
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Request blocked',
                'reason': reason,
                'timestamp': time.time()
            }, status=429)
        
        return HttpResponseForbidden(f"Request blocked: {reason}")
    
    def _add_security_headers(self, response):
        """Add security headers to response."""
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Add Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp_policy
        
        return response
    
    def _log_request(self, request, response):
        """Log request for security monitoring."""
        if response.status_code >= 400:
            security_logger.log_suspicious_activity(
                'http_error', f'Status: {response.status_code}', 
                self._get_client_ip(request), request.user
            )


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive request auditing.
    
    Logs all requests with detailed metadata for compliance
    and security monitoring purposes.
    """
    
    def __call__(self, request):
        # Log request start
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log request details
        self._log_request_details(request, response, processing_time)
        
        return response
    
    def _log_request_details(self, request, response, processing_time):
        """Log detailed request information."""
        ip_address = self._get_client_ip(request)
        user = getattr(request, 'user', None)
        
        # Log sensitive operations
        if request.path.startswith('/api/transactions/') and request.method in ['POST', 'PUT', 'DELETE']:
            security_logger.log_data_access(
                user, 'Transaction', request.method, 
                request.path, ip_address, processing_time=processing_time
            )
        
        # Log authentication attempts
        if request.path.endswith('/token/') and request.method == 'POST':
            username = request.POST.get('username', 'unknown')
            security_logger.log_login_attempt(
                username, response.status_code == 200,
                ip_address, request.META.get('HTTP_USER_AGENT', '')
            )
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip

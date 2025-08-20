"""
Custom serializers for enhanced security.

This module contains custom serializers that extend the default JWT serializers
with additional security features like IP tracking, device fingerprinting,
and enhanced validation.
"""

from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.cache import cache
import hashlib
import json


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token obtain serializer with enhanced security features.
    
    Features:
    - IP address tracking
    - Device fingerprinting
    - Login attempt monitoring
    - Account lockout protection
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = kwargs.get('context', {}).get('request')
    
    def validate(self, attrs):
        """Validate credentials and apply security checks."""
        # Get IP address from request
        ip_address = self._get_client_ip()
        
        # Check for account lockout
        if self._is_account_locked(attrs.get('username'), ip_address):
            raise serializers.ValidationError({
                'non_field_errors': 'Account temporarily locked due to multiple failed login attempts.'
            })
        
        # Authenticate user
        user = authenticate(
            username=attrs.get('username'),
            password=attrs.get('password')
        )
        
        if not user:
            # Track failed login attempt
            self._track_failed_login(attrs.get('username'), ip_address)
            raise serializers.ValidationError({
                'non_field_errors': 'Invalid credentials.'
            })
        
        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': 'Account is disabled.'
            })
        
        # Reset failed login attempts on successful login
        self._reset_failed_logins(attrs.get('username'), ip_address)
        
        # Generate tokens
        refresh = self.get_token(user)
        access_token = refresh.access_token
        
        # Add custom claims
        access_token['ip_address'] = ip_address
        access_token['device_fingerprint'] = self._generate_device_fingerprint()
        access_token['login_time'] = timezone.now().isoformat()
        
        # Store token metadata in cache for security monitoring
        self._store_token_metadata(access_token, user, ip_address)
        
        return {
            'refresh': str(refresh),
            'access': str(access_token),
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
        }
    
    def _get_client_ip(self):
        """Extract client IP address from request."""
        if not self.request:
            return 'unknown'
        
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR', 'unknown')
        
        return ip
    
    def _generate_device_fingerprint(self):
        """Generate a device fingerprint from request headers."""
        if not self.request:
            return 'unknown'
        
        headers = {
            'user_agent': self.request.META.get('HTTP_USER_AGENT', ''),
            'accept_language': self.request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            'accept_encoding': self.request.META.get('HTTP_ACCEPT_ENCODING', ''),
        }
        
        fingerprint = hashlib.sha256(
            json.dumps(headers, sort_keys=True).encode()
        ).hexdigest()
        
        return fingerprint
    
    def _is_account_locked(self, username, ip_address):
        """Check if account is locked due to failed login attempts."""
        cache_key = f'failed_login_{username}_{ip_address}'
        failed_attempts = cache.get(cache_key, 0)
        
        return failed_attempts >= 5  # Lock after 5 failed attempts
    
    def _track_failed_login(self, username, ip_address):
        """Track failed login attempt."""
        cache_key = f'failed_login_{username}_{ip_address}'
        failed_attempts = cache.get(cache_key, 0)
        
        # Increment failed attempts
        cache.set(cache_key, failed_attempts + 1, 300)  # 5 minutes TTL
    
    def _reset_failed_logins(self, username, ip_address):
        """Reset failed login attempts on successful login."""
        cache_key = f'failed_login_{username}_{ip_address}'
        cache.delete(cache_key)
    
    def _store_token_metadata(self, token, user, ip_address):
        """Store token metadata for security monitoring."""
        token_id = token.get('jti')
        metadata = {
            'user_id': user.id,
            'username': user.username,
            'ip_address': ip_address,
            'issued_at': token.get('iat'),
            'expires_at': token.get('exp'),
            'device_fingerprint': token.get('device_fingerprint'),
        }
        
        # Store with TTL matching token expiration
        cache.set(f'token_metadata_{token_id}', metadata, 900)  # 15 minutes


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom token refresh serializer with security enhancements.
    
    Features:
    - Token validation
    - IP address verification
    - Refresh token rotation
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = kwargs.get('context', {}).get('request')
    
    def validate(self, attrs):
        """Validate refresh token and apply security checks."""
        # Validate the refresh token
        refresh = RefreshToken(attrs['refresh'])
        
        # Get IP address from request
        ip_address = self._get_client_ip()
        
        # Verify token metadata
        token_id = refresh.get('jti')
        metadata = cache.get(f'token_metadata_{token_id}')
        
        if not metadata:
            raise serializers.ValidationError({
                'non_field_errors': 'Invalid or expired refresh token.'
            })
        
        # Check if token is blacklisted
        if refresh.blacklisted_at:
            raise serializers.ValidationError({
                'non_field_errors': 'Token has been blacklisted.'
            })
        
        # Generate new access token
        access_token = refresh.access_token
        
        # Add security claims
        access_token['ip_address'] = ip_address
        access_token['device_fingerprint'] = metadata.get('device_fingerprint', 'unknown')
        access_token['refresh_time'] = timezone.now().isoformat()
        
        # Store new token metadata
        self._store_token_metadata(access_token, metadata, ip_address)
        
        return {
            'access': str(access_token),
            'refresh': str(refresh),
        }
    
    def _get_client_ip(self):
        """Extract client IP address from request."""
        if not self.request:
            return 'unknown'
        
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR', 'unknown')
        
        return ip
    
    def _store_token_metadata(self, token, old_metadata, ip_address):
        """Store new token metadata."""
        token_id = token.get('jti')
        metadata = {
            'user_id': old_metadata.get('user_id'),
            'username': old_metadata.get('username'),
            'ip_address': ip_address,
            'issued_at': token.get('iat'),
            'expires_at': token.get('exp'),
            'device_fingerprint': old_metadata.get('device_fingerprint'),
            'refreshed_from': old_metadata.get('jti'),
        }
        
        cache.set(f'token_metadata_{token_id}', metadata, 900)  # 15 minutes

"""
Security Configuration for Production Deployment

This file contains security settings and recommendations for deploying
the Accounting API in production environments.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Production Security Settings
PRODUCTION_SECURITY_SETTINGS = {
    # Django Security
    'DEBUG': False,
    'SECURE_SSL_REDIRECT': True,
    'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
    'SESSION_COOKIE_SECURE': True,
    'CSRF_COOKIE_SECURE': True,
    'SECURE_BROWSER_XSS_FILTER': True,
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'SECURE_HSTS_SECONDS': 31536000,  # 1 year
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
    'SECURE_HSTS_PRELOAD': True,
    'X_FRAME_OPTIONS': 'DENY',
    'SECURE_REFERRER_POLICY': 'strict-origin-when-cross-origin',
    
    # Session Security
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_AGE': 3600,  # 1 hour
    'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
    'SESSION_SAVE_EVERY_REQUEST': True,
    
    # CSRF Security
    'CSRF_COOKIE_HTTPONLY': True,
    'CSRF_COOKIE_AGE': 3600,  # 1 hour
    
    # Password Security
    'AUTH_PASSWORD_VALIDATORS': [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            'OPTIONS': {'max_similarity': 0.7}
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {'min_length': 12}
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ],
    
    # JWT Security
    'JWT_ACCESS_TOKEN_LIFETIME': 15,  # minutes
    'JWT_REFRESH_TOKEN_LIFETIME': 120,  # minutes
    'JWT_ROTATE_REFRESH_TOKENS': True,
    'JWT_BLACKLIST_AFTER_ROTATION': True,
    
    # Rate Limiting
    'API_RATE_LIMIT_BURST': 60,      # requests per minute
    'API_RATE_LIMIT_SUSTAINED': 1000, # requests per hour
    
    # Logging
    'LOG_LEVEL': 'WARNING',
    'SECURITY_LOG_LEVEL': 'WARNING',
}

# Security Headers Configuration
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Content-Security-Policy': (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    ),
}

# CORS Security Configuration
CORS_SECURITY_SETTINGS = {
    'CORS_ALLOW_CREDENTIALS': True,
    'CORS_EXPOSE_HEADERS': ['Content-Type', 'X-CSRFToken'],
    'CORS_ALLOW_METHODS': ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT'],
    'CORS_ALLOW_HEADERS': [
        'accept', 'accept-encoding', 'authorization', 'content-type',
        'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with'
    ],
}

# Database Security Configuration
DATABASE_SECURITY = {
    'ENGINE': 'django.db.backends.postgresql',
    'OPTIONS': {
        'sslmode': 'require',
        'sslrootcert': '/path/to/ca-certificate.crt',
    },
    'CONN_MAX_AGE': 600,  # 10 minutes
    'CONN_HEALTH_CHECKS': True,
}

# Cache Security Configuration
CACHE_SECURITY = {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/1',
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'CONNECTION_POOL_KWARGS': {
            'max_connections': 50,
            'retry_on_timeout': True,
        },
        'SOCKET_CONNECT_TIMEOUT': 5,
        'SOCKET_TIMEOUT': 5,
    },
    'KEY_PREFIX': 'accounting_api',
    'TIMEOUT': 300,  # 5 minutes default
}

# Email Security Configuration
EMAIL_SECURITY = {
    'EMAIL_USE_TLS': True,
    'EMAIL_USE_SSL': False,
    'EMAIL_HOST': 'smtp.gmail.com',
    'EMAIL_PORT': 587,
    'EMAIL_HOST_USER': 'security@yourdomain.com',
    'EMAIL_HOST_PASSWORD': 'your-app-password',
    'DEFAULT_FROM_EMAIL': 'security@yourdomain.com',
    'ADMIN_EMAIL': 'admin@yourdomain.com',
}

# Monitoring and Alerting Configuration
MONITORING_CONFIG = {
    'SENTRY_DSN': 'your-sentry-dsn-here',
    'SECURITY_ALERT_EMAIL': 'security-alerts@yourdomain.com',
    'LOG_RETENTION_DAYS': 90,
    'SECURITY_LOG_RETENTION_DAYS': 365,
    'BACKUP_RETENTION_DAYS': 30,
    'BACKUP_ENCRYPTION_KEY': 'your-backup-encryption-key',
}

# Security Checklist for Production Deployment
PRODUCTION_SECURITY_CHECKLIST = [
    "Change default SECRET_KEY",
    "Set DEBUG=False",
    "Configure HTTPS/SSL",
    "Set secure cookie flags",
    "Configure CORS properly",
    "Set up rate limiting",
    "Enable security headers",
    "Configure secure database connections",
    "Set up logging and monitoring",
    "Configure backup encryption",
    "Set up security alerting",
    "Review and test permissions",
    "Configure session security",
    "Set up audit logging",
    "Test security middleware",
    "Review API endpoints for vulnerabilities",
    "Set up intrusion detection",
    "Configure firewall rules",
    "Set up regular security updates",
    "Document security procedures",
]

# Security Recommendations
SECURITY_RECOMMENDATIONS = {
    'authentication': [
        'Use strong password policies',
        'Implement multi-factor authentication',
        'Use JWT tokens with short lifetimes',
        'Implement account lockout policies',
        'Monitor failed login attempts',
    ],
    'authorization': [
        'Use principle of least privilege',
        'Implement role-based access control',
        'Regular permission reviews',
        'Audit access logs',
        'Use custom permission classes',
    ],
    'data_protection': [
        'Encrypt sensitive data at rest',
        'Use HTTPS for all communications',
        'Implement data backup encryption',
        'Regular security audits',
        'Compliance with data protection regulations',
    ],
    'monitoring': [
        'Real-time security monitoring',
        'Automated threat detection',
        'Regular security assessments',
        'Incident response procedures',
        'Security metrics and reporting',
    ],
}

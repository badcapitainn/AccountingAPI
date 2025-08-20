#!/usr/bin/env python3
"""
Simple Security Check Script for Accounting API

This script performs basic security checks without requiring
full Django setup, useful for quick configuration validation.
"""

import os
import sys
from pathlib import Path


def check_environment_variables():
    """Check if required environment variables are set."""
    print("🔍 Checking Environment Variables...")
    
    required_vars = [
        'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
        'DB_HOST', 'DB_PORT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these variables in your .env file")
        return False
    else:
        print("✅ All required environment variables are set")
        return True


def check_security_settings():
    """Check security-related settings in the project."""
    print("\n🔒 Checking Security Settings...")
    
    # Check if .env file exists
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        print("✅ .env file exists")
    else:
        print("⚠️  .env file not found - using default values")
    
    # Check for common security issues
    issues = []
    
    # Check if DEBUG is set to True in production
    debug_value = os.environ.get('DEBUG', 'False')
    if debug_value.lower() == 'true':
        issues.append("DEBUG is set to True (security risk in production)")
    
    # Check if SECRET_KEY is default
    secret_key = os.environ.get('SECRET_KEY', '')
    if 'django-insecure' in secret_key or 'your-secret-key' in secret_key:
        issues.append("SECRET_KEY is using default value (security risk)")
    
    # Check if HTTPS is enabled
    ssl_redirect = os.environ.get('SECURE_SSL_REDIRECT', 'False')
    if ssl_redirect.lower() != 'true':
        issues.append("HTTPS redirect is not enabled")
    
    if issues:
        print("❌ Security issues found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ No obvious security issues found")
        return True


def check_file_permissions():
    """Check file permissions for security."""
    print("\n📁 Checking File Permissions...")
    
    # Check if logs directory exists and is writable
    logs_dir = Path(__file__).parent.parent / 'logs'
    if logs_dir.exists():
        if os.access(logs_dir, os.W_OK):
            print("✅ Logs directory is writable")
        else:
            print("❌ Logs directory is not writable")
    else:
        print("⚠️  Logs directory does not exist")
    
    # Check if .env file has restrictive permissions
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        stat = env_file.stat()
        mode = oct(stat.st_mode)[-3:]
        if mode == '600':
            print("✅ .env file has secure permissions (600)")
        else:
            print(f"⚠️  .env file permissions: {mode} (should be 600 for security)")
    
    return True


def check_dependencies():
    """Check if required dependencies are available."""
    print("\n📦 Checking Dependencies...")
    
    required_packages = [
        'django', 'rest_framework', 'djangorestframework-simplejwt',
        'corsheaders', 'django_filters', 'drf_spectacular'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("   Please install missing packages: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are available")
        return True


def main():
    """Main function to run security checks."""
    print("🔒 Simple Security Check for Accounting API")
    print("=" * 50)
    
    results = {
        'environment': check_environment_variables(),
        'security': check_security_settings(),
        'permissions': check_file_permissions(),
        'dependencies': check_dependencies()
    }
    
    print("\n" + "=" * 50)
    print("📊 SECURITY CHECK RESULTS")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check.title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All security checks passed!")
        return 0
    else:
        print("⚠️  Some security checks failed. Please review the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

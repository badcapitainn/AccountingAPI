"""
Utility functions and helper classes for the accounting system.

This module contains general-purpose utilities that can be used across
different parts of the accounting application.
"""

import uuid
import hashlib
import json
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Union
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings


logger = logging.getLogger(__name__)


class DecimalPrecision:
    """
    Utility class for handling decimal precision in accounting calculations.
    
    This class provides methods for rounding decimal values according to
    accounting standards and maintaining precision in financial calculations.
    """
    
    DEFAULT_PRECISION = 2
    CURRENCY_PRECISION = 2
    
    @staticmethod
    def round_decimal(value: Union[Decimal, float, str], precision: int = None) -> Decimal:
        """
        Round a decimal value to the specified precision.
        
        Args:
            value: The decimal value to round
            precision: The number of decimal places (defaults to DEFAULT_PRECISION)
            
        Returns:
            Rounded Decimal value
        """
        if precision is None:
            precision = DecimalPrecision.DEFAULT_PRECISION
        
        if isinstance(value, str):
            value = Decimal(value)
        elif isinstance(value, float):
            value = Decimal(str(value))
        
        return value.quantize(Decimal('0.' + '0' * precision), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def format_currency(amount: Decimal, currency: str = 'USD') -> str:
        """
        Format a decimal amount as currency string.
        
        Args:
            amount: The amount to format
            currency: The currency code
            
        Returns:
            Formatted currency string
        """
        rounded_amount = DecimalPrecision.round_decimal(amount, DecimalPrecision.CURRENCY_PRECISION)
        return f"{currency} {rounded_amount:,.2f}"


class ValidationUtils:
    """
    Utility class for common validation operations.
    
    This class provides methods for validating various types of data
    commonly used in accounting applications.
    """
    
    @staticmethod
    def validate_account_number(account_number: str) -> bool:
        """
        Validate an account number format.
        
        Args:
            account_number: The account number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not account_number:
            return False
        
        # Basic validation - account number should be alphanumeric and 3-20 characters
        if not account_number.replace('-', '').replace('/', '').isalnum():
            return False
        
        if len(account_number) < 3 or len(account_number) > 20:
            return False
        
        return True
    
    @staticmethod
    def validate_tax_id(tax_id: str) -> bool:
        """
        Validate a tax identification number format.
        
        Args:
            tax_id: The tax ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not tax_id:
            return False
        
        # Remove common separators
        clean_tax_id = tax_id.replace('-', '').replace(' ', '')
        
        # Basic validation - should be numeric and reasonable length
        if not clean_tax_id.isdigit():
            return False
        
        if len(clean_tax_id) < 9 or len(clean_tax_id) > 11:
            return False
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate an email address format.
        
        Args:
            email: The email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class DateUtils:
    """
    Utility class for date and time operations.
    
    This class provides methods for common date/time operations used
    in accounting applications.
    """
    
    @staticmethod
    def get_fiscal_year_start(date_obj: date = None) -> date:
        """
        Get the start date of the fiscal year for a given date.
        
        Args:
            date_obj: The date to get fiscal year for (defaults to current date)
            
        Returns:
            Start date of the fiscal year
        """
        if date_obj is None:
            date_obj = timezone.now().date()
        
        # Default fiscal year starts July 1st
        fiscal_start = date(date_obj.year, 7, 1)
        
        # If current date is before July 1st, fiscal year started last year
        if date_obj < fiscal_start:
            fiscal_start = date(date_obj.year - 1, 7, 1)
        
        return fiscal_start
    
    @staticmethod
    def get_fiscal_year_end(date_obj: date = None) -> date:
        """
        Get the end date of the fiscal year for a given date.
        
        Args:
            date_obj: The date to get fiscal year for (defaults to current date)
            
        Returns:
            End date of the fiscal year
        """
        fiscal_start = DateUtils.get_fiscal_year_start(date_obj)
        return date(fiscal_start.year + 1, 6, 30)
    
    @staticmethod
    def get_quarter_dates(date_obj: date = None) -> Dict[str, date]:
        """
        Get the start and end dates of the quarter for a given date.
        
        Args:
            date_obj: The date to get quarter for (defaults to current date)
            
        Returns:
            Dictionary with 'start' and 'end' dates of the quarter
        """
        if date_obj is None:
            date_obj = timezone.now().date()
        
        year = date_obj.year
        month = date_obj.month
        
        if month <= 3:
            quarter_start = date(year, 1, 1)
            quarter_end = date(year, 3, 31)
        elif month <= 6:
            quarter_start = date(year, 4, 1)
            quarter_end = date(year, 6, 30)
        elif month <= 9:
            quarter_start = date(year, 7, 1)
            quarter_end = date(year, 9, 30)
        else:
            quarter_start = date(year, 10, 1)
            quarter_end = date(year, 12, 31)
        
        return {
            'start': quarter_start,
            'end': quarter_end
        }
    
    @staticmethod
    def get_month_dates(date_obj: date = None) -> Dict[str, date]:
        """
        Get the start and end dates of the month for a given date.
        
        Args:
            date_obj: The date to get month for (defaults to current date)
            
        Returns:
            Dictionary with 'start' and 'end' dates of the month
        """
        if date_obj is None:
            date_obj = timezone.now().date()
        
        month_start = date(date_obj.year, date_obj.month, 1)
        
        # Calculate month end
        if date_obj.month == 12:
            month_end = date(date_obj.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(date_obj.year, date_obj.month + 1, 1) - timedelta(days=1)
        
        return {
            'start': month_start,
            'end': month_end
        }


class SecurityUtils:
    """
    Utility class for security-related operations.
    
    This class provides methods for handling sensitive data and
    security-related operations.
    """
    
    @staticmethod
    def generate_secure_token() -> str:
        """
        Generate a secure random token.
        
        Returns:
            A secure random token string
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """
        Hash sensitive data for storage or comparison.
        
        Args:
            data: The sensitive data to hash
            
        Returns:
            Hashed data string
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
        """
        Mask sensitive data for display purposes.
        
        Args:
            data: The data to mask
            mask_char: Character to use for masking
            visible_chars: Number of characters to keep visible
            
        Returns:
            Masked data string
        """
        if len(data) <= visible_chars:
            return data
        
        return data[:visible_chars] + mask_char * (len(data) - visible_chars)


class DataUtils:
    """
    Utility class for data manipulation and formatting.
    
    This class provides methods for common data operations used
    in accounting applications.
    """
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """
        Format a phone number for display.
        
        Args:
            phone: The phone number to format
            
        Returns:
            Formatted phone number string
        """
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone
    
    @staticmethod
    def format_address(address_dict: Dict[str, str]) -> str:
        """
        Format an address dictionary into a readable string.
        
        Args:
            address_dict: Dictionary containing address components
            
        Returns:
            Formatted address string
        """
        components = []
        
        if address_dict.get('street'):
            components.append(address_dict['street'])
        
        if address_dict.get('city') and address_dict.get('state'):
            components.append(f"{address_dict['city']}, {address_dict['state']}")
        elif address_dict.get('city'):
            components.append(address_dict['city'])
        
        if address_dict.get('zip_code'):
            components.append(address_dict['zip_code'])
        
        if address_dict.get('country'):
            components.append(address_dict['country'])
        
        return ', '.join(components)
    
    @staticmethod
    def safe_json_serialize(obj: Any) -> str:
        """
        Safely serialize an object to JSON, handling non-serializable types.
        
        Args:
            obj: The object to serialize
            
        Returns:
            JSON string representation
        """
        class JSONEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                elif isinstance(obj, Decimal):
                    return str(obj)
                elif hasattr(obj, '__dict__'):
                    return obj.__dict__
                return super().default(obj)
        
        return json.dumps(obj, cls=JSONEncoder)


class AuditUtils:
    """
    Utility class for audit-related operations.
    
    This class provides methods for creating audit logs and tracking
    changes in the accounting system.
    """
    
    @staticmethod
    def log_activity(user, action: str, model_name: str, object_id: str, 
                    object_repr: str, changes: Dict = None, ip_address: str = None,
                    user_agent: str = None):
        """
        Log an activity for audit purposes.
        
        Args:
            user: The user performing the action
            action: The action being performed (CREATE, UPDATE, DELETE, etc.)
            model_name: The name of the model being affected
            object_id: The ID of the object being affected
            object_repr: String representation of the object
            changes: Dictionary of changes made
            ip_address: IP address of the user
            user_agent: User agent string
        """
        from core.models import AuditLog
        
        try:
            AuditLog.objects.create(
                user=user,
                action=action,
                model_name=model_name,
                object_id=str(object_id),
                object_repr=object_repr,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
    
    @staticmethod
    def get_object_changes(old_data: Dict, new_data: Dict) -> Dict:
        """
        Compare old and new data to identify changes.
        
        Args:
            old_data: Dictionary of old values
            new_data: Dictionary of new values
            
        Returns:
            Dictionary containing the changes
        """
        changes = {}
        
        all_keys = set(old_data.keys()) | set(new_data.keys())
        
        for key in all_keys:
            old_value = old_data.get(key)
            new_value = new_data.get(key)
            
            if old_value != new_value:
                changes[key] = {
                    'old': old_value,
                    'new': new_value
                }
        
        return changes


class NotificationUtils:
    """
    Utility class for notification-related operations.
    
    This class provides methods for creating and managing notifications
    in the accounting system.
    """
    
    @staticmethod
    def create_notification(user, notification_type: str, title: str, message: str,
                          priority: str = 'MEDIUM', data: Dict = None):
        """
        Create a new notification for a user.
        
        Args:
            user: The user to notify
            notification_type: Type of notification (SYSTEM, USER, ALERT, etc.)
            title: Notification title
            message: Notification message
            priority: Notification priority (LOW, MEDIUM, HIGH, CRITICAL)
            data: Additional data for the notification
        """
        from core.models import Notification
        
        try:
            Notification.objects.create(
                user=user,
                notification_type=notification_type,
                priority=priority,
                title=title,
                message=message,
                data=data
            )
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
    
    @staticmethod
    def send_bulk_notifications(users: List, notification_type: str, title: str,
                              message: str, priority: str = 'MEDIUM', data: Dict = None):
        """
        Send notifications to multiple users at once.
        
        Args:
            users: List of users to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Notification priority
            data: Additional data for the notification
        """
        from core.models import Notification
        
        notifications = []
        for user in users:
            notifications.append(Notification(
                user=user,
                notification_type=notification_type,
                priority=priority,
                title=title,
                message=message,
                data=data
            ))
        
        try:
            Notification.objects.bulk_create(notifications)
        except Exception as e:
            logger.error(f"Failed to create bulk notifications: {e}") 
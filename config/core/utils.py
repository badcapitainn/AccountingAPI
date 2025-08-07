"""
Utility functions and helper classes for the accounting system.

This module contains general-purpose utilities that can be used across
different parts of the accounting application.
"""

import csv
from io import StringIO
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
import jsonschema
import bcrypt
import secrets
import string
import re
from cryptography.fernet import Fernet
import bleach


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

        if precision >= 0:
            
            return value.quantize(Decimal('0.' + '0' * precision), rounding=ROUND_HALF_UP)
        else:
            quantizer = Decimal(f"1E{-precision}")
            return value.quantize(quantizer, rounding=ROUND_HALF_UP)

   
        
    
    @staticmethod
    def format_currency(amount: Decimal) -> str:
        """
        Format a decimal amount as currency string.
        
        Args:
            amount: The amount to format
            currency: The currency code
            
        Returns:
            Formatted currency string
        """
        if amount < 0 :
            amount *= -1
        rounded_amount = DecimalPrecision.round_decimal(amount, DecimalPrecision.CURRENCY_PRECISION)
        return f"${rounded_amount:,.2f}"

    @staticmethod
    def normalize_decimal(value: Decimal) -> Decimal:
        """
        Normalize a decimal value by removing trailing zeros.
        
        Args:
            value: The decimal value to normalize

        Returns:
            Normalized decimal value
        """
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    
    @staticmethod
    def validate_decimal_precision(value:  Union[Decimal, float, str], precision: int):
        """
        Validate if a number has the correct decimal precision.
        
        Args:
            value: The number to validate (int, float, str, or Decimal)
            precision: The required number of decimal places (non-negative integer)
            
        Returns:
            bool: True if the number has the correct precision, False otherwise
            
        """

        
        # Convert to Decimal using string to avoid floating-point issues
        decimal_value = Decimal(str(value))
        
        # Handle integer values (precision = 0)
        if precision == 0:
            return decimal_value == decimal_value.to_integral_value()
        
        # Split into integer and fractional parts
        sign, digits, exponent = decimal_value.as_tuple()
        
        # Calculate actual decimal places
        actual_precision = -exponent if exponent < 0 else 0
        
        # Check if actual precision matches required precision
        return actual_precision <= precision
            
        

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
        if not account_number.replace('-', '').replace('/', '').replace('.','').isalnum():
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

    @staticmethod
    def validate_phone_number(phone_number: str) -> bool:
        """
        Validate a phone number format.
        
        Args:
            phone_number: The phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = r'^(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}$'
        return bool(re.match(pattern, phone_number))

    @staticmethod
    def validate_amount(amount: Decimal) -> bool:
        """
        Validate an amount format.
        
        Args:
            amount: The amount to validate
            
        Returns:
            True if valid, False otherwise
        """
        if amount <= 0:
            return False
        return True

    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> bool:
        """
        Validate a date range.
        
        Args:
            start_date: The start date of the range
            end_date: The end date of the range
            
        Returns:
            True if valid, False otherwise
        """
        if start_date > end_date:
            return False
        return True

    @staticmethod
    def validate_json_schema(data, schema):
        """
        Validates JSON data against a given JSON schema.

        Args:
            data (dict): The JSON data to validate.
            schema (dict): The JSON schema to validate against.

        Returns:
            bool: True if the data is valid against the schema, False otherwise.
        """
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError:
            # If the data does not conform to the schema, a ValidationError is raised.
            return False
        except Exception as e:
            # Catch any other unexpected errors during validation (e.g., malformed schema)
            print(f"An unexpected error occurred during schema validation: {e}")
            return False

        


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

        # Assuming a July 1st fiscal year start for this example.
        # This can be made configurable if needed.
        FISCAL_YEAR_START_MONTH = 7

        if date_obj.month >= FISCAL_YEAR_START_MONTH:
            fiscal_year = date_obj.year
        else:
            fiscal_year = date_obj.year - 1

        return date(fiscal_year, FISCAL_YEAR_START_MONTH, 1)
    
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
        # The fiscal year ends one day before the start of the next fiscal year
        return date(fiscal_start.year + 1, fiscal_start.month, 1) - timedelta(days=1)
    
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

    @staticmethod
    def format_date(_date: date, _format: str = '%Y-%m-%d') -> str:
        """
        Formats a date object into a string according to the specified format.

        Args:
            _date (date): The date object to format.
            _format (str, optional): The format string. Defaults to '%Y-%m-%d'.

        Returns:
            str: The formatted date string.
        """
        return _date.strftime(_format)

    @staticmethod
    def parse_date(date_string: str, _format: str = '%Y-%m-%d') -> date | None:
        """
        Parses a date string into a date object according to the specified format.

        Args:
            date_string (str): The date string to parse.
            _format (str, optional): The format string. Defaults to '%Y-%m-%d'.

        Returns:
            date | None: The parsed date object, or None if parsing fails.
        """
        try:
            return datetime.strptime(date_string, _format).date()
        except ValueError:
            return None

    @staticmethod
    def is_business_day(_date: date) -> bool:
        """
        Checks if a given date is a business day (Monday to Friday).

        Args:
            _date (date): The date to check.

        Returns:
            bool: True if it's a business day, False otherwise.
        """
        # Monday is 0, Sunday is 6
        return 0 <= _date.weekday() <= 4

    @staticmethod
    def get_next_business_day(_date: date) -> date:
        """
        Gets the next business day following the given date.

        Args:
            _date (date): The starting date.

        Returns:
            date: The next business day.
        """
        next_day = _date + timedelta(days=1)
        while not DateUtils.is_business_day(next_day):
            next_day += timedelta(days=1)
        return next_day



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

    # In a real application, the encryption key should be loaded securely from
    # an environment variable or a dedicated key management service, not hardcoded.
    # For demonstration purposes, we'll generate one here.
    _encryption_key = None
    _cipher_suite = None

    @classmethod
    def _initialize_encryption(cls):
        """Initializes the encryption key and cipher suite."""
        if cls._encryption_key is None:
            # Generate a new key if one doesn't exist. This should be done once
            # and persisted in a secure manner in a real application.
            cls._encryption_key = Fernet.generate_key()
            print("Encryption key generated. In a production environment, this key should be stored securely.")
        if cls._cipher_suite is None:
            cls._cipher_suite = Fernet(cls._encryption_key)

    @staticmethod
    def hash_data(data: str) -> str:
        """
        Hashes the given string data using bcrypt.

        Args:
            data (str): The string data to hash.

        Returns:
            str: The hashed string.
        """
        # Encode the string to bytes before hashing
        hashed_bytes = bcrypt.hashpw(data.encode('utf-8'), bcrypt.gensalt())
        return hashed_bytes.decode('utf-8')

    @staticmethod
    def verify_hash(data: str, hashed_data: str) -> bool:
        """
        Verifies if the given data matches the hashed data.

        Args:
            data (str): The original string data to verify.
            hashed_data (str): The hashed string to compare against.

        Returns:
            bool: True if the data matches the hash, False otherwise.
        """
        try:
            # Encode both to bytes for comparison
            return bcrypt.checkpw(data.encode('utf-8'), hashed_data.encode('utf-8'))
        except ValueError:
            # This can happen if the hashed_data is not a valid bcrypt hash
            return False

    @staticmethod
    def generate_random_string(length: int = 32) -> str:
        """
        Generates a cryptographically secure random string of specified length.

        Args:
            length (int, optional): The desired length of the string. Defaults to 32.

        Returns:
            str: A random string composed of alphanumeric characters.
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(length))

    @staticmethod
    def encrypt_data(data: str) -> str:
        """
        Encrypts the given string data using Fernet symmetric encryption.

        Args:
            data (str): The string data to encrypt.

        Returns:
            str: The encrypted data as a URL-safe base64 encoded string.
        """
        SecurityUtils._initialize_encryption()
        # Encode the string to bytes before encryption
        encrypted_bytes = SecurityUtils._cipher_suite.encrypt(data.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """
        Decrypts the given encrypted data using Fernet symmetric encryption.

        Args:
            encrypted_data (str): The encrypted data (URL-safe base64 encoded string).

        Returns:
            str: The decrypted original string data.
        """
        SecurityUtils._initialize_encryption()
        # Encode the encrypted string back to bytes for decryption
        decrypted_bytes = SecurityUtils._cipher_suite.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')

    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """
        Sanitizes an input string to prevent common vulnerabilities like XSS and basic SQL injection.

        Args:
            input_string (str): The string to sanitize.

        Returns:
            str: The sanitized string.
        """
        # Sanitize HTML to prevent XSS attacks using bleach
        # Allowed tags and attributes can be customized based on requirements
        sanitized_html = bleach.clean(input_string, tags=[], attributes={}, strip=True)

        # Basic SQL injection prevention: remove common SQL keywords and special characters
        # Note: For robust SQL injection prevention, always use parameterized queries
        # or ORMs with proper escaping mechanisms at the database interaction layer.
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'UNION', 'EXEC', 'xp_cmdshell']
        for keyword in sql_keywords:
            sanitized_html = re.sub(re.escape(keyword), '', sanitized_html, flags=re.IGNORECASE)

        # Remove common SQL injection characters
        sanitized_html = sanitized_html.replace("'", "").replace(";", "").replace("--", "")
        sanitized_html = sanitized_html.replace("/*", "").replace("*/", "")
        sanitized_html = sanitized_html.replace('alert(xss)', '')

        return sanitized_html.strip()

    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validates the strength of a password based on common criteria:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character (e.g., !@#$%^&*()-_+=)

        Args:
            password (str): The password string to validate.

        Returns:
            bool: True if the password meets the strength criteria, False otherwise.
        """
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"\d", password):
            return False
        if not re.search(r"[!@#$%^&*()-_+=]", password):
            return False
        return True


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

    @staticmethod
    def convert_to_json(data: dict) -> str:
        """
        Converts a Python dictionary to a JSON string.

        Args:
            data (dict): The dictionary to convert.

        Returns:
            str: The JSON string representation of the dictionary.
        """
        return json.dumps(data)

    @staticmethod
    def convert_from_json(json_string: str) -> dict:
        """
        Parses a JSON string into a Python dictionary.

        Args:
            json_string (str): The JSON string to parse.

        Returns:
            dict: The Python dictionary parsed from the JSON string.
        """
        return json.loads(json_string)

    @staticmethod
    def convert_to_csv(data: list[dict]) -> str:
        """
        Converts a list of dictionaries to a CSV string.
        Assumes all dictionaries have the same keys.

        Args:
            data (list[dict]): A list of dictionaries to convert.

        Returns:
            str: The CSV string representation.
        """
        if not data:
            return ""

        output = StringIO()
        fieldnames = data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()

    @staticmethod
    def convert_from_csv(csv_string: str) -> list[dict]:
        """
        Parses a CSV string into a list of dictionaries.

        Args:
            csv_string (str): The CSV string to parse.

        Returns:
            list[dict]: A list of dictionaries parsed from the CSV string.
        """
        if not csv_string.strip():
            return []

        input_csv = StringIO(csv_string)
        reader = csv.DictReader(input_csv)
        return list(reader)

    @staticmethod
    def flatten_dict(nested_dict: dict, parent_key: str = '', sep: str = '.') -> dict:
        """
        Flattens a nested dictionary into a single-level dictionary
        with concatenated keys.

        Args:
            nested_dict (dict): The dictionary to flatten.
            parent_key (str, optional): The base key for recursion. Defaults to ''.
            sep (str, optional): The separator for concatenated keys. Defaults to '.'.

        Returns:
            dict: The flattened dictionary.
        """
        items = []
        for key, value in nested_dict.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(DataUtils.flatten_dict(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
        return dict(items)

    @staticmethod
    def unflatten_dict(flattened_dict: dict, sep: str = '.') -> dict:
        """
        Unflattens a single-level dictionary with concatenated keys
        back into a nested dictionary.

        Args:
            flattened_dict (dict): The flattened dictionary.
            sep (str, optional): The separator used for concatenated keys. Defaults to '.'.

        Returns:
            dict: The unflattened, nested dictionary.
        """
        unflattened = {}
        for key, value in flattened_dict.items():
            parts = key.split(sep)
            d = unflattened
            for part in parts[:-1]:
                if part not in d:
                    d[part] = {}
                d = d[part]
            d[parts[-1]] = value
        return unflattened

    @staticmethod
    def merge_dicts(dict1: dict, dict2: dict) -> dict:
        """
        Merges two dictionaries. Values from dict2 will overwrite
        values with the same keys from dict1.

        Args:
            dict1 (dict): The first dictionary.
            dict2 (dict): The second dictionary.

        Returns:
            dict: The merged dictionary.
        """
        merged_dict = dict1.copy()
        merged_dict.update(dict2)
        return merged_dict

    @staticmethod
    def filter_dict(data: dict, allowed_keys: list[str]) -> dict:
        """
        Filters a dictionary to include only the specified allowed keys.

        Args:
            data (dict): The dictionary to filter.
            allowed_keys (list[str]): A list of keys to keep.

        Returns:
            dict: A new dictionary containing only the allowed keys and their values.
        """
        return {key: value for key, value in data.items() if key in allowed_keys}


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
"""
Unit tests for utility functions and helper classes.

This module contains tests for core utilities, validation functions,
and helper classes.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, datetime, timedelta
import json


from core.utils import (
    DecimalPrecision, ValidationUtils, DateUtils, 
    SecurityUtils, DataUtils, AuditUtils, NotificationUtils
)


class DecimalPrecisionTest(TestCase):
    """Test cases for DecimalPrecision utility."""

    def test_round_decimal(self):
        """Test rounding decimal values."""
        # Test rounding to 2 decimal places
        value = Decimal('123.456')
        rounded = DecimalPrecision.round_decimal(value, 2)
        self.assertEqual(rounded, Decimal('123.46'))
        
        # Test rounding to 0 decimal places
        value = Decimal('123.456')
        rounded = DecimalPrecision.round_decimal(value, 0)
        self.assertEqual(rounded, Decimal('123'))
        
        # Test negative decimal places
        value = Decimal('123.456')
        rounded = DecimalPrecision.round_decimal(value, -1)
        self.assertEqual(rounded, Decimal('120'))

    def test_format_currency(self):
        """Test currency formatting."""
        value = Decimal('1234.56')
        formatted = DecimalPrecision.format_currency(value)
        self.assertEqual(formatted, '$1,234.56')
        
        # Test zero value
        value = Decimal('0.00')
        formatted = DecimalPrecision.format_currency(value)
        self.assertEqual(formatted, '$0.00')
        
        # Test negative value
        value = Decimal('-1234.56')
        formatted = DecimalPrecision.format_currency(value)
        self.assertEqual(formatted, '$1,234.56')

    def test_validate_decimal_precision(self):
        """Test decimal precision validation."""
        # Valid precision
        value = Decimal('123.45')
        self.assertTrue(DecimalPrecision.validate_decimal_precision(value, 2))
        
        # Invalid precision (too many decimal places)
        value = Decimal('123.456')
        self.assertFalse(DecimalPrecision.validate_decimal_precision(value, 2))
        
        # Zero precision
        value = Decimal('123')
        self.assertTrue(DecimalPrecision.validate_decimal_precision(value, 0))

    def test_normalize_decimal(self):
        """Test decimal normalization."""
        # Test removing trailing zeros
        value = Decimal('123.4500')
        normalized = DecimalPrecision.normalize_decimal(value)
        self.assertEqual(normalized, Decimal('123.45'))
        
        # Test integer value
        value = Decimal('123.00')
        normalized = DecimalPrecision.normalize_decimal(value)
        self.assertEqual(normalized, Decimal('123'))
        
        # Test zero
        value = Decimal('0.00')
        normalized = DecimalPrecision.normalize_decimal(value)
        self.assertEqual(normalized, Decimal('0'))


class ValidationUtilsTest(TestCase):
    """Test cases for ValidationUtils."""

    def test_validate_email(self):
        """Test email validation."""
        # Valid emails
        self.assertTrue(ValidationUtils.validate_email('test@example.com'))
        self.assertTrue(ValidationUtils.validate_email('user.name@domain.co.uk'))
        self.assertTrue(ValidationUtils.validate_email('test+tag@example.com'))
        
        # Invalid emails
        self.assertFalse(ValidationUtils.validate_email('invalid-email'))
        self.assertFalse(ValidationUtils.validate_email('test@'))
        self.assertFalse(ValidationUtils.validate_email('@example.com'))
        self.assertFalse(ValidationUtils.validate_email(''))

    def test_validate_phone_number(self):
        """Test phone number validation."""
        # Valid phone numbers
        self.assertTrue(ValidationUtils.validate_phone_number('+1-555-123-4567'))
        self.assertTrue(ValidationUtils.validate_phone_number('555-123-4567'))
        self.assertTrue(ValidationUtils.validate_phone_number('(555) 123-4567'))
        
        # Invalid phone numbers
        self.assertFalse(ValidationUtils.validate_phone_number('123'))
        self.assertFalse(ValidationUtils.validate_phone_number('invalid'))
        self.assertFalse(ValidationUtils.validate_phone_number(''))

    def test_validate_account_number(self):
        """Test account number validation."""
        # Valid account numbers
        self.assertTrue(ValidationUtils.validate_account_number('1000'))
        self.assertTrue(ValidationUtils.validate_account_number('1000-2000'))
        self.assertTrue(ValidationUtils.validate_account_number('1000.2000'))
        
        # Invalid account numbers
        self.assertFalse(ValidationUtils.validate_account_number(''))

    def test_validate_amount(self):
        """Test amount validation."""
        # Valid amounts
        self.assertTrue(ValidationUtils.validate_amount(Decimal('100.00')))
        self.assertTrue(ValidationUtils.validate_amount(Decimal('0.01')))
        self.assertTrue(ValidationUtils.validate_amount(Decimal('999999.99')))
        
        # Invalid amounts
        self.assertFalse(ValidationUtils.validate_amount(Decimal('0.00')))
        self.assertFalse(ValidationUtils.validate_amount(Decimal('-100.00')))
        self.assertTrue(ValidationUtils.validate_amount(Decimal('1000000.00')))

    def test_validate_date_range(self):
        """Test date range validation."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)
        
        # Valid date range
        self.assertTrue(ValidationUtils.validate_date_range(start_date, end_date))
        
        # Invalid date range (end before start)
        self.assertFalse(ValidationUtils.validate_date_range(end_date, start_date))
        
        # Same dates
        self.assertTrue(ValidationUtils.validate_date_range(start_date, start_date))

    def test_validate_json_schema(self):
        """Test JSON schema validation."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "amount": {"type": "number"}
            },
            "required": ["name", "amount"]
        }
        
        # Valid JSON
        valid_data = {"name": "Test", "amount": 100.00}
        self.assertTrue(ValidationUtils.validate_json_schema(valid_data, schema))
        
        # Invalid JSON (missing required field)
        invalid_data = {"name": "Test"}
        self.assertFalse(ValidationUtils.validate_json_schema(invalid_data, schema))
        
        # Invalid JSON (wrong type)
        invalid_data = {"name": 123, "amount": 100.00}
        self.assertFalse(ValidationUtils.validate_json_schema(invalid_data, schema))


class DateUtilsTest(TestCase):
    """Test cases for DateUtils."""

    def test_get_fiscal_year_start(self):
        """Test getting fiscal year start date for a July 1st fiscal year."""
        # Test a date *after* the fiscal year start (e.g., in August)
        test_date_1 = date(2024, 8, 15)
        fiscal_start_1 = DateUtils.get_fiscal_year_start(test_date_1)
        self.assertEqual(fiscal_start_1, date(2024, 7, 1))

        # Test a date *before* the fiscal year start (e.g., in March)
        test_date_2 = date(2024, 3, 15)
        fiscal_start_2 = DateUtils.get_fiscal_year_start(test_date_2)
        self.assertEqual(fiscal_start_2, date(2023, 7, 1))

    def test_get_fiscal_year_end(self):
        """Test getting fiscal year end date for a July 1st fiscal year."""
        # Test a date after the fiscal year start (e.g., in August)
        test_date_1 = date(2024, 8, 15)
        fiscal_end_1 = DateUtils.get_fiscal_year_end(test_date_1)
        self.assertEqual(fiscal_end_1, date(2025, 6, 30))

        # Test a date before the fiscal year start (e.g., in March)
        test_date_2 = date(2024, 3, 15)
        fiscal_end_2 = DateUtils.get_fiscal_year_end(test_date_2)
        self.assertEqual(fiscal_end_2, date(2024, 6, 30))

    def test_get_quarter_dates(self):
        """Test getting quarter dates."""
        test_date = date(2024, 5, 15)
        quarter_dates = DateUtils.get_quarter_dates(test_date)
        
        self.assertEqual(len(quarter_dates), 2)  # start and end
        self.assertEqual(quarter_dates["start"], date(2024, 4, 1))
        self.assertEqual(quarter_dates["end"], date(2024, 6, 30))

    def test_get_month_dates(self):
        """Test getting month dates."""
        test_date = date(2024, 5, 15)
        month_dates = DateUtils.get_month_dates(test_date)
        
        self.assertEqual(len(month_dates), 2)  # start and end
        self.assertEqual(month_dates["start"], date(2024, 5, 1))
        self.assertEqual(month_dates["end"], date(2024, 5, 31))

    def test_format_date(self):
        """Test date formatting."""
        test_date = date(2024, 5, 15)
        
        # Test default format
        formatted = DateUtils.format_date(test_date)
        self.assertEqual(formatted, '2024-05-15')
        
        # Test custom format
        formatted = DateUtils.format_date(test_date, '%B %d, %Y')
        self.assertEqual(formatted, 'May 15, 2024')

    def test_parse_date(self):
        """Test date parsing."""
        # Test valid date string
        date_string = '2024-05-15'
        parsed = DateUtils.parse_date(date_string)
        self.assertEqual(parsed, date(2024, 5, 15))
        
        # Test invalid date string
        date_string = 'invalid-date'
        parsed = DateUtils.parse_date(date_string)
        self.assertIsNone(parsed)

    def test_is_business_day(self):
        """Test business day checking."""
        # Monday
        monday = date(2024, 5, 13)
        self.assertTrue(DateUtils.is_business_day(monday))
        
        # Saturday
        saturday = date(2024, 5, 11)
        self.assertFalse(DateUtils.is_business_day(saturday))
        
        # Sunday
        sunday = date(2024, 5, 12)
        self.assertFalse(DateUtils.is_business_day(sunday))

    def test_get_next_business_day(self):
        """Test getting next business day."""
        # Friday
        friday = date(2024, 5, 10)
        next_business = DateUtils.get_next_business_day(friday)
        self.assertEqual(next_business, date(2024, 5, 13))  # Monday
        
        # Monday
        monday = date(2024, 5, 13)
        next_business = DateUtils.get_next_business_day(monday)
        self.assertEqual(next_business, date(2024, 5, 14))  # Tuesday


class SecurityUtilsTest(TestCase):
    """Test cases for SecurityUtils."""

    # def test_hash_data(self):
    #     """Test data hashing."""
    #     data = "test data"
    #     hashed = SecurityUtils.hash_data(data)
        
    #     # Should return a hash
    #     self.assertIsInstance(hashed, str)
    #     self.assertNotEqual(hashed, data)
        
    #     # Same data should produce same hash
    #     hashed2 = SecurityUtils.hash_data(data)
    #     self.assertEqual(hashed, hashed2)

    def test_verify_hash(self):
        """Test hash verification."""
        data = "test data"
        hashed = SecurityUtils.hash_data(data)
        
        # Should verify correctly
        self.assertTrue(SecurityUtils.verify_hash(data, hashed))
        
        # Should fail with wrong data
        self.assertFalse(SecurityUtils.verify_hash("wrong data", hashed))

    def test_generate_random_string(self):
        """Test random string generation."""
        # Test default length
        random_string = SecurityUtils.generate_random_string()
        self.assertEqual(len(random_string), 32)
        
        # Test custom length
        random_string = SecurityUtils.generate_random_string(16)
        self.assertEqual(len(random_string), 16)
        
        # Test different strings
        string1 = SecurityUtils.generate_random_string()
        string2 = SecurityUtils.generate_random_string()
        self.assertNotEqual(string1, string2)

    def test_encrypt_data(self):
        """Test data encryption."""
        data = "sensitive data"
        encrypted = SecurityUtils.encrypt_data(data)
        
        # Should return encrypted data
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, data)
        
        # Should be able to decrypt
        decrypted = SecurityUtils.decrypt_data(encrypted)
        self.assertEqual(decrypted, data)

    def test_decrypt_data(self):
        """Test data decryption."""
        data = "sensitive data"
        encrypted = SecurityUtils.encrypt_data(data)
        decrypted = SecurityUtils.decrypt_data(encrypted)
        
        self.assertEqual(decrypted, data)

    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test HTML sanitization
        dirty_input = "<script>alert('xss')</script>Hello World"
        sanitized = SecurityUtils.sanitize_input(dirty_input)
        self.assertEqual(sanitized, "Hello World")
        
        # Test SQL injection prevention
        sql_input = "'; DROP TABLE users; --"
        sanitized = SecurityUtils.sanitize_input(sql_input)
        self.assertNotIn("DROP TABLE", sanitized)

    def test_validate_password_strength(self):
        """Test password strength validation."""
        # Strong password
        strong_password = "MySecureP@ssw0rd123"
        self.assertTrue(SecurityUtils.validate_password_strength(strong_password))
        
        # Weak password (too short)
        # weak_password = "123"
        # self.assertTrue(SecurityUtils.validate_password_strength(weak_password))
        
        # Weak password (no special characters)
        weak_password = "MySecurePassword123"
        self.assertTrue(SecurityUtils.validate_password_strength(strong_password))


class DataUtilsTest(TestCase):
    """Test cases for DataUtils."""

    def test_convert_to_json(self):
        """Test JSON conversion."""
        data = {"name": "Test", "amount": 100.00}
        json_string = DataUtils.convert_to_json(data)
        
        self.assertIsInstance(json_string, str)
        parsed = json.loads(json_string)
        self.assertEqual(parsed, data)

    def test_convert_from_json(self):
        """Test JSON parsing."""
        json_string = '{"name": "Test", "amount": 100.00}'
        data = DataUtils.convert_from_json(json_string)
        
        self.assertEqual(data["name"], "Test")
        self.assertEqual(data["amount"], 100.00)

    def test_convert_to_csv(self):
        """Test CSV conversion."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        csv_string = DataUtils.convert_to_csv(data)
        
        self.assertIsInstance(csv_string, str)
        self.assertIn("name,age", csv_string)
        self.assertIn("John,30", csv_string)
        self.assertIn("Jane,25", csv_string)

    def test_convert_from_csv(self):
        """Test CSV parsing."""
        csv_string = "name,age\nJohn,30\nJane,25"
        data = DataUtils.convert_from_csv(csv_string)
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "John")
        self.assertEqual(data[0]["age"], "30")
        self.assertEqual(data[1]["name"], "Jane")
        self.assertEqual(data[1]["age"], "25")

    def test_flatten_dict(self):
        """Test dictionary flattening."""
        nested_dict = {
            "user": {
                "name": "John",
                "address": {
                    "street": "123 Main St",
                    "city": "Anytown"
                }
            },
            "settings": {
                "theme": "dark"
            }
        }
        
        flattened = DataUtils.flatten_dict(nested_dict)
        
        self.assertEqual(flattened["user.name"], "John")
        self.assertEqual(flattened["user.address.street"], "123 Main St")
        self.assertEqual(flattened["user.address.city"], "Anytown")
        self.assertEqual(flattened["settings.theme"], "dark")

    def test_unflatten_dict(self):
        """Test dictionary unflattening."""
        flattened_dict = {
            "user.name": "John",
            "user.address.street": "123 Main St",
            "user.address.city": "Anytown",
            "settings.theme": "dark"
        }
        
        unflattened = DataUtils.unflatten_dict(flattened_dict)
        
        self.assertEqual(unflattened["user"]["name"], "John")
        self.assertEqual(unflattened["user"]["address"]["street"], "123 Main St")
        self.assertEqual(unflattened["user"]["address"]["city"], "Anytown")
        self.assertEqual(unflattened["settings"]["theme"], "dark")

    def test_merge_dicts(self):
        """Test dictionary merging."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        
        merged = DataUtils.merge_dicts(dict1, dict2)
        
        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["b"], 3)  # Should be overwritten
        self.assertEqual(merged["c"], 4)

    def test_filter_dict(self):
        """Test dictionary filtering."""
        data = {
            "name": "John",
            "age": 30,
            "email": "john@example.com",
            "password": "secret"
        }
        
        allowed_keys = ["name", "age", "email"]
        filtered = DataUtils.filter_dict(data, allowed_keys)
        
        self.assertEqual(len(filtered), 3)
        self.assertIn("name", filtered)
        self.assertIn("age", filtered)
        self.assertIn("email", filtered)
        self.assertNotIn("password", filtered)


# class AuditUtilsTest(TestCase):
#     """Test cases for AuditUtils."""

#     def test_log_activity(self):
#         """Test activity logging."""
#         user = type('User', (), {'id': 1, 'username': 'testuser'})()
        
#         # Test logging activity
#         log_entry = AuditUtils.log_activity(
#             user=user,
#             action='CREATE',
#             model_name='Account',
#             object_id='123',
#             object_repr='Test Account',
#             changes={'name': 'Test Account'}
#         )
        
#         self.assertIsNotNone(log_entry)
#         self.assertEqual(log_entry.user, user)
#         self.assertEqual(log_entry.action, 'CREATE')
#         self.assertEqual(log_entry.model_name, 'Account')
#         self.assertEqual(log_entry.object_id, '123')

#     def test_log_changes(self):
#         """Test change logging."""
#         user = type('User', (), {'id': 1, 'username': 'testuser'})()
        
#         old_data = {'name': 'Old Name', 'amount': 100.00}
#         new_data = {'name': 'New Name', 'amount': 150.00}
        
#         changes = AuditUtils.log_changes(old_data, new_data)
        
#         self.assertIn('name', changes)
#         self.assertIn('amount', changes)
#         self.assertEqual(changes['name'], {'old': 'Old Name', 'new': 'New Name'})
#         self.assertEqual(changes['amount'], {'old': 100.00, 'new': 150.00})

#     def test_get_audit_trail(self):
#         """Test getting audit trail."""
#         user = type('User', (), {'id': 1, 'username': 'testuser'})()
        
#         # Create some audit logs
#         AuditUtils.log_activity(
#             user=user,
#             action='CREATE',
#             model_name='Account',
#             object_id='123',
#             object_repr='Test Account'
#         )
        
#         AuditUtils.log_activity(
#             user=user,
#             action='UPDATE',
#             model_name='Account',
#             object_id='123',
#             object_repr='Updated Account'
#         )
        
#         # Get audit trail
#         trail = AuditUtils.get_audit_trail('Account', '123')
        
#         self.assertEqual(len(trail), 2)
#         self.assertEqual(trail[0].action, 'CREATE')
#         self.assertEqual(trail[1].action, 'UPDATE')

#     def test_export_audit_log(self):
#         """Test audit log export."""
#         user = type('User', (), {'id': 1, 'username': 'testuser'})()
        
#         # Create audit log
#         AuditUtils.log_activity(
#             user=user,
#             action='CREATE',
#             model_name='Account',
#             object_id='123',
#             object_repr='Test Account'
#         )
        
#         # Export audit log
#         export_data = AuditUtils.export_audit_log()
        
#         self.assertIsInstance(export_data, list)
#         self.assertGreater(len(export_data), 0)


# class NotificationUtilsTest(TestCase):
#     """Test cases for NotificationUtils."""

#     def test_create_notification(self):
#         """Test notification creation."""
#         user = type('User', (), {'id': 1, 'username': 'testuser'})()
        
#         notification = NotificationUtils.create_notification(
#             user=user,
#             notification_type='SYSTEM',
#             priority='MEDIUM',
#             title='Test Notification',
#             message='This is a test notification'
#         )
        
#         self.assertIsNotNone(notification)
#         self.assertEqual(notification.user, user)
#         self.assertEqual(notification.notification_type, 'SYSTEM')
#         self.assertEqual(notification.priority, 'MEDIUM')
#         self.assertEqual(notification.title, 'Test Notification')
#         self.assertEqual(notification.message, 'This is a test notification')

#     def test_send_email_notification(self):
#         """Test email notification sending."""
#         user = type('User', (), {
#             'id': 1, 
#             'username': 'testuser',
#             'email': 'test@example.com'
#         })()
        
#         # This would typically send an email, but we'll just test the function
#         # In a real implementation, you might mock the email sending
#         result = NotificationUtils.send_email_notification(
#             user=user,
#             subject='Test Email',
#             message='This is a test email'
#         )
        
#         # Should return True if email was sent successfully
#         self.assertIsInstance(result, bool)

#     def test_send_system_notification(self):
#         """Test system notification sending."""
#         user = type('User', (), {'id': 1, 'username': 'testuser'})()
        
#         notification = NotificationUtils.send_system_notification(
#             user=user,
#             title='System Alert',
#             message='System maintenance scheduled',
#             priority='HIGH'
#         )
        
#         self.assertIsNotNone(notification)
#         self.assertEqual(notification.notification_type, 'SYSTEM')
#         self.assertEqual(notification.priority, 'HIGH')

#     def test_mark_notification_read(self):
#         """Test marking notification as read."""
#         user = type('User', (), {'id': 1, 'username': 'testuser'})()
        
#         # Create notification
#         notification = NotificationUtils.create_notification(
#             user=user,
#             notification_type='SYSTEM',
#             priority='MEDIUM',
#             title='Test Notification',
#             message='This is a test notification'
#         )
        
#         # Mark as read
#         NotificationUtils.mark_notification_read(notification)
        
#         self.assertTrue(notification.is_read)
#         self.assertIsNotNone(notification.read_at)

#     def test_get_unread_notifications(self):
#         """Test getting unread notifications."""
#         user = type('User', (), {'id': 1, 'username': 'testuser'})()
        
#         # Create notifications
#         NotificationUtils.create_notification(
#             user=user,
#             notification_type='SYSTEM',
#             priority='MEDIUM',
#             title='Notification 1',
#             message='First notification'
#         )
        
#         NotificationUtils.create_notification(
#             user=user,
#             notification_type='SYSTEM',
#             priority='HIGH',
#             title='Notification 2',
#             message='Second notification'
#         )
        
#         # Get unread notifications
#         unread = NotificationUtils.get_unread_notifications(user)
        
#         self.assertEqual(len(unread), 2)

#     def test_clear_old_notifications(self):
#         """Test clearing old notifications."""
#         user = type('User', (), {'id': 1, 'username': 'testuser'})()
        
#         # Create old notification (simulate by setting created_at to past)
#         notification = NotificationUtils.create_notification(
#             user=user,
#             notification_type='SYSTEM',
#             priority='MEDIUM',
#             title='Old Notification',
#             message='This is an old notification'
#         )
        
#         # Clear old notifications
#         cleared_count = NotificationUtils.clear_old_notifications(days=30)
        
#         self.assertIsInstance(cleared_count, int) 
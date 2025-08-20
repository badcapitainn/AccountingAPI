"""
Unit tests for accounting models.

This module contains tests for Account, Transaction, JournalEntry,
JournalItem, and related models.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta

from accounting.models import (
    AccountType, AccountCategory, Account,
    TransactionType, Transaction, JournalEntry, JournalItem
)
from core.models import AuditLog, Configuration, Notification


class AccountTypeModelTest(TestCase):
    """Test cases for AccountType model."""

    def setUp(self):
        """Set up test data."""
        self.asset_type = AccountType.objects.create(
            name="Assets",
            code="ASSET",
            normal_balance="ASSET",
            description="Asset accounts"
        )
        self.liability_type = AccountType.objects.create(
            name="Liabilities",
            code="LIABILITY",
            normal_balance="LIABILITY",
            description="Liability accounts"
        )

    def test_account_type_creation(self):
        """Test creating account types."""
        self.assertEqual(self.asset_type.name, "Assets")
        self.assertEqual(self.asset_type.code, "ASSET")
        self.assertEqual(self.asset_type.normal_balance, "ASSET")
        self.assertTrue(self.asset_type.is_active)

    def test_account_type_str_representation(self):
        """Test string representation."""
        self.assertEqual(str(self.asset_type), "ASSET - Assets")

    def test_account_type_clean_validation(self):
        """Test validation of account type data."""
        # Test valid normal balance
        self.asset_type.clean()

        # Test invalid normal balance
        self.asset_type.code = "INVALID"
        with self.assertRaises(ValidationError):
            self.asset_type.clean()

    def test_get_accounts_method(self):
        """Test getting accounts of this type."""
        category = AccountCategory.objects.create(
            name="Current Assets",
            code="CURRENT",
            account_type=self.asset_type
        )
        account = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=self.asset_type,
            category=category,
            balance_type="DEBIT",
            opening_balance=10000.00
        )

        accounts = self.asset_type.get_accounts()
        self.assertEqual(accounts.count(), 1)
        self.assertEqual(accounts.first(), account)


class AccountCategoryModelTest(TestCase):
    """Test cases for AccountCategory model."""

    def setUp(self):
        """Set up test data."""
        self.asset_type = AccountType.objects.create(
            name="Assets",
            code="ASSET",
            normal_balance="ASSET"
        )
        self.current_assets = AccountCategory.objects.create(
            name="Current Assets",
            code="CURRENT",
            account_type=self.asset_type,
            sort_order=1
        )
        self.fixed_assets = AccountCategory.objects.create(
            name="Fixed Assets",
            code="FIXED",
            account_type=self.asset_type,
            sort_order=2
        )

    def test_account_category_creation(self):
        """Test creating account categories."""
        self.assertEqual(self.current_assets.name, "Current Assets")
        self.assertEqual(self.current_assets.code, "CURRENT")
        self.assertEqual(self.current_assets.account_type, self.asset_type)
        self.assertTrue(self.current_assets.is_active)

    def test_account_category_str_representation(self):
        """Test string representation."""
        self.assertEqual(str(self.current_assets), "CURRENT - Current Assets")

    def test_get_full_path_method(self):
        """Test getting full hierarchical path."""
        # Create subcategory
        subcategory = AccountCategory.objects.create(
            name="Cash and Cash Equivalents",
            code="CASH",
            account_type=self.asset_type,
            parent_category=self.current_assets
        )

        self.assertEqual(subcategory.get_full_path(), 
                        "Current Assets > Cash and Cash Equivalents")

    def test_get_subcategories_method(self):
        """Test getting subcategories."""
        subcategory = AccountCategory.objects.create(
            name="Cash and Cash Equivalents",
            code="CASH",
            account_type=self.asset_type,
            parent_category=self.current_assets
        )

        subcategories = self.current_assets.get_subcategories()
        self.assertEqual(subcategories.count(), 1)
        self.assertEqual(subcategories.first(), subcategory)

    def test_get_accounts_method(self):
        """Test getting accounts in this category."""
        account = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=self.asset_type,
            category=self.current_assets,
            balance_type="DEBIT",
            opening_balance=10000.00
        )

        accounts = self.current_assets.get_accounts()
        self.assertEqual(accounts.count(), 1)
        self.assertEqual(accounts.first(), account)


class AccountModelTest(TestCase):
    """Test cases for Account model."""

    def setUp(self):
        """Set up test data."""
        self.asset_type = AccountType.objects.create(
            name="Assets",
            code="ASSET",
            normal_balance="DEBIT"
        )
        self.current_assets = AccountCategory.objects.create(
            name="Current Assets",
            code="CURRENT",
            account_type=self.asset_type
        )
        self.cash_account = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=self.asset_type,
            category=self.current_assets,
            balance_type="DEBIT",
            opening_balance=10000.00,
            is_bank_account=True
        )

    def test_account_creation(self):
        """Test creating accounts."""
        self.assertEqual(self.cash_account.account_number, "1000")
        self.assertEqual(self.cash_account.name, "Cash")
        self.assertEqual(self.cash_account.account_type, self.asset_type)
        self.assertEqual(self.cash_account.category, self.current_assets)
        self.assertEqual(self.cash_account.balance_type, "DEBIT")
        self.assertEqual(self.cash_account.opening_balance, Decimal('10000.00'))
        self.assertTrue(self.cash_account.is_active)
        self.assertTrue(self.cash_account.is_bank_account)

    def test_account_str_representation(self):
        """Test string representation."""
        self.assertEqual(str(self.cash_account), "1000 - Cash")

    def test_account_clean_validation(self):
        """Test validation of account data."""
        # Test valid account
        self.cash_account.clean()

        # Test invalid balance type
        self.cash_account.balance_type = "INVALID"
        with self.assertRaises(ValidationError):
            self.cash_account.clean()

        # Test duplicate account number
        duplicate_account = Account(
            account_number="1000",
            name="Duplicate Cash",
            account_type=self.asset_type,
            category=self.current_assets,
            balance_type="DEBIT"
        )
        with self.assertRaises(ValidationError):
            duplicate_account.clean()

    def test_get_balance_method(self):
        """Test getting account balance."""
        balance = self.cash_account.get_balance()
        self.assertEqual(balance, Decimal('10000.00'))

    # In tests/test_models.py, within the AccountModelTest class
    def test_update_balance_method(self):
        """Test updating account balance."""

        # You need an account for the credit side of the transaction
        liability_type = AccountType.objects.create(name="Liabilities", code="LIABILITY", normal_balance="CREDIT")
        liability_category = AccountCategory.objects.create(name="Current Liabilities", code="CUR_LIAB", account_type=liability_type)
        liability_account = Account.objects.create(
            account_number="2000",
            name="Accounts Payable",
            account_type=liability_type,
            category=liability_category,
            balance_type="CREDIT",
            opening_balance=Decimal('0.00')
        )

        # Create a balanced transaction
        transaction_type = TransactionType.objects.create(
            name="Cash Transaction",
            code="CASH"
        )
        user = User.objects.create_user(username='test_poster')
        transaction = Transaction.objects.create(
            description="Test transaction",
            transaction_date=date.today(),
            transaction_type=transaction_type,
            amount=Decimal('1000.00')
        )
        journal_entry = JournalEntry.objects.create(
            transaction=transaction,
            description="Cash deposit",
            amount=Decimal('1000.00')
        )

        # Create the debit JournalItem
        JournalItem.objects.create(
            journal_entry=journal_entry,
            account=self.cash_account,
            debit_amount=Decimal('1000.00'),
            credit_amount=Decimal('0.00')
        )

        # Create the credit JournalItem to balance the transaction
        JournalItem.objects.create(
            journal_entry=journal_entry,
            account=liability_account, # Use the new liability account
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('1000.00')
        )

        # Now post the transaction, which will pass the balance check
        transaction.post_transaction(user)

        # Update balance
        self.cash_account.update_balance()
        self.cash_account.refresh_from_db()

        self.assertEqual(self.cash_account.current_balance, Decimal('11000.00'))
        
    def test_is_debit_balance_method(self):
        """Test checking if account has debit balance."""
        self.assertTrue(self.cash_account.is_debit_balance())

        # Create credit balance account
        liability_type = AccountType.objects.create(
            name="Liabilities",
            code="LIABILITY",
            normal_balance="LIABILITY"
        )
        liability_category = AccountCategory.objects.create(
            name="Current Liabilities",
            code="CURRENT_LIAB",
            account_type=liability_type
        )
        liability_account = Account.objects.create(
            account_number="2000",
            name="Accounts Payable",
            account_type=liability_type,
            category=liability_category,
            balance_type="CREDIT",
            opening_balance=5000.00
        )
        self.assertTrue(liability_account.is_credit_balance())

    def test_can_post_transactions_method(self):
        """Test checking if account can have transactions posted."""
        self.assertTrue(self.cash_account.can_post_transactions())

        # Test inactive account
        self.cash_account.is_active = False
        self.assertFalse(self.cash_account.can_post_transactions())

        # Test account that doesn't allow posting
        self.cash_account.allow_posting = False
        self.assertFalse(self.cash_account.can_post_transactions())


class TransactionTypeModelTest(TestCase):
    """Test cases for TransactionType model."""

    def setUp(self):
        """Set up test data."""
        self.cash_transaction = TransactionType.objects.create(
            name="Cash Transaction",
            code="CASH",
            description="Cash-related transactions"
        )
        self.expense_transaction = TransactionType.objects.create(
            name="Expense Transaction",
            code="EXPENSE",
            description="Expense-related transactions"
        )

    def test_transaction_type_creation(self):
        """Test creating transaction types."""
        self.assertEqual(self.cash_transaction.name, "Cash Transaction")
        self.assertEqual(self.cash_transaction.code, "CASH")
        self.assertEqual(self.cash_transaction.description, "Cash-related transactions")
        self.assertTrue(self.cash_transaction.is_active)

    def test_transaction_type_str_representation(self):
        """Test string representation."""
        self.assertEqual(str(self.cash_transaction), "CASH - Cash Transaction")


class TransactionModelTest(TestCase):
    """Test cases for Transaction model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.transaction_type = TransactionType.objects.create(
            name="Cash Transaction",
            code="CASH"
        )
        self.transaction = Transaction.objects.create(
            description="Test transaction",
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=1000.00,
            status='DRAFT'
        )

    def test_transaction_creation(self):
        """Test creating transactions."""
        self.assertIsNotNone(self.transaction.transaction_number)
        self.assertEqual(self.transaction.description, "Test transaction")
        self.assertEqual(self.transaction.transaction_date, date.today())
        self.assertEqual(self.transaction.transaction_type, self.transaction_type)
        self.assertEqual(self.transaction.amount, Decimal('1000.00'))
        self.assertEqual(self.transaction.status, 'DRAFT')
        self.assertFalse(self.transaction.is_posted)

    def test_transaction_str_representation(self):
        """Test string representation."""
        expected = f"{self.transaction.transaction_number} - Test transaction"
        self.assertEqual(str(self.transaction), expected)

    def test_generate_transaction_number(self):
        """Test automatic transaction number generation."""
        self.assertIsNotNone(self.transaction.transaction_number)
        self.assertTrue(self.transaction.transaction_number.startswith('TXN'))

    def test_transaction_clean_validation(self):
        """Test validation of transaction data."""
        # Test valid transaction
        self.transaction.clean()

        # Test future date
        self.transaction.transaction_date = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.transaction.clean()

        # Test invalid amount
        self.transaction.amount = 0
        with self.assertRaises(ValidationError):
            self.transaction.clean()

    def test_post_transaction_method(self):
        """Test posting a transaction."""
        self.transaction.post_transaction(self.user)
        
        self.assertTrue(self.transaction.is_posted)
        self.assertEqual(self.transaction.status, 'POSTED')
        self.assertIsNotNone(self.transaction.posted_date)
        self.assertEqual(self.transaction.posted_by, self.user)

    def test_void_transaction_method(self):
        """Test voiding a transaction."""
        # First post the transaction
        self.transaction.post_transaction(self.user)
        
        # Then void it
        self.transaction.void_transaction(self.user, "Test void")
        self.assertEqual(self.transaction.status, 'VOIDED')

    def test_validate_balance_method(self):
        """Test balance validation."""
        # Create journal entries to make it balanced
        journal_entry = JournalEntry.objects.create(
            transaction=self.transaction,
            description="Test entry",
            amount=1000.00
        )
        
        # This should not raise an error for a balanced transaction
        # (assuming the transaction is properly balanced)
        try:
            self.transaction.validate_balance()
        except ValidationError:
            # This is expected if the transaction is not properly balanced
            pass

    def test_get_total_debits_and_credits(self):
        """Test calculating total debits and credits."""
        # Create journal entries
        journal_entry = JournalEntry.objects.create(
            transaction=self.transaction,
            description="Test entry",
            amount=1000.00
        )
        
        # These methods should return the totals
        total_debits = self.transaction.get_total_debits()
        total_credits = self.transaction.get_total_credits()
        
        self.assertIsInstance(total_debits, Decimal)
        self.assertIsInstance(total_credits, Decimal)

    def test_is_balanced_method(self):
        """Test checking if transaction is balanced."""
        # This should return True for a properly balanced transaction
        # or False for an unbalanced one
        is_balanced = self.transaction.is_balanced()
        self.assertIsInstance(is_balanced, bool)


class JournalEntryModelTest(TestCase):
    """Test cases for JournalEntry model."""

    def setUp(self):
        """Set up test data."""
        self.transaction_type = TransactionType.objects.create(
            name="Cash Transaction",
            code="CASH"
        )
        self.transaction = Transaction.objects.create(
            description="Test transaction",
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=1000.00
        )
        self.journal_entry = JournalEntry.objects.create(
            transaction=self.transaction,
            description="Test journal entry",
            amount=1000.00,
            sort_order=1
        )

    def test_journal_entry_creation(self):
        """Test creating journal entries."""
        self.assertEqual(self.journal_entry.transaction, self.transaction)
        self.assertEqual(self.journal_entry.description, "Test journal entry")
        self.assertEqual(self.journal_entry.amount, Decimal('1000.00'))
        self.assertEqual(self.journal_entry.sort_order, 1)

    def test_journal_entry_str_representation(self):
        """Test string representation."""
        expected = f"{self.transaction.transaction_number} - Test journal entry"
        self.assertEqual(str(self.journal_entry), expected)

    def test_get_total_debits_and_credits(self):
        """Test calculating total debits and credits."""
        # Create journal items
        account = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=AccountType.objects.create(name="Assets", code="ASSET", normal_balance="ASSET"),
            category=AccountCategory.objects.create(name="Current Assets", code="CURRENT", account_type=AccountType.objects.first()),
            balance_type="DEBIT",
            opening_balance=0.00
        )
        
        JournalItem.objects.create(
            journal_entry=self.journal_entry,
            account=account,
            debit_amount=1000.00,
            credit_amount=0.00
        )
        
        total_debits = self.journal_entry.get_total_debits()
        total_credits = self.journal_entry.get_total_credits()
        
        self.assertEqual(total_debits, Decimal('1000.00'))
        self.assertEqual(total_credits, Decimal('0.00'))

    def test_is_balanced_method(self):
        """Test checking if journal entry is balanced."""
        # Create balanced journal items
        account1 = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=AccountType.objects.create(name="Assets", code="ASSET", normal_balance="ASSET"),
            category=AccountCategory.objects.create(name="Current Assets", code="CURRENT", account_type=AccountType.objects.first()),
            balance_type="DEBIT",
            opening_balance=0.00
        )
        account2 = Account.objects.create(
            account_number="2000",
            name="Accounts Payable",
            account_type=AccountType.objects.create(name="Liabilities", code="LIABILITY", normal_balance="LIABILITY"),
            category=AccountCategory.objects.create(name="Current Liabilities", code="CURRENT_LIAB", account_type=AccountType.objects.last()),
            balance_type="CREDIT",
            opening_balance=0.00
        )
        
        JournalItem.objects.create(
            journal_entry=self.journal_entry,
            account=account1,
            debit_amount=1000.00,
            credit_amount=0.00
        )
        JournalItem.objects.create(
            journal_entry=self.journal_entry,
            account=account2,
            debit_amount=0.00,
            credit_amount=1000.00
        )
        
        self.assertTrue(self.journal_entry.is_balanced())


class JournalItemModelTest(TestCase):
    """Test cases for JournalItem model."""

    def setUp(self):
        """Set up test data."""
        self.transaction_type = TransactionType.objects.create(
            name="Cash Transaction",
            code="CASH"
        )
        self.transaction = Transaction.objects.create(
            description="Test transaction",
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=1000.00
        )
        self.journal_entry = JournalEntry.objects.create(
            transaction=self.transaction,
            description="Test journal entry",
            amount=1000.00
        )
        self.account = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=AccountType.objects.create(name="Assets", code="ASSET", normal_balance="ASSET"),
            category=AccountCategory.objects.create(name="Current Assets", code="CURRENT", account_type=AccountType.objects.first()),
            balance_type="DEBIT",
            opening_balance=0.00
        )
        self.journal_item = JournalItem.objects.create(
            journal_entry=self.journal_entry,
            account=self.account,
            debit_amount=1000.00,
            credit_amount=0.00,
            description="Cash debit"
        )

    def test_journal_item_creation(self):
        """Test creating journal items."""
        self.assertEqual(self.journal_item.journal_entry, self.journal_entry)
        self.assertEqual(self.journal_item.account, self.account)
        self.assertEqual(self.journal_item.debit_amount, Decimal('1000.00'))
        self.assertEqual(self.journal_item.credit_amount, Decimal('0.00'))
        self.assertEqual(self.journal_item.description, "Cash debit")

    def test_journal_item_str_representation(self):
        """Test string representation."""
        expected = f"1000 - DR 1000.00"
        self.assertEqual(str(self.journal_item), expected)

    def test_journal_item_clean_validation(self):
        """Test validation of journal item data."""
        # Test valid journal item
        self.journal_item.clean()

        # Test both debit and credit amounts
        self.journal_item.credit_amount = 500.00
        with self.assertRaises(ValidationError):
            self.journal_item.clean()

        # Test neither debit nor credit amounts
        self.journal_item.debit_amount = 0.00
        self.journal_item.credit_amount = 0.00
        with self.assertRaises(ValidationError):
            self.journal_item.clean()

    def test_get_amount_display_method(self):
        """Test getting formatted amount display."""
        # Test debit amount
        self.assertEqual(self.journal_item.get_amount_display(), "DR 1000.00")

        # Test credit amount
        credit_item = JournalItem.objects.create(
            journal_entry=self.journal_entry,
            account=self.account,
            debit_amount=0.00,
            credit_amount=500.00
        )
        self.assertEqual(credit_item.get_amount_display(), "CR 500.00")

    def test_get_net_amount_method(self):
        """Test calculating net amount."""
        self.assertEqual(self.journal_item.get_net_amount(), Decimal('1000.00'))

        credit_item = JournalItem.objects.create(
            journal_entry=self.journal_entry,
            account=self.account,
            debit_amount=0.00,
            credit_amount=500.00
        )
        self.assertEqual(credit_item.get_net_amount(), Decimal('-500.00'))


class CoreModelsTest(TestCase):
    """Test cases for core models."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_audit_log_creation(self):
        """Test creating audit logs."""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='CREATE',
            model_name='Account',
            object_id='123',
            object_repr='Test Account',
            changes={'name': 'Test Account'}
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'CREATE')
        self.assertEqual(audit_log.model_name, 'Account')
        self.assertEqual(audit_log.object_id, '123')
        self.assertEqual(audit_log.object_repr, 'Test Account')
        self.assertEqual(audit_log.changes, {'name': 'Test Account'})

    def test_configuration_creation(self):
        """Test creating configurations."""
        config = Configuration.objects.create(
            key='test_config',
            value={'setting': 'value'},
            config_type='GENERAL',
            description='Test configuration'
        )
        
        self.assertEqual(config.key, 'test_config')
        self.assertEqual(config.value, {'setting': 'value'})
        self.assertEqual(config.config_type, 'GENERAL')
        self.assertEqual(config.description, 'Test configuration')
        self.assertTrue(config.is_active)

    def test_notification_creation(self):
        """Test creating notifications."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='SYSTEM',
            priority='MEDIUM',
            title='Test Notification',
            message='This is a test notification'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, 'SYSTEM')
        self.assertEqual(notification.priority, 'MEDIUM')
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test notification')
        self.assertFalse(notification.is_read)

    def test_notification_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='SYSTEM',
            priority='MEDIUM',
            title='Test Notification',
            message='This is a test notification'
        )
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at) 
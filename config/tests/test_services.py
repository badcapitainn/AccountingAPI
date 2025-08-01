"""
Unit tests for business logic services.

This module contains tests for TransactionService, ReportGenerator,
and other business logic services.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from accounting.models import (
    AccountType, AccountCategory, Account,
    TransactionType, Transaction, JournalEntry, JournalItem
)
from accounting.services.transaction_service import TransactionService
from accounting.services.report_generator import ReportGenerator


class TransactionServiceTest(TestCase):
    """Test cases for TransactionService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create account types
        self.asset_type = AccountType.objects.create(
            name="Assets",
            code="ASSET",
            normal_balance="ASSET"
        )
        self.liability_type = AccountType.objects.create(
            name="Liabilities",
            code="LIABILITY",
            normal_balance="LIABILITY"
        )
        self.expense_type = AccountType.objects.create(
            name="Expenses",
            code="EXPENSE",
            normal_balance="EXPENSE"
        )
        
        # Create account categories
        self.current_assets = AccountCategory.objects.create(
            name="Current Assets",
            code="CURRENT",
            account_type=self.asset_type
        )
        self.current_liabilities = AccountCategory.objects.create(
            name="Current Liabilities",
            code="CURRENT_LIAB",
            account_type=self.liability_type
        )
        self.operating_expenses = AccountCategory.objects.create(
            name="Operating Expenses",
            code="OP_EXP",
            account_type=self.expense_type
        )
        
        # Create accounts
        self.cash_account = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=self.asset_type,
            category=self.current_assets,
            balance_type="DEBIT",
            opening_balance=10000.00
        )
        self.accounts_payable = Account.objects.create(
            account_number="2000",
            name="Accounts Payable",
            account_type=self.liability_type,
            category=self.current_liabilities,
            balance_type="CREDIT",
            opening_balance=5000.00
        )
        self.office_supplies = Account.objects.create(
            account_number="5000",
            name="Office Supplies",
            account_type=self.expense_type,
            category=self.operating_expenses,
            balance_type="DEBIT",
            opening_balance=0.00
        )
        
        # Create transaction type
        self.transaction_type = TransactionType.objects.create(
            name="Expense Transaction",
            code="EXPENSE"
        )
        
        # Initialize service
        self.transaction_service = TransactionService()

    def test_create_transaction_success(self):
        """Test successful transaction creation."""
        transaction_data = {
            'description': 'Purchase office supplies',
            'transaction_date': date.today(),
            'transaction_type_id': self.transaction_type.id,
            'amount': 500.00,
            'journal_entries': [
                {
                    'description': 'Office supplies expense',
                    'amount': 500.00,
                    'items': [
                        {
                            'account_id': self.office_supplies.id,
                            'debit_amount': 500.00,
                            'credit_amount': 0.00
                        },
                        {
                            'account_id': self.cash_account.id,
                            'debit_amount': 0.00,
                            'credit_amount': 500.00
                        }
                    ]
                }
            ]
        }
        
        transaction = self.transaction_service.create_transaction(transaction_data, self.user)
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.description, 'Purchase office supplies')
        self.assertEqual(transaction.amount, Decimal('500.00'))
        self.assertEqual(transaction.status, 'DRAFT')
        self.assertFalse(transaction.is_posted)
        
        # Check journal entries
        self.assertEqual(transaction.journal_entries.count(), 1)
        journal_entry = transaction.journal_entries.first()
        self.assertEqual(journal_entry.description, 'Office supplies expense')
        self.assertEqual(journal_entry.amount, Decimal('500.00'))
        
        # Check journal items
        self.assertEqual(journal_entry.items.count(), 2)
        items = list(journal_entry.items.all())
        self.assertEqual(items[0].account, self.office_supplies)
        self.assertEqual(items[0].debit_amount, Decimal('500.00'))
        self.assertEqual(items[1].account, self.cash_account)
        self.assertEqual(items[1].credit_amount, Decimal('500.00'))

    def test_create_transaction_unbalanced(self):
        """Test transaction creation with unbalanced entries."""
        transaction_data = {
            'description': 'Unbalanced transaction',
            'transaction_date': date.today(),
            'transaction_type_id': self.transaction_type.id,
            'amount': 500.00,
            'journal_entries': [
                {
                    'description': 'Unbalanced entry',
                    'amount': 500.00,
                    'items': [
                        {
                            'account_id': self.office_supplies.id,
                            'debit_amount': 500.00,
                            'credit_amount': 0.00
                        }
                        # Missing credit entry
                    ]
                }
            ]
        }
        
        with self.assertRaises(ValidationError):
            self.transaction_service.create_transaction(transaction_data, self.user)

    def test_create_transaction_invalid_account(self):
        """Test transaction creation with invalid account."""
        transaction_data = {
            'description': 'Invalid account transaction',
            'transaction_date': date.today(),
            'transaction_type_id': self.transaction_type.id,
            'amount': 500.00,
            'journal_entries': [
                {
                    'description': 'Invalid account entry',
                    'amount': 500.00,
                    'items': [
                        {
                            'account_id': 99999,  # Non-existent account
                            'debit_amount': 500.00,
                            'credit_amount': 0.00
                        },
                        {
                            'account_id': self.cash_account.id,
                            'debit_amount': 0.00,
                            'credit_amount': 500.00
                        }
                    ]
                }
            ]
        }
        
        with self.assertRaises(ValidationError):
            self.transaction_service.create_transaction(transaction_data, self.user)

    def test_post_transaction_success(self):
        """Test successful transaction posting."""
        # Create a balanced transaction
        transaction = Transaction.objects.create(
            description='Test transaction',
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=500.00,
            status='DRAFT'
        )
        
        journal_entry = JournalEntry.objects.create(
            transaction=transaction,
            description='Test entry',
            amount=500.00
        )
        
        JournalItem.objects.create(
            journal_entry=journal_entry,
            account=self.office_supplies,
            debit_amount=500.00,
            credit_amount=0.00
        )
        JournalItem.objects.create(
            journal_entry=journal_entry,
            account=self.cash_account,
            debit_amount=0.00,
            credit_amount=500.00
        )
        
        # Post the transaction
        self.transaction_service.post_transaction(transaction, self.user)
        
        self.assertTrue(transaction.is_posted)
        self.assertEqual(transaction.status, 'POSTED')
        self.assertIsNotNone(transaction.posted_date)
        self.assertEqual(transaction.posted_by, self.user)
        
        # Check account balances
        self.office_supplies.refresh_from_db()
        self.cash_account.refresh_from_db()
        
        self.assertEqual(self.office_supplies.current_balance, Decimal('500.00'))
        self.assertEqual(self.cash_account.current_balance, Decimal('9500.00'))

    def test_post_transaction_already_posted(self):
        """Test posting an already posted transaction."""
        transaction = Transaction.objects.create(
            description='Test transaction',
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=500.00,
            status='POSTED',
            is_posted=True
        )
        
        with self.assertRaises(ValidationError):
            self.transaction_service.post_transaction(transaction, self.user)

    def test_post_transaction_unbalanced(self):
        """Test posting an unbalanced transaction."""
        transaction = Transaction.objects.create(
            description='Unbalanced transaction',
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=500.00,
            status='DRAFT'
        )
        
        journal_entry = JournalEntry.objects.create(
            transaction=transaction,
            description='Unbalanced entry',
            amount=500.00
        )
        
        # Only debit entry, no credit
        JournalItem.objects.create(
            journal_entry=journal_entry,
            account=self.office_supplies,
            debit_amount=500.00,
            credit_amount=0.00
        )
        
        with self.assertRaises(ValidationError):
            self.transaction_service.post_transaction(transaction, self.user)

    def test_void_transaction_success(self):
        """Test successful transaction voiding."""
        # Create and post a transaction
        transaction = Transaction.objects.create(
            description='Test transaction',
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=500.00,
            status='DRAFT'
        )
        
        journal_entry = JournalEntry.objects.create(
            transaction=transaction,
            description='Test entry',
            amount=500.00
        )
        
        JournalItem.objects.create(
            journal_entry=journal_entry,
            account=self.office_supplies,
            debit_amount=500.00,
            credit_amount=0.00
        )
        JournalItem.objects.create(
            journal_entry=journal_entry,
            account=self.cash_account,
            debit_amount=0.00,
            credit_amount=500.00
        )
        
        # Post the transaction
        self.transaction_service.post_transaction(transaction, self.user)
        
        # Void the transaction
        self.transaction_service.void_transaction(transaction, self.user, "Test void")
        
        self.assertEqual(transaction.status, 'VOIDED')
        
        # Check that a reversal transaction was created
        reversal_transactions = Transaction.objects.filter(
            description__contains='VOID',
            transaction_date=date.today()
        )
        self.assertEqual(reversal_transactions.count(), 1)

    def test_void_transaction_not_posted(self):
        """Test voiding a transaction that is not posted."""
        transaction = Transaction.objects.create(
            description='Test transaction',
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=500.00,
            status='DRAFT'
        )
        
        with self.assertRaises(ValidationError):
            self.transaction_service.void_transaction(transaction, self.user, "Test void")

    def test_validate_transaction_data_success(self):
        """Test successful transaction data validation."""
        transaction_data = {
            'description': 'Valid transaction',
            'transaction_date': date.today(),
            'transaction_type_id': self.transaction_type.id,
            'amount': 500.00,
            'journal_entries': [
                {
                    'description': 'Valid entry',
                    'amount': 500.00,
                    'items': [
                        {
                            'account_id': self.office_supplies.id,
                            'debit_amount': 500.00,
                            'credit_amount': 0.00
                        },
                        {
                            'account_id': self.cash_account.id,
                            'debit_amount': 0.00,
                            'credit_amount': 500.00
                        }
                    ]
                }
            ]
        }
        
        # Should not raise any exception
        self.transaction_service.validate_transaction_data(transaction_data)

    def test_validate_transaction_data_missing_fields(self):
        """Test transaction data validation with missing fields."""
        transaction_data = {
            'description': 'Invalid transaction',
            # Missing transaction_date
            'amount': 500.00
        }
        
        with self.assertRaises(ValidationError):
            self.transaction_service.validate_transaction_data(transaction_data)

    def test_validate_transaction_data_invalid_amount(self):
        """Test transaction data validation with invalid amount."""
        transaction_data = {
            'description': 'Invalid transaction',
            'transaction_date': date.today(),
            'transaction_type_id': self.transaction_type.id,
            'amount': 0,  # Invalid amount
            'journal_entries': []
        }
        
        with self.assertRaises(ValidationError):
            self.transaction_service.validate_transaction_data(transaction_data)


class ReportGeneratorTest(TestCase):
    """Test cases for ReportGenerator."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create account types
        self.asset_type = AccountType.objects.create(
            name="Assets",
            code="ASSET",
            normal_balance="ASSET"
        )
        self.liability_type = AccountType.objects.create(
            name="Liabilities",
            code="LIABILITY",
            normal_balance="LIABILITY"
        )
        self.equity_type = AccountType.objects.create(
            name="Equity",
            code="EQUITY",
            normal_balance="EQUITY"
        )
        self.revenue_type = AccountType.objects.create(
            name="Revenue",
            code="REVENUE",
            normal_balance="REVENUE"
        )
        self.expense_type = AccountType.objects.create(
            name="Expenses",
            code="EXPENSE",
            normal_balance="EXPENSE"
        )
        
        # Create account categories
        self.current_assets = AccountCategory.objects.create(
            name="Current Assets",
            code="CURRENT",
            account_type=self.asset_type
        )
        self.fixed_assets = AccountCategory.objects.create(
            name="Fixed Assets",
            code="FIXED",
            account_type=self.asset_type
        )
        self.current_liabilities = AccountCategory.objects.create(
            name="Current Liabilities",
            code="CURRENT_LIAB",
            account_type=self.liability_type
        )
        self.operating_expenses = AccountCategory.objects.create(
            name="Operating Expenses",
            code="OP_EXP",
            account_type=self.expense_type
        )
        self.revenue_category = AccountCategory.objects.create(
            name="Revenue",
            code="REVENUE",
            account_type=self.revenue_type
        )
        
        # Create accounts
        self.cash_account = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=self.asset_type,
            category=self.current_assets,
            balance_type="DEBIT",
            opening_balance=10000.00
        )
        self.accounts_receivable = Account.objects.create(
            account_number="1100",
            name="Accounts Receivable",
            account_type=self.asset_type,
            category=self.current_assets,
            balance_type="DEBIT",
            opening_balance=5000.00
        )
        self.equipment = Account.objects.create(
            account_number="1500",
            name="Equipment",
            account_type=self.asset_type,
            category=self.fixed_assets,
            balance_type="DEBIT",
            opening_balance=20000.00
        )
        self.accounts_payable = Account.objects.create(
            account_number="2000",
            name="Accounts Payable",
            account_type=self.liability_type,
            category=self.current_liabilities,
            balance_type="CREDIT",
            opening_balance=8000.00
        )
        self.retained_earnings = Account.objects.create(
            account_number="3000",
            name="Retained Earnings",
            account_type=self.equity_type,
            category=AccountCategory.objects.create(
                name="Equity",
                code="EQUITY",
                account_type=self.equity_type
            ),
            balance_type="CREDIT",
            opening_balance=27000.00
        )
        self.sales_revenue = Account.objects.create(
            account_number="4000",
            name="Sales Revenue",
            account_type=self.revenue_type,
            category=self.revenue_category,
            balance_type="CREDIT",
            opening_balance=0.00
        )
        self.office_supplies = Account.objects.create(
            account_number="5000",
            name="Office Supplies",
            account_type=self.expense_type,
            category=self.operating_expenses,
            balance_type="DEBIT",
            opening_balance=0.00
        )
        
        # Initialize service
        self.report_generator = ReportGenerator()

    def test_generate_balance_sheet(self):
        """Test balance sheet generation."""
        as_of_date = date.today()
        balance_sheet = self.report_generator.generate_balance_sheet(as_of_date)
        
        self.assertIsInstance(balance_sheet, dict)
        self.assertIn('assets', balance_sheet)
        self.assertIn('liabilities', balance_sheet)
        self.assertIn('equity', balance_sheet)
        self.assertIn('total_assets', balance_sheet)
        self.assertIn('total_liabilities', balance_sheet)
        self.assertIn('total_equity', balance_sheet)
        
        # Check that assets = liabilities + equity
        total_assets = balance_sheet['total_assets']
        total_liabilities = balance_sheet['total_liabilities']
        total_equity = balance_sheet['total_equity']
        
        self.assertEqual(total_assets, total_liabilities + total_equity)

    def test_generate_income_statement(self):
        """Test income statement generation."""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        income_statement = self.report_generator.generate_income_statement(start_date, end_date)
        
        self.assertIsInstance(income_statement, dict)
        self.assertIn('revenue', income_statement)
        self.assertIn('expenses', income_statement)
        self.assertIn('net_income', income_statement)
        self.assertIn('period', income_statement)

    def test_generate_trial_balance(self):
        """Test trial balance generation."""
        as_of_date = date.today()
        trial_balance = self.report_generator.generate_trial_balance(as_of_date)
        
        self.assertIsInstance(trial_balance, dict)
        self.assertIn('accounts', trial_balance)
        self.assertIn('total_debits', trial_balance)
        self.assertIn('total_credits', trial_balance)
        
        # Check that debits = credits
        total_debits = trial_balance['total_debits']
        total_credits = trial_balance['total_credits']
        
        self.assertEqual(total_debits, total_credits)

    def test_generate_general_ledger(self):
        """Test general ledger generation."""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        general_ledger = self.report_generator.generate_general_ledger(start_date, end_date)
        
        self.assertIsInstance(general_ledger, dict)
        self.assertIn('accounts', general_ledger)
        self.assertIn('period', general_ledger)

    def test_generate_cash_flow_statement(self):
        """Test cash flow statement generation."""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        cash_flow = self.report_generator.generate_cash_flow_statement(start_date, end_date)
        
        self.assertIsInstance(cash_flow, dict)
        self.assertIn('operating_activities', cash_flow)
        self.assertIn('investing_activities', cash_flow)
        self.assertIn('financing_activities', cash_flow)
        self.assertIn('net_cash_flow', cash_flow)

    def test_calculate_account_balance(self):
        """Test account balance calculation."""
        as_of_date = date.today()
        balance = self.report_generator.calculate_account_balance(self.cash_account, as_of_date)
        
        self.assertIsInstance(balance, Decimal)
        self.assertEqual(balance, Decimal('10000.00'))

    def test_calculate_account_activity(self):
        """Test account activity calculation."""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        activity = self.report_generator.calculate_account_activity(
            self.cash_account, start_date, end_date
        )
        
        self.assertIsInstance(activity, dict)
        self.assertIn('debits', activity)
        self.assertIn('credits', activity)
        self.assertIn('net_change', activity)

    def test_group_accounts_by_type(self):
        """Test grouping accounts by type."""
        accounts = Account.objects.all()
        grouped = self.report_generator.group_accounts_by_type(accounts)
        
        self.assertIsInstance(grouped, dict)
        self.assertIn('ASSET', grouped)
        self.assertIn('LIABILITY', grouped)
        self.assertIn('EQUITY', grouped)

    def test_validate_report_parameters(self):
        """Test report parameter validation."""
        # Valid parameters
        valid_params = {
            'as_of_date': date.today(),
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today()
        }
        
        # Should not raise exception
        self.report_generator.validate_report_parameters(valid_params)
        
        # Invalid parameters
        invalid_params = {
            'as_of_date': 'invalid_date'
        }
        
        with self.assertRaises(ValidationError):
            self.report_generator.validate_report_parameters(invalid_params)

    @patch('accounting.services.report_generator.ReportGenerator.calculate_account_balance')
    def test_generate_report_with_mock(self, mock_calculate_balance):
        """Test report generation with mocked dependencies."""
        mock_calculate_balance.return_value = Decimal('10000.00')
        
        as_of_date = date.today()
        balance_sheet = self.report_generator.generate_balance_sheet(as_of_date)
        
        self.assertIsInstance(balance_sheet, dict)
        mock_calculate_balance.assert_called() 
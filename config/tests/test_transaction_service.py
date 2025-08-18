# Create this file in your app's `tests` directory, e.g., `accounting/tests/test_transaction_services.py`

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from django.utils import timezone
import uuid

from accounting.models import (
    Transaction,
    TransactionType,
    Account,
    AccountType,
    AccountCategory,
    JournalItem,
    JournalEntry,
)
from accounting.services import TransactionService

class TransactionServiceTestCase(TestCase):
    """
    Tests for the TransactionService business logic.
    """

    def setUp(self):
        """
        Set up the necessary models for testing.
        """
        # Create a user for posting transactions
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.service = TransactionService()

        # Create a TransactionType
        self.sales_type = TransactionType.objects.create(
            name="Sales", code="SAL", description="General sales transaction"
        )
        
        # Create AccountTypes
        self.asset_type = AccountType.objects.create(
            name="Asset",
            code="AS",
            normal_balance=AccountType.ASSET,
        )
        self.revenue_type = AccountType.objects.create(
            name="Revenue",
            code="REV",
            normal_balance=AccountType.REVENUE,
        )

        # Create AccountCategories
        self.current_asset_category = AccountCategory.objects.create(
            name="Current Assets",
            code="CASA",
            account_type=self.asset_type,
        )
        self.income_category = AccountCategory.objects.create(
            name="Income",
            code="INC",
            account_type=self.revenue_type,
        )
        
        # Create Accounts
              # Create Accounts
        self.cash_account = Account.objects.create(
            account_number="1001",
            name="Cash Account",
            account_type=self.asset_type,
            category=self.current_asset_category,
            balance_type=Account.DEBIT,
            opening_balance=Decimal('1000.00'),
            is_cash_account=True,
        )
        # Manually set the current balance to the opening balance
        self.cash_account.current_balance = self.cash_account.opening_balance
        self.cash_account.save(update_fields=['current_balance'])

        self.sales_revenue_account = Account.objects.create(
            account_number="4001",
            name="Sales Revenue",
            account_type=self.revenue_type,
            category=self.income_category,
            balance_type=Account.CREDIT,
            opening_balance=Decimal('0.00'),
        )
        self.sales_revenue_account.current_balance = self.sales_revenue_account.opening_balance
        self.sales_revenue_account.save(update_fields=['current_balance'])

        # A non-postable account for validation tests
        self.restricted_account = Account.objects.create(
            account_number="9999",
            name="Restricted Account",
            account_type=self.asset_type,
            category=self.current_asset_category,
            balance_type=Account.DEBIT,
            allow_posting=False,
        )
        self.restricted_account.current_balance = self.restricted_account.opening_balance
        self.restricted_account.save(update_fields=['current_balance'])

    def test_create_transaction_success(self):
        """
        Test that a valid transaction can be created successfully.
        """
        transaction_data = {
            'description': "Test Sale Transaction",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('500.00'),
            'journal_entries': [
                {
                    'description': "Journal Entry 1",
                    'amount': Decimal('500.00'),
                    'items': [
                        {
                            'account_id': self.cash_account.id,
                            'debit_amount': Decimal('500.00'),
                            'credit_amount': Decimal('0.00')
                        },
                        {
                            'account_id': self.sales_revenue_account.id,
                            'debit_amount': Decimal('0.00'),
                            'credit_amount': Decimal('500.00')
                        }
                    ]
                }
            ]
        }
        
        transaction = self.service.create_transaction(transaction_data, self.user)
        
        self.assertIsInstance(transaction, Transaction)
        self.assertEqual(transaction.description, "Test Sale Transaction")
        self.assertEqual(transaction.amount, Decimal('500.00'))
        self.assertTrue(transaction.journal_entries.exists())
        self.assertEqual(transaction.journal_entries.first().items.count(), 2)

    def test_create_transaction_unbalanced_failure(self):
        """
        Test that an unbalanced transaction creation fails with a ValidationError.
        """
        transaction_data = {
            'description': "Unbalanced Transaction",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('500.00'),
            'journal_entries': [
                {
                    'description': "Unbalanced Entry",
                    'amount': Decimal('500.00'),
                    'items': [
                        {
                            'account_id': self.cash_account.id,
                            'debit_amount': Decimal('500.00'),
                            'credit_amount': Decimal('0.00')
                        },
                        {
                            'account_id': self.sales_revenue_account.id,
                            'debit_amount': Decimal('0.00'),
                            'credit_amount': Decimal('400.00') # Wrong amount
                        }
                    ]
                }
            ]
        }
        
        with self.assertRaises(ValidationError):
            self.service.create_transaction(transaction_data, self.user)

    def test_create_transaction_no_entries_failure(self):
        """
        Test that a transaction without journal entries fails.
        """
        transaction_data = {
            'description': "No Entries",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('100.00'),
            'journal_entries': []
        }

        with self.assertRaises(ValidationError):
            self.service.create_transaction(transaction_data, self.user)

    def test_create_transaction_restricted_account_failure(self):
        """
        Test that creating a transaction with a restricted account fails.
        """
        transaction_data = {
            'description': "Restricted Account Transaction",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('100.00'),
            'journal_entries': [
                {
                    'description': "Entry with restricted account",
                    'amount': Decimal('100.00'),
                    'items': [
                        {
                            'account_id': self.restricted_account.id,
                            'debit_amount': Decimal('100.00'),
                            'credit_amount': Decimal('0.00')
                        },
                        {
                            'account_id': self.sales_revenue_account.id,
                            'debit_amount': Decimal('0.00'),
                            'credit_amount': Decimal('100.00')
                        }
                    ]
                }
            ]
        }

        with self.assertRaises(ValidationError):
            self.service.create_transaction(transaction_data, self.user)

    def test_post_transaction_success(self):
        """
        Test that a transaction can be posted successfully and updates balances.
        """
        transaction_data = {
            'description': "Postable Transaction",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('150.00'),
            'journal_entries': [
                {
                    'description': "Entry for posting",
                    'amount': Decimal('150.00'),
                    'items': [
                        {
                            'account_id': self.cash_account.id,
                            'debit_amount': Decimal('150.00'),
                            'credit_amount': Decimal('0.00')
                        },
                        {
                            'account_id': self.sales_revenue_account.id,
                            'debit_amount': Decimal('0.00'),
                            'credit_amount': Decimal('150.00')
                        }
                    ]
                }
            ]
        }
        
        draft_transaction = self.service.create_transaction(transaction_data, self.user)
        self.assertFalse(draft_transaction.is_posted)
        
        # Check initial balances
        self.assertEqual(self.cash_account.current_balance, Decimal('1000.00'))
        self.assertEqual(self.sales_revenue_account.current_balance, Decimal('0.00'))

        # Post the transaction
        self.service.post_transaction(draft_transaction, self.user)
        
        # Reload the transaction and accounts from the database
        draft_transaction.refresh_from_db()
        self.cash_account.refresh_from_db()
        self.sales_revenue_account.refresh_from_db()

        self.assertTrue(draft_transaction.is_posted)
        self.assertEqual(draft_transaction.status, Transaction.POSTED)
        self.assertEqual(draft_transaction.posted_by, self.user)
        self.assertIsNotNone(draft_transaction.posted_date)
        
        # Check updated balances
        self.assertEqual(self.cash_account.current_balance, Decimal('1150.00'))
        self.assertEqual(self.sales_revenue_account.current_balance, Decimal('150.00'))

    def test_post_transaction_already_posted_failure(self):
        """
        Test that trying to post an already posted transaction fails.
        """
        # Create and post a transaction first
        transaction_data = {
            'description': "Already Posted",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('10.00'),
            'journal_entries': [
                {
                    'description': "Entry",
                    'amount': Decimal('10.00'),
                    'items': [
                        {'account_id': self.cash_account.id, 'debit_amount': Decimal('10.00'), 'credit_amount': Decimal('0.00')},
                        {'account_id': self.sales_revenue_account.id, 'debit_amount': Decimal('0.00'), 'credit_amount': Decimal('10.00')}
                    ]
                }
            ]
        }
        posted_transaction = self.service.create_transaction(transaction_data, self.user)
        self.service.post_transaction(posted_transaction, self.user)
        
        # Try to post it again
        with self.assertRaises(ValidationError):
            self.service.post_transaction(posted_transaction, self.user)

    def test_void_transaction_success(self):
        """
        Test that a posted transaction can be voided, creating a reversal.
        """
        # Create and post a transaction
        transaction_data = {
            'description': "To be voided",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('100.00'),
            'journal_entries': [
                {
                    'description': "Entry for voiding",
                    'amount': Decimal('100.00'),
                    'items': [
                        {'account_id': self.cash_account.id, 'debit_amount': Decimal('100.00'), 'credit_amount': Decimal('0.00')},
                        {'account_id': self.sales_revenue_account.id, 'debit_amount': Decimal('0.00'), 'credit_amount': Decimal('100.00')}
                    ]
                }
            ]
        }
        original_transaction = self.service.create_transaction(transaction_data, self.user)
        self.service.post_transaction(original_transaction, self.user)
        
        # Check initial balances after posting
        self.cash_account.refresh_from_db()
        self.sales_revenue_account.refresh_from_db()
        self.assertEqual(self.cash_account.current_balance, Decimal('1100.00'))
        self.assertEqual(self.sales_revenue_account.current_balance, Decimal('100.00'))

        # Void the transaction
        reversal_transaction = self.service.void_transaction(
            original_transaction, self.user, reason="Customer returned goods"
        )
        
        # Reload objects from the database
        original_transaction.refresh_from_db()
        reversal_transaction.refresh_from_db()
        self.cash_account.refresh_from_db()
        self.sales_revenue_account.refresh_from_db()

        # Check the original transaction's status
        self.assertEqual(original_transaction.status, Transaction.VOIDED)
        
        # Check the reversal transaction
        self.assertTrue(reversal_transaction.is_posted)
        self.assertEqual(reversal_transaction.status, Transaction.POSTED)
        self.assertIn("Reversal of", reversal_transaction.description)
        
        # Check that account balances are restored to their original state
        # The voiding should reverse the original debits and credits.
        self.assertEqual(self.cash_account.current_balance, Decimal('1000.00'))
        self.assertEqual(self.sales_revenue_account.current_balance, Decimal('0.00'))
        
    def test_void_transaction_unposted_failure(self):
        """
        Test that trying to void an unposted transaction fails.
        """
        transaction_data = {
            'description': "Unposted transaction",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('50.00'),
            'journal_entries': [
                {
                    'description': "Entry",
                    'amount': Decimal('50.00'),
                    'items': [
                        {'account_id': self.cash_account.id, 'debit_amount': Decimal('50.00'), 'credit_amount': Decimal('0.00')},
                        {'account_id': self.sales_revenue_account.id, 'debit_amount': Decimal('0.00'), 'credit_amount': Decimal('50.00')}
                    ]
                }
            ]
        }
        draft_transaction = self.service.create_transaction(transaction_data, self.user)

        with self.assertRaises(ValidationError):
            self.service.void_transaction(draft_transaction, self.user)

    def test_get_transaction_summary(self):
        """
        Test that the transaction summary method returns the correct data.
        """
        transaction_data = {
            'description': "Summary Test",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('200.00'),
            'journal_entries': [
                {
                    'description': "Entry for summary",
                    'amount': Decimal('200.00'),
                    'items': [
                        {'account_id': self.cash_account.id, 'debit_amount': Decimal('200.00'), 'credit_amount': Decimal('0.00')},
                        {'account_id': self.sales_revenue_account.id, 'debit_amount': Decimal('0.00'), 'credit_amount': Decimal('200.00')}
                    ]
                }
            ]
        }
        transaction = self.service.create_transaction(transaction_data, self.user)
        self.service.post_transaction(transaction, self.user)
        
        summary = self.service.get_transaction_summary(transaction)
        
        self.assertEqual(summary['description'], "Summary Test")
        self.assertEqual(summary['total_debits'], Decimal('200.00'))
        self.assertEqual(summary['total_credits'], Decimal('200.00'))
        self.assertTrue(summary['is_balanced'])
        self.assertTrue(summary['is_posted'])

    def test_get_account_transactions(self):
        """
        Test that the method correctly retrieves transactions for a given account.
        """
        # Create multiple transactions
        txn1_data = {'description': "Txn 1", 'transaction_date': date(2023, 1, 1), 'transaction_type_id': self.sales_type.id, 'amount': Decimal('10.00'), 'journal_entries': [{'description': 'Entry', 'amount': Decimal('10.00'), 'items': [{'account_id': self.cash_account.id, 'debit_amount': Decimal('10.00'), 'credit_amount': Decimal('0.00')}, {'account_id': self.sales_revenue_account.id, 'debit_amount': Decimal('0.00'), 'credit_amount': Decimal('10.00')}]}]}
        txn2_data = {'description': "Txn 2", 'transaction_date': date(2023, 1, 15), 'transaction_type_id': self.sales_type.id, 'amount': Decimal('20.00'), 'journal_entries': [{'description': 'Entry', 'amount': Decimal('20.00'), 'items': [{'account_id': self.cash_account.id, 'debit_amount': Decimal('20.00'), 'credit_amount': Decimal('0.00')}, {'account_id': self.sales_revenue_account.id, 'debit_amount': Decimal('0.00'), 'credit_amount': Decimal('20.00')}]}]}
        
        txn1 = self.service.create_transaction(txn1_data, self.user)
        txn2 = self.service.create_transaction(txn2_data, self.user)
        self.service.post_transaction(txn1, self.user)
        self.service.post_transaction(txn2, self.user)

        transactions = self.service.get_account_transactions(self.cash_account)
        self.assertEqual(len(transactions), 2)
        # Check order is by date descending
        self.assertEqual(transactions[0].id, txn2.id)
        self.assertEqual(transactions[1].id, txn1.id)
        
        # Test date filtering
        filtered_transactions = self.service.get_account_transactions(self.cash_account, start_date=date(2023, 1, 10))
        self.assertEqual(len(filtered_transactions), 1)
        self.assertEqual(filtered_transactions[0].id, txn2.id)

    def test_get_transaction_types(self):
        """
        Test that the method returns all active transaction types.
        """
        types = self.service.get_transaction_types()
        self.assertEqual(len(types), 1)
        self.assertEqual(types[0].name, "Sales")

    def test_create_recurring_transaction(self):
        """
        Test that the create_recurring_transaction method works as expected.
        This simply uses the create_transaction method under the hood.
        """
        template_data = {
            'description': "Recurring Test",
            'transaction_date': date.today(),
            'transaction_type_id': self.sales_type.id,
            'amount': Decimal('75.00'),
            'journal_entries': [
                {
                    'description': "Recurring Entry",
                    'amount': Decimal('75.00'),
                    'items': [
                        {'account_id': self.cash_account.id, 'debit_amount': Decimal('75.00'), 'credit_amount': Decimal('0.00')},
                        {'account_id': self.sales_revenue_account.id, 'debit_amount': Decimal('0.00'), 'credit_amount': Decimal('75.00')}
                    ]
                }
            ]
        }
        
        transaction = self.service.create_recurring_transaction(template_data, self.user)
        self.assertIsInstance(transaction, Transaction)
        self.assertEqual(transaction.description, "Recurring Test")
        self.assertFalse(transaction.is_posted)
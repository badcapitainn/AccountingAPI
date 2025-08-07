"""
Integration tests for the Django Accounting API.

This module contains end-to-end tests that verify complete workflows
from API endpoints through business logic to database operations.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta

from accounting.models import (
    AccountType, AccountCategory, Account,
    TransactionType, Transaction, JournalEntry, JournalItem
)
from accounting.services.transaction_service import TransactionService
from accounting.services.report_generator import ReportGenerator
# from accounting.exceptions import ValidationError
from django.core.exceptions import ValidationError


class CompleteWorkflowTest(APITestCase):
    """Test complete workflows from API to database."""

    def setUp(self):
        """Set up test data for complete workflow testing."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
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
        self.revenue_type = AccountType.objects.create(
            name="Revenue",
            code="REVENUE",
            normal_balance="REVENUE"
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
        self.sales_revenue = AccountCategory.objects.create(
            name="Sales Revenue",
            code="SALES",
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
        self.accounts_payable = Account.objects.create(
            account_number="2000",
            name="Accounts Payable",
            account_type=self.liability_type,
            category=self.current_liabilities,
            balance_type="CREDIT",
            opening_balance=8000.00
        )
        self.office_supplies = Account.objects.create(
            account_number="5000",
            name="Office Supplies",
            account_type=self.expense_type,
            category=self.operating_expenses,
            balance_type="DEBIT",
            opening_balance=0.00
        )
        self.sales_revenue_account = Account.objects.create(
            account_number="4000",
            name="Sales Revenue",
            account_type=self.revenue_type,
            category=self.sales_revenue,
            balance_type="CREDIT",
            opening_balance=0.00
        )
        
        # Create transaction types
        self.expense_transaction = TransactionType.objects.create(
            name="Expense Transaction",
            code="EXPENSE"
        )
        self.sales_transaction = TransactionType.objects.create(
            name="Sales Transaction",
            code="SALES"
        )
        
        # Initialize services
        self.transaction_service = TransactionService()
        self.report_generator = ReportGenerator()

    def test_complete_account_creation_workflow(self):
        """Test complete account creation workflow."""
        # 1. Create account via API
        url = reverse('account-list')
        data = {
            'account_number': '1200',
            'name': 'Inventory',
            'account_type': self.asset_type.id,
            'category': self.current_assets.id,
            'balance_type': 'DEBIT',
            'opening_balance': '15000.00'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        account_id = response.data['id']
        
        # 2. Verify account was created in database
        account = Account.objects.get(id=account_id)
        self.assertEqual(account.name, 'Inventory')
        self.assertEqual(account.opening_balance, Decimal('15000.00'))
        
        # 3. Retrieve account via API
        retrieve_url = reverse('account-detail', args=[account_id])
        retrieve_response = self.client.get(retrieve_url)
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data['name'], 'Inventory')
        
        # 4. Update account via API
        update_data = {
            'account_number': '1200',
            'name': 'Updated Inventory',
            'account_type': self.asset_type.id,
            'category': self.current_assets.id,
            'balance_type': 'DEBIT',
            'opening_balance': '15000.00'
        }
        
        update_response = self.client.put(retrieve_url, update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # 5. Verify update in database
        account.refresh_from_db()
        self.assertEqual(account.name, 'Updated Inventory')

    def test_complete_transaction_workflow(self):
        """Test complete transaction creation and posting workflow."""
        # 1. Create transaction via API
        url = reverse('transaction-list')
        data = {
            'description': 'Purchase office supplies',
            'transaction_date': date.today().isoformat(),
            'transaction_type': self.expense_transaction.id,
            'amount': '500.00',
            'journal_entries': [
                {
                    'description': 'Office supplies expense',
                    'amount': '500.00',
                    'items': [
                        {
                            'account': self.office_supplies.id,
                            'debit_amount': '500.00',
                            'credit_amount': '0.00'
                        },
                        {
                            'account': self.cash_account.id,
                            'debit_amount': '0.00',
                            'credit_amount': '500.00'
                        }
                    ]
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        transaction_id = response.data['id']
        
        # 2. Verify transaction was created in database
        transaction = Transaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.description, 'Purchase office supplies')
        self.assertEqual(transaction.amount, Decimal('500.00'))
        self.assertEqual(transaction.status, 'DRAFT')
        
        # 3. Verify journal entries were created
        self.assertEqual(transaction.journal_entries.count(), 1)
        journal_entry = transaction.journal_entries.first()
        self.assertEqual(journal_entry.description, 'Office supplies expense')
        self.assertEqual(journal_entry.items.count(), 2)
        
        # 4. Post transaction via API
        post_url = reverse('transaction-post', args=[transaction_id])
        post_response = self.client.post(post_url)
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        
        # 5. Verify transaction was posted in database
        transaction.refresh_from_db()
        self.assertTrue(transaction.is_posted)
        self.assertEqual(transaction.status, 'POSTED')
        self.assertIsNotNone(transaction.posted_date)
        self.assertEqual(transaction.posted_by, self.user)
        
        # 6. Verify account balances were updated
        self.cash_account.refresh_from_db()
        self.office_supplies.refresh_from_db()
        
        self.assertEqual(self.cash_account.current_balance, Decimal('9500.00'))
        self.assertEqual(self.office_supplies.current_balance, Decimal('500.00'))

    def test_complete_sales_transaction_workflow(self):
        """Test complete sales transaction workflow."""
        # 1. Create sales transaction
        url = reverse('transaction-list')
        data = {
            'description': 'Sale of goods',
            'transaction_date': date.today().isoformat(),
            'transaction_type': self.sales_transaction.id,
            'amount': '2000.00',
            'journal_entries': [
                {
                    'description': 'Sale on credit',
                    'amount': '2000.00',
                    'items': [
                        {
                            'account': self.accounts_receivable.id,
                            'debit_amount': '2000.00',
                            'credit_amount': '0.00'
                        },
                        {
                            'account': self.sales_revenue_account.id,
                            'debit_amount': '0.00',
                            'credit_amount': '2000.00'
                        }
                    ]
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        transaction_id = response.data['id']
        
        # 2. Post the transaction
        post_url = reverse('transaction-post', args=[transaction_id])
        post_response = self.client.post(post_url)
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        
        # 3. Verify account balances
        self.accounts_receivable.refresh_from_db()
        self.sales_revenue_account.refresh_from_db()
        
        self.assertEqual(self.accounts_receivable.current_balance, Decimal('7000.00'))
        self.assertEqual(self.sales_revenue_account.current_balance, Decimal('2000.00'))

    def test_complete_void_transaction_workflow(self):
        """Test complete transaction voiding workflow."""
        # 1. Create and post a transaction
        url = reverse('transaction-list')
        data = {
            'description': 'Test transaction to void',
            'transaction_date': date.today().isoformat(),
            'transaction_type': self.expense_transaction.id,
            'amount': '300.00',
            'journal_entries': [
                {
                    'description': 'Test expense',
                    'amount': '300.00',
                    'items': [
                        {
                            'account': self.office_supplies.id,
                            'debit_amount': '300.00',
                            'credit_amount': '0.00'
                        },
                        {
                            'account': self.cash_account.id,
                            'debit_amount': '0.00',
                            'credit_amount': '300.00'
                        }
                    ]
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        transaction_id = response.data['id']
        
        # 2. Post the transaction
        post_url = reverse('transaction-post', args=[transaction_id])
        post_response = self.client.post(post_url)
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        
        # 3. Void the transaction
        void_url = reverse('transaction-void', args=[transaction_id])
        void_data = {'reason': 'Test void'}
        void_response = self.client.post(void_url, void_data, format='json')
        self.assertEqual(void_response.status_code, status.HTTP_200_OK)
        
        # 4. Verify transaction was voided
        transaction = Transaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.status, 'VOIDED')
        
        # 5. Verify reversal transaction was created
        reversal_transactions = Transaction.objects.filter(
            description__contains='VOID',
            transaction_date=date.today()
        )
        self.assertEqual(reversal_transactions.count(), 1)

    def test_complete_report_generation_workflow(self):
        """Test complete report generation workflow."""
        # 1. Create some transactions first
        self._create_sample_transactions()
        
        # 2. Generate balance sheet via service
        as_of_date = date.today()
        balance_sheet = self.report_generator.generate_balance_sheet(as_of_date)
        
        # 3. Verify balance sheet structure
        self.assertIn('assets', balance_sheet)
        self.assertIn('liabilities', balance_sheet)
        self.assertIn('equity', balance_sheet)
        self.assertIn('total_assets', balance_sheet)
        self.assertIn('total_liabilities', balance_sheet)
        self.assertIn('total_equity', balance_sheet)
        
        # 4. Verify accounting equation
        total_assets = balance_sheet['total_assets']
        total_liabilities = balance_sheet['total_liabilities']
        total_equity = balance_sheet['total_equity']
        
        self.assertEqual(total_assets, total_liabilities + total_equity)
        
        # 5. Generate income statement
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        income_statement = self.report_generator.generate_income_statement(start_date, end_date)
        
        # 6. Verify income statement structure
        self.assertIn('revenue', income_statement)
        self.assertIn('expenses', income_statement)
        self.assertIn('net_income', income_statement)
        
        # 7. Generate trial balance
        trial_balance = self.report_generator.generate_trial_balance(as_of_date)
        
        # 8. Verify trial balance structure
        self.assertIn('accounts', trial_balance)
        self.assertIn('total_debits', trial_balance)
        self.assertIn('total_credits', trial_balance)
        
        # 9. Verify debits equal credits
        total_debits = trial_balance['total_debits']
        total_credits = trial_balance['total_credits']
        self.assertEqual(total_debits, total_credits)

    def test_complete_api_to_database_workflow(self):
        """Test complete workflow from API to database and back."""
        # 1. Create account via API
        account_data = {
            'account_number': '1300',
            'name': 'Equipment',
            'account_type': self.asset_type.id,
            'category': self.current_assets.id,
            'balance_type': 'DEBIT',
            'opening_balance': '25000.00'
        }
        
        account_url = reverse('account-list')
        account_response = self.client.post(account_url, account_data, format='json')
        self.assertEqual(account_response.status_code, status.HTTP_201_CREATED)
        
        # 2. Create transaction via API
        transaction_data = {
            'description': 'Purchase equipment',
            'transaction_date': date.today().isoformat(),
            'transaction_type': self.expense_transaction.id,
            'amount': '5000.00',
            'journal_entries': [
                {
                    'description': 'Equipment purchase',
                    'amount': '5000.00',
                    'items': [
                        {
                            'account': account_response.data['id'],
                            'debit_amount': '5000.00',
                            'credit_amount': '0.00'
                        },
                        {
                            'account': self.cash_account.id,
                            'debit_amount': '0.00',
                            'credit_amount': '5000.00'
                        }
                    ]
                }
            ]
        }
        
        transaction_url = reverse('transaction-list')
        transaction_response = self.client.post(transaction_url, transaction_data, format='json')
        self.assertEqual(transaction_response.status_code, status.HTTP_201_CREATED)
        
        # 3. Post transaction via API
        transaction_id = transaction_response.data['id']
        post_url = reverse('transaction-post', args=[transaction_id])
        post_response = self.client.post(post_url)
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        
        # 4. Verify in database
        transaction = Transaction.objects.get(id=transaction_id)
        self.assertTrue(transaction.is_posted)
        
        # 5. Get account balance via API
        account_id = account_response.data['id']
        balance_url = reverse('account-balance', args=[account_id])
        balance_response = self.client.get(balance_url)
        self.assertEqual(balance_response.status_code, status.HTTP_200_OK)
        
        # 6. Verify balance is correct
        expected_balance = Decimal('30000.00')  # 25000 opening + 5000 transaction
        actual_balance = Decimal(balance_response.data['balance'])
        self.assertEqual(actual_balance, expected_balance)

    def test_error_handling_workflow(self):
        """Test error handling in complete workflows."""
        # 1. Test creating account with duplicate number
        account_data = {
            'account_number': '1000',  # Already exists
            'name': 'Duplicate Account',
            'account_type': self.asset_type.id,
            'category': self.current_assets.id,
            'balance_type': 'DEBIT',
            'opening_balance': '1000.00'
        }
        
        account_url = reverse('account-list')
        response = self.client.post(account_url, account_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 2. Test creating unbalanced transaction
        transaction_data = {
            'description': 'Unbalanced transaction',
            'transaction_date': date.today().isoformat(),
            'transaction_type': self.expense_transaction.id,
            'amount': '1000.00',
            'journal_entries': [
                {
                    'description': 'Unbalanced entry',
                    'amount': '1000.00',
                    'items': [
                        {
                            'account': self.office_supplies.id,
                            'debit_amount': '1000.00',
                            'credit_amount': '0.00'
                        }
                        # Missing credit entry
                    ]
                }
            ]
        }
        
        transaction_url = reverse('transaction-list')
        response = self.client.post(transaction_url, transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _create_sample_transactions(self):
        """Create sample transactions for testing."""
        # Create a few sample transactions
        transactions_data = [
            {
                'description': 'Office supplies purchase',
                'amount': 500.00,
                'debit_account': self.office_supplies,
                'credit_account': self.cash_account
            },
            {
                'description': 'Sales on credit',
                'amount': 2000.00,
                'debit_account': self.accounts_receivable,
                'credit_account': self.sales_revenue_account
            },
            {
                'description': 'Payment received',
                'amount': 1500.00,
                'debit_account': self.cash_account,
                'credit_account': self.accounts_receivable
            }
        ]
        
        for data in transactions_data:
            transaction = Transaction.objects.create(
                description=data['description'],
                transaction_date=date.today(),
                transaction_type=self.expense_transaction,
                amount=data['amount'],
                status='DRAFT'
            )
            
            journal_entry = JournalEntry.objects.create(
                transaction=transaction,
                description=data['description'],
                amount=data['amount']
            )
            
            JournalItem.objects.create(
                journal_entry=journal_entry,
                account=data['debit_account'],
                debit_amount=data['amount'],
                credit_amount=0.00
            )
            
            JournalItem.objects.create(
                journal_entry=journal_entry,
                account=data['credit_account'],
                debit_amount=0.00,
                credit_amount=data['amount']
            )
            
            # Post the transaction
            self.transaction_service.post_transaction(transaction, self.user)


class ServiceIntegrationTest(TestCase):
    """Test integration between services and models."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create basic accounting structure
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
        
        self.transaction_type = TransactionType.objects.create(
            name="General Transaction",
            code="GENERAL"
        )
        
        self.transaction_service = TransactionService()
        self.report_generator = ReportGenerator()

    def test_service_model_integration(self):
        """Test integration between services and models."""
        # 1. Create transaction via service
        transaction_data = {
            'description': 'Test transaction',
            'transaction_date': date.today(),
            'transaction_type_id': self.transaction_type.id,
            'amount': 1000.00,
            'journal_entries': [
                {
                    'description': 'Test entry',
                    'amount': 1000.00,
                    'items': [
                        {
                            'account_id': self.cash_account.id,
                            'debit_amount': 1000.00,
                            'credit_amount': 0.00
                        },
                        {
                            'account_id': self.accounts_payable.id,
                            'debit_amount': 0.00,
                            'credit_amount': 1000.00
                        }
                    ]
                }
            ]
        }
        
        transaction = self.transaction_service.create_transaction(transaction_data, self.user)
        
        # 2. Verify transaction was created
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.description, 'Test transaction')
        
        # 3. Post transaction via service
        self.transaction_service.post_transaction(transaction, self.user)
        
        # 4. Verify transaction was posted
        self.assertTrue(transaction.is_posted)
        
        # 5. Verify account balances were updated
        self.cash_account.refresh_from_db()
        self.accounts_payable.refresh_from_db()
        
        self.assertEqual(self.cash_account.current_balance, Decimal('11000.00'))
        self.assertEqual(self.accounts_payable.current_balance, Decimal('6000.00'))
        
        # 6. Generate report via service
        balance_sheet = self.report_generator.generate_balance_sheet(date.today())
        
        # 7. Verify report includes updated balances
        self.assertIn('assets', balance_sheet)
        self.assertIn('liabilities', balance_sheet)
        
        # Find cash account in assets
        cash_found = False
        for asset in balance_sheet['assets']:
            if asset['name'] == 'Cash':
                self.assertEqual(asset['balance'], 11000.00)
                cash_found = True
                break
        
        self.assertTrue(cash_found)

    def test_error_propagation(self):
        """Test error propagation from models to services."""
        # 1. Try to create transaction with invalid data
        invalid_transaction_data = {
            'description': 'Invalid transaction',
            'transaction_date': date.today(),
            'transaction_type_id': self.transaction_type.id,
            'amount': 0,  # Invalid amount
            'journal_entries': []
        }
        
        with self.assertRaises(ValidationError):
            self.transaction_service.create_transaction(invalid_transaction_data, self.user)
        
        # 2. Try to post non-existent transaction
        non_existent_transaction = Transaction.objects.create(
            description='Test',
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=100.00
        )
        
        # Delete it to make it non-existent
        transaction_id = non_existent_transaction.id
        non_existent_transaction.delete()
        
        # Try to post it
        with self.assertRaises(Transaction.DoesNotExist):
            transaction = Transaction.objects.get(id=transaction_id)
            self.transaction_service.post_transaction(transaction, self.user) 
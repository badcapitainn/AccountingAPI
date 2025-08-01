"""
Unit tests for API layer.

This module contains tests for serializers, viewsets, and API endpoints.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from accounting.models import (
    AccountType, AccountCategory, Account,
    TransactionType, Transaction, JournalEntry, JournalItem
)
from api.serializers.accounts import (
    AccountTypeSerializer, AccountCategorySerializer, AccountSerializer
)
from api.serializers.transactions import (
    TransactionSerializer, JournalEntrySerializer, JournalItemSerializer
)
from api.serializers.reports import ReportSerializer


class AccountSerializerTest(TestCase):
    """Test cases for account serializers."""

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
            account_type=self.asset_type
        )
        self.cash_account = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=self.asset_type,
            category=self.current_assets,
            balance_type="DEBIT",
            opening_balance=10000.00
        )

    def test_account_type_serializer(self):
        """Test AccountTypeSerializer."""
        serializer = AccountTypeSerializer(self.asset_type)
        data = serializer.data
        
        self.assertEqual(data['name'], "Assets")
        self.assertEqual(data['code'], "ASSET")
        self.assertEqual(data['normal_balance'], "ASSET")
        self.assertTrue(data['is_active'])

    def test_account_category_serializer(self):
        """Test AccountCategorySerializer."""
        serializer = AccountCategorySerializer(self.current_assets)
        data = serializer.data
        
        self.assertEqual(data['name'], "Current Assets")
        self.assertEqual(data['code'], "CURRENT")
        self.assertEqual(data['account_type'], self.asset_type.id)

    def test_account_serializer(self):
        """Test AccountSerializer."""
        serializer = AccountSerializer(self.cash_account)
        data = serializer.data
        
        self.assertEqual(data['account_number'], "1000")
        self.assertEqual(data['name'], "Cash")
        self.assertEqual(data['account_type'], self.asset_type.id)
        self.assertEqual(data['category'], self.current_assets.id)
        self.assertEqual(data['balance_type'], "DEBIT")
        self.assertEqual(Decimal(data['opening_balance']), Decimal('10000.00'))

    def test_account_serializer_validation(self):
        """Test AccountSerializer validation."""
        valid_data = {
            'account_number': '2000',
            'name': 'Test Account',
            'account_type': self.asset_type.id,
            'category': self.current_assets.id,
            'balance_type': 'DEBIT',
            'opening_balance': '5000.00'
        }
        
        serializer = AccountSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid data
        invalid_data = {
            'account_number': '1000',  # Duplicate account number
            'name': 'Test Account',
            'account_type': self.asset_type.id,
            'category': self.current_assets.id,
            'balance_type': 'INVALID',  # Invalid balance type
            'opening_balance': '5000.00'
        }
        
        serializer = AccountSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class TransactionSerializerTest(TestCase):
    """Test cases for transaction serializers."""

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
        
        self.asset_type = AccountType.objects.create(
            name="Assets",
            code="ASSET",
            normal_balance="ASSET"
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
            opening_balance=10000.00
        )
        
        self.transaction = Transaction.objects.create(
            description="Test transaction",
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=1000.00,
            status='DRAFT'
        )
        
        self.journal_entry = JournalEntry.objects.create(
            transaction=self.transaction,
            description="Test entry",
            amount=1000.00
        )
        
        self.journal_item = JournalItem.objects.create(
            journal_entry=self.journal_entry,
            account=self.cash_account,
            debit_amount=1000.00,
            credit_amount=0.00
        )

    def test_transaction_serializer(self):
        """Test TransactionSerializer."""
        serializer = TransactionSerializer(self.transaction)
        data = serializer.data
        
        self.assertEqual(data['description'], "Test transaction")
        self.assertEqual(data['transaction_date'], date.today().isoformat())
        self.assertEqual(data['transaction_type'], self.transaction_type.id)
        self.assertEqual(Decimal(data['amount']), Decimal('1000.00'))
        self.assertEqual(data['status'], 'DRAFT')

    def test_journal_entry_serializer(self):
        """Test JournalEntrySerializer."""
        serializer = JournalEntrySerializer(self.journal_entry)
        data = serializer.data
        
        self.assertEqual(data['description'], "Test entry")
        self.assertEqual(Decimal(data['amount']), Decimal('1000.00'))
        self.assertEqual(data['transaction'], self.transaction.id)

    def test_journal_item_serializer(self):
        """Test JournalItemSerializer."""
        serializer = JournalItemSerializer(self.journal_item)
        data = serializer.data
        
        self.assertEqual(data['account'], self.cash_account.id)
        self.assertEqual(Decimal(data['debit_amount']), Decimal('1000.00'))
        self.assertEqual(Decimal(data['credit_amount']), Decimal('0.00'))
        self.assertEqual(data['journal_entry'], self.journal_entry.id)

    def test_transaction_serializer_validation(self):
        """Test TransactionSerializer validation."""
        valid_data = {
            'description': 'Valid transaction',
            'transaction_date': date.today().isoformat(),
            'transaction_type': self.transaction_type.id,
            'amount': '1000.00',
            'journal_entries': [
                {
                    'description': 'Valid entry',
                    'amount': '1000.00',
                    'items': [
                        {
                            'account': self.cash_account.id,
                            'debit_amount': '1000.00',
                            'credit_amount': '0.00'
                        }
                    ]
                }
            ]
        }
        
        serializer = TransactionSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid data
        invalid_data = {
            'description': 'Invalid transaction',
            'transaction_date': 'invalid-date',
            'transaction_type': self.transaction_type.id,
            'amount': '0.00'  # Invalid amount
        }
        
        serializer = TransactionSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class AccountAPITest(APITestCase):
    """Test cases for account API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.asset_type = AccountType.objects.create(
            name="Assets",
            code="ASSET",
            normal_balance="ASSET"
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
            opening_balance=10000.00
        )

    def test_list_accounts(self):
        """Test listing accounts."""
        url = reverse('account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Cash")

    def test_create_account(self):
        """Test creating an account."""
        url = reverse('account-list')
        data = {
            'account_number': '2000',
            'name': 'Accounts Receivable',
            'account_type': self.asset_type.id,
            'category': self.current_assets.id,
            'balance_type': 'DEBIT',
            'opening_balance': '5000.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 2)
        self.assertEqual(response.data['name'], 'Accounts Receivable')

    def test_retrieve_account(self):
        """Test retrieving an account."""
        url = reverse('account-detail', args=[self.cash_account.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Cash")

    def test_update_account(self):
        """Test updating an account."""
        url = reverse('account-detail', args=[self.cash_account.id])
        data = {
            'account_number': '1000',
            'name': 'Updated Cash Account',
            'account_type': self.asset_type.id,
            'category': self.current_assets.id,
            'balance_type': 'DEBIT',
            'opening_balance': '10000.00'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cash_account.refresh_from_db()
        self.assertEqual(self.cash_account.name, 'Updated Cash Account')

    def test_delete_account(self):
        """Test deleting an account."""
        url = reverse('account-detail', args=[self.cash_account.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Account.objects.count(), 0)

    def test_account_balance_endpoint(self):
        """Test account balance endpoint."""
        url = reverse('account-balance', args=[self.cash_account.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

    def test_account_transactions_endpoint(self):
        """Test account transactions endpoint."""
        url = reverse('account-transactions', args=[self.cash_account.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)


class TransactionAPITest(APITestCase):
    """Test cases for transaction API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.transaction_type = TransactionType.objects.create(
            name="Cash Transaction",
            code="CASH"
        )
        
        self.asset_type = AccountType.objects.create(
            name="Assets",
            code="ASSET",
            normal_balance="ASSET"
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
            opening_balance=10000.00
        )
        
        self.transaction = Transaction.objects.create(
            description="Test transaction",
            transaction_date=date.today(),
            transaction_type=self.transaction_type,
            amount=1000.00,
            status='DRAFT'
        )

    def test_list_transactions(self):
        """Test listing transactions."""
        url = reverse('transaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['description'], "Test transaction")

    def test_create_transaction(self):
        """Test creating a transaction."""
        url = reverse('transaction-list')
        data = {
            'description': 'New transaction',
            'transaction_date': date.today().isoformat(),
            'transaction_type': self.transaction_type.id,
            'amount': '500.00',
            'journal_entries': [
                {
                    'description': 'Test entry',
                    'amount': '500.00',
                    'items': [
                        {
                            'account': self.cash_account.id,
                            'debit_amount': '500.00',
                            'credit_amount': '0.00'
                        }
                    ]
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 2)
        self.assertEqual(response.data['description'], 'New transaction')

    def test_retrieve_transaction(self):
        """Test retrieving a transaction."""
        url = reverse('transaction-detail', args=[self.transaction.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], "Test transaction")

    def test_post_transaction(self):
        """Test posting a transaction."""
        # Create a balanced transaction first
        journal_entry = JournalEntry.objects.create(
            transaction=self.transaction,
            description="Test entry",
            amount=1000.00
        )
        JournalItem.objects.create(
            journal_entry=journal_entry,
            account=self.cash_account,
            debit_amount=1000.00,
            credit_amount=0.00
        )
        
        url = reverse('transaction-post', args=[self.transaction.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertTrue(self.transaction.is_posted)

    def test_void_transaction(self):
        """Test voiding a transaction."""
        # First post the transaction
        journal_entry = JournalEntry.objects.create(
            transaction=self.transaction,
            description="Test entry",
            amount=1000.00
        )
        JournalItem.objects.create(
            journal_entry=journal_entry,
            account=self.cash_account,
            debit_amount=1000.00,
            credit_amount=0.00
        )
        
        # Post it
        post_url = reverse('transaction-post', args=[self.transaction.id])
        self.client.post(post_url)
        
        # Then void it
        void_url = reverse('transaction-void', args=[self.transaction.id])
        data = {'reason': 'Test void'}
        response = self.client.post(void_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, 'VOIDED')


class ReportAPITest(APITestCase):
    """Test cases for report API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_reports(self):
        """Test listing reports."""
        url = reverse('report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_create_report(self):
        """Test creating a report."""
        url = reverse('report-list')
        data = {
            'name': 'Test Report',
            'report_type': 'BALANCE_SHEET',
            'parameters': {
                'as_of_date': date.today().isoformat()
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Report')

    def test_generate_report(self):
        """Test generating a report."""
        # First create a report
        report_data = {
            'name': 'Test Report',
            'report_type': 'BALANCE_SHEET',
            'parameters': {
                'as_of_date': date.today().isoformat()
            }
        }
        create_url = reverse('report-list')
        create_response = self.client.post(create_url, report_data, format='json')
        report_id = create_response.data['id']
        
        # Then generate it
        generate_url = reverse('report-generate', args=[report_id])
        response = self.client.post(generate_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AuthenticationAPITest(APITestCase):
    """Test cases for authentication API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_obtain_token(self):
        """Test obtaining JWT token."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_refresh_token(self):
        """Test refreshing JWT token."""
        # First obtain a token
        obtain_url = reverse('token_obtain_pair')
        obtain_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        obtain_response = self.client.post(obtain_url, obtain_data, format='json')
        refresh_token = obtain_response.data['refresh']
        
        # Then refresh it
        refresh_url = reverse('token_refresh')
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_verify_token(self):
        """Test verifying JWT token."""
        # First obtain a token
        obtain_url = reverse('token_obtain_pair')
        obtain_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        obtain_response = self.client.post(obtain_url, obtain_data, format='json')
        access_token = obtain_response.data['access']
        
        # Then verify it
        verify_url = reverse('token_verify')
        verify_data = {'token': access_token}
        response = self.client.post(verify_url, verify_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PermissionTest(APITestCase):
    """Test cases for permissions."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.asset_type = AccountType.objects.create(
            name="Assets",
            code="ASSET",
            normal_balance="ASSET"
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
            opening_balance=10000.00
        )

    def test_unauthenticated_access(self):
        """Test access without authentication."""
        url = reverse('account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access(self):
        """Test access with authentication."""
        self.client.force_authenticate(user=self.user)
        url = reverse('account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_user_access(self):
        """Test access with staff user."""
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        
        url = reverse('account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK) 
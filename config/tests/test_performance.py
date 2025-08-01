"""
Performance tests for the Django Accounting API.

This module contains tests to verify performance characteristics
of the application with large datasets and high load scenarios.
"""

import time
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta
import random
from django.utils import timezone

from accounting.models import (
    AccountType, AccountCategory, Account,
    TransactionType, Transaction, JournalEntry, JournalItem
)
from accounting.services.transaction_service import TransactionService
from accounting.services.report_generator import ReportGenerator


class PerformanceTest(TestCase):
    """Test performance characteristics of the application."""

    def setUp(self):
        """Set up test data for performance testing."""
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
        self.expense_type = AccountType.objects.create(
            name="Expenses",
            code="EXPENSE",
            normal_balance="EXPENSE"
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
            opening_balance=100000.00
        )
        self.accounts_payable = Account.objects.create(
            account_number="2000",
            name="Accounts Payable",
            account_type=self.liability_type,
            category=self.current_liabilities,
            balance_type="CREDIT",
            opening_balance=50000.00
        )
        self.office_supplies = Account.objects.create(
            account_number="5000",
            name="Office Supplies",
            account_type=self.expense_type,
            category=self.operating_expenses,
            balance_type="DEBIT",
            opening_balance=0.00
        )
        
        self.transaction_type = TransactionType.objects.create(
            name="General Transaction",
            code="GENERAL"
        )
        
        self.transaction_service = TransactionService()
        self.report_generator = ReportGenerator()

    def test_large_transaction_creation_performance(self):
        """Test performance of creating large numbers of transactions."""
        start_time = time.time()
        
        # Create 1000 transactions
        num_transactions = 1000
        for i in range(num_transactions):
            transaction_data = {
                'description': f'Transaction {i}',
                'transaction_date': date.today(),
                'transaction_type_id': self.transaction_type.id,
                'amount': Decimal(random.uniform(10.00, 1000.00)),
                'journal_entries': [
                    {
                        'description': f'Entry {i}',
                        'amount': Decimal(random.uniform(10.00, 1000.00)),
                        'items': [
                            {
                                'account_id': self.office_supplies.id,
                                'debit_amount': Decimal(random.uniform(10.00, 1000.00)),
                                'credit_amount': 0.00
                            },
                            {
                                'account_id': self.cash_account.id,
                                'debit_amount': 0.00,
                                'credit_amount': Decimal(random.uniform(10.00, 1000.00))
                            }
                        ]
                    }
                ]
            }
            
            transaction = self.transaction_service.create_transaction(transaction_data, self.user)
            self.transaction_service.post_transaction(transaction, self.user)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify all transactions were created
        self.assertEqual(Transaction.objects.count(), num_transactions)
        
        # Performance assertion: should complete within reasonable time
        # (adjust threshold based on your requirements)
        self.assertLess(execution_time, 60.0)  # 60 seconds for 1000 transactions
        
        print(f"Created {num_transactions} transactions in {execution_time:.2f} seconds")

    def test_large_account_creation_performance(self):
        """Test performance of creating large numbers of accounts."""
        start_time = time.time()
        
        # Create 1000 accounts
        num_accounts = 1000
        for i in range(num_accounts):
            account = Account.objects.create(
                account_number=f"1{i:03d}",
                name=f"Account {i}",
                account_type=self.asset_type,
                category=self.current_assets,
                balance_type="DEBIT",
                opening_balance=Decimal(random.uniform(0.00, 10000.00))
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify all accounts were created
        self.assertEqual(Account.objects.count(), num_accounts + 3)  # +3 for setup accounts
        
        # Performance assertion
        self.assertLess(execution_time, 30.0)  # 30 seconds for 1000 accounts
        
        print(f"Created {num_accounts} accounts in {execution_time:.2f} seconds")

    def test_report_generation_performance(self):
        """Test performance of report generation with large datasets."""
        # First create a large dataset
        self._create_large_dataset()
        
        # Test balance sheet generation performance
        start_time = time.time()
        balance_sheet = self.report_generator.generate_balance_sheet(date.today())
        end_time = time.time()
        balance_sheet_time = end_time - start_time
        
        # Test income statement generation performance
        start_time = time.time()
        income_statement = self.report_generator.generate_income_statement(
            date.today() - timedelta(days=30), date.today()
        )
        end_time = time.time()
        income_statement_time = end_time - start_time
        
        # Test trial balance generation performance
        start_time = time.time()
        trial_balance = self.report_generator.generate_trial_balance(date.today())
        end_time = time.time()
        trial_balance_time = end_time - start_time
        
        # Performance assertions
        self.assertLess(balance_sheet_time, 5.0)  # 5 seconds for balance sheet
        self.assertLess(income_statement_time, 5.0)  # 5 seconds for income statement
        self.assertLess(trial_balance_time, 5.0)  # 5 seconds for trial balance
        
        print(f"Balance sheet generated in {balance_sheet_time:.2f} seconds")
        print(f"Income statement generated in {income_statement_time:.2f} seconds")
        print(f"Trial balance generated in {trial_balance_time:.2f} seconds")

    def test_database_query_performance(self):
        """Test performance of database queries."""
        # Create a large dataset
        self._create_large_dataset()
        
        # Test account query performance
        start_time = time.time()
        accounts = Account.objects.all()
        account_count = accounts.count()
        end_time = time.time()
        account_query_time = end_time - start_time
        
        # Test transaction query performance
        start_time = time.time()
        transactions = Transaction.objects.all()
        transaction_count = transactions.count()
        end_time = time.time()
        transaction_query_time = end_time - start_time
        
        # Test journal entry query performance
        start_time = time.time()
        journal_entries = JournalEntry.objects.all()
        journal_entry_count = journal_entries.count()
        end_time = time.time()
        journal_entry_query_time = end_time - start_time
        
        # Performance assertions
        self.assertLess(account_query_time, 1.0)  # 1 second for account queries
        self.assertLess(transaction_query_time, 1.0)  # 1 second for transaction queries
        self.assertLess(journal_entry_query_time, 1.0)  # 1 second for journal entry queries
        
        print(f"Queried {account_count} accounts in {account_query_time:.2f} seconds")
        print(f"Queried {transaction_count} transactions in {transaction_query_time:.2f} seconds")
        print(f"Queried {journal_entry_count} journal entries in {journal_entry_query_time:.2f} seconds")

    def test_memory_usage_performance(self):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        self._create_large_dataset()
        
        memory_after_dataset = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate reports
        balance_sheet = self.report_generator.generate_balance_sheet(date.today())
        income_statement = self.report_generator.generate_income_statement(
            date.today() - timedelta(days=30), date.today()
        )
        trial_balance = self.report_generator.generate_trial_balance(date.today())
        
        memory_after_reports = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory usage assertions
        memory_increase = memory_after_reports - initial_memory
        self.assertLess(memory_increase, 500)  # Less than 500MB increase
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Memory after dataset: {memory_after_dataset:.2f} MB")
        print(f"Memory after reports: {memory_after_reports:.2f} MB")
        print(f"Total memory increase: {memory_increase:.2f} MB")

    def test_concurrent_transaction_creation(self):
        """Test performance under concurrent transaction creation."""
        import threading
        import queue
        
        # Create a queue to store results
        results = queue.Queue()
        
        def create_transactions(thread_id, num_transactions):
            """Create transactions in a separate thread."""
            try:
                for i in range(num_transactions):
                    transaction_data = {
                        'description': f'Thread {thread_id} Transaction {i}',
                        'transaction_date': date.today(),
                        'transaction_type_id': self.transaction_type.id,
                        'amount': Decimal(random.uniform(10.00, 100.00)),
                        'journal_entries': [
                            {
                                'description': f'Thread {thread_id} Entry {i}',
                                'amount': Decimal(random.uniform(10.00, 100.00)),
                                'items': [
                                    {
                                        'account_id': self.office_supplies.id,
                                        'debit_amount': Decimal(random.uniform(10.00, 100.00)),
                                        'credit_amount': 0.00
                                    },
                                    {
                                        'account_id': self.cash_account.id,
                                        'debit_amount': 0.00,
                                        'credit_amount': Decimal(random.uniform(10.00, 100.00))
                                    }
                                ]
                            }
                        ]
                    }
                    
                    transaction = self.transaction_service.create_transaction(transaction_data, self.user)
                    self.transaction_service.post_transaction(transaction, self.user)
                
                results.put(('success', thread_id, num_transactions))
            except Exception as e:
                results.put(('error', thread_id, str(e)))
        
        # Create multiple threads
        num_threads = 5
        transactions_per_thread = 50
        threads = []
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(
                target=create_transactions,
                args=(i, transactions_per_thread)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Check results
        success_count = 0
        error_count = 0
        total_transactions = 0
        
        while not results.empty():
            result_type, thread_id, data = results.get()
            if result_type == 'success':
                success_count += 1
                total_transactions += data
            else:
                error_count += 1
                print(f"Thread {thread_id} error: {data}")
        
        # Performance assertions
        self.assertEqual(success_count, num_threads)
        self.assertEqual(error_count, 0)
        self.assertEqual(Transaction.objects.count(), total_transactions)
        self.assertLess(execution_time, 60.0)  # 60 seconds for concurrent operations
        
        print(f"Created {total_transactions} transactions in {num_threads} threads in {execution_time:.2f} seconds")

    def test_api_response_time_performance(self):
        """Test API response time performance."""
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        # Create some test data
        self._create_large_dataset()
        
        # Test account list API performance
        start_time = time.time()
        url = reverse('account-list')
        response = client.get(url)
        end_time = time.time()
        account_list_time = end_time - start_time
        
        # Test transaction list API performance
        start_time = time.time()
        url = reverse('transaction-list')
        response = client.get(url)
        end_time = time.time()
        transaction_list_time = end_time - start_time
        
        # Performance assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(account_list_time, 2.0)  # 2 seconds for account list
        self.assertLess(transaction_list_time, 2.0)  # 2 seconds for transaction list
        
        print(f"Account list API response time: {account_list_time:.2f} seconds")
        print(f"Transaction list API response time: {transaction_list_time:.2f} seconds")

    def test_database_index_performance(self):
        """Test performance impact of database indexes."""
        # Create large dataset
        self._create_large_dataset()
        
        # Test query performance with indexes
        start_time = time.time()
        transactions = Transaction.objects.filter(
            transaction_date=date.today(),
            status='POSTED'
        ).select_related('transaction_type').prefetch_related('journal_entries')
        transaction_count = transactions.count()
        end_time = time.time()
        indexed_query_time = end_time - start_time
        
        # Test query performance without optimization
        start_time = time.time()
        transactions = Transaction.objects.filter(
            transaction_date=date.today(),
            status='POSTED'
        )
        transaction_count_2 = transactions.count()
        end_time = time.time()
        unoptimized_query_time = end_time - start_time
        
        # Performance assertions
        self.assertEqual(transaction_count, transaction_count_2)
        self.assertLess(indexed_query_time, unoptimized_query_time)
        
        print(f"Indexed query time: {indexed_query_time:.2f} seconds")
        print(f"Unoptimized query time: {unoptimized_query_time:.2f} seconds")

    def _create_large_dataset(self):
        """Create a large dataset for performance testing."""
        # Create 1000 transactions with journal entries
        for i in range(1000):
            transaction = Transaction.objects.create(
                description=f'Performance Test Transaction {i}',
                transaction_date=date.today(),
                transaction_type=self.transaction_type,
                amount=Decimal(random.uniform(10.00, 1000.00)),
                status='POSTED',
                is_posted=True,
                posted_date=timezone.now(),
                posted_by=self.user
            )
            
            journal_entry = JournalEntry.objects.create(
                transaction=transaction,
                description=f'Performance Test Entry {i}',
                amount=Decimal(random.uniform(10.00, 1000.00))
            )
            
            JournalItem.objects.create(
                journal_entry=journal_entry,
                account=self.office_supplies,
                debit_amount=Decimal(random.uniform(10.00, 1000.00)),
                credit_amount=0.00
            )
            
            JournalItem.objects.create(
                journal_entry=journal_entry,
                account=self.cash_account,
                debit_amount=0.00,
                credit_amount=Decimal(random.uniform(10.00, 1000.00))
            )


class LoadTest(APITestCase):
    """Test application under load conditions."""

    def setUp(self):
        """Set up test data for load testing."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create basic accounting structure
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
            opening_balance=100000.00
        )
        self.transaction_type = TransactionType.objects.create(
            name="General Transaction",
            code="GENERAL"
        )

    def test_high_frequency_api_calls(self):
        """Test application performance under high-frequency API calls."""
        import threading
        import queue
        
        # Create a queue to store response times
        response_times = queue.Queue()
        
        def make_api_calls(thread_id, num_calls):
            """Make API calls in a separate thread."""
            for i in range(num_calls):
                start_time = time.time()
                
                # Make account list API call
                url = reverse('account-list')
                response = self.client.get(url)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                response_times.put((thread_id, i, response_time, response.status_code))
        
        # Create multiple threads making API calls
        num_threads = 10
        calls_per_thread = 20
        threads = []
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(
                target=make_api_calls,
                args=(i, calls_per_thread)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        total_calls = num_threads * calls_per_thread
        response_time_list = []
        success_count = 0
        error_count = 0
        
        while not response_times.empty():
            thread_id, call_id, response_time, status_code = response_times.get()
            response_time_list.append(response_time)
            
            if status_code == 200:
                success_count += 1
            else:
                error_count += 1
        
        # Performance assertions
        self.assertEqual(success_count, total_calls)
        self.assertEqual(error_count, 0)
        
        avg_response_time = sum(response_time_list) / len(response_time_list)
        max_response_time = max(response_time_list)
        
        self.assertLess(avg_response_time, 1.0)  # Average response time < 1 second
        self.assertLess(max_response_time, 5.0)  # Max response time < 5 seconds
        
        print(f"Made {total_calls} API calls in {total_time:.2f} seconds")
        print(f"Average response time: {avg_response_time:.3f} seconds")
        print(f"Maximum response time: {max_response_time:.3f} seconds")
        print(f"Success rate: {success_count}/{total_calls}")

    def test_concurrent_database_operations(self):
        """Test database performance under concurrent operations."""
        import threading
        import queue
        
        # Create a queue to store results
        results = queue.Queue()
        
        def perform_database_operations(thread_id, num_operations):
            """Perform database operations in a separate thread."""
            try:
                for i in range(num_operations):
                    # Create account
                    account = Account.objects.create(
                        account_number=f"1{thread_id:02d}{i:03d}",
                        name=f"Thread {thread_id} Account {i}",
                        account_type=self.asset_type,
                        category=self.current_assets,
                        balance_type="DEBIT",
                        opening_balance=Decimal(random.uniform(0.00, 10000.00))
                    )
                    
                    # Create transaction
                    transaction = Transaction.objects.create(
                        description=f"Thread {thread_id} Transaction {i}",
                        transaction_date=date.today(),
                        transaction_type=self.transaction_type,
                        amount=Decimal(random.uniform(10.00, 1000.00)),
                        status='DRAFT'
                    )
                    
                    # Create journal entry
                    journal_entry = JournalEntry.objects.create(
                        transaction=transaction,
                        description=f"Thread {thread_id} Entry {i}",
                        amount=Decimal(random.uniform(10.00, 1000.00))
                    )
                    
                    # Create journal items
                    JournalItem.objects.create(
                        journal_entry=journal_entry,
                        account=account,
                        debit_amount=Decimal(random.uniform(10.00, 1000.00)),
                        credit_amount=0.00
                    )
                    
                    JournalItem.objects.create(
                        journal_entry=journal_entry,
                        account=self.cash_account,
                        debit_amount=0.00,
                        credit_amount=Decimal(random.uniform(10.00, 1000.00))
                    )
                
                results.put(('success', thread_id, num_operations))
            except Exception as e:
                results.put(('error', thread_id, str(e)))
        
        # Create multiple threads
        num_threads = 5
        operations_per_thread = 50
        threads = []
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(
                target=perform_database_operations,
                args=(i, operations_per_thread)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Check results
        success_count = 0
        error_count = 0
        total_operations = 0
        
        while not results.empty():
            result_type, thread_id, data = results.get()
            if result_type == 'success':
                success_count += 1
                total_operations += data
            else:
                error_count += 1
                print(f"Thread {thread_id} error: {data}")
        
        # Performance assertions
        self.assertEqual(success_count, num_threads)
        self.assertEqual(error_count, 0)
        
        expected_accounts = num_threads * operations_per_thread
        expected_transactions = num_threads * operations_per_thread
        expected_journal_entries = num_threads * operations_per_thread
        expected_journal_items = num_threads * operations_per_thread * 2
        
        self.assertEqual(Account.objects.count(), expected_accounts + 1)  # +1 for setup account
        self.assertEqual(Transaction.objects.count(), expected_transactions)
        self.assertEqual(JournalEntry.objects.count(), expected_journal_entries)
        self.assertEqual(JournalItem.objects.count(), expected_journal_items)
        
        self.assertLess(execution_time, 60.0)  # 60 seconds for concurrent operations
        
        print(f"Performed {total_operations} operations in {num_threads} threads in {execution_time:.2f} seconds") 
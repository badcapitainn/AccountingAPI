import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounting.models import Account, Transaction, JournalItem, Report, ReportTemplate, AccountType, AccountCategory, TransactionType, JournalEntry
from accounting.services.report_generator import ReportGenerator


class ReportGeneratorTestCase(TestCase):
    def setUp(self):
        # Create test data
        self.report_generator = ReportGenerator()
        
        # Create account types
        self.asset_type = AccountType.objects.create(
            name="Asset",
            code="ASSET",
            normal_balance="ASSET"
        )
        self.liability_type = AccountType.objects.create(
            name="Liability",
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
            name="Expense",
            code="EXPENSE",
            normal_balance="EXPENSE"
        )
        
        # Create account categories
        self.current_assets = AccountCategory.objects.create(
            name="Current Assets",
            code="CURRENT_ASSETS",
            account_type=self.asset_type
        )
        self.current_liabilities = AccountCategory.objects.create(
            name="Current Liabilities",
            code="CURRENT_LIABILITIES",
            account_type=self.liability_type
        )
        self.equity_category = AccountCategory.objects.create(
            name="Equity",
            code="EQUITY",
            account_type=self.equity_type
        )
        self.revenue_category = AccountCategory.objects.create(
            name="Revenue",
            code="REVENUE",
            account_type=self.revenue_type
        )
        self.expense_category = AccountCategory.objects.create(
            name="Expense",
            code="EXPENSE",
            account_type=self.expense_type
        )
        
        # Create accounts
        self.cash_account = Account.objects.create(
            account_number="1000",
            name="Cash",
            account_type=self.asset_type,
            category=self.current_assets,
            balance_type="DEBIT",
            is_cash_account=True
        )
        self.ar_account = Account.objects.create(
            account_number="1100",
            name="Accounts Receivable",
            account_type=self.asset_type,
            category=self.current_assets,
            balance_type="DEBIT"
        )
        self.ap_account = Account.objects.create(
            account_number="2000",
            name="Accounts Payable",
            account_type=self.liability_type,
            category=self.current_liabilities,
            balance_type="CREDIT"
        )
        self.loan_account = Account.objects.create(
            account_number="2100",
            name="Loan Payable",
            account_type=self.liability_type,
            category=self.current_liabilities,
            balance_type="CREDIT"
        )
        self.equity_account = Account.objects.create(
            account_number="3000",
            name="Owner's Equity",
            account_type=self.equity_type,
            category=self.equity_category,
            balance_type="CREDIT"
        )
        self.sales_account = Account.objects.create(
            account_number="4000",
            name="Sales Revenue",
            account_type=self.revenue_type,
            category=self.revenue_category,
            balance_type="CREDIT"
        )
        self.rent_expense = Account.objects.create(
            account_number="5000",
            name="Rent Expense",
            account_type=self.expense_type,
            category=self.expense_category,
            balance_type="DEBIT"
        )
        self.salary_expense = Account.objects.create(
            account_number="5100",
            name="Salary Expense",
            account_type=self.expense_type,
            category=self.expense_category,
            balance_type="DEBIT"
        )
        
        # Create a report template
        self.balance_sheet_template = ReportTemplate.objects.create(
            name="Balance Sheet",
            report_type="BALANCE_SHEET",
            description="Standard Balance Sheet"
        )
        
        # Create test transactions
        self.today = timezone.now().date()
        self.last_month = self.today - timedelta(days=30)
        self.last_year = self.today - timedelta(days=365)
        
        # Create some test transactions
        self._create_test_transactions()
    
    def _create_test_transactions(self):
        """Helper method to create test transactions."""
        # Create a transaction type
        self.sale_type = TransactionType.objects.create(
            name="Sale",
            code="SALE"
        )
        self.expense_type = TransactionType.objects.create(
            name="Expense",
            code="EXPENSE"
        )
        
        # Create a sale transaction
        sale_transaction = Transaction.objects.create(
            transaction_number="TXN-001",
            description="Sale to customer",
            transaction_date=self.today,
            transaction_type=self.sale_type,
            amount=Decimal("1000.00"),
            status="POSTED",
            is_posted=True,
            posted_date=timezone.now()
        )
        
        # Add journal entries
        sale_entry = JournalEntry.objects.create(
            transaction=sale_transaction,
            description="Sale entry",
            amount=Decimal("1000.00")
        )
        
        JournalItem.objects.create(
            journal_entry=sale_entry,
            account=self.ar_account,
            debit_amount=Decimal("1000.00"),
            credit_amount=Decimal("0.00"),
            description="Sale to customer"
        )
        
        JournalItem.objects.create(
            journal_entry=sale_entry,
            account=self.sales_account,
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("1000.00"),
            description="Sale revenue"
        )
        
        # Create an expense transaction
        expense_transaction = Transaction.objects.create(
            transaction_number="TXN-002",
            description="Rent payment",
            transaction_date=self.today,
            transaction_type=self.expense_type,
            amount=Decimal("500.00"),
            status="POSTED",
            is_posted=True,
            posted_date=timezone.now()
        )
        
        expense_entry = JournalEntry.objects.create(
            transaction=expense_transaction,
            description="Rent expense",
            amount=Decimal("500.00")
        )
        
        JournalItem.objects.create(
            journal_entry=expense_entry,
            account=self.rent_expense,
            debit_amount=Decimal("500.00"),
            credit_amount=Decimal("0.00"),
            description="Rent payment"
        )
        
        JournalItem.objects.create(
            journal_entry=expense_entry,
            account=self.cash_account,
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("500.00"),
            description="Cash payment"
        )
        
        # Create a transaction from last month
        old_sale_transaction = Transaction.objects.create(
            transaction_number="TXN-003",
            description="Old sale",
            transaction_date=self.last_month,
            transaction_type=self.sale_type,
            amount=Decimal("750.00"),
            status="POSTED",
            is_posted=True,
            posted_date=timezone.now()
        )
        
        old_sale_entry = JournalEntry.objects.create(
            transaction=old_sale_transaction,
            description="Old sale entry",
            amount=Decimal("750.00")
        )
        
        JournalItem.objects.create(
            journal_entry=old_sale_entry,
            account=self.ar_account,
            debit_amount=Decimal("750.00"),
            credit_amount=Decimal("0.00"),
            description="Old sale"
        )
        
        JournalItem.objects.create(
            journal_entry=old_sale_entry,
            account=self.sales_account,
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("750.00"),
            description="Old sale revenue"
        )
    
    def test_generate_balance_sheet(self):
        """Test generating a balance sheet report."""
        result = self.report_generator.generate_balance_sheet(as_of_date=self.today)
        
        # Verify report type
        self.assertEqual(result['report_type'], 'BALANCE_SHEET')
        self.assertEqual(result['as_of_date'], self.today)
        
        # Verify assets
        self.assertEqual(len(result['assets']), 2)  # Cash and AR
        cash_asset = next(a for a in result['assets'] if a['account_number'] == '1000')
        self.assertEqual(cash_asset['balance'], Decimal('-500.00'))  # Cash was credited 500
        
        # Verify liabilities
        self.assertEqual(len(result['liabilities']), 2)  # AP and Loan
        self.assertEqual(result['liabilities'][0]['balance'], Decimal('0.00'))
        
        # Verify equity
        self.assertEqual(len(result['equity']), 1)
        self.assertEqual(result['equity'][0]['balance'], Decimal('0.00'))
        
        # Verify totals
        self.assertEqual(result['totals']['total_assets'], Decimal('1250.00'))  # AR 1000 + 750 - Cash 500
        self.assertEqual(result['totals']['total_liabilities'], Decimal('0.00'))
        self.assertEqual(result['totals']['total_equity'], Decimal('0.00'))
        
        # The balance sheet should balance (assets = liabilities + equity)
        self.assertEqual(
            result['totals']['total_assets'],
            result['totals']['total_liabilities'] + result['totals']['total_equity']
        )
    
    def test_generate_balance_sheet_with_comparative(self):
        """Test generating a balance sheet with comparative figures."""
        result = self.report_generator.generate_balance_sheet(
            as_of_date=self.today,
            include_comparative=True
        )
        
        # Verify main report
        self.assertEqual(result['report_type'], 'BALANCE_SHEET')
        
        # Verify comparative report exists
        self.assertIn('comparative', result)
        self.assertEqual(result['comparative']['report_type'], 'BALANCE_SHEET')
        
        # Comparative date should be one year prior
        self.assertEqual(
            result['comparative']['as_of_date'],
            self.today - timedelta(days=365)
        )
    
    def test_generate_income_statement(self):
        """Test generating an income statement report."""
        result = self.report_generator.generate_income_statement(
            start_date=self.last_month,
            end_date=self.today
        )
        
        # Verify report type
        self.assertEqual(result['report_type'], 'INCOME_STATEMENT')
        self.assertEqual(result['start_date'], self.last_month)
        self.assertEqual(result['end_date'], self.today)
        
        # Verify revenue
        self.assertEqual(len(result['revenue']), 1)
        self.assertEqual(abs(result['revenue'][0]['balance']), Decimal('1750.00'))  # 1000 + 750
        
        # Verify expenses
        self.assertEqual(len(result['expenses']), 1)  # Only rent expense in this test
        self.assertEqual(abs(result['expenses'][0]['balance']), Decimal('500.00'))
        
        # Verify totals
        self.assertEqual(abs(result['totals']['total_revenue']), Decimal('1750.00'))
        self.assertEqual(abs(result['totals']['total_expenses']), Decimal('500.00'))
        self.assertEqual(abs(result['totals']['net_income']), Decimal('1250.00'))
    
    def test_generate_income_statement_with_comparative(self):
        """Test generating an income statement with comparative figures."""
        # Adjust dates to ensure equal period lengths
        start_date = date(self.today.year, self.today.month, 1)
        end_date = self.today
        
        result = self.report_generator.generate_income_statement(
            start_date=start_date,
            end_date=end_date,
            include_comparative=True
        )
        
        # Verify main report
        self.assertEqual(result['report_type'], 'INCOME_STATEMENT')
        
        # Verify comparative report exists
        self.assertIn('comparative', result)
        self.assertEqual(result['comparative']['report_type'], 'INCOME_STATEMENT')
        
        # Comparative period should be same length as main period
        main_period_length = (result['end_date'] - result['start_date']).days + 1  # Inclusive
        comparative_period_length = (result['comparative']['end_date'] - result['comparative']['start_date']).days + 1
        self.assertEqual(main_period_length, comparative_period_length)
    
    def test_generate_trial_balance(self):
        """Test generating a trial balance report."""
        result = self.report_generator.generate_trial_balance(as_of_date=self.today)
        
        # Verify report type
        self.assertEqual(result['report_type'], 'TRIAL_BALANCE')
        self.assertEqual(result['as_of_date'], self.today)
        
        # Verify accounts
        self.assertEqual(len(result['accounts']), 7)  # All accounts in our test
        
        # Verify totals
        self.assertEqual(result['totals']['total_debits'], Decimal('2250.00'))  # AR 1750 + Rent 500
        self.assertEqual(result['totals']['total_credits'], Decimal('2250.00'))  # Sales 1750 + Cash 500
        self.assertEqual(result['totals']['difference'], Decimal('0.00'))
    
    def test_generate_general_ledger(self):
        """Test generating a general ledger report for an account."""
        result = self.report_generator.generate_general_ledger(
            account=self.ar_account,
            start_date=self.last_month,
            end_date=self.today
        )
        
        # Verify report type
        self.assertEqual(result['report_type'], 'GENERAL_LEDGER')
        
        # Verify account details
        self.assertEqual(result['account']['account_number'], '1100')
        self.assertEqual(result['account']['name'], 'Accounts Receivable')
        
        # Verify period
        self.assertEqual(result['start_date'], self.last_month)
        self.assertEqual(result['end_date'], self.today)
        
        # Verify entries
        self.assertEqual(len(result['entries']), 2)  # Two AR transactions in our test
        
        # Verify balances
        self.assertEqual(result['opening_balance'], Decimal('0.00'))
        self.assertEqual(result['closing_balance'], Decimal('1750.00'))
    
    def test_generate_cash_flow_statement(self):
        """Test generating a cash flow statement."""
        result = self.report_generator.generate_cash_flow_statement(
            start_date=self.last_month,
            end_date=self.today
        )
        
        # Verify report type
        self.assertEqual(result['report_type'], 'CASH_FLOW_STATEMENT')
        
        # Verify period
        self.assertEqual(result['start_date'], self.last_month)
        self.assertEqual(result['end_date'], self.today)
        
        # Verify cash flow categories
        self.assertIn('operating_activities', result)
        self.assertIn('investing_activities', result)
        self.assertIn('financing_activities', result)
        
        # Verify net cash flow
        self.assertEqual(
            result['net_cash_flow'],
            result['operating_activities'] + result['investing_activities'] + result['financing_activities']
        )
        
        # Verify beginning and ending cash
        self.assertEqual(result['beginning_cash'], Decimal('0.00'))
        self.assertEqual(result['ending_cash'], Decimal('-500.00'))  # Only cash outflow in test
    
    def test_get_account_balances_by_type(self):
        """Test getting account balances by type."""
        result = self.report_generator._get_account_balances_by_type(
            account_type='ASSET',
            as_of_date=self.today
        )
        
        # Should return 2 asset accounts (cash and AR)
        self.assertEqual(len(result), 2)
        
        # Verify AR balance
        ar_balance = next(a for a in result if a['account_number'] == '1100')
        self.assertEqual(ar_balance['balance'], Decimal('1750.00'))
    
    def test_get_account_balances_by_type_for_period(self):
        """Test getting account balances by type for a period."""
        result = self.report_generator._get_account_balances_by_type_for_period(
            account_type='REVENUE',
            start_date=self.today - timedelta(days=1),
            end_date=self.today
        )
        
        # Should return 1 revenue account (sales)
        self.assertEqual(len(result), 1)
        
        # Verify sales balance (only the 1000 transaction, not the 750 from last month)
        self.assertEqual(abs(result[0]['balance']), Decimal('1000.00'))
    
    def test_get_all_account_balances(self):
        """Test getting balances for all accounts."""
        result = self.report_generator._get_all_account_balances(as_of_date=self.today)
        
        # Should return all 7 accounts
        self.assertEqual(len(result), 7)
        
        # Verify debit and credit balances are correctly assigned
        for account in result:
            if account['account_type'] == 'Asset':
                self.assertGreaterEqual(abs(account['debit_balance']), Decimal('0.00'))
                self.assertEqual(account['credit_balance'], Decimal('0.00'))
            elif account['account_type'] == 'Liability':
                self.assertEqual(account['debit_balance'], Decimal('0.00'))
                self.assertGreaterEqual(abs(account['credit_balance']), Decimal('0.00'))
    
    def test_calculate_period_activity(self):
        """Test calculating period activity for an account."""
        activity = self.report_generator._calculate_period_activity(
            account=self.sales_account,
            start_date=self.today - timedelta(days=1),
            end_date=self.today
        )
        
        # Only the 1000 transaction should be included (not the 750 from last month)
        self.assertEqual(abs(activity), Decimal('1000.00'))
    
    @patch('accounting.services.report_generator.timezone')
    def test_get_comparative_date(self, mock_timezone):
        """Test getting comparative date."""
        test_date = date(2023, 1, 15)
        mock_timedelta = MagicMock()
        mock_timedelta.days = 365
        mock_timezone.timedelta.return_value = mock_timedelta
        
        result = self.report_generator._get_comparative_date(test_date)
        self.assertEqual(result, date(2022, 1, 15))
    
    def test_report_generator_error_handling(self):
        """Test error handling in report generator."""
        # Test with invalid account type
        with self.assertRaises(ValidationError):
            self.report_generator._get_account_balances_by_type(
                account_type='INVALID_TYPE',
                as_of_date=self.today
            )
        
        # Test with invalid date range for income statement
        with self.assertRaises(ValidationError):
            self.report_generator.generate_income_statement(
                start_date=self.today,
                end_date=self.last_month
            )
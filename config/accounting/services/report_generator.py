"""
Report generator service for financial reporting.

This module contains the core logic for generating financial reports
like Balance Sheet, Income Statement, and other financial statements.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounting.models import Account, Transaction, JournalItem, Report, ReportTemplate
from core.utils import DateUtils, DecimalPrecision

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Service class for generating financial reports.
    
    This class encapsulates all the business logic for generating
    various types of financial reports and statements.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        self.date_utils = DateUtils()
        self.decimal_precision = DecimalPrecision()
    
    def generate_balance_sheet(self, as_of_date: date = None, include_comparative: bool = False) -> Dict[str, Any]:
        """
        Generate a Balance Sheet report.
        
        Args:
            as_of_date: Date for the balance sheet (defaults to current date)
            include_comparative: Whether to include comparative figures
            
        Returns:
            Dictionary containing balance sheet data
        """
        if as_of_date is None:
            as_of_date = timezone.now().date()
        
        try:
            # Get account balances as of the specified date
            assets = self._get_account_balances_by_type('ASSET', as_of_date)
            liabilities = self._get_account_balances_by_type('LIABILITY', as_of_date)
            equity = self._get_account_balances_by_type('EQUITY', as_of_date)
            
            # Calculate totals
            total_assets = sum(account['balance'] for account in assets)
            total_liabilities = sum(account['balance'] for account in liabilities)
            total_equity = sum(account['balance'] for account in equity)
            
            # Validate accounting equation
            if abs(total_assets - (total_liabilities + total_equity)) > Decimal('0.01'):
                logger.warning("Balance sheet does not balance")
            
            report_data = {
                'report_type': 'BALANCE_SHEET',
                'as_of_date': as_of_date,
                'generated_at': timezone.now(),
                'assets': assets,
                'liabilities': liabilities,
                'equity': equity,
                'totals': {
                    'total_assets': total_assets,
                    'total_liabilities': total_liabilities,
                    'total_equity': total_equity,
                    'total_liabilities_and_equity': total_liabilities + total_equity
                }
            }
            
            if include_comparative:
                # Get comparative figures (previous period)
                comparative_date = self._get_comparative_date(as_of_date)
                report_data['comparative'] = self.generate_balance_sheet(comparative_date, False)
            
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to generate balance sheet: {e}")
            raise ValidationError(f"Failed to generate balance sheet: {str(e)}")
    
    def generate_income_statement(self, start_date: date = None, end_date: date = None, 
                                include_comparative: bool = False) -> Dict[str, Any]:
        """
        Generate an Income Statement report.
        
        Args:
            start_date: Start date for the period
            end_date: End date for the period
            include_comparative: Whether to include comparative figures
            
        Returns:
            Dictionary containing income statement data
        """
        if start_date is None or end_date is None:
            # Default to current month
            month_dates = self.date_utils.get_month_dates()
            start_date = month_dates['start']
            end_date = month_dates['end']
        
        try:
            # Get revenue and expense accounts for the period
            revenue = self._get_account_balances_by_type_for_period('REVENUE', start_date, end_date)
            expenses = self._get_account_balances_by_type_for_period('EXPENSE', start_date, end_date)
            
            # Calculate totals
            total_revenue = sum(account['balance'] for account in revenue)
            total_expenses = sum(account['balance'] for account in expenses)
            net_income = total_revenue - total_expenses
            
            report_data = {
                'report_type': 'INCOME_STATEMENT',
                'start_date': start_date,
                'end_date': end_date,
                'generated_at': timezone.now(),
                'revenue': revenue,
                'expenses': expenses,
                'totals': {
                    'total_revenue': total_revenue,
                    'total_expenses': total_expenses,
                    'net_income': net_income
                }
            }
            
            if include_comparative:
                # Get comparative figures (previous period)
                period_length = (end_date - start_date).days
                comparative_start = start_date - timezone.timedelta(days=period_length)
                comparative_end = start_date - timezone.timedelta(days=1)
                report_data['comparative'] = self.generate_income_statement(
                    comparative_start, comparative_end, False
                )
            
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to generate income statement: {e}")
            raise ValidationError(f"Failed to generate income statement: {str(e)}")
    
    def generate_trial_balance(self, as_of_date: date = None) -> Dict[str, Any]:
        """
        Generate a Trial Balance report.
        
        Args:
            as_of_date: Date for the trial balance (defaults to current date)
            
        Returns:
            Dictionary containing trial balance data
        """
        if as_of_date is None:
            as_of_date = timezone.now().date()
        
        try:
            # Get all account balances
            accounts = self._get_all_account_balances(as_of_date)
            
            # Calculate totals
            total_debits = sum(account['debit_balance'] for account in accounts)
            total_credits = sum(account['credit_balance'] for account in accounts)
            
            report_data = {
                'report_type': 'TRIAL_BALANCE',
                'as_of_date': as_of_date,
                'generated_at': timezone.now(),
                'accounts': accounts,
                'totals': {
                    'total_debits': total_debits,
                    'total_credits': total_credits,
                    'difference': total_debits - total_credits
                }
            }
            
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to generate trial balance: {e}")
            raise ValidationError(f"Failed to generate trial balance: {str(e)}")
    
    def generate_general_ledger(self, account: Account, start_date: date = None, 
                               end_date: date = None) -> Dict[str, Any]:
        """
        Generate a General Ledger report for a specific account.
        
        Args:
            account: The account to generate ledger for
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            Dictionary containing general ledger data
        """
        if start_date is None or end_date is None:
            # Default to current month
            month_dates = self.date_utils.get_month_dates()
            start_date = month_dates['start']
            end_date = month_dates['end']
        
        try:
            # Get journal items for the account in the period
            journal_items = JournalItem.objects.filter(
                account=account,
                journal_entry__transaction__transaction_date__gte=start_date,
                journal_entry__transaction__transaction_date__lte=end_date,
                journal_entry__transaction__is_posted=True
            ).order_by('journal_entry__transaction__transaction_date', 'created_at')
            
            # Calculate running balance
            running_balance = account.get_balance(start_date - timezone.timedelta(days=1))
            ledger_entries = []
            
            for item in journal_items:
                if item.debit_amount > 0:
                    running_balance += item.debit_amount
                else:
                    running_balance -= item.credit_amount
                
                ledger_entries.append({
                    'date': item.journal_entry.transaction.transaction_date,
                    'description': item.description or item.journal_entry.description,
                    'reference': item.journal_entry.transaction.transaction_number,
                    'debit': item.debit_amount,
                    'credit': item.credit_amount,
                    'balance': running_balance
                })
            
            report_data = {
                'report_type': 'GENERAL_LEDGER',
                'account': {
                    'account_number': account.account_number,
                    'name': account.name,
                    'account_type': account.account_type.name
                },
                'start_date': start_date,
                'end_date': end_date,
                'opening_balance': account.get_balance(start_date - timezone.timedelta(days=1)),
                'closing_balance': account.get_balance(end_date),
                'generated_at': timezone.now(),
                'entries': ledger_entries
            }
            
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to generate general ledger: {e}")
            raise ValidationError(f"Failed to generate general ledger: {str(e)}")
    
    def generate_cash_flow_statement(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """
        Generate a Cash Flow Statement.
        
        Args:
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            Dictionary containing cash flow statement data
        """
        if start_date is None or end_date is None:
            # Default to current month
            month_dates = self.date_utils.get_month_dates()
            start_date = month_dates['start']
            end_date = month_dates['end']
        
        try:
            # Get cash accounts
            cash_accounts = Account.objects.filter(
                is_cash_account=True,
                is_active=True
            )
            
            # Calculate cash flows by category
            operating_activities = self._calculate_operating_cash_flows(start_date, end_date)
            investing_activities = self._calculate_investing_cash_flows(start_date, end_date)
            financing_activities = self._calculate_financing_cash_flows(start_date, end_date)
            
            # Calculate net cash flow
            net_cash_flow = operating_activities + investing_activities + financing_activities
            
            # Get beginning and ending cash balances
            beginning_cash = sum(account.get_balance(start_date - timezone.timedelta(days=1)) 
                               for account in cash_accounts)
            ending_cash = sum(account.get_balance(end_date) for account in cash_accounts)
            
            report_data = {
                'report_type': 'CASH_FLOW_STATEMENT',
                'start_date': start_date,
                'end_date': end_date,
                'generated_at': timezone.now(),
                'operating_activities': operating_activities,
                'investing_activities': investing_activities,
                'financing_activities': financing_activities,
                'net_cash_flow': net_cash_flow,
                'beginning_cash': beginning_cash,
                'ending_cash': ending_cash
            }
            
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to generate cash flow statement: {e}")
            raise ValidationError(f"Failed to generate cash flow statement: {str(e)}")
    
    def _get_account_balances_by_type(self, account_type: str, as_of_date: date) -> List[Dict[str, Any]]:
        """
        Get account balances for a specific account type as of a date.
        
        Args:
            account_type: The account type to get balances for
            as_of_date: Date to calculate balances as of
            
        Returns:
            List of account balance dictionaries
        """
        accounts = Account.objects.filter(
            account_type__code=account_type,
            is_active=True
        ).order_by('account_number')
        
        balances = []
        for account in accounts:
            balance = account.get_balance(as_of_date)
            balances.append({
                'account_number': account.account_number,
                'name': account.name,
                'category': account.category.name,
                'balance': balance,
                'formatted_balance': self.decimal_precision.format_currency(balance)
            })
        
        return balances
    
    def _get_account_balances_by_type_for_period(self, account_type: str, start_date: date, 
                                                end_date: date) -> List[Dict[str, Any]]:
        """
        Get account balances for a specific account type for a period.
        
        Args:
            account_type: The account type to get balances for
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            List of account balance dictionaries
        """
        accounts = Account.objects.filter(
            account_type__code=account_type,
            is_active=True
        ).order_by('account_number')
        
        balances = []
        for account in accounts:
            # Calculate period activity
            period_activity = self._calculate_period_activity(account, start_date, end_date)
            balances.append({
                'account_number': account.account_number,
                'name': account.name,
                'category': account.category.name,
                'balance': period_activity,
                'formatted_balance': self.decimal_precision.format_currency(period_activity)
            })
        
        return balances
    
    def _get_all_account_balances(self, as_of_date: date) -> List[Dict[str, Any]]:
        """
        Get balances for all accounts as of a date.
        
        Args:
            as_of_date: Date to calculate balances as of
            
        Returns:
            List of account balance dictionaries
        """
        accounts = Account.objects.filter(is_active=True).order_by('account_number')
        
        balances = []
        for account in accounts:
            balance = account.get_balance(as_of_date)
            
            if account.is_debit_balance():
                debit_balance = balance if balance > 0 else Decimal('0')
                credit_balance = Decimal('0')
            else:
                debit_balance = Decimal('0')
                credit_balance = balance if balance > 0 else Decimal('0')
            
            balances.append({
                'account_number': account.account_number,
                'name': account.name,
                'account_type': account.account_type.name,
                'debit_balance': debit_balance,
                'credit_balance': credit_balance,
                'formatted_debit': self.decimal_precision.format_currency(debit_balance),
                'formatted_credit': self.decimal_precision.format_currency(credit_balance)
            })
        
        return balances
    
    def _calculate_period_activity(self, account: Account, start_date: date, end_date: date) -> Decimal:
        """
        Calculate account activity for a specific period.
        
        Args:
            account: The account to calculate activity for
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            Decimal representing the period activity
        """
        journal_items = JournalItem.objects.filter(
            account=account,
            journal_entry__transaction__transaction_date__gte=start_date,
            journal_entry__transaction__transaction_date__lte=end_date,
            journal_entry__transaction__is_posted=True
        )
        
        activity = Decimal('0')
        for item in journal_items:
            if item.debit_amount > 0:
                activity += item.debit_amount
            else:
                activity -= item.credit_amount
        
        return activity
    
    def _calculate_operating_cash_flows(self, start_date: date, end_date: date) -> Decimal:
        """
        Calculate operating cash flows for a period.
        
        Args:
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            Decimal representing operating cash flows
        """
        # This is a simplified calculation
        # In a real implementation, you would need more sophisticated logic
        operating_accounts = Account.objects.filter(
            account_type__code__in=['REVENUE', 'EXPENSE'],
            is_active=True
        )
        
        total_operating = Decimal('0')
        for account in operating_accounts:
            activity = self._calculate_period_activity(account, start_date, end_date)
            if account.account_type.code == 'REVENUE':
                total_operating += activity
            else:
                total_operating -= activity
        
        return total_operating
    
    def _calculate_investing_cash_flows(self, start_date: date, end_date: date) -> Decimal:
        """
        Calculate investing cash flows for a period.
        
        Args:
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            Decimal representing investing cash flows
        """
        # This is a simplified calculation
        # In a real implementation, you would need more sophisticated logic
        investing_accounts = Account.objects.filter(
            account_type__code='ASSET',
            category__name__icontains='fixed',
            is_active=True
        )
        
        total_investing = Decimal('0')
        for account in investing_accounts:
            activity = self._calculate_period_activity(account, start_date, end_date)
            total_investing -= activity  # Investing activities typically reduce cash
        
        return total_investing
    
    def _calculate_financing_cash_flows(self, start_date: date, end_date: date) -> Decimal:
        """
        Calculate financing cash flows for a period.
        
        Args:
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            Decimal representing financing cash flows
        """
        # This is a simplified calculation
        # In a real implementation, you would need more sophisticated logic
        financing_accounts = Account.objects.filter(
            account_type__code__in=['LIABILITY', 'EQUITY'],
            is_active=True
        )
        
        total_financing = Decimal('0')
        for account in financing_accounts:
            activity = self._calculate_period_activity(account, start_date, end_date)
            if account.account_type.code == 'LIABILITY':
                total_financing += activity  # Borrowing increases cash
            else:
                total_financing -= activity  # Equity transactions typically reduce cash
        
        return total_financing
    
    def _get_comparative_date(self, current_date: date) -> date:
        """
        Get the comparative date for a given date.
        
        Args:
            current_date: The current date
            
        Returns:
            The comparative date
        """
        # This is a simplified calculation
        # In a real implementation, you would need more sophisticated logic
        return current_date - timezone.timedelta(days=365)  # Previous year 
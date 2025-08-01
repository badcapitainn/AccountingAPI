"""
Custom Model Managers for accounting models.

This module contains custom Model Managers that encapsulate complex
query logic and provide convenient methods for common operations.
"""

from django.db import models
from django.db.models import Sum, Q, F
from django.core.exceptions import ValidationError
from decimal import Decimal


class AccountManager(models.Manager):
    """
    Custom manager for Account model.
    
    Provides methods for common account-related queries and operations.
    """
    
    def active(self):
        """Get all active accounts."""
        return self.filter(is_active=True, is_deleted=False)
    
    def by_type(self, account_type):
        """Get accounts by account type."""
        return self.filter(account_type=account_type, is_active=True, is_deleted=False)
    
    def by_category(self, category):
        """Get accounts by category."""
        return self.filter(category=category, is_active=True, is_deleted=False)
    
    def bank_accounts(self):
        """Get all bank accounts."""
        return self.filter(is_bank_account=True, is_active=True, is_deleted=False)
    
    def cash_accounts(self):
        """Get all cash accounts."""
        return self.filter(is_cash_account=True, is_active=True, is_deleted=False)
    
    def reconcilable_accounts(self):
        """Get all reconcilable accounts."""
        return self.filter(is_reconcilable=True, is_active=True, is_deleted=False)
    
    def with_balances(self, as_of_date=None):
        """Get accounts with their current balances."""
        from django.utils import timezone
        if as_of_date is None:
            as_of_date = timezone.now().date()
        
        accounts = self.active()
        for account in accounts:
            account.current_balance = account.get_balance(as_of_date)
        
        return accounts
    
    def with_activity(self, start_date, end_date):
        """Get accounts with activity in a date range."""
        from accounting.models import JournalItem
        
        accounts = self.active()
        for account in accounts:
            activity = JournalItem.objects.filter(
                account=account,
                journal_entry__transaction__transaction_date__gte=start_date,
                journal_entry__transaction__transaction_date__lte=end_date,
                journal_entry__transaction__is_posted=True
            ).aggregate(
                total_debits=Sum('debit_amount'),
                total_credits=Sum('credit_amount')
            )
            
            account.period_debits = activity['total_debits'] or Decimal('0')
            account.period_credits = activity['total_credits'] or Decimal('0')
            account.period_activity = account.period_debits - account.period_credits
        
        return accounts


class TransactionManager(models.Manager):
    """
    Custom manager for Transaction model.
    
    Provides methods for common transaction-related queries and operations.
    """
    
    def posted(self):
        """Get all posted transactions."""
        return self.filter(is_posted=True, is_deleted=False)
    
    def pending(self):
        """Get all pending transactions."""
        return self.filter(status='PENDING', is_deleted=False)
    
    def draft(self):
        """Get all draft transactions."""
        return self.filter(status='DRAFT', is_deleted=False)
    
    def voided(self):
        """Get all voided transactions."""
        return self.filter(status='VOIDED', is_deleted=False)
    
    def by_date_range(self, start_date, end_date):
        """Get transactions in a date range."""
        return self.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            is_deleted=False
        )
    
    def by_type(self, transaction_type):
        """Get transactions by type."""
        return self.filter(transaction_type=transaction_type, is_deleted=False)
    
    def by_account(self, account):
        """Get transactions involving a specific account."""
        from accounting.models import JournalItem
        
        journal_items = JournalItem.objects.filter(account=account)
        transaction_ids = journal_items.values_list('journal_entry__transaction', flat=True).distinct()
        
        return self.filter(id__in=transaction_ids, is_deleted=False)
    
    def with_totals(self):
        """Get transactions with calculated totals."""
        transactions = self.all()
        for transaction in transactions:
            transaction.total_debits = transaction.get_total_debits()
            transaction.total_credits = transaction.get_total_credits()
            transaction.is_balanced = transaction.is_balanced()
        
        return transactions
    
    def large_transactions(self, threshold):
        """Get transactions above a certain amount threshold."""
        return self.filter(amount__gte=threshold, is_deleted=False)
    
    def recent_transactions(self, days=30):
        """Get recent transactions within specified days."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now().date() - timedelta(days=days)
        return self.filter(transaction_date__gte=cutoff_date, is_deleted=False)


class JournalEntryManager(models.Manager):
    """
    Custom manager for JournalEntry model.
    
    Provides methods for common journal entry-related queries and operations.
    """
    
    def by_transaction(self, transaction):
        """Get journal entries for a specific transaction."""
        return self.filter(transaction=transaction)
    
    def by_account(self, account):
        """Get journal entries involving a specific account."""
        from accounting.models import JournalItem
        
        journal_items = JournalItem.objects.filter(account=account)
        entry_ids = journal_items.values_list('journal_entry', flat=True).distinct()
        
        return self.filter(id__in=entry_ids)
    
    def with_items(self):
        """Get journal entries with their items."""
        return self.prefetch_related('items', 'items__account')
    
    def balanced_entries(self):
        """Get only balanced journal entries."""
        entries = self.all()
        balanced = []
        
        for entry in entries:
            if entry.is_balanced():
                balanced.append(entry)
        
        return balanced


class ReportManager(models.Manager):
    """
    Custom manager for Report model.
    
    Provides methods for common report-related queries and operations.
    """
    
    def completed(self):
        """Get all completed reports."""
        return self.filter(status='COMPLETED', is_deleted=False)
    
    def pending(self):
        """Get all pending reports."""
        return self.filter(status='PENDING', is_deleted=False)
    
    def failed(self):
        """Get all failed reports."""
        return self.filter(status='FAILED', is_deleted=False)
    
    def by_template(self, template):
        """Get reports by template."""
        return self.filter(template=template, is_deleted=False)
    
    def by_user(self, user):
        """Get reports generated by a specific user."""
        return self.filter(generated_by=user, is_deleted=False)
    
    def recent_reports(self, days=30):
        """Get recent reports within specified days."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date, is_deleted=False)
    
    def downloadable_reports(self):
        """Get reports that are available for download."""
        return self.filter(
            status='COMPLETED',
            file_path__isnull=False,
            is_deleted=False
        ).exclude(file_path='')


class AccountTypeManager(models.Manager):
    """
    Custom manager for AccountType model.
    
    Provides methods for common account type-related queries and operations.
    """
    
    def active(self):
        """Get all active account types."""
        return self.filter(is_active=True)
    
    def with_accounts(self):
        """Get account types with their associated accounts."""
        return self.prefetch_related('accounts')
    
    def by_normal_balance(self, balance_type):
        """Get account types by normal balance type."""
        return self.filter(normal_balance=balance_type, is_active=True)


class TransactionTypeManager(models.Manager):
    """
    Custom manager for TransactionType model.
    
    Provides methods for common transaction type-related queries and operations.
    """
    
    def active(self):
        """Get all active transaction types."""
        return self.filter(is_active=True)
    
    def with_transactions(self):
        """Get transaction types with their associated transactions."""
        return self.prefetch_related('transactions')
    
    def frequently_used(self, limit=10):
        """Get most frequently used transaction types."""
        return self.annotate(
            transaction_count=models.Count('transactions')
        ).order_by('-transaction_count')[:limit] 
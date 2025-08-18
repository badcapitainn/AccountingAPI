"""
Account models for the Chart of Accounts.

This module contains models for managing the Chart of Accounts,
including account types, categories, and individual accounts.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

from core.models import TimeStampedModel, SoftDeleteModel


class AccountType(models.Model):
    """
    Model for defining account types in the Chart of Accounts.
    
    Account types define the fundamental categories of accounts such as
    Assets, Liabilities, Equity, Revenue, and Expenses.
    """
    ASSET = 'ASSET'
    LIABILITY = 'LIABILITY'
    EQUITY = 'EQUITY'
    REVENUE = 'REVENUE'
    EXPENSE = 'EXPENSE'
    
    ACCOUNT_TYPE_CHOICES = [
        (ASSET, 'Asset'),
        (LIABILITY, 'Liability'),
        (EQUITY, 'Equity'),
        (REVENUE, 'Revenue'),
        (EXPENSE, 'Expense'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name="Account Type Name")
    code = models.CharField(max_length=10, unique=True, verbose_name="Account Type Code")
    description = models.TextField(blank=True, verbose_name="Description")
    normal_balance = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, verbose_name="Normal Balance")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Account Type"
        verbose_name_plural = "Account Types"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        """Validate account type data."""
        if self.normal_balance not in dict(self.ACCOUNT_TYPE_CHOICES):
            raise ValidationError("Invalid normal balance type.")
    
    def get_accounts(self):
        """Get all accounts of this type."""
        return self.accounts.filter(is_active=True)


class AccountCategory(models.Model):
    """
    Model for organizing accounts into categories within account types.
    
    Account categories provide a way to group related accounts together,
    such as "Current Assets", "Fixed Assets", "Current Liabilities", etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Category Name")
    code = models.CharField(max_length=100, verbose_name="Category Code")
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name='categories', verbose_name="Account Type")
    description = models.TextField(blank=True, verbose_name="Description")
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories', verbose_name="Parent Category")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Sort Order")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Account Category"
        verbose_name_plural = "Account Categories"
        ordering = ['account_type', 'sort_order', 'name']
        unique_together = ['code', 'account_type']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_full_path(self):
        """Get the full hierarchical path of this category."""
        path = [self.name]
        parent = self.parent_category
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent_category
        return ' > '.join(path)
    
    def get_subcategories(self):
        """Get all active subcategories."""
        return self.subcategories.filter(is_active=True)
    
    def get_accounts(self):
        """Get all accounts in this category."""
        return self.accounts.filter(is_active=True)


class Account(TimeStampedModel, SoftDeleteModel):
    """
    Model for individual accounts in the Chart of Accounts.
    
    This is the core model for the Chart of Accounts, representing
    individual accounts that can be used for recording transactions.
    """
    ASSET = 'ASSET'
    LIABILITY = 'LIABILITY'
    EQUITY = 'EQUITY'
    REVENUE = 'REVENUE'
    EXPENSE = 'EXPENSE'
    
    ACCOUNT_TYPE_CHOICES = [
        (ASSET, 'Asset'),
        (LIABILITY, 'Liability'),
        (EQUITY, 'Equity'),
        (REVENUE, 'Revenue'),
        (EXPENSE, 'Expense'),
    ]
    
    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'
    
    BALANCE_TYPE_CHOICES = [
        (DEBIT, 'Debit'),
        (CREDIT, 'Credit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_number = models.CharField(max_length=20, unique=True, verbose_name="Account Number")
    name = models.CharField(max_length=200, verbose_name="Account Name")
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Account classification
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, related_name='accounts', verbose_name="Account Type")
    category = models.ForeignKey(AccountCategory, on_delete=models.PROTECT, related_name='accounts', verbose_name="Account Category")
    
    # Balance information
    balance_type = models.CharField(max_length=10, choices=BALANCE_TYPE_CHOICES, verbose_name="Normal Balance")
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Opening Balance")
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Current Balance")
    
    # Account properties
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    is_contra_account = models.BooleanField(default=False, verbose_name="Is Contra Account")
    is_bank_account = models.BooleanField(default=False, verbose_name="Is Bank Account")
    is_cash_account = models.BooleanField(default=False, verbose_name="Is Cash Account")
    is_reconcilable = models.BooleanField(default=False, verbose_name="Is Reconcilable")
    
    # Account restrictions
    allow_posting = models.BooleanField(default=True, verbose_name="Allow Posting")
    require_reconciliation = models.BooleanField(default=False, verbose_name="Require Reconciliation")
    
    # Metadata
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Sort Order")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ['account_number']
        indexes = [
            models.Index(fields=['account_number']),
            models.Index(fields=['account_type', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.account_number} - {self.name}"
    
    def clean(self):
        """Validate account data."""
        if self.account_type and self.balance_type:
            # Ensure balance type matches account type normal balance
            if self.account_type.normal_balance != self.balance_type:
                raise ValidationError("Balance type must match account type normal balance.")
        
        # Validate account number format
        if not self.account_number:
            raise ValidationError("Account number is required.")
        
        # Check for duplicate account numbers
        if Account.objects.filter(account_number=self.account_number).exclude(pk=self.pk).exists():
            raise ValidationError("Account number must be unique.")
    
    def get_balance(self, as_of_date=None):
        """
        Get the account balance as of a specific date.

        Args:
            as_of_date: Date to calculate balance for (defaults to current date)

        Returns:
            Decimal representing the account balance
        """
        balance = self.opening_balance
        from .transactions import JournalItem

        # The filter query should apply to all cases
        if as_of_date:
            items = JournalItem.objects.filter(
                account=self,
                journal_entry__transaction__transaction_date__lte=as_of_date,
                journal_entry__transaction__is_posted=True
            )
        else:
            items = JournalItem.objects.filter(
                account=self,
                journal_entry__transaction__is_posted=True
            )

        for item in items:
            if item.debit_amount > 0:
                balance += item.debit_amount
            else:
                balance -= item.credit_amount

        # Adjust balance based on account balance type
        # For CREDIT balance accounts (liabilities, equity, revenue), 
        # we need to return the opposite of the calculated balance
        if self.balance_type == self.CREDIT:
            return -balance
        else:
            return balance
    
    def update_balance(self):
        """Update the current balance based on posted journal items."""
        balance = self.opening_balance
        from .transactions import JournalItem
        
        # Calculate current balance from all posted journal items
        items = JournalItem.objects.filter(
            account=self,
            journal_entry__transaction__is_posted=True
        )
        
        converted_balance : Decimal = Decimal(str(balance))
        for item in items:
            
            if item.debit_amount > 0:
                converted_balance += Decimal(str(item.debit_amount))
            else:
                converted_balance -= Decimal(str(item.credit_amount))
        
        # Adjust balance based on account balance type
        if self.balance_type == self.CREDIT:
            self.current_balance = -converted_balance
        else:
            self.current_balance = converted_balance
            
        self.save(update_fields=['current_balance'])
    
    def get_transaction_history(self, start_date=None, end_date=None):
        """
        Get transaction history for this account.
        
        Args:
            start_date: Start date for history (defaults to None)
            end_date: End date for history (defaults to None)
            
        Returns:
            QuerySet of JournalItem objects
        """
        from .transactions import JournalItem
        
        queryset = JournalItem.objects.filter(account=self)
        
        if start_date:
            queryset = queryset.filter(journal_entry__transaction_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(journal_entry__transaction_date__lte=end_date)
        
        return queryset.order_by('journal_entry__transaction_date', 'created_at')
    
    def is_debit_balance(self):
        """Check if this account normally has a debit balance."""
        return self.balance_type == self.DEBIT
    
    def is_credit_balance(self):
        """Check if this account normally has a credit balance."""
        return self.balance_type == self.CREDIT
    
    def get_formatted_balance(self):
        """Get the current balance formatted as currency."""
        from core.utils import DecimalPrecision
        return DecimalPrecision.format_currency(self.current_balance)
    
    def can_post_transactions(self):
        """Check if this account can have transactions posted to it."""
        return self.is_active and self.allow_posting and not self.is_deleted 
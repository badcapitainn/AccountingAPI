"""
Transaction models for recording financial transactions.

This module contains models for managing financial transactions,
journal entries, and related data structures.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid

from core.models import TimeStampedModel, SoftDeleteModel


class TransactionType(models.Model):
    """
    Model for defining types of transactions.
    
    Transaction types help categorize and organize different kinds
    of financial transactions for reporting and analysis purposes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name="Transaction Type Name")
    code = models.CharField(max_length=10, unique=True, verbose_name="Transaction Type Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Transaction Type"
        verbose_name_plural = "Transaction Types"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Transaction(TimeStampedModel, SoftDeleteModel):
    """
    Model for recording financial transactions.
    
    This is the main model for recording financial transactions in the system.
    Each transaction can have multiple journal entries and represents a complete
    financial event.
    """
    PENDING = 'PENDING'
    POSTED = 'POSTED'
    VOIDED = 'VOIDED'
    DRAFT = 'DRAFT'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (POSTED, 'Posted'),
        (VOIDED, 'Voided'),
        (DRAFT, 'Draft'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_number = models.CharField(max_length=50, unique=True, verbose_name="Transaction Number")
    reference_number = models.CharField(max_length=100, blank=True, verbose_name="Reference Number")
    description = models.TextField(verbose_name="Description")
    
    # Transaction details
    transaction_date = models.DateField(verbose_name="Transaction Date")
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.PROTECT, related_name='transactions', verbose_name="Transaction Type")
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Total Amount")
    
    # Status and posting
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT, verbose_name="Status")
    is_posted = models.BooleanField(default=False, verbose_name="Is Posted")
    posted_date = models.DateTimeField(null=True, blank=True, verbose_name="Posted Date")
    posted_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_transactions', verbose_name="Posted By")
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Notes")
    attachments = models.JSONField(default=list, blank=True, verbose_name="Attachments")
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_number']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['status', 'is_posted']),
            models.Index(fields=['transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.transaction_number} - {self.description}"
    
    def clean(self):
        """Validate transaction data."""
        if self.transaction_date > timezone.now().date():
            raise ValidationError("Transaction date cannot be in the future.")
        
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be greater than zero.")
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate transaction number if not provided."""
        if not self.transaction_number:
            self.transaction_number = self.generate_transaction_number()
        super().save(*args, **kwargs)
    
    def generate_transaction_number(self):
        """Generate a unique transaction number."""
        import datetime
        prefix = f"TXN{datetime.datetime.now().strftime('%Y%m%d')}"
        last_transaction = Transaction.objects.filter(
            transaction_number__startswith=prefix
        ).order_by('-transaction_number').first()
        
        if last_transaction:
            last_number = int(last_transaction.transaction_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def post_transaction(self, user):
        """
        Post the transaction to the general ledger.
        
        Args:
            user: The user posting the transaction
        """
        if self.is_posted:
            raise ValidationError("Transaction is already posted.")
        
        if self.status == self.VOIDED:
            raise ValidationError("Cannot post a voided transaction.")
        
        # Validate that debits equal credits
        self.validate_balance()
        
        # Mark as posted
        self.is_posted = True
        self.status = self.POSTED
        self.posted_date = timezone.now()
        self.posted_by = user
        self.save()
        
        # Update account balances
        self.update_account_balances()
    
    def void_transaction(self, user, reason=""):
        """
        Void the transaction.
        
        Args:
            user: The user voiding the transaction
            reason: Reason for voiding the transaction
        """
        if not self.is_posted:
            raise ValidationError("Cannot void an unposted transaction.")
        
        # Reverse the transaction
        self.reverse_transaction(user, reason)
        
        # Mark as voided
        self.status = self.VOIDED
        self.save()
    
    def reverse_transaction(self, user, reason=""):
        """
        Create a reversing transaction.
        
        Args:
            user: The user creating the reversal
            reason: Reason for the reversal
        """
        # Create a new transaction that reverses this one
        reversal = Transaction.objects.create(
            description=f"Reversal of {self.transaction_number} - {reason}",
            transaction_date=timezone.now().date(),
            transaction_type=self.transaction_type,
            amount=self.amount,
            status=self.DRAFT
        )
        
        # Create reversing journal entries
        for entry in self.journal_entries.all():
            reversal_entry = entry.journalentry_set.create(
                transaction=reversal,
                description=entry.description,
                amount=-entry.amount  # Reverse the amount
            )
            
            # Create reversing journal items
            for item in entry.items.all():
                reversal_entry.items.create(
                    account=item.account,
                    debit_amount=item.credit_amount,  # Swap debit and credit
                    credit_amount=item.debit_amount,
                    description=item.description
                )
        
        return reversal
    
    def validate_balance(self):
        """Validate that debits equal credits."""
        total_debits = Decimal('0')
        total_credits = Decimal('0')
        
        for entry in self.journal_entries.all():
            for item in entry.items.all():
                total_debits += item.debit_amount
                total_credits += item.credit_amount
        
        if total_debits != total_credits:
            raise ValidationError(f"Transaction is not balanced. Debits: {total_debits}, Credits: {total_credits}")
    
    def update_account_balances(self):
        """Update balances for all accounts involved in this transaction."""
        for entry in self.journal_entries.all():
            for item in entry.items.all():
                item.account.update_balance()
    
    def get_total_debits(self):
        """Get the total debits for this transaction."""
        total = Decimal('0')
        for entry in self.journal_entries.all():
            for item in entry.items.all():
                total += item.debit_amount
        return total
    
    def get_total_credits(self):
        """Get the total credits for this transaction."""
        total = Decimal('0')
        for entry in self.journal_entries.all():
            for item in entry.items.all():
                total += item.credit_amount
        return total
    
    def is_balanced(self):
        """Check if the transaction is balanced (debits = credits)."""
        return self.get_total_debits() == self.get_total_credits()


class JournalEntry(TimeStampedModel):
    """
    Model for individual journal entries within a transaction.
    
    Each journal entry represents a single line item in a transaction,
    typically corresponding to one account and one amount.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='journal_entries', verbose_name="Transaction")
    description = models.TextField(verbose_name="Description")
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Amount")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Sort Order")
    
    class Meta:
        verbose_name = "Journal Entry"
        verbose_name_plural = "Journal Entries"
        ordering = ['transaction', 'sort_order']
    
    def __str__(self):
        return f"{self.transaction.transaction_number} - {self.description}"
    
    def get_total_debits(self):
        """Get the total debits for this journal entry."""
        return sum(item.debit_amount for item in self.items.all())
    
    def get_total_credits(self):
        """Get the total credits for this journal entry."""
        return sum(item.credit_amount for item in self.items.all())
    
    def is_balanced(self):
        """Check if this journal entry is balanced."""
        return self.get_total_debits() == self.get_total_credits()


class JournalItem(TimeStampedModel):
    """
    Model for individual journal items within a journal entry.
    
    Each journal item represents the actual posting to a specific account,
    with either a debit or credit amount.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='items', verbose_name="Journal Entry")
    account = models.ForeignKey('accounting.Account', on_delete=models.PROTECT, related_name='journal_items', verbose_name="Account")
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))], verbose_name="Debit Amount")
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))], verbose_name="Credit Amount")
    description = models.TextField(blank=True, verbose_name="Description")
    
    class Meta:
        verbose_name = "Journal Item"
        verbose_name_plural = "Journal Items"
        ordering = ['journal_entry', 'created_at']
        indexes = [
            models.Index(fields=['account', 'journal_entry']),
            models.Index(fields=['debit_amount', 'credit_amount']),
        ]
    
    def __str__(self):
        return f"{self.account.account_number} - {self.get_amount_display()}"
    
    def clean(self):
        """Validate journal item data."""
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValidationError("A journal item cannot have both debit and credit amounts.")
        
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValidationError("A journal item must have either a debit or credit amount.")
    
    def get_amount_display(self):
        """Get a formatted display of the amount."""
        if self.debit_amount > 0:
            return f"DR {self.debit_amount}"
        else:
            return f"CR {self.credit_amount}"
    
    def get_net_amount(self):
        """Get the net amount (debit - credit)."""
        return self.debit_amount - self.credit_amount 
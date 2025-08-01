"""
Transaction service for handling complex business logic.

This module contains the core business logic for creating, validating,
and posting transactions in the accounting system.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

from accounting.models import Transaction, JournalEntry, JournalItem, Account, TransactionType
from core.utils import AuditUtils, NotificationUtils

logger = logging.getLogger(__name__)


class TransactionService:
    """
    Service class for handling transaction-related business logic.
    
    This class encapsulates all the complex business logic for creating,
    validating, and posting transactions in the accounting system.
    """
    
    def __init__(self):
        """Initialize the transaction service."""
        self.audit_utils = AuditUtils()
        self.notification_utils = NotificationUtils()
    
    def create_transaction(self, data: Dict[str, Any], user: User) -> Transaction:
        """
        Create a new transaction with journal entries.
        
        Args:
            data: Dictionary containing transaction data
            user: The user creating the transaction
            
        Returns:
            Created Transaction object
            
        Raises:
            ValidationError: If transaction data is invalid
        """
        try:
            with db_transaction.atomic():
                # Extract transaction data
                transaction_data = {
                    'description': data.get('description', ''),
                    'transaction_date': data.get('transaction_date'),
                    'transaction_type_id': data.get('transaction_type_id'),
                    'amount': data.get('amount', 0),
                    'reference_number': data.get('reference_number', ''),
                    'notes': data.get('notes', ''),
                }
                
                # Create the transaction
                transaction = Transaction.objects.create(**transaction_data)
                
                # Create journal entries
                journal_entries_data = data.get('journal_entries', [])
                for entry_data in journal_entries_data:
                    self._create_journal_entry(transaction, entry_data)
                
                # Validate the transaction
                self.validate_transaction(transaction)
                
                # Log the activity
                self.audit_utils.log_activity(
                    user=user,
                    action='CREATE',
                    model_name='Transaction',
                    object_id=str(transaction.id),
                    object_repr=str(transaction),
                    changes={'transaction_number': transaction.transaction_number}
                )
                
                logger.info(f"Transaction {transaction.transaction_number} created by {user.username}")
                return transaction
                
        except Exception as e:
            logger.error(f"Failed to create transaction: {e}")
            raise ValidationError(f"Failed to create transaction: {str(e)}")
    
    def _create_journal_entry(self, transaction: Transaction, entry_data: Dict[str, Any]) -> JournalEntry:
        """
        Create a journal entry for a transaction.
        
        Args:
            transaction: The parent transaction
            entry_data: Dictionary containing journal entry data
            
        Returns:
            Created JournalEntry object
        """
        entry = JournalEntry.objects.create(
            transaction=transaction,
            description=entry_data.get('description', ''),
            amount=entry_data.get('amount', 0),
            sort_order=entry_data.get('sort_order', 0)
        )
        
        # Create journal items
        items_data = entry_data.get('items', [])
        for item_data in items_data:
            self._create_journal_item(entry, item_data)
        
        return entry
    
    def _create_journal_item(self, journal_entry: JournalEntry, item_data: Dict[str, Any]) -> JournalItem:
        """
        Create a journal item for a journal entry.
        
        Args:
            journal_entry: The parent journal entry
            item_data: Dictionary containing journal item data
            
        Returns:
            Created JournalItem object
        """
        return JournalItem.objects.create(
            journal_entry=journal_entry,
            account_id=item_data.get('account_id'),
            debit_amount=item_data.get('debit_amount', 0),
            credit_amount=item_data.get('credit_amount', 0),
            description=item_data.get('description', '')
        )
    
    def validate_transaction(self, transaction: Transaction) -> bool:
        """
        Validate a transaction for posting.
        
        Args:
            transaction: The transaction to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If transaction is invalid
        """
        errors = []
        
        # Check if transaction has journal entries
        if not transaction.journal_entries.exists():
            errors.append("Transaction must have at least one journal entry")
        
        # Check if transaction is balanced
        if not transaction.is_balanced():
            total_debits = transaction.get_total_debits()
            total_credits = transaction.get_total_credits()
            errors.append(f"Transaction is not balanced. Debits: {total_debits}, Credits: {total_credits}")
        
        # Validate each journal entry
        for entry in transaction.journal_entries.all():
            entry_errors = self._validate_journal_entry(entry)
            errors.extend(entry_errors)
        
        # Check account permissions
        account_errors = self._validate_account_permissions(transaction)
        errors.extend(account_errors)
        
        if errors:
            raise ValidationError("; ".join(errors))
        
        return True
    
    def _validate_journal_entry(self, entry: JournalEntry) -> List[str]:
        """
        Validate a journal entry.
        
        Args:
            entry: The journal entry to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check if entry has items
        if not entry.items.exists():
            errors.append(f"Journal entry '{entry.description}' must have at least one item")
        
        # Check if entry is balanced
        if not entry.is_balanced():
            total_debits = entry.get_total_debits()
            total_credits = entry.get_total_credits()
            errors.append(f"Journal entry '{entry.description}' is not balanced. Debits: {total_debits}, Credits: {total_credits}")
        
        # Validate each item
        for item in entry.items.all():
            item_errors = self._validate_journal_item(item)
            errors.extend(item_errors)
        
        return errors
    
    def _validate_journal_item(self, item: JournalItem) -> List[str]:
        """
        Validate a journal item.
        
        Args:
            item: The journal item to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check if item has either debit or credit amount
        if item.debit_amount == 0 and item.credit_amount == 0:
            errors.append(f"Journal item for account {item.account.account_number} must have either debit or credit amount")
        
        # Check if item has both debit and credit amounts
        if item.debit_amount > 0 and item.credit_amount > 0:
            errors.append(f"Journal item for account {item.account.account_number} cannot have both debit and credit amounts")
        
        # Check if account is active and allows posting
        if not item.account.can_post_transactions():
            errors.append(f"Account {item.account.account_number} is not active or does not allow posting")
        
        return errors
    
    def _validate_account_permissions(self, transaction: Transaction) -> List[str]:
        """
        Validate account permissions for a transaction.
        
        Args:
            transaction: The transaction to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for entry in transaction.journal_entries.all():
            for item in entry.items.all():
                account = item.account
                
                # Check if account is active
                if not account.is_active:
                    errors.append(f"Account {account.account_number} is not active")
                
                # Check if account allows posting
                if not account.allow_posting:
                    errors.append(f"Account {account.account_number} does not allow posting")
                
                # Check if account is deleted
                if account.is_deleted:
                    errors.append(f"Account {account.account_number} has been deleted")
        
        return errors
    
    def post_transaction(self, transaction: Transaction, user: User) -> bool:
        """
        Post a transaction to the general ledger.
        
        Args:
            transaction: The transaction to post
            user: The user posting the transaction
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValidationError: If transaction cannot be posted
        """
        try:
            with db_transaction.atomic():
                # Validate the transaction
                self.validate_transaction(transaction)
                
                # Post the transaction
                transaction.post_transaction(user)
                
                # Update account balances
                self._update_account_balances(transaction)
                
                # Log the activity
                self.audit_utils.log_activity(
                    user=user,
                    action='POST',
                    model_name='Transaction',
                    object_id=str(transaction.id),
                    object_repr=str(transaction),
                    changes={'status': 'POSTED', 'posted_date': timezone.now().isoformat()}
                )
                
                # Send notification if needed
                self._send_posting_notification(transaction, user)
                
                logger.info(f"Transaction {transaction.transaction_number} posted by {user.username}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to post transaction {transaction.transaction_number}: {e}")
            raise ValidationError(f"Failed to post transaction: {str(e)}")
    
    def _update_account_balances(self, transaction: Transaction):
        """
        Update account balances for all accounts in a transaction.
        
        Args:
            transaction: The transaction to update balances for
        """
        for entry in transaction.journal_entries.all():
            for item in entry.items.all():
                item.account.update_balance()
    
    def _send_posting_notification(self, transaction: Transaction, user: User):
        """
        Send notification about posted transaction.
        
        Args:
            transaction: The posted transaction
            user: The user who posted the transaction
        """
        # This could send notifications to relevant users
        # For now, just log the action
        logger.info(f"Transaction {transaction.transaction_number} posted successfully")
    
    def void_transaction(self, transaction: Transaction, user: User, reason: str = "") -> Transaction:
        """
        Void a posted transaction.
        
        Args:
            transaction: The transaction to void
            user: The user voiding the transaction
            reason: Reason for voiding the transaction
            
        Returns:
            The reversal transaction
            
        Raises:
            ValidationError: If transaction cannot be voided
        """
        try:
            with db_transaction.atomic():
                # Check if transaction can be voided
                if not transaction.is_posted:
                    raise ValidationError("Only posted transactions can be voided")
                
                if transaction.status == Transaction.VOIDED:
                    raise ValidationError("Transaction is already voided")
                
                # Create reversal transaction
                reversal = transaction.reverse_transaction(user, reason)
                
                # Post the reversal
                self.post_transaction(reversal, user)
                
                # Void the original transaction
                transaction.void_transaction(user, reason)
                
                # Log the activity
                self.audit_utils.log_activity(
                    user=user,
                    action='VOID',
                    model_name='Transaction',
                    object_id=str(transaction.id),
                    object_repr=str(transaction),
                    changes={'status': 'VOIDED', 'reason': reason}
                )
                
                logger.info(f"Transaction {transaction.transaction_number} voided by {user.username}")
                return reversal
                
        except Exception as e:
            logger.error(f"Failed to void transaction {transaction.transaction_number}: {e}")
            raise ValidationError(f"Failed to void transaction: {str(e)}")
    
    def get_transaction_summary(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Get a summary of a transaction.
        
        Args:
            transaction: The transaction to summarize
            
        Returns:
            Dictionary containing transaction summary
        """
        return {
            'transaction_number': transaction.transaction_number,
            'description': transaction.description,
            'transaction_date': transaction.transaction_date,
            'amount': transaction.amount,
            'status': transaction.status,
            'is_posted': transaction.is_posted,
            'total_debits': transaction.get_total_debits(),
            'total_credits': transaction.get_total_credits(),
            'is_balanced': transaction.is_balanced(),
            'journal_entries_count': transaction.journal_entries.count(),
            'created_at': transaction.created_at,
            'posted_date': transaction.posted_date,
        }
    
    def get_account_transactions(self, account: Account, start_date=None, end_date=None) -> List[Transaction]:
        """
        Get all transactions for a specific account.
        
        Args:
            account: The account to get transactions for
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of transactions
        """
        journal_items = account.journal_items.filter(
            journal_entry__transaction__is_posted=True
        )
        
        if start_date:
            journal_items = journal_items.filter(
                journal_entry__transaction__transaction_date__gte=start_date
            )
        
        if end_date:
            journal_items = journal_items.filter(
                journal_entry__transaction__transaction_date__lte=end_date
            )
        
        transactions = journal_items.values_list(
            'journal_entry__transaction', flat=True
        ).distinct()
        
        return Transaction.objects.filter(id__in=transactions).order_by('-transaction_date')
    
    def get_transaction_types(self) -> List[TransactionType]:
        """
        Get all active transaction types.
        
        Returns:
            List of active transaction types
        """
        return TransactionType.objects.filter(is_active=True).order_by('name')
    
    def create_recurring_transaction(self, template_data: Dict[str, Any], user: User) -> Transaction:
        """
        Create a recurring transaction based on a template.
        
        Args:
            template_data: Dictionary containing recurring transaction template
            user: The user creating the transaction
            
        Returns:
            Created Transaction object
        """
        # This would implement recurring transaction logic
        # For now, just create a regular transaction
        return self.create_transaction(template_data, user) 
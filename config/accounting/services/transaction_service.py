"""
Transaction service for handling complex business logic.

This module contains the core business logic for creating, validating,
and posting transactions in the accounting system.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Any
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
                print(f"Transaction data: {transaction_data}")

                # Create the transaction
                transaction = Transaction.objects.create(**transaction_data)
                
                
                journal_entries_data = data.get('journal_entries_data', [])
                print(f"Journal entries data: {journal_entries_data}")
                if not journal_entries_data:
                    raise ValidationError("Transaction must have at least one journal entry.")

                for entry_data in journal_entries_data:
                    # Create journal entry and link it to the transaction
                    # This line is key: it correctly links the entry to the new transaction
                    entry = JournalEntry.objects.create(
                        transaction=transaction,
                        description=entry_data.get('description', ''),
                        amount=entry_data.get('amount', 0),
                        sort_order=entry_data.get('sort_order', 0)
                    )

                    items_data = entry_data.get('items', [])
                    if not items_data:
                        raise ValidationError("Each journal entry must have at least one item.")
                        
                    # Create JournalItem objects for bulk creation
                    journal_items_to_create = []
                    for item_data in items_data:
                        journal_items_to_create.append(
                            JournalItem(
                                journal_entry=entry,
                                account_id=item_data.get('account_id'),
                                debit_amount=item_data.get('debit_amount', 0),
                                credit_amount=item_data.get('credit_amount', 0),
                                description=item_data.get('description', '')
                            )
                        )
                    
                    # Use bulk_create for efficiency and robustness
                    JournalItem.objects.bulk_create(journal_items_to_create)

                # Validate the transaction
                # The validation will now pass as entries exist
                self.validate_transaction(transaction)
                
                # ... (audit logging and logger.info calls remain the same)
                self.audit_utils.log_activity(
                    user=user,
                    action='CREATE',
                    model_name='Transaction',
                    object_id=str(transaction.id),
                    object_repr=str(transaction),
                    changes={'transaction_number': transaction.transaction_number},
                    # Pass a user_agent to satisfy the audit log constraint
                    user_agent="Django Test Runner"
                )
                
                logger.info(f"Transaction {transaction.transaction_number} created by {user.username}")
                return transaction
                
        except ValidationError as e:
            logger.error(f"Failed to create transaction due to validation error: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to create transaction: {e}")
            raise ValidationError(f"Failed to create transaction: {str(e)}")

    def validate_transaction(self, transaction: Transaction) -> bool:
        """
        Validate a transaction for posting.
        
        Args:
            transaction: The transaction to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If transaction is invalid
        """
        errors = []
        
        # Check if transaction has journal entries
        if not transaction.journal_entries.exists():
            errors.append("Transaction must have at least one journal entry.")
        
        # Check if transaction is balanced
        if not transaction.is_balanced():
            total_debits = transaction.get_total_debits()
            total_credits = transaction.get_total_credits()
            errors.append(f"Transaction is not balanced. Debits: {total_debits}, Credits: {total_credits}.")
        
        # Validate each journal entry and its items
        for entry in transaction.journal_entries.all():
            if not entry.items.exists():
                errors.append(f"Journal entry '{entry.description}' must have at least one item.")
            
            if not entry.is_balanced():
                total_debits = entry.get_total_debits()
                total_credits = entry.get_total_credits()
                errors.append(f"Journal entry '{entry.description}' is not balanced. Debits: {total_debits}, Credits: {total_credits}.")
            
            for item in entry.items.all():
                item_errors = self._validate_journal_item(item)
                errors.extend(item_errors)
        
        # Check account permissions
        account_errors = self._validate_account_permissions(transaction)
        errors.extend(account_errors)
        
        if errors:
            raise ValidationError("; ".join(errors))
        
        return True
    
    def _validate_journal_item(self, item: JournalItem) -> List[str]:
        """
        Validate a journal item.
        
        Args:
            item: The journal item to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if item.debit_amount == 0 and item.credit_amount == 0:
            errors.append(f"Journal item for account {item.account.account_number} must have either a debit or credit amount.")
        
        if item.debit_amount > 0 and item.credit_amount > 0:
            errors.append(f"Journal item for account {item.account.account_number} cannot have both a debit and a credit amount.")
        
        if not item.account.can_post_transactions():
            errors.append(f"Account {item.account.account_number} is not active or does not allow posting.")
        
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
                
                if not account.is_active:
                    errors.append(f"Account {account.account_number} is not active.")
                
                if not account.allow_posting:
                    errors.append(f"Account {account.account_number} does not allow posting.")
                
                if account.is_deleted:
                    errors.append(f"Account {account.account_number} has been deleted.")
        
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
                
                # Check if transaction is already posted
                if transaction.is_posted:
                    raise ValidationError("Transaction is already posted.")
                
                # Update transaction status and metadata
                transaction.status = Transaction.POSTED
                transaction.is_posted = True
                transaction.posted_date = timezone.now()
                transaction.posted_by = user
                transaction.save()
                
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
                title = "Post Transaction"
                
                # Send notification if needed
                self._send_posting_notification(transaction, user, title)
                
                logger.info(f"Transaction {transaction.transaction_number} posted by {user.username}")
                return True
                
        except ValidationError as e:
            logger.error(f"Failed to post transaction {transaction.transaction_number}: {e}")
            raise e
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
                account = item.account
                
                # Lock the account row to prevent race conditions
                with db_transaction.atomic():
                    account_for_update = Account.objects.select_for_update().get(pk=account.pk)
                    
                    if account_for_update.is_debit_balance():
                        account_for_update.current_balance += item.debit_amount - item.credit_amount
                    else: # Is a credit balance account
                        account_for_update.current_balance += item.credit_amount - item.debit_amount

                    account_for_update.save(update_fields=['current_balance', 'updated_at'])

    def _send_posting_notification(self, transaction: Transaction, user: User, title: str):
        """
        Send notification about posted transaction.
        """
        self.notification_utils.create_notification(
            title = title,
            user=user,
            message=f"Transaction {transaction.transaction_number} was successfully posted.",
            notification_type='transaction_posted'
        )
        logger.info(f"Notification sent for transaction {transaction.transaction_number} posted by {user.username}.")
    
    def void_transaction(self, transaction: Transaction, user: User, reason: str = "") -> Transaction:
        """
        Void a posted transaction by creating a reversal transaction.
        
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
                    raise ValidationError("Only posted transactions can be voided.")
                
                if transaction.status == Transaction.VOIDED:
                    raise ValidationError("Transaction is already voided.")
                
                # Create and post the reversal transaction
                reversal = transaction.reverse_transaction(user, reason)
                self.post_transaction(reversal, user)
                
                # Mark the original transaction as voided
                transaction.status = Transaction.VOIDED
                transaction.save(update_fields=['status'])
                
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
                
        except ValidationError as e:
            logger.error(f"Failed to void transaction {transaction.transaction_number}: {e}")
            raise e
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
        # The query to get all JournalItems for the account
        journal_items = JournalItem.objects.filter(
            account=account,
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
        
        # Get the unique transaction IDs from the filtered journal items
        transaction_ids = journal_items.values_list(
            'journal_entry__transaction_id', flat=True
        ).distinct()
        
        return Transaction.objects.filter(id__in=transaction_ids).order_by('-transaction_date')
    
    def get_transaction_types(self) -> List[TransactionType]:
        """
        Get all active transaction types.
        
        Returns:
            List of active transaction types
        """
        return list(TransactionType.objects.filter(is_active=True).order_by('name'))
    
    def create_recurring_transaction(self, template_data: Dict[str, Any], user: User) -> Transaction:
        """
        Create a recurring transaction based on a template.
        
        Args:
            template_data: Dictionary containing recurring transaction template
            user: The user creating the transaction
            
        Returns:
            Created Transaction object
        """
        # A simple implementation for now, assuming template_data is the same
        # as the regular transaction data format.
        return self.create_transaction(template_data, user)
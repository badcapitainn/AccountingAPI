"""
Django signals for the accounting app.

This module defines signals that are triggered when certain events
occur in the accounting system, such as updating account balances
when transactions are posted.
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import logging

from .models import Transaction, JournalItem, Account, Report
from core.utils import AuditUtils, NotificationUtils

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def transaction_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Transaction post_save events.
    
    This signal is triggered when a transaction is created or updated.
    It performs various actions such as logging, notifications, and
    balance updates.
    """
    audit_utils = AuditUtils()
    notification_utils = NotificationUtils()
    
    try:
        if created:
            # Log the creation
            audit_utils.log_activity(
                user=instance.posted_by if hasattr(instance, 'posted_by') and instance.posted_by else None,
                action='CREATE',
                model_name='Transaction',
                object_id=str(instance.id),
                object_repr=str(instance),
                changes={'transaction_number': instance.transaction_number}
            )
            
            logger.info(f"Transaction {instance.transaction_number} created")
            
        else:
            # Log the update
            audit_utils.log_activity(
                user=instance.posted_by if hasattr(instance, 'posted_by') and instance.posted_by else None,
                action='UPDATE',
                model_name='Transaction',
                object_id=str(instance.id),
                object_repr=str(instance),
                changes={'status': instance.status}
            )
            
            logger.info(f"Transaction {instance.transaction_number} updated")
        
        # Send notifications for important events
        if instance.is_posted and instance.status == Transaction.POSTED:
            notification_utils.create_notification(
                user=instance.posted_by,
                notification_type='SYSTEM',
                title='Transaction Posted',
                message=f'Transaction {instance.transaction_number} has been posted successfully.',
                priority='MEDIUM'
            )
        
        elif instance.status == Transaction.VOIDED:
            notification_utils.create_notification(
                user=instance.posted_by,
                notification_type='ALERT',
                title='Transaction Voided',
                message=f'Transaction {instance.transaction_number} has been voided.',
                priority='HIGH'
            )
    
    except Exception as e:
        logger.error(f"Error in transaction_post_save signal: {e}")


@receiver(post_save, sender=JournalItem)
def journal_item_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for JournalItem post_save events.
    
    This signal is triggered when a journal item is created or updated.
    It updates account balances and performs related actions.
    """
    try:
        if created:
            # Log the creation
            audit_utils = AuditUtils()
            audit_utils.log_activity(
                user=None,  # Could be passed from the transaction
                action='CREATE',
                model_name='JournalItem',
                object_id=str(instance.id),
                object_repr=f"{instance.account.account_number} - {instance.get_amount_display()}",
                changes={
                    'account': instance.account.account_number,
                    'debit_amount': str(instance.debit_amount),
                    'credit_amount': str(instance.credit_amount)
                }
            )
            
            logger.info(f"Journal item created for account {instance.account.account_number}")
        
        # Update account balance if the transaction is posted
        if instance.journal_entry.transaction.is_posted:
            instance.account.update_balance()
    
    except Exception as e:
        logger.error(f"Error in journal_item_post_save signal: {e}")


@receiver(post_delete, sender=JournalItem)
def journal_item_post_delete(sender, instance, **kwargs):
    """
    Signal handler for JournalItem post_delete events.
    
    This signal is triggered when a journal item is deleted.
    It updates account balances and logs the deletion.
    """
    try:
        # Log the deletion
        audit_utils = AuditUtils()
        audit_utils.log_activity(
            user=None,
            action='DELETE',
            model_name='JournalItem',
            object_id=str(instance.id),
            object_repr=f"{instance.account.account_number} - {instance.get_amount_display()}",
            changes={
                'account': instance.account.account_number,
                'debit_amount': str(instance.debit_amount),
                'credit_amount': str(instance.credit_amount)
            }
        )
        
        logger.info(f"Journal item deleted for account {instance.account.account_number}")
        
        # Update account balance if the transaction was posted
        if instance.journal_entry.transaction.is_posted:
            instance.account.update_balance()
    
    except Exception as e:
        logger.error(f"Error in journal_item_post_delete signal: {e}")


@receiver(post_save, sender=Account)
def account_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Account post_save events.
    
    This signal is triggered when an account is created or updated.
    It performs validation and logging.
    """
    try:
        audit_utils = AuditUtils()
        
        if created:
            # Log the creation
            audit_utils.log_activity(
                user=None,
                action='CREATE',
                model_name='Account',
                object_id=str(instance.id),
                object_repr=str(instance),
                changes={
                    'account_number': instance.account_number,
                    'name': instance.name,
                    'account_type': instance.account_type.name
                }
            )
            
            logger.info(f"Account {instance.account_number} created")
            
        else:
            # Log the update
            audit_utils.log_activity(
                user=None,
                action='UPDATE',
                model_name='Account',
                object_id=str(instance.id),
                object_repr=str(instance),
                changes={
                    'account_number': instance.account_number,
                    'name': instance.name,
                    'is_active': instance.is_active
                }
            )
            
            logger.info(f"Account {instance.account_number} updated")
    
    except Exception as e:
        logger.error(f"Error in account_post_save signal: {e}")


@receiver(post_save, sender=Report)
def report_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Report post_save events.
    
    This signal is triggered when a report is created or updated.
    It handles notifications and logging.
    """
    try:
        audit_utils = AuditUtils()
        notification_utils = NotificationUtils()
        
        if created:
            # Log the creation
            audit_utils.log_activity(
                user=instance.generated_by,
                action='CREATE',
                model_name='Report',
                object_id=str(instance.id),
                object_repr=str(instance),
                changes={'report_number': instance.report_number}
            )
            
            logger.info(f"Report {instance.report_number} created")
            
        else:
            # Log status changes
            if instance.status == Report.COMPLETED:
                audit_utils.log_activity(
                    user=instance.generated_by,
                    action='UPDATE',
                    model_name='Report',
                    object_id=str(instance.id),
                    object_repr=str(instance),
                    changes={'status': 'COMPLETED'}
                )
                
                # Send notification for completed report
                if instance.generated_by:
                    notification_utils.create_notification(
                        user=instance.generated_by,
                        notification_type='REPORT',
                        title='Report Generated',
                        message=f'Report {instance.report_number} has been generated successfully.',
                        priority='MEDIUM'
                    )
                
                logger.info(f"Report {instance.report_number} completed")
            
            elif instance.status == Report.FAILED:
                audit_utils.log_activity(
                    user=instance.generated_by,
                    action='UPDATE',
                    model_name='Report',
                    object_id=str(instance.id),
                    object_repr=str(instance),
                    changes={'status': 'FAILED', 'error': instance.error_message}
                )
                
                # Send notification for failed report
                if instance.generated_by:
                    notification_utils.create_notification(
                        user=instance.generated_by,
                        notification_type='ALERT',
                        title='Report Generation Failed',
                        message=f'Report {instance.report_number} generation failed: {instance.error_message}',
                        priority='HIGH'
                    )
                
                logger.error(f"Report {instance.report_number} failed: {instance.error_message}")
    
    except Exception as e:
        logger.error(f"Error in report_post_save signal: {e}")


@receiver(pre_save, sender=Transaction)
def transaction_pre_save(sender, instance, **kwargs):
    """
    Signal handler for Transaction pre_save events.
    
    This signal is triggered before a transaction is saved.
    It performs validation and business logic checks.
    """
    try:
        # Validate transaction before saving
        if instance.pk:  # Only for updates
            old_instance = Transaction.objects.get(pk=instance.pk)
            
            # Check if status is being changed from POSTED to something else
            if old_instance.status == Transaction.POSTED and instance.status != Transaction.POSTED:
                if instance.status != Transaction.VOIDED:
                    raise ValidationError("Posted transactions can only be voided, not changed to other statuses.")
        
        # Validate that transaction is balanced if it has journal entries
        if instance.journal_entries.exists():
            if not instance.is_balanced():
                logger.warning(f"Transaction {instance.transaction_number} is not balanced")
    
    except Exception as e:
        logger.error(f"Error in transaction_pre_save signal: {e}")
        raise


@receiver(pre_save, sender=Account)
def account_pre_save(sender, instance, **kwargs):
    """
    Signal handler for Account pre_save events.
    
    This signal is triggered before an account is saved.
    It performs validation and business logic checks.
    """
    try:
        # Validate account number uniqueness
        if Account.objects.filter(account_number=instance.account_number).exclude(pk=instance.pk).exists():
            raise ValidationError(f"Account number {instance.account_number} already exists.")
        
        # Validate account type and balance type consistency
        if instance.account_type and instance.balance_type:
            if instance.account_type.normal_balance != instance.balance_type:
                raise ValidationError("Account balance type must match account type normal balance.")
    
    except Exception as e:
        logger.error(f"Error in account_pre_save signal: {e}")
        raise


# Custom signal for when account balances are updated
from django.dispatch import Signal

account_balance_updated = Signal(providing_args=['account', 'old_balance', 'new_balance'])


@receiver(account_balance_updated)
def handle_account_balance_update(sender, account, old_balance, new_balance, **kwargs):
    """
    Signal handler for account balance updates.
    
    This signal is triggered when an account balance is updated.
    It can be used for notifications, logging, or other business logic.
    """
    try:
        # Log significant balance changes
        balance_change = abs(new_balance - old_balance)
        if balance_change > 10000:  # Threshold for significant changes
            audit_utils = AuditUtils()
            audit_utils.log_activity(
                user=None,
                action='UPDATE',
                model_name='Account',
                object_id=str(account.id),
                object_repr=str(account),
                changes={
                    'old_balance': str(old_balance),
                    'new_balance': str(new_balance),
                    'change': str(balance_change)
                }
            )
            
            logger.info(f"Significant balance change for account {account.account_number}: {old_balance} -> {new_balance}")
    
    except Exception as e:
        logger.error(f"Error in handle_account_balance_update signal: {e}")


# Custom signal for when transactions are posted
transaction_posted = Signal(providing_args=['transaction', 'user'])


@receiver(transaction_posted)
def handle_transaction_posted(sender, transaction, user, **kwargs):
    """
    Signal handler for when transactions are posted.
    
    This signal is triggered when a transaction is posted to the general ledger.
    It can be used for notifications, reporting, or other business logic.
    """
    try:
        # Send notifications to relevant users
        notification_utils = NotificationUtils()
        
        # Notify users with specific permissions
        from django.contrib.auth.models import Group
        accountants = Group.objects.filter(name='accountant').first()
        if accountants:
            for accountant in accountants.user_set.all():
                notification_utils.create_notification(
                    user=accountant,
                    notification_type='SYSTEM',
                    title='Transaction Posted',
                    message=f'Transaction {transaction.transaction_number} has been posted by {user.username}.',
                    priority='MEDIUM'
                )
        
        logger.info(f"Transaction {transaction.transaction_number} posted by {user.username}")
    
    except Exception as e:
        logger.error(f"Error in handle_transaction_posted signal: {e}")


# Custom signal for when reports are generated
report_generated = Signal(providing_args=['report', 'user'])


@receiver(report_generated)
def handle_report_generated(sender, report, user, **kwargs):
    """
    Signal handler for when reports are generated.
    
    This signal is triggered when a report is successfully generated.
    It can be used for notifications, archiving, or other business logic.
    """
    try:
        # Send notification to the user who generated the report
        notification_utils = NotificationUtils()
        notification_utils.create_notification(
            user=user,
            notification_type='REPORT',
            title='Report Ready',
            message=f'Report {report.report_number} is ready for download.',
            priority='MEDIUM'
        )
        
        logger.info(f"Report {report.report_number} generated by {user.username}")
    
    except Exception as e:
        logger.error(f"Error in handle_report_generated signal: {e}") 
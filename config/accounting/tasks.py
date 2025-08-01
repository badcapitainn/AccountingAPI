"""
Background tasks for the accounting system.

This module contains Celery tasks for long-running processes such as
generating reports, syncing with banks, and other background operations.
"""

import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json

from .models import Report, ReportSchedule, Transaction, Account
from .services import ReportGenerator, TransactionService
from core.utils import NotificationUtils

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_report_task(self, report_id, user_id=None):
    """
    Background task to generate a financial report.
    
    Args:
        report_id: ID of the report to generate
        user_id: ID of the user requesting the report
    """
    try:
        # Get the report
        report = Report.objects.get(id=report_id)
        user = None
        if user_id:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
        
        # Start generation
        report.start_generation(user)
        
        # Get the report generator
        report_generator = ReportGenerator()
        
        # Generate report based on template type
        if report.template.report_type == ReportTemplate.BALANCE_SHEET:
            report_data = report_generator.generate_balance_sheet(
                as_of_date=report.parameters.get('as_of_date'),
                include_comparative=report.parameters.get('include_comparative', False)
            )
        
        elif report.template.report_type == ReportTemplate.INCOME_STATEMENT:
            report_data = report_generator.generate_income_statement(
                start_date=report.parameters.get('start_date'),
                end_date=report.parameters.get('end_date'),
                include_comparative=report.parameters.get('include_comparative', False)
            )
        
        elif report.template.report_type == ReportTemplate.TRIAL_BALANCE:
            report_data = report_generator.generate_trial_balance(
                as_of_date=report.parameters.get('as_of_date')
            )
        
        elif report.template.report_type == ReportTemplate.GENERAL_LEDGER:
            account_id = report.parameters.get('account_id')
            if account_id:
                account = Account.objects.get(id=account_id)
                report_data = report_generator.generate_general_ledger(
                    account=account,
                    start_date=report.parameters.get('start_date'),
                    end_date=report.parameters.get('end_date')
                )
            else:
                raise ValueError("Account ID is required for General Ledger reports")
        
        elif report.template.report_type == ReportTemplate.CASH_FLOW:
            report_data = report_generator.generate_cash_flow_statement(
                start_date=report.parameters.get('start_date'),
                end_date=report.parameters.get('end_date')
            )
        
        else:
            raise ValueError(f"Unsupported report type: {report.template.report_type}")
        
        # Generate file based on format
        file_path = None
        file_size = 0
        
        if report.format == Report.PDF:
            file_path, file_size = _generate_pdf_report(report_data, report)
        elif report.format == Report.EXCEL:
            file_path, file_size = _generate_excel_report(report_data, report)
        elif report.format == Report.CSV:
            file_path, file_size = _generate_csv_report(report_data, report)
        elif report.format == Report.JSON:
            file_path, file_size = _generate_json_report(report_data, report)
        
        # Complete the report
        report.complete_generation(report_data, file_path, file_size)
        
        # Send notification
        if user:
            notification_utils = NotificationUtils()
            notification_utils.create_notification(
                user=user,
                notification_type='REPORT',
                title='Report Generated',
                message=f'Report {report.report_number} has been generated successfully.',
                priority='MEDIUM'
            )
        
        logger.info(f"Report {report.report_number} generated successfully")
        
    except Exception as e:
        logger.error(f"Failed to generate report {report_id}: {e}")
        
        # Mark report as failed
        try:
            report = Report.objects.get(id=report_id)
            report.fail_generation(str(e))
        except:
            pass
        
        # Send notification about failure
        if user:
            notification_utils = NotificationUtils()
            notification_utils.create_notification(
                user=user,
                notification_type='ALERT',
                title='Report Generation Failed',
                message=f'Report generation failed: {str(e)}',
                priority='HIGH'
            )
        
        raise


@shared_task
def process_scheduled_reports():
    """
    Background task to process scheduled reports.
    
    This task checks for reports that are scheduled to be generated
    and creates the appropriate report generation tasks.
    """
    try:
        schedules = ReportSchedule.objects.filter(is_active=True)
        
        for schedule in schedules:
            if schedule.should_run():
                # Create a report based on the schedule
                report = Report.objects.create(
                    name=schedule.name,
                    description=f"Automatically generated report based on schedule {schedule.name}",
                    template=schedule.template,
                    parameters=schedule.parameters,
                    filters=schedule.filters,
                    format=schedule.format,
                    generated_by=schedule.created_by
                )
                
                # Start the report generation task
                generate_report_task.delay(str(report.id), schedule.created_by.id)
                
                # Update the next run date
                schedule.next_run = schedule.calculate_next_run()
                schedule.save()
                
                logger.info(f"Scheduled report {schedule.name} triggered")
        
        logger.info("Scheduled reports processing completed")
        
    except Exception as e:
        logger.error(f"Failed to process scheduled reports: {e}")
        raise


@shared_task
def sync_bank_transactions():
    """
    Background task to sync bank transactions.
    
    This task would integrate with bank APIs to download and sync
    bank transactions with the accounting system.
    """
    try:
        # Get bank accounts
        bank_accounts = Account.objects.filter(is_bank_account=True, is_active=True)
        
        for account in bank_accounts:
            try:
                # This would contain the actual bank API integration logic
                # For now, it's just a placeholder
                logger.info(f"Syncing transactions for bank account {account.account_number}")
                
                # Example bank sync logic:
                # 1. Connect to bank API
                # 2. Download transactions
                # 3. Match with existing transactions
                # 4. Create new transactions for unmatched items
                # 5. Update reconciliation status
                
                # Placeholder for actual implementation
                _mock_bank_sync(account)
                
            except Exception as e:
                logger.error(f"Failed to sync bank account {account.account_number}: {e}")
        
        logger.info("Bank transaction sync completed")
        
    except Exception as e:
        logger.error(f"Failed to sync bank transactions: {e}")
        raise


@shared_task
def reconcile_accounts():
    """
    Background task to reconcile accounts.
    
    This task performs automatic reconciliation of accounts that
    require reconciliation.
    """
    try:
        reconcilable_accounts = Account.objects.filter(
            is_reconcilable=True,
            is_active=True
        )
        
        for account in reconcilable_accounts:
            try:
                logger.info(f"Reconciling account {account.account_number}")
                
                # This would contain the actual reconciliation logic
                # For now, it's just a placeholder
                _mock_account_reconciliation(account)
                
            except Exception as e:
                logger.error(f"Failed to reconcile account {account.account_number}: {e}")
        
        logger.info("Account reconciliation completed")
        
    except Exception as e:
        logger.error(f"Failed to reconcile accounts: {e}")
        raise


@shared_task
def cleanup_old_reports():
    """
    Background task to cleanup old reports.
    
    This task removes old reports that are no longer needed
    to free up storage space.
    """
    try:
        from datetime import timedelta
        
        # Delete reports older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        old_reports = Report.objects.filter(
            created_at__lt=cutoff_date,
            status__in=[Report.COMPLETED, Report.FAILED]
        )
        
        count = old_reports.count()
        old_reports.delete()
        
        logger.info(f"Cleaned up {count} old reports")
        
    except Exception as e:
        logger.error(f"Failed to cleanup old reports: {e}")
        raise


@shared_task
def send_report_notifications():
    """
    Background task to send report notifications.
    
    This task sends email notifications for completed reports.
    """
    try:
        # Get completed reports that haven't been notified
        completed_reports = Report.objects.filter(
            status=Report.COMPLETED,
            generated_by__isnull=False
        )
        
        for report in completed_reports:
            try:
                # Send email notification
                send_mail(
                    subject=f'Report Ready: {report.name}',
                    message=f'Your report {report.report_number} is ready for download.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[report.generated_by.email],
                    fail_silently=False,
                )
                
                logger.info(f"Notification sent for report {report.report_number}")
                
            except Exception as e:
                logger.error(f"Failed to send notification for report {report.report_number}: {e}")
        
        logger.info("Report notifications sent")
        
    except Exception as e:
        logger.error(f"Failed to send report notifications: {e}")
        raise


@shared_task
def validate_transactions():
    """
    Background task to validate transactions.
    
    This task checks for transactions that may have validation issues
    and flags them for review.
    """
    try:
        # Get transactions that need validation
        transactions = Transaction.objects.filter(
            is_posted=True,
            is_deleted=False
        )
        
        validation_issues = []
        
        for transaction in transactions:
            try:
                # Check if transaction is balanced
                if not transaction.is_balanced():
                    validation_issues.append({
                        'transaction': transaction,
                        'issue': 'Transaction is not balanced',
                        'severity': 'HIGH'
                    })
                
                # Check for large transactions
                if transaction.amount > 100000:  # Threshold for large transactions
                    validation_issues.append({
                        'transaction': transaction,
                        'issue': 'Large transaction amount',
                        'severity': 'MEDIUM'
                    })
                
                # Check for unusual patterns
                if _check_unusual_patterns(transaction):
                    validation_issues.append({
                        'transaction': transaction,
                        'issue': 'Unusual transaction pattern detected',
                        'severity': 'MEDIUM'
                    })
                
            except Exception as e:
                logger.error(f"Failed to validate transaction {transaction.transaction_number}: {e}")
        
        # Log validation issues
        if validation_issues:
            logger.warning(f"Found {len(validation_issues)} validation issues")
            for issue in validation_issues:
                logger.warning(f"Transaction {issue['transaction'].transaction_number}: {issue['issue']}")
        
        logger.info("Transaction validation completed")
        
    except Exception as e:
        logger.error(f"Failed to validate transactions: {e}")
        raise


def _generate_pdf_report(report_data, report):
    """
    Generate a PDF report file.
    
    Args:
        report_data: The report data
        report: The report object
        
    Returns:
        Tuple of (file_path, file_size)
    """
    # This would contain the actual PDF generation logic
    # For now, it's just a placeholder
    import os
    
    filename = f"report_{report.report_number}.pdf"
    file_path = os.path.join('reports', filename)
    
    # Create the reports directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Placeholder for PDF generation
    with open(file_path, 'w') as f:
        f.write("PDF content would be generated here")
    
    file_size = os.path.getsize(file_path)
    return file_path, file_size


def _generate_excel_report(report_data, report):
    """
    Generate an Excel report file.
    
    Args:
        report_data: The report data
        report: The report object
        
    Returns:
        Tuple of (file_path, file_size)
    """
    # This would contain the actual Excel generation logic
    # For now, it's just a placeholder
    import os
    
    filename = f"report_{report.report_number}.xlsx"
    file_path = os.path.join('reports', filename)
    
    # Create the reports directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Placeholder for Excel generation
    with open(file_path, 'w') as f:
        f.write("Excel content would be generated here")
    
    file_size = os.path.getsize(file_path)
    return file_path, file_size


def _generate_csv_report(report_data, report):
    """
    Generate a CSV report file.
    
    Args:
        report_data: The report data
        report: The report object
        
    Returns:
        Tuple of (file_path, file_size)
    """
    # This would contain the actual CSV generation logic
    # For now, it's just a placeholder
    import os
    
    filename = f"report_{report.report_number}.csv"
    file_path = os.path.join('reports', filename)
    
    # Create the reports directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Placeholder for CSV generation
    with open(file_path, 'w') as f:
        f.write("CSV content would be generated here")
    
    file_size = os.path.getsize(file_path)
    return file_path, file_size


def _generate_json_report(report_data, report):
    """
    Generate a JSON report file.
    
    Args:
        report_data: The report data
        report: The report object
        
    Returns:
        Tuple of (file_path, file_size)
    """
    import os
    
    filename = f"report_{report.report_number}.json"
    file_path = os.path.join('reports', filename)
    
    # Create the reports directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write JSON data
    with open(file_path, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    file_size = os.path.getsize(file_path)
    return file_path, file_size


def _mock_bank_sync(account):
    """
    Mock bank sync function.
    
    Args:
        account: The bank account to sync
    """
    # This is a placeholder for actual bank API integration
    logger.info(f"Mock bank sync for account {account.account_number}")


def _mock_account_reconciliation(account):
    """
    Mock account reconciliation function.
    
    Args:
        account: The account to reconcile
    """
    # This is a placeholder for actual reconciliation logic
    logger.info(f"Mock reconciliation for account {account.account_number}")


def _check_unusual_patterns(transaction):
    """
    Check for unusual transaction patterns.
    
    Args:
        transaction: The transaction to check
        
    Returns:
        True if unusual patterns are detected, False otherwise
    """
    # This is a placeholder for actual pattern detection logic
    # In a real implementation, this would use machine learning or
    # rule-based systems to detect unusual patterns
    
    # Example checks:
    # - Transactions outside normal business hours
    # - Transactions with unusual amounts
    # - Transactions with unusual account combinations
    # - Transactions from unusual locations
    
    return False 
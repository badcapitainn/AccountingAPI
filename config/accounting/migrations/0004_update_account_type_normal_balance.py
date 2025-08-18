"""
Update AccountType normal_balance to use DEBIT/CREDIT instead of account type codes.
"""

from django.db import migrations


def update_normal_balance_values(apps, schema_editor):
    """Update existing AccountType records to use proper balance values."""
    AccountType = apps.get_model('accounting', 'AccountType')
    
    # Update existing records based on account type
    AccountType.objects.filter(code='ASSET').update(normal_balance='DEBIT')
    AccountType.objects.filter(code='LIABILITY').update(normal_balance='CREDIT')
    AccountType.objects.filter(code='EQUITY').update(normal_balance='CREDIT')
    AccountType.objects.filter(code='REVENUE').update(normal_balance='CREDIT')
    AccountType.objects.filter(code='EXPENSE').update(normal_balance='DEBIT')


def reverse_normal_balance_values(apps, schema_editor):
    """Reverse the migration by setting normal_balance back to account type codes."""
    AccountType = apps.get_model('accounting', 'AccountType')
    
    # Reverse the changes
    AccountType.objects.filter(code='ASSET').update(normal_balance='ASSET')
    AccountType.objects.filter(code='LIABILITY').update(normal_balance='LIABILITY')
    AccountType.objects.filter(code='EQUITY').update(normal_balance='EQUITY')
    AccountType.objects.filter(code='REVENUE').update(normal_balance='REVENUE')
    AccountType.objects.filter(code='EXPENSE').update(normal_balance='EXPENSE')


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0003_transaction_is_reversal_and_more'),
    ]

    operations = [
        migrations.RunPython(
            update_normal_balance_values,
            reverse_normal_balance_values
        ),
    ]

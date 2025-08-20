#!/usr/bin/env python3
"""
Setup script for Accounting API testing environment.

This script creates sample data for testing all API endpoints.
Run this script after setting up your Django environment and before testing with Postman.
"""

import os
import sys
import django
from datetime import date, datetime
from decimal import Decimal

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Try to determine the correct settings module
if os.path.exists(os.path.join(current_dir, 'config', 'settings.py')):
    # We're in the config directory, settings is at config.settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
elif os.path.exists(os.path.join(current_dir, '..', 'config', 'config', 'settings.py')):
    # We're in the project root, settings is at config.config.settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.config.settings')
    sys.path.append(os.path.join(current_dir, '..'))
else:
    print("❌ Could not find Django settings file. Please run this script from the project root or config directory.")
    sys.exit(1)

django.setup()

from django.contrib.auth import get_user_model
from accounting.models import (
    AccountType, AccountCategory, Account, TransactionType, 
    Transaction, JournalEntry, ReportTemplate
)

User = get_user_model()

def create_superuser():
    """Create a superuser for testing."""
    try:
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print(f"✅ Superuser created: {user.username}")
        return user
    except Exception as e:
        print(f"⚠️  Superuser creation failed: {e}")
        # Try to get existing user
        try:
            user = User.objects.get(username='admin')
            print(f"✅ Using existing superuser: {user.username}")
            return user
        except User.DoesNotExist:
            print("❌ No superuser available. Please create one manually.")
            return None

def create_account_types():
    """Create basic account types."""
    account_types = [
        {
            'name': 'Asset',
            'code': 'ASSET',
            'description': 'Assets are economic resources owned by the business',
            'normal_balance': 'DEBIT'
        },
        {
            'name': 'Liability',
            'code': 'LIABILITY',
            'description': 'Liabilities are obligations of the business',
            'normal_balance': 'CREDIT'
        },
        {
            'name': 'Equity',
            'code': 'EQUITY',
            'description': "Owner's equity in the business",
            'normal_balance': 'CREDIT'
        },
        {
            'name': 'Revenue',
            'code': 'REVENUE',
            'description': 'Revenue accounts track income from business operations',
            'normal_balance': 'CREDIT'
        },
        {
            'name': 'Expense',
            'code': 'EXPENSE',
            'description': 'Expense accounts track business costs',
            'normal_balance': 'DEBIT'
        }
    ]
    
    created_types = {}
    for type_data in account_types:
        try:
            account_type, created = AccountType.objects.get_or_create(
                code=type_data['code'],
                defaults=type_data
            )
            if created:
                print(f"✅ Account type created: {account_type.name}")
            else:
                print(f"ℹ️  Account type exists: {account_type.name}")
            created_types[type_data['code']] = account_type
        except Exception as e:
            print(f"❌ Failed to create account type {type_data['code']}: {e}")
    
    return created_types

def create_account_categories(account_types):
    """Create account categories."""
    categories = [
        {
            'name': 'Current Assets',
            'code': 'CURRENT_ASSETS',
            'description': 'Assets expected to be converted to cash within one year',
            'account_type': account_types['ASSET'],
            'sort_order': 1
        },
        {
            'name': 'Fixed Assets',
            'code': 'FIXED_ASSETS',
            'description': 'Long-term assets like buildings and equipment',
            'account_type': account_types['ASSET'],
            'sort_order': 2
        },
        {
            'name': 'Current Liabilities',
            'code': 'CURRENT_LIABILITIES',
            'description': 'Obligations due within one year',
            'account_type': account_types['LIABILITY'],
            'sort_order': 1
        },
        {
            'name': 'Long-term Liabilities',
            'code': 'LONG_TERM_LIABILITIES',
            'description': 'Obligations due beyond one year',
            'account_type': account_types['LIABILITY'],
            'sort_order': 2
        },
        {
            'name': 'Owner Equity',
            'code': 'OWNER_EQUITY',
            'description': "Owner's investment and retained earnings",
            'account_type': account_types['EQUITY'],
            'sort_order': 1
        },
        {
            'name': 'Operating Revenue',
            'code': 'OPERATING_REVENUE',
            'description': 'Revenue from primary business operations',
            'account_type': account_types['REVENUE'],
            'sort_order': 1
        },
        {
            'name': 'Operating Expenses',
            'code': 'OPERATING_EXPENSES',
            'description': 'Expenses from primary business operations',
            'account_type': account_types['EXPENSE'],
            'sort_order': 1
        }
    ]
    
    created_categories = {}
    for category_data in categories:
        try:
            category, created = AccountCategory.objects.get_or_create(
                code=category_data['code'],
                defaults=category_data
            )
            if created:
                print(f"✅ Account category created: {category.name}")
            else:
                print(f"ℹ️  Account category exists: {category.name}")
            created_categories[category_data['code']] = category
        except Exception as e:
            print(f"❌ Failed to create category {category_data['code']}: {e}")
    
    return created_categories

def create_accounts(account_types, categories):
    """Create sample accounts."""
    accounts = [
        {
            'account_number': '1000',
            'name': 'Cash',
            'description': 'Main cash account',
            'account_type': account_types['ASSET'],
            'category': categories['CURRENT_ASSETS'],
            'balance_type': 'DEBIT',
            'is_bank_account': False,
            'is_cash_account': True,
            'is_reconcilable': True,
            'sort_order': 1
        },
        {
            'account_number': '1100',
            'name': 'Accounts Receivable',
            'description': 'Amounts owed by customers',
            'account_type': account_types['ASSET'],
            'category': categories['CURRENT_ASSETS'],
            'balance_type': 'DEBIT',
            'is_bank_account': False,
            'is_cash_account': False,
            'is_reconcilable': True,
            'sort_order': 2
        },
        {
            'account_number': '1500',
            'name': 'Equipment',
            'description': 'Office equipment and machinery',
            'account_type': account_types['ASSET'],
            'category': categories['FIXED_ASSETS'],
            'balance_type': 'DEBIT',
            'is_bank_account': False,
            'is_cash_account': False,
            'is_reconcilable': False,
            'sort_order': 3
        },
        {
            'account_number': '2000',
            'name': 'Accounts Payable',
            'description': 'Amounts owed to suppliers',
            'account_type': account_types['LIABILITY'],
            'category': categories['CURRENT_LIABILITIES'],
            'balance_type': 'CREDIT',
            'is_bank_account': False,
            'is_cash_account': False,
            'is_reconcilable': True,
            'sort_order': 1
        },
        {
            'account_number': '3000',
            'name': "Owner's Equity",
            'description': "Owner's investment in the business",
            'account_type': account_types['EQUITY'],
            'category': categories['OWNER_EQUITY'],
            'balance_type': 'CREDIT',
            'is_bank_account': False,
            'is_cash_account': False,
            'is_reconcilable': False,
            'sort_order': 1
        },
        {
            'account_number': '4000',
            'name': 'Sales Revenue',
            'description': 'Revenue from product sales',
            'account_type': account_types['REVENUE'],
            'category': categories['OPERATING_REVENUE'],
            'balance_type': 'CREDIT',
            'is_bank_account': False,
            'is_cash_account': False,
            'is_reconcilable': False,
            'sort_order': 1
        },
        {
            'account_number': '5000',
            'name': 'Cost of Goods Sold',
            'description': 'Direct costs of producing goods',
            'account_type': account_types['EXPENSE'],
            'category': categories['OPERATING_EXPENSES'],
            'balance_type': 'DEBIT',
            'is_bank_account': False,
            'is_cash_account': False,
            'is_reconcilable': False,
            'sort_order': 1
        }
    ]
    
    created_accounts = {}
    for account_data in accounts:
        try:
            account, created = Account.objects.get_or_create(
                account_number=account_data['account_number'],
                defaults=account_data
            )
            if created:
                print(f"✅ Account created: {account.name} ({account.account_number})")
            else:
                print(f"ℹ️  Account exists: {account.name} ({account.account_number})")
            created_accounts[account_data['account_number']] = account
        except Exception as e:
            print(f"❌ Failed to create account {account_data['account_number']}: {e}")
    
    return created_accounts

def create_transaction_types():
    """Create transaction types."""
    transaction_types = [
        {
            'name': 'Sale',
            'code': 'SALE',
            'description': 'Sales transactions'
        },
        {
            'name': 'Purchase',
            'code': 'PURCHASE',
            'description': 'Purchase transactions'
        },
        {
            'name': 'Payment',
            'code': 'PAYMENT',
            'description': 'Payment transactions'
        },
        {
            'name': 'Receipt',
            'code': 'RECEIPT',
            'description': 'Receipt transactions'
        },
        {
            'name': 'Adjustment',
            'code': 'ADJUSTMENT',
            'description': 'Account adjustments'
        }
    ]
    
    created_types = {}
    for type_data in transaction_types:
        try:
            transaction_type, created = TransactionType.objects.get_or_create(
                code=type_data['code'],
                defaults=type_data
            )
            if created:
                print(f"✅ Transaction type created: {transaction_type.name}")
            else:
                print(f"ℹ️  Transaction type exists: {transaction_type.name}")
            created_types[type_data['code']] = transaction_type
        except Exception as e:
            print(f"❌ Failed to create transaction type {type_data['code']}: {e}")
    
    return created_types

def create_sample_transactions(transaction_types, accounts, user):
    """Create sample transactions."""
    # Initial investment transaction
    try:
        init_transaction = Transaction.objects.create(
            transaction_number='TXN-001',
            reference_number='INIT-001',
            description='Initial capital investment',
            transaction_date=date(2024, 1, 1),
            amount=Decimal('50000.00'),
            transaction_type=transaction_types['ADJUSTMENT'],
            status='PENDING',
            is_posted=False
        )
        print(f"✅ Initial transaction created: {init_transaction.transaction_number}")
        
        # Create journal entry for initial transaction
        JournalEntry.objects.create(
            transaction=init_transaction,
            description='Debit cash, credit owner equity',
            amount=Decimal('50000.00'),
            sort_order=1
        )
        print(f"✅ Journal entry created for initial transaction")
        
    except Exception as e:
        print(f"❌ Failed to create initial transaction: {e}")
    
    # Sales transaction
    try:
        sale_transaction = Transaction.objects.create(
            transaction_number='TXN-002',
            reference_number='SALE-001',
            description='Cash sale of products',
            transaction_date=date(2024, 1, 15),
            amount=Decimal('2500.00'),
            transaction_type=transaction_types['SALE'],
            status='PENDING',
            is_posted=False
        )
        print(f"✅ Sales transaction created: {sale_transaction.transaction_number}")
        
        # Create journal entries for sales transaction
        JournalEntry.objects.create(
            transaction=sale_transaction,
            description='Debit cash',
            amount=Decimal('2500.00'),
            sort_order=1
        )
        JournalEntry.objects.create(
            transaction=sale_transaction,
            description='Credit sales revenue',
            amount=Decimal('2500.00'),
            sort_order=2
        )
        print(f"✅ Journal entries created for sales transaction")
        
    except Exception as e:
        print(f"❌ Failed to create sales transaction: {e}")
    
    # Purchase transaction
    try:
        purchase_transaction = Transaction.objects.create(
            transaction_number='TXN-003',
            reference_number='PURCH-001',
            description='Purchase of inventory on credit',
            transaction_date=date(2024, 1, 20),
            amount=Decimal('1500.00'),
            transaction_type=transaction_types['PURCHASE'],
            status='PENDING',
            is_posted=False
        )
        print(f"✅ Purchase transaction created: {purchase_transaction.transaction_number}")
        
        # Create journal entries for purchase transaction
        JournalEntry.objects.create(
            transaction=purchase_transaction,
            description='Debit inventory',
            amount=Decimal('1500.00'),
            sort_order=1
        )
        JournalEntry.objects.create(
            transaction=purchase_transaction,
            description='Credit accounts payable',
            amount=Decimal('1500.00'),
            sort_order=2
        )
        print(f"✅ Journal entries created for purchase transaction")
        
    except Exception as e:
        print(f"❌ Failed to create purchase transaction: {e}")

def create_report_templates():
    """Create sample report templates."""
    templates = [
        {
            'name': 'Monthly Balance Sheet',
            'description': 'Standard monthly balance sheet template',
            'report_type': 'BALANCE_SHEET',
            'template_config': {
                'sections': ['assets', 'liabilities', 'equity']
            },
            'sort_order': 1
        },
        {
            'name': 'Monthly Income Statement',
            'description': 'Standard monthly income statement template',
            'report_type': 'INCOME_STATEMENT',
            'template_config': {
                'sections': ['revenue', 'expenses', 'net_income']
            },
            'sort_order': 2
        },
        {
            'name': 'Trial Balance',
            'description': 'Trial balance report template',
            'report_type': 'TRIAL_BALANCE',
            'template_config': {
                'sections': ['debits', 'credits']
            },
            'sort_order': 3
        }
    ]
    
    for template_data in templates:
        try:
            template, created = ReportTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                print(f"✅ Report template created: {template.name}")
            else:
                print(f"ℹ️  Report template exists: {template.name}")
        except Exception as e:
            print(f"❌ Failed to create report template {template_data['name']}: {e}")

def main():
    """Main setup function."""
    print("🚀 Setting up Accounting API test environment...")
    print("=" * 50)
    
    # Create superuser
    user = create_superuser()
    if not user:
        print("❌ Cannot proceed without a superuser. Please create one manually.")
        return
    
    print("\n📊 Creating account types...")
    account_types = create_account_types()
    
    print("\n📁 Creating account categories...")
    categories = create_account_categories(account_types)
    
    print("\n💰 Creating accounts...")
    accounts = create_accounts(account_types, categories)
    
    print("\n🔄 Creating transaction types...")
    transaction_types = create_transaction_types()
    
    print("\n📝 Creating sample transactions...")
    create_sample_transactions(transaction_types, accounts, user)
    
    print("\n📋 Creating report templates...")
    create_report_templates()
    
    print("\n" + "=" * 50)
    print("✅ Test environment setup complete!")
    print("\n📋 Next steps:")
    print("1. Start your Django server: python manage.py runserver")
    print("2. Import the Postman collection: AccountingAPI_Postman_Collection.json")
    print("3. Start testing with the 'Get JWT Token' endpoint")
    print("4. Follow the testing guide: API_Testing_Guide.md")
    print("\n🔑 Default credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n🌐 API Base URL: http://localhost:8000/api/v1")

if __name__ == '__main__':
    main()

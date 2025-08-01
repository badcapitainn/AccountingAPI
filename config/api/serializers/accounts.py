"""
Serializers for account-related models.

This module contains DRF serializers for Account, AccountType,
and AccountCategory models.
"""

from rest_framework import serializers
from accounting.models import Account, AccountType, AccountCategory


class AccountTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for AccountType model.
    
    Provides serialization and deserialization for account types,
    including validation and nested relationships.
    """
    
    class Meta:
        model = AccountType
        fields = [
            'id', 'name', 'code', 'description', 'normal_balance',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_code(self, value):
        """Validate account type code."""
        if len(value) > 10:
            raise serializers.ValidationError("Code must be 10 characters or less.")
        return value.upper()
    
    def validate_normal_balance(self, value):
        """Validate normal balance type."""
        valid_choices = [choice[0] for choice in AccountType.ACCOUNT_TYPE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError("Invalid normal balance type.")
        return value


class AccountCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for AccountCategory model.
    
    Provides serialization and deserialization for account categories,
    including nested relationships and validation.
    """
    
    account_type = AccountTypeSerializer(read_only=True)
    account_type_id = serializers.UUIDField(write_only=True)
    parent_category = serializers.PrimaryKeyRelatedField(
        queryset=AccountCategory.objects.all(),
        required=False,
        allow_null=True
    )
    full_path = serializers.CharField(read_only=True)
    
    class Meta:
        model = AccountCategory
        fields = [
            'id', 'name', 'code', 'account_type', 'account_type_id',
            'description', 'parent_category', 'sort_order', 'is_active',
            'created_at', 'updated_at', 'full_path'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_path']
    
    def validate(self, data):
        """Validate category data."""
        # Check if code is unique within account type
        account_type = data.get('account_type_id')
        code = data.get('code')
        
        if account_type and code:
            existing = AccountCategory.objects.filter(
                code=code,
                account_type_id=account_type
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    "Code must be unique within the account type."
                )
        
        return data


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer for Account model.
    
    Provides serialization and deserialization for accounts,
    including nested relationships, validation, and computed fields.
    """
    
    account_type = AccountTypeSerializer(read_only=True)
    account_type_id = serializers.UUIDField(write_only=True)
    category = AccountCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    formatted_balance = serializers.CharField(read_only=True)
    can_post_transactions = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'name', 'description',
            'account_type', 'account_type_id', 'category', 'category_id',
            'balance_type', 'opening_balance', 'current_balance',
            'is_active', 'is_contra_account', 'is_bank_account',
            'is_cash_account', 'is_reconcilable', 'allow_posting',
            'require_reconciliation', 'sort_order', 'notes',
            'created_at', 'updated_at', 'formatted_balance',
            'can_post_transactions'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'formatted_balance',
            'can_post_transactions'
        ]
    
    def validate_account_number(self, value):
        """Validate account number."""
        from core.utils import ValidationUtils
        
        if not ValidationUtils.validate_account_number(value):
            raise serializers.ValidationError(
                "Account number must be 3-20 characters and alphanumeric."
            )
        
        # Check uniqueness
        existing = Account.objects.filter(account_number=value)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise serializers.ValidationError("Account number must be unique.")
        
        return value
    
    def validate(self, data):
        """Validate account data."""
        account_type_id = data.get('account_type_id')
        balance_type = data.get('balance_type')
        
        if account_type_id and balance_type:
            try:
                account_type = AccountType.objects.get(id=account_type_id)
                if account_type.normal_balance != balance_type:
                    raise serializers.ValidationError(
                        "Balance type must match account type normal balance."
                    )
            except AccountType.DoesNotExist:
                raise serializers.ValidationError("Invalid account type.")
        
        return data
    
    def to_representation(self, instance):
        """Custom representation with computed fields."""
        data = super().to_representation(instance)
        
        # Add computed fields
        data['formatted_balance'] = instance.get_formatted_balance()
        data['can_post_transactions'] = instance.can_post_transactions()
        
        return data


class AccountDetailSerializer(AccountSerializer):
    """
    Detailed serializer for Account model.
    
    Includes additional fields and relationships for detailed views.
    """
    
    transaction_count = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    
    class Meta(AccountSerializer.Meta):
        fields = AccountSerializer.Meta.fields + [
            'transaction_count', 'recent_activity'
        ]
    
    def get_transaction_count(self, obj):
        """Get the number of transactions for this account."""
        return obj.journal_items.count()
    
    def get_recent_activity(self, obj):
        """Get recent activity for this account."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Get activity from the last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        recent_items = obj.journal_items.filter(
            journal_entry__transaction__transaction_date__gte=start_date,
            journal_entry__transaction__transaction_date__lte=end_date,
            journal_entry__transaction__is_posted=True
        ).order_by('-journal_entry__transaction__transaction_date')[:10]
        
        return [
            {
                'date': item.journal_entry.transaction.transaction_date,
                'description': item.description or item.journal_entry.description,
                'debit': float(item.debit_amount),
                'credit': float(item.credit_amount),
                'transaction_number': item.journal_entry.transaction.transaction_number
            }
            for item in recent_items
        ]


class AccountBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer for account balance information.
    
    Used for balance sheet and other financial reports.
    """
    
    account_type = serializers.CharField(source='account_type.name')
    category = serializers.CharField(source='category.name')
    formatted_balance = serializers.CharField(read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'account_number', 'name', 'account_type', 'category',
            'current_balance', 'formatted_balance'
        ]
    
    def to_representation(self, instance):
        """Custom representation with formatted balance."""
        data = super().to_representation(instance)
        data['formatted_balance'] = instance.get_formatted_balance()
        return data


class AccountSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer for Account model.
    
    Used for lists and summaries where full details aren't needed.
    """
    
    account_type = serializers.CharField(source='account_type.name')
    category = serializers.CharField(source='category.name')
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'name', 'account_type', 'category',
            'current_balance', 'is_active'
        ] 
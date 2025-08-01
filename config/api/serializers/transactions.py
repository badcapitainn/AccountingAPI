"""
Serializers for transaction-related models.

This module contains DRF serializers for Transaction, JournalEntry,
JournalItem, and TransactionType models.
"""

from rest_framework import serializers
from accounting.models import Transaction, JournalEntry, JournalItem, TransactionType


class TransactionTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for TransactionType model.
    
    Provides serialization and deserialization for transaction types,
    including validation and nested relationships.
    """
    
    class Meta:
        model = TransactionType
        fields = [
            'id', 'name', 'code', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_code(self, value):
        """Validate transaction type code."""
        if len(value) > 10:
            raise serializers.ValidationError("Code must be 10 characters or less.")
        return value.upper()


class JournalItemSerializer(serializers.ModelSerializer):
    """
    Serializer for JournalItem model.
    
    Provides serialization and deserialization for journal items,
    including validation and account information.
    """
    
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    
    class Meta:
        model = JournalItem
        fields = [
            'id', 'journal_entry', 'account', 'account_number', 'account_name',
            'debit_amount', 'credit_amount', 'description', 'formatted_amount',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'formatted_amount']
    
    def validate(self, data):
        """Validate journal item data."""
        debit_amount = data.get('debit_amount', 0)
        credit_amount = data.get('credit_amount', 0)
        
        # Check that either debit or credit amount is provided
        if debit_amount == 0 and credit_amount == 0:
            raise serializers.ValidationError(
                "Either debit or credit amount must be provided."
            )
        
        # Check that both debit and credit amounts are not provided
        if debit_amount > 0 and credit_amount > 0:
            raise serializers.ValidationError(
                "Cannot have both debit and credit amounts."
            )
        
        return data
    
    def to_representation(self, instance):
        """Custom representation with formatted amount."""
        data = super().to_representation(instance)
        data['formatted_amount'] = instance.get_amount_display()
        return data


class JournalEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for JournalEntry model.
    
    Provides serialization and deserialization for journal entries,
    including nested journal items and validation.
    """
    
    items = JournalItemSerializer(many=True, read_only=True)
    total_debits = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_credits = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = JournalEntry
        fields = [
            'id', 'transaction', 'description', 'amount', 'sort_order',
            'items', 'total_debits', 'total_credits', 'is_balanced',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'total_debits', 'total_credits', 'is_balanced']
    
    def to_representation(self, instance):
        """Custom representation with calculated totals."""
        data = super().to_representation(instance)
        data['total_debits'] = instance.get_total_debits()
        data['total_credits'] = instance.get_total_credits()
        data['is_balanced'] = instance.is_balanced()
        return data


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model.
    
    Provides serialization and deserialization for transactions,
    including nested journal entries and validation.
    """
    
    transaction_type = TransactionTypeSerializer(read_only=True)
    transaction_type_id = serializers.UUIDField(write_only=True)
    journal_entries = JournalEntrySerializer(many=True, read_only=True)
    total_debits = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_credits = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_number', 'reference_number', 'description',
            'transaction_date', 'transaction_type', 'transaction_type_id',
            'amount', 'status', 'is_posted', 'posted_date', 'posted_by',
            'notes', 'attachments', 'journal_entries', 'total_debits',
            'total_credits', 'is_balanced', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_number', 'posted_date', 'posted_by',
            'total_debits', 'total_credits', 'is_balanced', 'created_at', 'updated_at'
        ]
    
    def validate_transaction_date(self, value):
        """Validate transaction date."""
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError("Transaction date cannot be in the future.")
        return value
    
    def validate_amount(self, value):
        """Validate transaction amount."""
        if value <= 0:
            raise serializers.ValidationError("Transaction amount must be greater than zero.")
        return value
    
    def to_representation(self, instance):
        """Custom representation with calculated totals."""
        data = super().to_representation(instance)
        data['total_debits'] = instance.get_total_debits()
        data['total_credits'] = instance.get_total_credits()
        data['is_balanced'] = instance.is_balanced()
        return data


class TransactionDetailSerializer(TransactionSerializer):
    """
    Detailed serializer for Transaction model.
    
    Includes additional fields and relationships for detailed views.
    """
    
    journal_entries_count = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta(TransactionSerializer.Meta):
        fields = TransactionSerializer.Meta.fields + [
            'journal_entries_count', 'items_count'
        ]
    
    def get_journal_entries_count(self, obj):
        """Get the number of journal entries for this transaction."""
        return obj.journal_entries.count()
    
    def get_items_count(self, obj):
        """Get the total number of journal items for this transaction."""
        total_items = 0
        for entry in obj.journal_entries.all():
            total_items += entry.items.count()
        return total_items


class TransactionSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer for Transaction model.
    
    Used for lists and summaries where full details aren't needed.
    """
    
    transaction_type = serializers.CharField(source='transaction_type.name')
    posted_by_name = serializers.CharField(source='posted_by.username', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_number', 'reference_number', 'description',
            'transaction_date', 'transaction_type', 'amount', 'status',
            'is_posted', 'posted_date', 'posted_by_name', 'created_at'
        ] 
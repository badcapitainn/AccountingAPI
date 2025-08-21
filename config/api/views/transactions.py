"""
API views for transaction management.

This module contains ViewSets for managing transactions, journal entries,
and transaction types in the accounting system.
"""

from rest_framework import viewsets, status, filters
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from django.utils import timezone

from accounting.models import Transaction, JournalEntry, JournalItem, TransactionType
from accounting.services.transaction_service import TransactionService
from api.serializers.transactions import (
    TransactionSerializer, TransactionDetailSerializer, TransactionSummarySerializer,
    JournalEntrySerializer, JournalItemSerializer, TransactionTypeSerializer
)
from core.permissions import IsAccountantOrReadOnly, IsManagerOrReadOnly


class TransactionTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transaction types.
    
    Provides CRUD operations for transaction types in the accounting system.
    """
    
    queryset = TransactionType.objects.all()
    serializer_class = TransactionTypeSerializer
    permission_classes = [IsManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Get filtered queryset."""
        #queryset = super().get_queryset()
        queryset = TransactionType.objects.all()
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions of this type."""
        #transaction_type = self.get_object()
        transaction_type = TransactionType.objects.get(id=pk)
        transactions = transaction_type.transactions.filter(is_deleted=False)
        
        serializer = TransactionSummarySerializer(transactions, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transactions.
    
    Provides CRUD operations for transactions in the accounting system,
    including posting, voiding, and balance validation.
    """
    
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAccountantOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'is_posted', 'transaction_type', 'transaction_date'
    ]
    search_fields = ['transaction_number', 'reference_number', 'description']
    ordering_fields = [
        'transaction_number', 'transaction_date', 'amount', 'created_at'
    ]
    ordering = ['-transaction_date', '-created_at']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transaction_service = TransactionService()
    
    def get_queryset(self):
        """Get filtered queryset."""
        #queryset = super().get_queryset()
        queryset = Transaction.objects.all()
        
        # Filter by transaction type if specified
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type__code=transaction_type)
        
        # Filter by status if specified
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by posting status if specified
        is_posted = self.request.query_params.get('is_posted')
        if is_posted is not None:
            queryset = queryset.filter(is_posted=is_posted.lower() == 'true')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(transaction_date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(transaction_date__lte=end_date)
            except ValueError:
                pass
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve':
            return TransactionDetailSerializer
        elif self.action == 'list':
            return TransactionSummarySerializer
        return TransactionSerializer
    
    def perform_create(self, serializer):
        """Create transaction with service layer, returning 400 on validation errors."""
        from django.core.exceptions import ValidationError as DjangoValidationError
        transaction_data = serializer.validated_data
        try:
            transaction = self.transaction_service.create_transaction(
                transaction_data, self.request.user
            )
            # Ensure DRF has the created instance for the response
            serializer.instance = transaction
            return transaction
        except DjangoValidationError as exc:
            # Surface business-rule validation as a 400 response instead of 500
            detail = getattr(exc, 'messages', None) or str(exc)
            raise DRFValidationError(detail)
    
    @action(detail=True, methods=['post'])
    def post_transaction(self, request, pk=None):
        """Post a transaction to the general ledger."""
        #transaction = self.get_object()
        transaction = Transaction.objects.get(id=pk)
        
        try:
            self.transaction_service.post_transaction(transaction, request.user)
            return Response({
                'message': 'Transaction posted successfully.',
                'transaction_number': transaction.transaction_number,
                'posted_date': transaction.posted_date
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def void_transaction(self, request, pk=None):
        """Void a posted transaction."""
        #transaction = self.get_object()
        transaction = Transaction.objects.get(id=pk)
        reason = request.data.get('reason', '')
        
        try:
            reversal = self.transaction_service.void_transaction(
                transaction, request.user, reason
            )
            return Response({
                'message': 'Transaction voided successfully.',
                'reversal_transaction_number': reversal.transaction_number
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get transaction summary."""
        #transaction = self.get_object()
        transaction = Transaction.objects.get(id=pk)
        summary = self.transaction_service.get_transaction_summary(transaction)
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def journal_entries(self, request, pk=None):
        """Get journal entries for this transaction."""
        #transaction = self.get_object()
        transaction = Transaction.objects.get(id=pk)
        journal_entries = transaction.journal_entries.all()
        
        serializer = JournalEntrySerializer(journal_entries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent_transactions(self, request):
        """Get recent transactions."""
        days = int(request.query_params.get('days', 30))
        transactions = self.get_queryset().filter(
            transaction_date__gte=timezone.now().date() - timezone.timedelta(days=days)
        )
        
        serializer = TransactionSummarySerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_transactions(self, request):
        """Get pending transactions."""
        pending = self.get_queryset().filter(status='PENDING')
        serializer = TransactionSummarySerializer(pending, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def large_transactions(self, request):
        """Get transactions above a certain amount."""
        threshold = request.query_params.get('threshold', 10000)
        try:
            threshold = float(threshold)
        except ValueError:
            threshold = 10000
        
        large_transactions = self.get_queryset().filter(amount__gte=threshold)
        serializer = TransactionSummarySerializer(large_transactions, many=True)
        return Response(serializer.data)


class JournalEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing journal entries.
    
    Provides CRUD operations for journal entries within transactions.
    """
    
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAccountantOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction']
    search_fields = ['description']
    ordering_fields = ['sort_order', 'created_at']
    ordering = ['transaction', 'sort_order']
    
    def get_queryset(self):
        """Get filtered queryset."""
        #queryset = super().get_queryset()
        queryset = JournalEntry.objects.all()
        
        # Filter by transaction if specified
        transaction_id = self.request.query_params.get('transaction')
        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get journal items for this entry."""
        #journal_entry = self.get_object()
        journal_entry = JournalEntry.objects.get(id=pk)
        items = journal_entry.items.all()
        
        serializer = JournalItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get journal entry summary."""
        #journal_entry = self.get_object()
        journal_entry = JournalEntry.objects.get(id=pk)
        
        return Response({
            'id': str(journal_entry.id),
            'description': journal_entry.description,
            'amount': float(journal_entry.amount),
            'total_debits': float(journal_entry.get_total_debits()),
            'total_credits': float(journal_entry.get_total_credits()),
            'is_balanced': journal_entry.is_balanced(),
            'items_count': journal_entry.items.count()
        }) 
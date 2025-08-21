"""
API views for account management.

This module contains ViewSets for managing accounts, account types,
and account categories in the Chart of Accounts.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from accounting.models import Account, AccountType, AccountCategory
from api.serializers.accounts import (
    AccountSerializer, AccountDetailSerializer, AccountSummarySerializer,
    AccountTypeSerializer, AccountCategorySerializer, AccountBalanceSerializer
)
from core.permissions import IsAccountantOrReadOnly, IsManagerOrReadOnly


class AccountTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing account types.
    
    Provides CRUD operations for account types in the Chart of Accounts.
    """
    
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
    permission_classes = [IsManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'normal_balance']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['code']
    
    def get_queryset(self):
        """Get filtered queryset."""
        #queryset = super().get_queryset()
        queryset = AccountType.objects.all()
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_active=False)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def accounts(self, request, pk=None):
        """Get all accounts of this type."""
        #account_type = self.get_object() # getting the wrong object value, requires the account type id 
        account_type = AccountType.objects.get(id=pk)
        accounts = account_type.get_accounts()
        
        serializer = AccountSummarySerializer(accounts, many=True)
        return Response(serializer.data)


class AccountCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing account categories.
    
    Provides CRUD operations for account categories in the Chart of Accounts.
    """
    
    queryset = AccountCategory.objects.all()
    serializer_class = AccountCategorySerializer
    permission_classes = [IsManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'sort_order', 'created_at']
    ordering = ['account_type', 'sort_order', 'name']
    
    def get_queryset(self):
        """Get filtered queryset."""
        #queryset = super().get_queryset()
        queryset = AccountCategory.objects.all()
        
        # Filter by account type if specified
        account_type = self.request.query_params.get('account_type')
        if account_type:
            # Try to filter by UUID first, then by code
            try:
                import uuid
                uuid.UUID(account_type)
                queryset = queryset.filter(account_type_id=account_type)
            except ValueError:
                queryset = queryset.filter(account_type__code=account_type)
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_active=False)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def accounts(self, request, pk=None):
        """Get all accounts in this category."""
        #category = self.get_object()
        category = AccountCategory.objects.get(id=pk)
        accounts = category.get_accounts()
        
        serializer = AccountSummarySerializer(accounts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """Get all subcategories of this category."""
        #category = self.get_object()
        category = AccountCategory.objects.get(id=pk)
        subcategories = category.get_subcategories()
        
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)


class AccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing accounts.
    
    Provides CRUD operations for accounts in the Chart of Accounts,
    including balance queries and transaction history.
    """
    
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAccountantOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'is_active', 'category', 'balance_type',
        'is_bank_account', 'is_cash_account', 'is_reconcilable'
    ]
    search_fields = ['account_number', 'name', 'description']
    ordering_fields = [
        'account_number', 'name', 'current_balance', 'sort_order', 'created_at'
    ]
    ordering = ['account_number']
    
    def get_queryset(self):
        """Get filtered queryset."""
        #queryset = super().get_queryset()
        queryset = Account.objects.all()
        
        # Filter by account type if specified
        account_type = self.request.query_params.get('account_type')
        if account_type:
            # Try to filter by UUID first, then by code
            try:
                import uuid
                uuid.UUID(account_type)
                queryset = queryset.filter(account_type_id=account_type)
            except ValueError:
                queryset = queryset.filter(account_type__code=account_type)
        
        # Filter by category if specified
        category = self.request.query_params.get('category')
        if category:
            # Try to filter by UUID first, then by code
            try:
                import uuid
                uuid.UUID(category)
                queryset = queryset.filter(category_id=category)
            except ValueError:
                queryset = queryset.filter(category__code=category)
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_active=False)
        
        # Filter by balance type if specified
        balance_type = self.request.query_params.get('balance_type')
        if balance_type:
            queryset = queryset.filter(balance_type=balance_type)
        
        # Filter by account properties
        is_bank_account = self.request.query_params.get('is_bank_account')
        if is_bank_account is not None:
            if is_bank_account.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_bank_account=True)
            elif is_bank_account.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_bank_account=False)
        
        is_cash_account = self.request.query_params.get('is_cash_account')
        if is_cash_account is not None:
            if is_cash_account.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_cash_account=True)
            elif is_cash_account.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_cash_account=False)
        
        is_reconcilable = self.request.query_params.get('is_reconcilable')
        if is_reconcilable is not None:
            if is_reconcilable.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_reconcilable=True)
            elif is_reconcilable.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_reconcilable=False)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve':
            return AccountDetailSerializer
        elif self.action == 'list':
            return AccountSummarySerializer
        return AccountSerializer
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get account balance as of a specific date."""
        #account = self.get_object()
        account = Account.objects.get(id=pk)
        as_of_date = request.query_params.get('as_of_date')
        
        if as_of_date:
            from datetime import datetime
            try:
                as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        balance = account.get_balance(as_of_date)
        
        return Response({
            'account_number': account.account_number,
            'account_name': account.name,
            'as_of_date': as_of_date or 'current',
            'balance': float(balance),
            'formatted_balance': account.get_formatted_balance()
        })
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get transaction history for this account."""
        #account = self.get_object()
        account = Account.objects.get(id=pk)
        
        # Get date range parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            from datetime import datetime
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid start_date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            from datetime import datetime
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid end_date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get transactions
        from accounting.models import Transaction
        transactions = account.get_transaction_history(start_date, end_date)
        
        # Paginate results
        page = self.paginate_queryset(transactions)
        if page is not None:
            from api.serializers.transactions import TransactionSummarySerializer
            serializer = TransactionSummarySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        from api.serializers.transactions import TransactionSummarySerializer
        serializer = TransactionSummarySerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_balance(self, request, pk=None):
        """Update account balance."""
        #account = self.get_object()
        account = Account.objects.get(id=pk)
        
        try:
            account.update_balance()
            return Response({
                'message': 'Account balance updated successfully.',
                'new_balance': float(account.current_balance),
                'formatted_balance': account.get_formatted_balance()
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to update balance: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def chart_of_accounts(self, request):
        """Get the complete chart of accounts organized by type and category."""
        accounts = self.get_queryset().select_related('account_type', 'category')
        
        # Organize by account type and category
        chart = {}
        for account in accounts:
            account_type = account.account_type.name
            category = account.category.name
            
            if account_type not in chart:
                chart[account_type] = {}
            
            if category not in chart[account_type]:
                chart[account_type][category] = []
            
            chart[account_type][category].append({
                'account_number': account.account_number,
                'name': account.name,
                'current_balance': float(account.current_balance),
                'formatted_balance': account.get_formatted_balance(),
                'is_active': account.is_active
            })
        
        return Response(chart)
    
    @action(detail=False, methods=['get'])
    def balance_sheet_accounts(self, request):
        """Get accounts organized for balance sheet."""
        # Get asset, liability, and equity accounts
        balance_sheet_types = ['ASSET', 'LIABILITY', 'EQUITY']
        accounts = self.get_queryset().filter(
            account_type__code__in=balance_sheet_types
        ).select_related('account_type', 'category')
        
        serializer = AccountBalanceSerializer(accounts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def income_statement_accounts(self, request):
        """Get accounts organized for income statement."""
        # Get revenue and expense accounts
        income_statement_types = ['REVENUE', 'EXPENSE']
        accounts = self.get_queryset().filter(
            account_type__code__in=income_statement_types
        ).select_related('account_type', 'category')
        
        serializer = AccountBalanceSerializer(accounts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bank_accounts(self, request):
        """Get all bank accounts."""
        bank_accounts = self.get_queryset().filter(is_bank_account=True)
        serializer = self.get_serializer(bank_accounts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def cash_accounts(self, request):
        """Get all cash accounts."""
        cash_accounts = self.get_queryset().filter(is_cash_account=True)
        serializer = self.get_serializer(cash_accounts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reconcilable_accounts(self, request):
        """Get all reconcilable accounts."""
        reconcilable_accounts = self.get_queryset().filter(is_reconcilable=True)
        serializer = self.get_serializer(reconcilable_accounts, many=True)
        return Response(serializer.data) 
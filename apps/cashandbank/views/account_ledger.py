from django.db import transaction as db_transaction
from django.db.models import Q, Sum, DecimalField
from django.utils import timezone
from django.utils.dateparse import parse_date
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from datetime import datetime

from apps.cashandbank.models import AccountLedger, CashierShift, ShiftTransaction
from apps.cashandbank.serializers import (
    AccountLedgerSerializer,
    AccountLedgerListSerializer,
    LedgerSummarySerializer,
)
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import CanManageBranchResources


class AccountLedgerViewSet(TenantViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Account Ledger - Complete financial records with running balance.
    
    Endpoints:
    - GET /api/account-ledger/ - List ledger entries with filtering
    - GET /api/account-ledger/{id}/ - Get ledger entry details
    - GET /api/account-ledger/summary/ - Get ledger summary with totals
    - GET /api/account-ledger/general/ - General Ledger
    - GET /api/account-ledger/sales/ - Sales Ledger
    - GET /api/account-ledger/purchase/ - Purchase Ledger
    """
    
    queryset = AccountLedger.objects.all()
    serializer_class = AccountLedgerSerializer
    permission_classes = [IsAuthenticated, CanManageBranchResources]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """Use lightweight serializer for list views"""
        if self.action == 'list':
            return AccountLedgerListSerializer
        elif self.action == 'summary':
            return LedgerSummarySerializer
        return AccountLedgerSerializer

    def get_queryset(self):
        """Filter ledger entries with extensive filtering options"""
        queryset = AccountLedger.objects.all().order_by('transaction_date', 'id')

        # Filter by ledger type
        ledger_type = self.request.query_params.get('ledger_type', None)
        if ledger_type:
            queryset = queryset.filter(ledger_type=ledger_type)

        # Filter by transaction type
        transaction_type = self.request.query_params.get('transaction_type', None)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        # Filter by shift
        shift_id = self.request.query_params.get('shift_id', None)
        if shift_id:
            queryset = queryset.filter(shift_id=shift_id)

        # Filter by date range
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        
        if from_date:
            try:
                from_date_obj = parse_date(from_date)
                if from_date_obj:
                    queryset = queryset.filter(transaction_date__date__gte=from_date_obj)
            except:
                pass

        if to_date:
            try:
                to_date_obj = parse_date(to_date)
                if to_date_obj:
                    queryset = queryset.filter(transaction_date__date__lte=to_date_obj)
            except:
                pass

        # Filter by reference type
        reference_type = self.request.query_params.get('reference_type', None)
        if reference_type:
            queryset = queryset.filter(reference_type=reference_type)

        # Filter by performed_by user
        performed_by_id = self.request.query_params.get('performed_by_id', None)
        if performed_by_id:
            queryset = queryset.filter(performed_by_id=performed_by_id)

        # Filter by branch
        branch_id = self.request.query_params.get('branch_id', None)
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        # Search by description or reference
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(reference__icontains=search) |
                Q(reference_id__icontains=search)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        """List ledger entries with summary in response headers"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Calculate summary statistics
        summary = self._calculate_summary(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response_with_summary(serializer.data, summary)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'summary': summary,
            'results': serializer.data,
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get ledger summary with totals and statistics.
        
        Query Parameters:
        - from_date: mm/dd/yyyy or yyyy-mm-dd
        - to_date: mm/dd/yyyy or yyyy-mm-dd
        - shift_id: Filter by specific shift
        - ledger_type: general, sales, purchase, account
        - transaction_type: opening, cash_in, cash_out, sale, closing
        """
        queryset = self.filter_queryset(self.get_queryset())
        summary = self._calculate_summary(queryset)
        
        return Response(summary)

    @action(detail=False, methods=['get'])
    def general(self, request):
        """Get General Ledger - all transactions"""
        request.query_params._mutable = True
        request.query_params['ledger_type'] = 'general'
        request.query_params._mutable = False
        
        return self.list(request)

    @action(detail=False, methods=['get'])
    def sales(self, request):
        """Get Sales Ledger - only sales-related transactions"""
        request.query_params._mutable = True
        request.query_params['ledger_type'] = 'sales'
        request.query_params._mutable = False
        
        return self.list(request)

    @action(detail=False, methods=['get'])
    def purchase(self, request):
        """Get Purchase Ledger - only purchase-related transactions (cash out)"""
        request.query_params._mutable = True
        request.query_params['ledger_type'] = 'purchase'
        request.query_params._mutable = False
        
        return self.list(request)

    @action(detail=False, methods=['get'])
    def by_shift(self, request):
        """
        Get ledger entries for a specific shift.
        
        Query Parameters:
        - shift_id: Required - ID of the shift
        - from_date: Optional - Filter from date
        - to_date: Optional - Filter to date
        """
        shift_id = request.query_params.get('shift_id', None)
        
        if not shift_id:
            return Response(
                {'detail': 'shift_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            shift = CashierShift.objects.get(
                id=shift_id,
                tenant=request.user.tenant
            )
        except CashierShift.DoesNotExist:
            return Response(
                {'detail': 'Shift not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        queryset = self.filter_queryset(self.get_queryset()).filter(shift=shift)
        summary = self._calculate_summary(queryset, shift=shift)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response_with_summary(serializer.data, summary)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'shift': {
                'id': shift.id,
                'cashier': str(shift.cashier),
                'opening_float': str(shift.opening_float),
                'opened_at': shift.opened_at.isoformat(),
                'status': shift.status,
            },
            'summary': summary,
            'results': serializer.data,
        })

    @action(detail=False, methods=['post'])
    def create_entry(self, request):
        """
        Create a manual ledger entry.
        
        Request Body:
        {
            "ledger_type": "general",
            "transaction_type": "cash_in",
            "debit": 1000.00,
            "credit": 0.00,
            "description": "Manual cash entry",
            "reference": "REF-123",
            "reference_type": "manual",
            "shift_id": 1,
            "notes": "Additional notes"
        }
        """
        serializer = AccountLedgerSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with db_transaction.atomic():
                    ledger_entry = serializer.save(
                        tenant=request.user.tenant,
                        performed_by=request.user,
                        is_manual_entry=True
                    )
                    return Response(
                        AccountLedgerSerializer(ledger_entry).data,
                        status=status.HTTP_201_CREATED
                    )
            except Exception as e:
                return Response(
                    {'detail': f'Error creating entry: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def print_ledger(self, request):
        """
        Get ledger data formatted for printing.
        
        Returns all ledger details without pagination for printing/export.
        """
        queryset = self.filter_queryset(self.get_queryset())
        summary = self._calculate_summary(queryset)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'summary': summary,
            'entries': serializer.data,
            'print_metadata': {
                'generated_at': timezone.now().isoformat(),
                'total_entries': queryset.count(),
            }
        })

    def _calculate_summary(self, queryset, shift=None):
        """Calculate summary statistics for ledger entries"""
        
        # Get date range from queryset or request parameters
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        
        if not from_date and queryset.exists():
            from_date = queryset.first().transaction_date.strftime('%m/%d/%Y')
        else:
            from_date = from_date or ''

        if not to_date and queryset.exists():
            to_date = queryset.last().transaction_date.strftime('%m/%d/%Y')
        else:
            to_date = to_date or ''

        # Calculate totals
        totals = queryset.aggregate(
            total_debit=Sum('debit', output_field=DecimalField()),
            total_credit=Sum('credit', output_field=DecimalField()),
        )

        total_debit = totals['total_debit'] or Decimal('0.00')
        total_credit = totals['total_credit'] or Decimal('0.00')
        net_balance = total_debit - total_credit

        # Get ledger type from query params
        ledger_type = self.request.query_params.get('ledger_type', 'general')

        # Base summary
        summary = {
            'total_debit': total_debit,
            'total_credit': total_credit,
            'net_balance': net_balance,
            'transaction_count': queryset.count(),
            'from_date': from_date,
            'to_date': to_date,
            'ledger_type': ledger_type,
            'filtered_by_shift': shift is not None,
            'currency': 'Rs',
        }

        # Add Sales Ledger specific summary
        if ledger_type == 'sales':
            sales_qs = queryset.filter(ledger_type='sales')
            if sales_qs.exists():
                # Total unique customers (based on reference_id for bills)
                from django.db.models import Count
                total_customers = sales_qs.filter(
                    reference_id__isnull=False,
                    reference_type__in=['bill', 'invoice']
                ).values('reference_id').distinct().count()
                
                if total_customers == 0:
                    total_customers = sales_qs.filter(
                        reference_id__isnull=False
                    ).values('reference_id').distinct().count()
                
                # Gross amount (sales transactions - debit)
                gross_sales = sales_qs.filter(
                    transaction_type='sale'
                ).aggregate(
                    total=Sum('debit', output_field=DecimalField())
                )['total'] or Decimal('0.00')
                
                # Return amount (refunds - credit)
                return_amount = sales_qs.filter(
                    transaction_type='refund'
                ).aggregate(
                    total=Sum('credit', output_field=DecimalField())
                )['total'] or Decimal('0.00')
                
                # Net amount
                net_sales = gross_sales - return_amount
                
                # Due remaining (calculated based on any pending amounts)
                due_remaining = Decimal('0.00')
                
                summary['sales_summary'] = {
                    'total_customers': total_customers,
                    'gross_amount': gross_sales,
                    'return_amount': return_amount,
                    'net_amount': net_sales,
                    'due_remaining': due_remaining,
                }

        # Add Purchase Ledger specific summary
        if ledger_type == 'purchase':
            purchase_qs = queryset.filter(ledger_type='purchase')
            if purchase_qs.exists():
                # Total unique suppliers (based on reference_id)
                from django.db.models import Count
                total_suppliers = purchase_qs.filter(
                    reference_id__isnull=False,
                    reference_type__in=['purchase_order', 'po', 'supplier']
                ).values('reference_id').distinct().count()
                
                if total_suppliers == 0:
                    total_suppliers = purchase_qs.filter(
                        reference_id__isnull=False
                    ).values('reference_id').distinct().count()
                
                # Gross amount (purchase transactions - credit)
                gross_purchases = purchase_qs.filter(
                    transaction_type='cash_out'
                ).aggregate(
                    total=Sum('credit', output_field=DecimalField())
                )['total'] or Decimal('0.00')
                
                # Return amount (purchase returns - debit)
                return_amount = purchase_qs.filter(
                    transaction_type='refund'
                ).aggregate(
                    total=Sum('debit', output_field=DecimalField())
                )['total'] or Decimal('0.00')
                
                # Net amount
                net_purchases = gross_purchases - return_amount
                
                # Due remaining (for supplier payments)
                due_remaining = Decimal('0.00')
                
                summary['purchase_summary'] = {
                    'total_suppliers': total_suppliers,
                    'gross_amount': gross_purchases,
                    'return_amount': return_amount,
                    'net_amount': net_purchases,
                    'due_remaining': due_remaining,
                }

        return summary

    def get_paginated_response_with_summary(self, data, summary):
        """Return paginated response with summary included"""
        return Response({
            'summary': summary,
            'count': self.paginator.page.paginator.count,
            'next': self.paginator.get_next_link(),
            'previous': self.paginator.get_previous_link(),
            'results': data,
        })

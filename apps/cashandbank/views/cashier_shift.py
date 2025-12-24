from django.db import transaction as db_transaction
from django.utils import timezone
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.cashandbank.models import CashierShift, ShiftTransaction
from apps.cashandbank.serializers import CashierShiftSerializer, ShiftTransactionSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import CanManageBranchResources


class CashierShiftViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing cashier shifts with full lifecycle support.
    
    Endpoints:
    - GET /api/shifts/ - List shifts
    - POST /api/shifts/ - Create shift
    - GET /api/shifts/{id}/ - Get shift details
    - POST /api/shifts/{id}/open/ - Open shift
    - POST /api/shifts/{id}/close_balanced/ - Close balanced shift
    - POST /api/shifts/{id}/close_variance/ - Close with variance
    - POST /api/shifts/{id}/cash_in/ - Add cash in
    - POST /api/shifts/{id}/cash_out/ - Add cash out
    - GET /api/shifts/active/ - Get active shift for user
    """
    
    queryset = CashierShift.objects.all()
    serializer_class = CashierShiftSerializer
    permission_classes = [IsAuthenticated, CanManageBranchResources]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Filter shifts by status and tenant"""
        queryset = CashierShift.objects.all()
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by cashier
        cashier_id = self.request.query_params.get('cashier_id', None)
        if cashier_id:
            queryset = queryset.filter(cashier_id=cashier_id)
        
        # Filter by flagged
        is_flagged = self.request.query_params.get('is_flagged', None)
        if is_flagged is not None:
            is_flagged_bool = is_flagged.lower() == 'true'
            queryset = queryset.filter(is_flagged=is_flagged_bool)
        
        return queryset

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get active (open) shift for the current user.
        
        Returns the current open shift or 404 if none exists.
        """
        try:
            shift = CashierShift.objects.get(
                cashier=request.user,
                status='open',
                tenant=request.user.tenant
            )
            serializer = self.get_serializer(shift)
            return Response(serializer.data)
        except CashierShift.DoesNotExist:
            return Response(
                {'detail': 'No active shift found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def open(self, request):
        """
        Open a new shift for the current user.
        
        Request body:
        {
            "opening_float": 1000.00,
            "branch_id": 1,
            "notes": "Opening shift"
        }
        """
        opening_float = request.data.get('opening_float')
        branch_id = request.data.get('branch_id')
        notes = request.data.get('notes', '')

        if opening_float is None:
            return Response(
                {'opening_float': 'This field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            opening_float = Decimal(str(opening_float))
            if opening_float < 0:
                raise ValidationError('Opening float must be non-negative')
        except (ValueError, TypeError):
            return Response(
                {'opening_float': 'Must be a valid decimal number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already has open shift
        existing_open = CashierShift.objects.filter(
            cashier=request.user,
            status='open',
            tenant=request.user.tenant
        ).first()

        if existing_open:
            return Response(
                {'detail': f'User already has open shift (ID: {existing_open.id})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with db_transaction.atomic():
            shift = CashierShift(
                cashier=request.user,
                tenant=request.user.tenant,
                branch_id=branch_id or getattr(request.user, 'branch_id', None),
                opening_float=opening_float,
                expected_amount=opening_float,
                status='open',
                notes=notes if notes else None
            )
            shift.save()

            # Create opening transaction
            ShiftTransaction.objects.create(
                shift=shift,
                tenant=request.user.tenant,
                transaction_type='opening',
                amount=opening_float,
                description='Shift opening float',
                performed_by=request.user,
                transaction_date=shift.opened_at
            )

        serializer = self.get_serializer(shift)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cash_in(self, request, pk=None):
        """
        Add cash in to the shift.
        
        Request body:
        {
            "amount": 500.00,
            "description": "Customer refund"
        }
        """
        shift = self.get_object()

        if shift.status != 'open':
            return Response(
                {'detail': 'Can only add cash to open shifts'},
                status=status.HTTP_400_BAD_REQUEST
            )

        amount = request.data.get('amount')
        description = request.data.get('description', '')

        if amount is None:
            return Response(
                {'amount': 'This field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValidationError('Amount must be positive')
        except (ValueError, TypeError):
            return Response(
                {'amount': 'Must be a valid decimal number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with db_transaction.atomic():
            # Update expected amount
            shift.adjust_expected_amount(amount)

            # Create cash_in transaction (automatically updates CashBalance)
            ShiftTransaction.objects.create(
                shift=shift,
                tenant=shift.tenant,
                transaction_type='cash_in',
                amount=amount,
                description=description if description else None,
                performed_by=request.user
            )

        serializer = self.get_serializer(shift)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cash_out(self, request, pk=None):
        """
        Remove cash from the shift.
        
        Request body:
        {
            "amount": 250.00,
            "description": "Reimbursement to manager"
        }
        """
        shift = self.get_object()

        if shift.status != 'open':
            return Response(
                {'detail': 'Can only remove cash from open shifts'},
                status=status.HTTP_400_BAD_REQUEST
            )

        amount = request.data.get('amount')
        description = request.data.get('description', '')

        if amount is None:
            return Response(
                {'amount': 'This field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValidationError('Amount must be positive')
        except (ValueError, TypeError):
            return Response(
                {'amount': 'Must be a valid decimal number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with db_transaction.atomic():
            # Update expected amount (subtract)
            shift.adjust_expected_amount(-amount)

            # Create cash_out transaction (automatically updates CashBalance)
            ShiftTransaction.objects.create(
                shift=shift,
                tenant=shift.tenant,
                transaction_type='cash_out',
                amount=amount,
                description=description if description else None,
                performed_by=request.user
            )

        serializer = self.get_serializer(shift)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def close_balanced(self, request, pk=None):
        """
        Close shift when actual amount matches expected (balanced).
        
        Request body:
        {
            "actual_amount": 2000.00,
            "notes": "Perfect balance"
        }
        """
        shift = self.get_object()

        if shift.status != 'open':
            return Response(
                {'detail': 'Can only close open shifts'},
                status=status.HTTP_400_BAD_REQUEST
            )

        actual_amount = request.data.get('actual_amount')
        notes = request.data.get('notes', '')

        if actual_amount is None:
            return Response(
                {'actxpected_amountual_amount': 'This field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            actual_amount = Decimal(str(actual_amount))
            if actual_amount < 0:
                raise ValidationError('Actual amount must be non-negative')
        except (ValueError, TypeError):
            return Response(
                {'actual_amount': 'Must be a valid decimal number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with db_transaction.atomic():
            # Check if balanced (within tolerance)
            expected = shift.expected_amount or Decimal('0.00')
            variance = actual_amount - expected

            if abs(variance) > Decimal('0.01'):
                return Response(
                    {
                        'detail': 'Shift is not balanced',
                        'expected': str(expected),
                        'actual': str(actual_amount),
                        'variance': str(variance)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update shift
            shift.actual_amount = actual_amount
            shift.variance_amount = variance
            shift.status = 'closed'
            shift.closed_at = timezone.now()
            if notes:
                shift.notes = notes
            shift.save()

            # Create closing transaction
            ShiftTransaction.objects.create(
                shift=shift,
                tenant=shift.tenant,
                transaction_type='closing',
                amount=actual_amount,
                description='Shift closing',
                performed_by=request.user
            )

        serializer = self.get_serializer(shift)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def close_variance(self, request, pk=None):
        """
        Close shift with variance when actual differs from expected.
        
        Request body:
        {
            "actual_amount": 1950.00,
            "variance_reason": "Miscounted initially",
            "notes": "Recounted and confirmed"
        }
        """
        shift = self.get_object()

        if shift.status != 'open':
            return Response(
                {'detail': 'Can only close open shifts'},
                status=status.HTTP_400_BAD_REQUEST
            )

        actual_amount = request.data.get('actual_amount')
        variance_reason = request.data.get('variance_reason', '')
        notes = request.data.get('notes', '')

        if actual_amount is None:
            return Response(
                {'actual_amount': 'This field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            actual_amount = Decimal(str(actual_amount))
            if actual_amount < 0:
                raise ValidationError('Actual amount must be non-negative')
        except (ValueError, TypeError):
            return Response(
                {'actual_amount': 'Must be a valid decimal number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with db_transaction.atomic():
            # Calculate variance
            expected = shift.expected_amount or Decimal('0.00')
            variance = actual_amount - expected
            
            # Require variance_reason if there's any variance
            if abs(variance) > Decimal('0.01') and not variance_reason:
                return Response(
                    {
                        'variance_reason': 'This field is required when actual amount differs from expected',
                        'expected_amount': str(expected),
                        'actual_amount': str(actual_amount),
                        'variance_amount': str(variance)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update shift
            shift.actual_amount = actual_amount
            shift.variance_amount = variance
            shift.status = 'closed'
            shift.closed_at = timezone.now()
            
            if variance_reason:
                shift.variance_reason = variance_reason
            if notes:
                shift.notes = notes
            
            # Auto-flag if variance exceeds threshold
            if abs(variance) > Decimal('100.00'):
                shift.is_flagged = True
            
            shift.save()

            # Create closing transaction
            ShiftTransaction.objects.create(
                shift=shift,
                tenant=shift.tenant,
                transaction_type='closing',
                amount=actual_amount,
                description=f'Shift closing (variance: {variance})',
                performed_by=request.user
            )

        serializer = self.get_serializer(shift)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for a shift"""
        shift = self.get_object()
        transactions = shift.shift_transactions.all()
        serializer = ShiftTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def transfer_shift(self, request, pk=None):
        """
        Transfer shift to another cashier with variance computation.

        Workflow:
        1. Compute variance vs expected
        2. If variance exists without variance_reason, return variance info (HTTP 202)
        3. Client shows variance modal to user
        4. If no variance or variance_reason provided, complete transfer immediately (HTTP 200)
        5. If variance and user confirms, call confirm_transfer endpoint with variance_reason

        Request body:
        {
            "counted_cash": 2000.00,
            "transferred_to": "John Doe",
            "variance_reason": "Optional: reason if variance"
        }
        """
        from apps.cashandbank.serializers import ShiftTransferInputSerializer

        shift = self.get_object()

        if shift.status != 'open':
            return Response(
                {'detail': 'Can only transfer open shifts'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ShiftTransferInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        counted_cash = serializer.validated_data['counted_cash']
        transferred_to = serializer.validated_data['transferred_to']
        variance_reason = serializer.validated_data.get('variance_reason', '')

        expected = shift.expected_amount or Decimal('0.00')
        variance = counted_cash - expected
        has_variance = variance != Decimal('0.00')
        will_be_flagged = abs(variance) > Decimal('100.00')

        if has_variance and not variance_reason:
            variance_data = {
                'expected_amount': str(expected),
                'counted_cash': str(counted_cash),
                'variance_amount': str(variance),
                'has_variance': True,
                'will_be_flagged': will_be_flagged,
                'detail': 'Variance detected; provide variance_reason to complete transfer.'
            }
            return Response(variance_data, status=status.HTTP_202_ACCEPTED)

        with db_transaction.atomic():
            shift.transfer_shift(
                counted_cash=counted_cash,
                transferred_to=transferred_to,
                transferred_by=request.user,
                variance_reason=variance_reason if variance_reason else None
            )

            ShiftTransaction.objects.create(
                shift=shift,
                tenant=shift.tenant,
                transaction_type='closing',
                amount=counted_cash,
                description=f'Shift transfer to {transferred_to}',
                performed_by=request.user
            )

        output_serializer = self.get_serializer(shift)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def confirm_transfer(self, request, pk=None):
        """
        Confirm transfer after variance modal. Call when user accepts variance.

        Request body:
        {
            "counted_cash": 2000.00,
            "transferred_to": "John Doe",
            "variance_reason": "Miscounted during count"
        }
        """
        from apps.cashandbank.serializers import ShiftTransferInputSerializer

        shift = self.get_object()

        if shift.status != 'open':
            return Response(
                {'detail': 'Can only transfer open shifts'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ShiftTransferInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        counted_cash = serializer.validated_data['counted_cash']
        transferred_to = serializer.validated_data['transferred_to']
        variance_reason = serializer.validated_data.get('variance_reason', '')

        expected = shift.expected_amount or Decimal('0.00')
        variance = counted_cash - expected
        if variance != Decimal('0.00') and not variance_reason:
            return Response(
                {
                    'variance_reason': 'Required when counted cash differs from expected',
                    'expected_amount': str(expected),
                    'counted_cash': str(counted_cash),
                    'variance_amount': str(variance)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        with db_transaction.atomic():
            shift.transfer_shift(
                counted_cash=counted_cash,
                transferred_to=transferred_to,
                transferred_by=request.user,
                variance_reason=variance_reason if variance_reason else None
            )

            ShiftTransaction.objects.create(
                shift=shift,
                tenant=shift.tenant,
                transaction_type='closing',
                amount=counted_cash,
                description=f'Shift transfer to {transferred_to}',
                performed_by=request.user
            )

        output_serializer = self.get_serializer(shift)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

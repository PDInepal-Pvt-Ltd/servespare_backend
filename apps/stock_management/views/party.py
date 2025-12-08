from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.stock_management.models import Party
from apps.stock_management.serializers import PartySerializer


class PartyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing parties (suppliers and customers)
    """
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    
    def get_queryset(self):
        """
        Optionally filter by party_type, customer_type, or is_active
        """
        queryset = Party.objects.all()
        
        # Filter by party_type
        party_type = self.request.query_params.get('party_type', None)
        if party_type is not None:
            queryset = queryset.filter(party_type=party_type)
        
        # Filter by customer_type
        customer_type = self.request.query_params.get('customer_type', None)
        if customer_type is not None:
            queryset = queryset.filter(customer_type=customer_type)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(party_name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def suppliers(self, request):
        """
        Get all suppliers
        """
        suppliers = Party.objects.filter(party_type='supplier', is_active=True)
        serializer = self.get_serializer(suppliers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def customers(self, request):
        """
        Get all customers
        """
        customers = Party.objects.filter(party_type='customer', is_active=True)
        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)


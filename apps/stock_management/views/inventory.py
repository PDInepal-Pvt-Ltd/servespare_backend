from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, F
from apps.stock_management.models import Inventory, InventoryImage
from apps.stock_management.serializers import InventorySerializer, InventoryImageSerializer


class InventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing inventory items
    """
    queryset = Inventory.objects.select_related('party').prefetch_related('images').all()
    serializer_class = InventorySerializer
    
    def get_queryset(self):
        """
        Optionally filter by category, vehicle_type, party, or stock level
        """
        queryset = Inventory.objects.select_related('party').prefetch_related('images').all()
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category is not None:
            queryset = queryset.filter(category=category)
        
        # Filter by vehicle_type
        vehicle_type = self.request.query_params.get('vehicle_type', None)
        if vehicle_type is not None:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        
        # Filter by party
        party_id = self.request.query_params.get('party', None)
        if party_id is not None:
            queryset = queryset.filter(party_id=party_id)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock', None)
        if low_stock and low_stock.lower() == 'true':
            queryset = queryset.filter(quantity__lte=models.F('min_stock_level'))
        
        # Search by item name, part number, or barcode
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(item_name__icontains=search) |
                Q(part_number__icontains=search) |
                Q(barcode__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Get all items with low stock (quantity <= min_stock_level)
        """
        low_stock_items = Inventory.objects.filter(
            quantity__lte=F('min_stock_level'),
            is_active=True
        ).select_related('party').prefetch_related('images')
        
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Get inventory items grouped by category
        """
        category = request.query_params.get('category', None)
        if not category:
            return Response(
                {'error': 'category parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        items = Inventory.objects.filter(
            category=category,
            is_active=True
        ).select_related('party').prefetch_related('images')
        
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_vehicle_type(self, request):
        """
        Get inventory items grouped by vehicle type
        """
        vehicle_type = request.query_params.get('vehicle_type', None)
        if not vehicle_type:
            return Response(
                {'error': 'vehicle_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        items = Inventory.objects.filter(
            vehicle_type=vehicle_type,
            is_active=True
        ).select_related('party').prefetch_related('images')
        
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        """
        Add an image to an inventory item
        """
        inventory = self.get_object()
        serializer = InventoryImageSerializer(data={
            **request.data,
            'inventory': inventory.id
        })
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing inventory images
    """
    queryset = InventoryImage.objects.select_related('inventory').all()
    serializer_class = InventoryImageSerializer
    
    def get_queryset(self):
        """
        Optionally filter by inventory
        """
        queryset = InventoryImage.objects.select_related('inventory').all()
        
        # Filter by inventory
        inventory_id = self.request.query_params.get('inventory', None)
        if inventory_id is not None:
            queryset = queryset.filter(inventory_id=inventory_id)
        
        # Filter by is_primary
        is_primary = self.request.query_params.get('is_primary', None)
        if is_primary is not None:
            is_primary_bool = is_primary.lower() == 'true'
            queryset = queryset.filter(is_primary=is_primary_bool)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset


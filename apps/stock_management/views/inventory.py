import csv
import io
from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, F, Sum, DecimalField
from apps.stock_management.models import Inventory, InventoryImage, Party
from apps.stock_management.serializers import InventorySerializer, InventoryImageSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.permissions import CanViewInventory
from apps.base.permission_utils import get_branch_queryset_for_user
from apps.base.pagination import StandardResultsSetPagination


class InventoryViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing inventory items with branch-level access control.
    
    Permissions:
    - Super Admin: Can manage inventory in all branches
    - Tenant Admin: Can manage inventory in all branches of their tenant
    - Inventory Manager: Can manage inventory only in their assigned branch
    - Customer: Can view inventory (read-only)
    """
    queryset = Inventory.objects.select_related('party').prefetch_related('images').all()
    serializer_class = InventorySerializer
    permission_classes = [CanViewInventory]
    pagination_class = StandardResultsSetPagination
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_authenticators(self):
        """
        Allow unauthenticated GET requests only when no Authorization
        header is present. If the client provides an Authorization header
        authenticate the request so role-based filtering can apply.
        """
        if self.request and self.request.method == 'GET':
            # Django stores Authorization in HTTP_AUTHORIZATION
            if not self.request.META.get('HTTP_AUTHORIZATION'):
                return []
        return super().get_authenticators()
    
    def get_permissions(self):
        """
        When an Authorization header is present, enforce `permission_classes`
        for all actions (including `list` and `retrieve`) so authenticated
        admin/inventory manager users are filtered to their tenant/branch.

        If no Authorization header is present, allow read-only access.
        """
        # If there's an auth header, enforce permissions for all actions
        if self.request and self.request.META.get('HTTP_AUTHORIZATION'):
            return [permission() for permission in self.permission_classes]

        # No auth header: allow safe methods (public read-only)
        if self.action in ['list', 'retrieve']:
            return []

        return [permission() for permission in self.permission_classes]

    def _create_images_from_request(self, inventory, request):
        """Attach uploaded images from the same request to the inventory item."""
        files = request.FILES.getlist('images') or []

        single_image = request.FILES.get('image')
        if single_image and single_image not in files:
            files.insert(0, single_image)

        if not files:
            return

        description = request.data.get('description', '')
        is_primary_param = request.data.get('is_primary')

        for idx, image_file in enumerate(files):
            is_primary = False
            if is_primary_param is not None:
                is_primary = str(is_primary_param).lower() == 'true'
            elif idx == 0 and not inventory.images.filter(is_primary=True, is_removed=False).exists():
                is_primary = True

            payload = {
                'inventory': inventory.id,
                'image': image_file,
                'description': description or f'Image {idx + 1}',
                'is_primary': is_primary,
            }

            serializer = InventoryImageSerializer(data=payload, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inventory = serializer.save()

        # Attach images if provided in the same request
        self._create_images_from_request(inventory, request)

        headers = self.get_success_headers(serializer.data)
        response_data = self.get_serializer(inventory).data
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    
    def get_queryset(self):
        """
        Filter inventory based on user's role and branch access.
        
        - Super Admin: See all inventory
        - Tenant Admin: See inventory from all branches in their tenant
        - Inventory Manager: See only inventory in their branch
        - Customer: See all active inventory (read-only)
        """
        from apps.users.models import User
        
        queryset = Inventory.objects.filter(is_removed=False).select_related('party').prefetch_related('images')
        
        # Customers should see everything (no active or branch filtering)
        # For authenticated users who are not customers, apply branch filtering
        if self.request.user.is_authenticated and self.request.user.role != User.Role.CUSTOMER:
            # Apply branch-level filtering based on user role for staff
            queryset = get_branch_queryset_for_user(self.request.user, queryset)
        
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
            queryset = queryset.filter(quantity__lte=F('min_stock_level'))
        
        # Search by item name, part number, or barcode
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(item_name__icontains=search) |
                Q(part_number__icontains=search) |
                Q(barcode__icontains=search)
            )
        
        return queryset

    def get_object(self):
        """
        Override to support delete/update when the object's tenant/branch
        filters exclude it from the default queryset (causing NotFound).

        If the standard lookup fails, try to fetch the instance directly
        and perform role-based checks to decide if the requesting user
        should be allowed to operate on it.
        """
        from rest_framework.exceptions import NotFound, PermissionDenied
        from django.http import Http404
        from apps.stock_management.models import Inventory as InventoryModel
        from apps.base.permission_utils import (
            can_manage_tenant,
            can_manage_branch_resources,
        )
        try:
            return super().get_object()
        except (NotFound, Http404):
            pk = self.kwargs.get(self.lookup_field)
            if not pk:
                raise NotFound("No Inventory matches the given query.")

            instance = InventoryModel.objects.filter(is_removed=False).select_related('tenant', 'branch').filter(pk=pk).first()
            if not instance:
                raise NotFound("No Inventory matches the given query.")

            user = getattr(self.request, 'user', None)
            try:
                from apps.users.models import User
            except Exception:
                User = None

            # Superuser / super admin
            if getattr(user, 'is_superuser', False) or (User and getattr(user, 'role', None) == User.Role.SUPER_ADMIN):
                return instance

            # Tenant admin can access if they manage tenant or branch (branch may belong to their tenant)
            if User and getattr(user, 'role', None) == User.Role.ADMIN:
                if can_manage_tenant(user, getattr(instance, 'tenant', None)) or can_manage_branch_resources(user, getattr(instance, 'branch', None)):
                    return instance

            # Inventory manager can access if branch matches
            if User and getattr(user, 'role', None) == User.Role.INVENTORY_MANAGER:
                if can_manage_branch_resources(user, getattr(instance, 'branch', None)):
                    return instance

            raise PermissionDenied("You do not have permission to access this inventory item.")
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get the 3 most recently added products
        GET /api/inventory/recent/
        """
        recent_items = self.filter_queryset(Inventory.objects.filter(
            is_active=True
        ).select_related('party').prefetch_related('images').order_by('-created')[:3])

        serializer = self.get_serializer(recent_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Get all items with low stock (quantity <= min_stock_level)
        """
        low_stock_items = self.filter_queryset(Inventory.objects.filter(
            quantity__lte=F('min_stock_level'),
            is_active=True
        ).select_related('party').prefetch_related('images'))

        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stock_stats(self, request):
        """
        Get comprehensive stock statistics
        GET /api/inventory/stock_stats/
        - Total low stock items (quantity <= min_stock_level)
        - Total out of stock items (quantity = 0)
        - Total stock value (sum of quantity * price)
        """
        all_inventory = self.filter_queryset(Inventory.objects.filter(is_active=True))
        
        # Count low stock items (quantity <= min_stock_level and quantity > 0)
        low_stock_count = all_inventory.filter(
            quantity__lte=F('min_stock_level'),
            quantity__gt=0
        ).count()
        
        # Count out of stock items (quantity = 0)
        out_of_stock_count = all_inventory.filter(quantity=0).count()
        
        # Calculate total stock value (quantity * price)
        stock_value_data = all_inventory.aggregate(
            total_stock_value=Sum(F('quantity') * F('price'), output_field=DecimalField())
        )
        total_stock_value = stock_value_data['total_stock_value'] or Decimal('0.00')
        
        # Additional stats
        total_items = all_inventory.count()
        total_quantity = all_inventory.aggregate(
            total=Sum('quantity', output_field=DecimalField())
        )['total'] or Decimal('0.00')
        
        return Response({
            'total_items': total_items,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'total_quantity': float(total_quantity),
            'total_stock_value': float(total_stock_value),
            'in_stock_count': total_items - out_of_stock_count,
        }, status=status.HTTP_200_OK)
    
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
        
        items = self.filter_queryset(Inventory.objects.filter(
            category=category,
            is_active=True
        ).select_related('party').prefetch_related('images'))

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
        
        items = self.filter_queryset(Inventory.objects.filter(
            vehicle_type=vehicle_type,
            is_active=True
        ).select_related('party').prefetch_related('images'))

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def pricing(self, request, pk=None):
        """
        Get pricing details for a specific inventory item
        Used by bill admin to auto-populate prices
        """
        inventory = self.get_object()
        pricing_data = {
            'id': inventory.id,
            'item_name': inventory.item_name,
            'price': float(inventory.price) if inventory.price else 0,
            'mrp': float(inventory.mrp) if inventory.mrp else 0,
            'retail_pricing': float(inventory.retail_pricing) if inventory.retail_pricing else 0,
            'wholesale_price': float(inventory.wholesale_price) if inventory.wholesale_price else 0,
            'distributor_price': float(inventory.distributor_price) if inventory.distributor_price else 0,
        }
        return Response(pricing_data)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def add_image(self, request, pk=None):
        """
        Add an image to an inventory item
        """
        inventory = self.get_object()
        serializer = InventoryImageSerializer(
            data={**request.data, 'inventory': inventory.id},
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        """
        Bulk upload inventory items from CSV file
        
        Expected CSV columns:
        - Item Name* (required)
        - Part Number* (required)
        - Category* (required: local/original)
        - Vehicle Type* (required: two_wheeler/four_wheeler)
        - Vehicle Name (optional)
        - Bike Model (optional)
        - Bike Type (optional)
        - HSN Code (optional)
        - Quantity* (required)
        - Min Stock Level* (required)
        - Price* (required)
        - MRP* (required)
        - Retail Price (optional)
        - Wholesale Price (optional)
        - Distributor Price (optional)
        - Supplier/Party Name (optional)
        - Barcode (optional)
        - Location (optional)
        - Warranty Period (months) (optional: numeric, will be converted to format like "6_month")
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'CSV file is required. Please upload a file with key "file".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        csv_file = request.FILES['file']
        
        # Check if file is CSV
        if not csv_file.name.endswith('.csv'):
            return Response(
                {'error': 'Invalid file type. Please upload a CSV file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Read CSV file
        try:
            decoded_file = csv_file.read().decode('utf-8-sig')  # Handle BOM
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Check if CSV has any rows
            if not reader.fieldnames:
                return Response(
                    {'error': 'CSV file is empty or invalid. Please ensure the file has headers and data rows.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': f'Error reading CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Field mapping from CSV column names to model fields
        field_mapping = {
            'Item Name': 'item_name',
            'Item Name*': 'item_name',
            'Part Number': 'part_number',
            'Part Number*': 'part_number',
            'Category': 'category',
            'Category*': 'category',
            'Category (local/original)': 'category',
            'Category* (local/original)': 'category',
            'Vehicle Type': 'vehicle_type',
            'Vehicle Type*': 'vehicle_type',
            'Vehicle Type (two_wheeler/four_wheeler)': 'vehicle_type',
            'Vehicle Type* (two_wheeler/four_wheeler)': 'vehicle_type',
            'Vehicle Name': 'vehicle_bike_details',
            'Bike Model': 'model',
            'Bike Type': 'type',
            'HSN Code': 'hsn_code',
            'Quantity': 'quantity',
            'Quantity*': 'quantity',
            'Min Stock Level': 'min_stock_level',
            'Min Stock Level*': 'min_stock_level',
            'Price': 'price',
            'Price*': 'price',
            'MRP': 'mrp',
            'MRP*': 'mrp',
            'Retail Price': 'retail_pricing',
            'Wholesale Price': 'wholesale_price',
            'Distributor Price': 'distributor_price',
            'Supplier/Party Name': 'party_name',
            'Supplier/Party Name*': 'party_name',
            'Barcode': 'barcode',
            'Location': 'storage_location',
            'Warranty Period (months)': 'warranty_period',
        }
        
        # Required fields
        required_fields = ['item_name', 'part_number', 'category', 'vehicle_type', 'quantity', 'min_stock_level', 'price', 'mrp']
        
        successful_imports = []
        failed_imports = []
        
        # Process each row
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
            try:
                # Skip completely empty rows
                if not any(str(v).strip() if v is not None else '' for v in row.values()):
                    continue
                
                # Map CSV columns to model fields
                inventory_data = {}
                errors = []
                
                # Process each field in the mapping
                for csv_col, model_field in field_mapping.items():
                    if csv_col in row and row[csv_col] is not None:
                        # Handle None and empty strings
                        value_str = str(row[csv_col]).strip() if row[csv_col] else ''
                        if not value_str:
                            continue
                        value = value_str
                        
                        # Special handling for different field types
                        if model_field == 'category':
                            value = value.lower()
                            if value not in ['local', 'original']:
                                errors.append(f"Category must be 'local' or 'original', got '{value}'")
                                continue
                        
                        elif model_field == 'vehicle_type':
                            value = value.lower()
                            if value not in ['two_wheeler', 'four_wheeler']:
                                errors.append(f"Vehicle Type must be 'two_wheeler' or 'four_wheeler', got '{value}'")
                                continue
                        
                        elif model_field in ['quantity', 'min_stock_level', 'price', 'mrp', 'retail_pricing', 'wholesale_price', 'distributor_price']:
                            try:
                                value = Decimal(str(value))
                                if value < 0:
                                    errors.append(f"{csv_col} cannot be negative")
                                    continue
                            except (InvalidOperation, ValueError):
                                errors.append(f"{csv_col} must be a valid number, got '{value}'")
                                continue
                        
                        elif model_field == 'warranty_period':
                            # Convert numeric months to warranty period format
                            try:
                                months = int(value)
                                if months == 0:
                                    value = 'no_warranty'
                                elif months == 1:
                                    value = '1_month'
                                elif months == 2:
                                    value = '2_month'
                                elif months == 3:
                                    value = '3_month'
                                elif months == 4:
                                    value = '4_month'
                                elif months == 5:
                                    value = '5_month'
                                elif months == 6:
                                    value = '6_month'
                                elif months == 9:
                                    value = '9_month'
                                elif months == 12:
                                    value = '12_month'
                                elif months == 24:
                                    value = '24_month'
                                else:
                                    errors.append("Warranty Period must be one of: 0, 1, 2, 3, 4, 5, 6, 9, 12, 24 months")
                                    continue
                            except ValueError:
                                # If already in format like "6_month", use as is
                                if value not in [choice[0] for choice in Inventory.WARRANTY_PERIOD_CHOICES]:
                                    errors.append(f"Invalid warranty period format: '{value}'")
                                    continue
                        
                        elif model_field == 'party_name':
                            # Lookup party by name
                            party = self.filter_queryset(Party.objects.filter(party_name__iexact=value, is_active=True)).first()
                            if party:
                                inventory_data['party'] = party.id
                            else:
                                errors.append(f"Party/Supplier '{value}' not found")
                            continue
                        
                        inventory_data[model_field] = value
                
                # Check required fields
                for req_field in required_fields:
                    if req_field not in inventory_data:
                        errors.append(f"Required field '{req_field}' is missing")
                
                if errors:
                    failed_imports.append({
                        'row': row_num,
                        'data': row,
                        'errors': errors
                     })
                    continue
                
                # Validate and create inventory item
                serializer = InventorySerializer(data=inventory_data)
                if serializer.is_valid():
                    inventory = serializer.save()
                    successful_imports.append({
                        'row': row_num,
                        'id': inventory.id,
                        'item_name': inventory.item_name,
                        'part_number': inventory.part_number
                    })
                else:
                    failed_imports.append({
                        'row': row_num,
                        'data': row,
                        'errors': serializer.errors
                    })
            
            except Exception as e:
                failed_imports.append({
                    'row': row_num,
                    'data': row,
                    'errors': [f'Unexpected error: {str(e)}']
                })
        
        # Prepare response
        response_data = {
            'total_rows': len(successful_imports) + len(failed_imports),
            'successful': len(successful_imports),
            'failed': len(failed_imports),
            'successful_imports': successful_imports,
            'failed_imports': failed_imports
        }
        
        if failed_imports:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        else:
            return Response(response_data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """
        Soft-delete inventory with role-based validation.

        - Super Admin: Can delete any inventory
        - Tenant Admin: Can delete inventory belonging to their tenant
        - Inventory Manager: Can delete inventory in their branch
        """
        from rest_framework.exceptions import PermissionDenied
        from apps.base.permission_utils import can_manage_tenant, can_manage_branch_resources

        user = self.request.user

        # Super admin can delete anything
        try:
            from apps.users.models import User
        except Exception:
            User = None

        if getattr(user, 'is_superuser', False) or (User and getattr(user, 'role', None) == User.Role.SUPER_ADMIN):
            instance.is_removed = True
            instance.save(update_fields=['is_removed', 'modified'])
            return

        # Tenant admin can delete if they manage the tenant or the branch
        # belongs to their tenant (covers records with tenant unset but branch set)
        if User and getattr(user, 'role', None) == User.Role.ADMIN:
            tenant = getattr(instance, 'tenant', None)
            branch = getattr(instance, 'branch', None)
            if can_manage_tenant(user, tenant) or can_manage_branch_resources(user, branch):
                instance.is_removed = True
                instance.save(update_fields=['is_removed', 'modified'])
                return

        # Inventory manager / branch-level check
        if User and getattr(user, 'role', None) == User.Role.INVENTORY_MANAGER:
            branch = getattr(instance, 'branch', None)
            if branch and can_manage_branch_resources(user, branch):
                instance.is_removed = True
                instance.save(update_fields=['is_removed', 'modified'])
                return

        # Otherwise deny
        raise PermissionDenied("You do not have permission to delete this inventory item.")


class InventoryImageViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing inventory images
    """
    queryset = InventoryImage.objects.filter(is_removed=False).select_related('inventory')
    serializer_class = InventoryImageSerializer
    pagination_class = StandardResultsSetPagination
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        """
        Optionally filter by inventory
        """
        queryset = InventoryImage.objects.filter(is_removed=False).select_related('inventory')
        
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
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        """
        Bulk upload images for an inventory item.
        
        POST /api/stock-management/inventory-images/bulk_upload/
        
        Form data:
        - inventory_id: ID of the inventory item
        - images: Multiple image files
        - description: (optional) Description for all images
        - is_primary: (optional) Set one as primary (default: first image)
        
        Returns: List of created image objects with full details
        """
        inventory_id = request.data.get('inventory_id')
        if not inventory_id:
            return Response(
                {'error': 'inventory_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            inventory = Inventory.objects.get(id=inventory_id, is_removed=False)
        except Inventory.DoesNotExist:
            return Response(
                {'error': f'Inventory item with id {inventory_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get multiple image files from request
        images = request.FILES.getlist('images')
        if not images:
            return Response(
                {'error': 'At least one image file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        description = request.data.get('description', '')
        is_primary_param = request.data.get('is_primary')
        
        created_images = []
        errors = []
        
        for idx, image_file in enumerate(images):
            try:
                # Determine if this should be primary
                is_primary = False
                if is_primary_param:
                    # If is_primary provided, make first image primary
                    is_primary = (idx == 0)
                elif idx == 0 and not InventoryImage.objects.filter(
                    inventory=inventory, is_primary=True
                ).exists():
                    # If no primary image exists, make first image primary
                    is_primary = True
                
                image_data = {
                    'inventory': inventory.id,
                    'image': image_file,
                    'description': description if description else f'Image {idx + 1}',
                    'is_primary': is_primary,
                }
                
                serializer = InventoryImageSerializer(
                    data=image_data,
                    context={'request': request}
                )
                
                if serializer.is_valid():
                    serializer.save()
                    created_images.append(serializer.data)
                else:
                    errors.append({
                        'image': image_file.name,
                        'errors': serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'image': image_file.name,
                    'error': str(e)
                })
        
        response_data = {
            'inventory_id': inventory_id,
            'uploaded': len(created_images),
            'failed': len(errors),
            'images': created_images,
        }
        
        if errors:
            response_data['errors'] = errors
        
        status_code = status.HTTP_201_CREATED if created_images else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)
    
    @action(detail=True, methods=['patch'], parser_classes=[MultiPartParser, FormParser])
    def update_image(self, request, pk=None):
        """
        Update an inventory image with new file and metadata.
        
        PATCH /api/stock-management/inventory-images/{id}/update_image/
        
        Form data:
        - image: New image file
        - description: (optional) New description
        - is_primary: (optional) Boolean to set as primary
        
        Returns: Updated image object
        """
        try:
            image_obj = InventoryImage.objects.get(id=pk, is_removed=False)
        except InventoryImage.DoesNotExist:
            return Response(
                {'error': f'Image with id {pk} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        image_file = request.FILES.get('image')
        if image_file:
            # Delete old image file if exists
            if image_obj.image:
                image_obj.image.delete(save=False)
            image_obj.image = image_file
        
        if 'description' in request.data:
            image_obj.description = request.data.get('description')
        
        if 'is_primary' in request.data:
            is_primary = request.data.get('is_primary').lower() == 'true'
            image_obj.is_primary = is_primary
        
        image_obj.save()
        
        serializer = InventoryImageSerializer(image_obj, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from apps.carts.models import Cart, CartItem
from apps.carts.serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
    CheckoutSerializer,
)
from apps.stock_management.models import Inventory
from apps.sales.models import SalesOrder, SalesOrderItem
from decimal import Decimal, ROUND_HALF_UP


class CartViewSet(viewsets.ViewSet):
    """
    ViewSet for managing shopping cart operations with user-level access control
    
    Endpoints:
    - GET /cart/ - View current cart (own user's cart)
    - POST /cart/add/ - Add item to cart
    - PATCH /cart/items/{id}/update/ - Update item quantity
    - DELETE /cart/items/{id}/remove/ - Remove item from cart
    - POST /cart/clear/ - Clear all items from cart
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer
    
    def get_or_create_cart(self, user):
        """Get or create cart for the current user"""
        cart, created = Cart.objects.get_or_create(
            user=user,
            defaults={'is_active': True}
        )
        return cart
    
    def list(self, request):
        """
        Get current user's cart with all items
        
        Returns cart details including items, total quantity, and subtotal
        """
        cart = self.get_or_create_cart(request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """
        Not supported - use list endpoint to view cart
        """
        return Response(
            {'detail': 'Use GET /carts/cart/ to view your cart.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    @action(detail=False, methods=['post'], url_path='add')
    def add_to_cart(self, request):
        """
        Add an item to cart or update quantity if already exists
        
        Body:
        {
            "inventory_id": 1,
            "quantity": 2.00
        }
        """
        try:
            serializer = AddToCartSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            inventory_id = serializer.validated_data['inventory_id']
            # Normalize quantity to 2 decimal places
            quantity = serializer.validated_data['quantity']
            quantity = (quantity or Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Get inventory item
            try:
                inventory = Inventory.objects.get(id=inventory_id, is_active=True, is_removed=False)
            except Inventory.DoesNotExist:
                return Response(
                    {'error': 'Inventory item not found or inactive'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check stock availability
            if inventory.quantity < quantity:
                return Response(
                    {
                        'error': 'Insufficient stock',
                        'available_quantity': float(inventory.quantity)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create cart
            cart = self.get_or_create_cart(request.user)
            
            # Get default price safely
            try:
                default_price = inventory.get_default_selling_price()
            except Exception as e:
                default_price = inventory.price if inventory.price else Decimal('0.00')
            
            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                inventory=inventory,
                defaults={
                    'quantity': quantity,
                    'price': default_price,
                    'is_active': True
                }
            )
            
            if not created:
                # Update quantity if item already exists
                new_quantity = (cart_item.quantity or Decimal('0.00')) + quantity
                new_quantity = new_quantity.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Check if new quantity exceeds available stock
                if new_quantity > inventory.quantity:
                    return Response(
                        {
                            'error': 'Insufficient stock for requested quantity',
                            'current_cart_quantity': float(cart_item.quantity),
                            'requested_additional': float(quantity),
                            'available_quantity': float(inventory.quantity)
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                cart_item.quantity = new_quantity
                cart_item.save()
                message = 'Item quantity updated in cart'
            else:
                message = 'Item added to cart successfully'
            
            # Return updated cart
            cart_serializer = CartSerializer(cart, context={'request': request})
            return Response(
                {
                    'message': message,
                    'cart': cart_serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error adding item to cart: {str(e)}", exc_info=True)
            
            return Response(
                {
                    'error': 'An error occurred while adding item to cart',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['patch'], url_path='update')
    def update_item(self, request, pk=None):
        """
        Update quantity of a specific cart item
        
        Body:
        {
            "quantity": 3.00
        }
        """
        cart = self.get_or_create_cart(request.user)
        cart_item = get_object_or_404(
            CartItem,
            id=pk,
            cart=cart
        )
        
        # Pass the cart item instance to serializer for stock validation
        serializer = UpdateCartItemSerializer(
            cart_item,
            data=request.data
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_quantity = serializer.validated_data['quantity']
        new_quantity = (new_quantity or Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        cart_item.quantity = new_quantity
        cart_item.save()
        
        # Return updated cart
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(
            {
                'message': 'Cart item updated successfully',
                'cart': cart_serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['delete'], url_path='remove')
    def remove_item(self, request, pk=None):
        """
        Remove a specific item from cart (permanent delete)
        """
        cart = self.get_or_create_cart(request.user)
        cart_item = get_object_or_404(
            CartItem,
            id=pk,
            cart=cart
        )
        
        cart_item.delete()
        
        # Return updated cart
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(
            {
                'message': 'Item removed from cart',
                'cart': cart_serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], url_path='clear')
    def clear_cart(self, request):
        """
        Clear all items from cart (permanent delete all items)
        """
        cart = self.get_or_create_cart(request.user)
        CartItem.objects.filter(cart=cart).delete()
        
        # Return updated cart
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(
            {
                'message': 'Cart cleared successfully',
                'cart': cart_serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        """
        Create an order from cart items and clear the cart.

        Body (optional):
        {
            "payment_method": "cash|card|upi|bank_transfer|credit",
            "delivery_address": "...",
            "delivery_city": "...",
            "delivery_province": "...",
            "delivery_district": "...",
            "delivery_pincode": "...",
            "notes": "..."
        }
        """
        # Validate input data
        checkout_serializer = CheckoutSerializer(data=request.data)
        if not checkout_serializer.is_valid():
            return Response(
                checkout_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        checkout_data = checkout_serializer.validated_data

        cart = self.get_or_create_cart(request.user)
        # Support selecting specific cart items via IDs
        selected_ids = checkout_data.get('selected_item_ids') or []
        if selected_ids:
            cart_items = cart.items.select_related('inventory').filter(id__in=selected_ids)
            # Ensure all provided IDs belong to this cart
            missing = set(selected_ids) - set(cart_items.values_list('id', flat=True))
            if missing:
                return Response(
                    {
                        'error': 'Some selected items were not found in your cart.',
                        'missing_item_ids': list(missing)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            cart_items = cart.items.select_related('inventory').all()
        
        # Validate cart is not empty
        if not cart_items.exists():
            return Response(
                {'error': 'Cart is empty. Add items before checkout.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate stock availability for selected items
        for cart_item in cart_items:
            if cart_item.inventory.quantity < cart_item.quantity:
                return Response(
                    {
                        'error': f'Insufficient stock for {cart_item.inventory.item_name}',
                        'item': cart_item.inventory.item_name,
                        'required': float(cart_item.quantity),
                        'available': float(cart_item.inventory.quantity)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            with transaction.atomic():
                # Create order
                order_data = {
                    'customer': request.user,
                    'created_by': request.user,
                    'tenant': request.user.tenant,
                    'delivery_address': checkout_data.get('delivery_address', ''),
                    'delivery_city': checkout_data.get('delivery_city', ''),
                    'delivery_province': checkout_data.get('delivery_province', ''),
                    'delivery_district': checkout_data.get('delivery_district', ''),
                    'delivery_pincode': checkout_data.get('delivery_pincode', ''),
                    'notes': checkout_data.get('notes', ''),
                }
                
                # Set branch if user has one
                if hasattr(request.user, 'branch') and request.user.branch:
                    order_data['branch'] = request.user.branch
                
                order = SalesOrder.objects.create(**order_data)
                
                # Create order items from selected cart items and deduct inventory
                for cart_item in cart_items:
                    order_item = SalesOrderItem.objects.create(
                        order=order,
                        tenant=order.tenant,
                        branch=order.branch,
                        inventory=cart_item.inventory,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.price,
                    )
                    # Deduct inventory immediately upon checkout
                    order_item.deduct_inventory()
                
                # Calculate order totals
                order.calculate_totals()
                
                # Generate invoice from sales order
                invoice = order.generate_invoice()
                
                # Update invoice payment method
                invoice.payment_method = checkout_data.get('payment_method', 'cash')
                invoice.save()
                
                # Remove only the selected items from the cart
                cart_items.delete()
                
                # Return order details
                from apps.sales.serializers import SalesOrderDetailSerializer
                order_serializer = SalesOrderDetailSerializer(order)
                
                return Response({
                    'message': 'Order placed successfully!',
                    'order': order_serializer.data,
                    'order_number': order.order_number,
                    'invoice_number': invoice.invoice_number,
                    'items_count': cart.items.count()
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': f'Failed to create order: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

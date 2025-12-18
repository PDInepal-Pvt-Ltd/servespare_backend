from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.carts.models import Cart, CartItem
from apps.carts.serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)
from apps.stock_management.models import Inventory
from apps.base.permission_utils import can_manage_user


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
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventory_id = serializer.validated_data['inventory_id']
        quantity = serializer.validated_data['quantity']
        
        # Get inventory item
        inventory = get_object_or_404(
            Inventory,
            id=inventory_id,
            is_active=True
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
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            inventory=inventory,
            defaults={
                'quantity': quantity,
                'price': inventory.retail_pricing,
                'is_active': True
            }
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            
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
    
    @action(detail=True, methods=['patch'], url_path='update')
    def update_item(self, request, pk=None):
        """
        Update quantity of a specific cart item
        
        Body:
        {
            "quantity": 3.00
        }
        """
        serializer = UpdateCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart = self.get_or_create_cart(request.user)
        cart_item = get_object_or_404(
            CartItem,
            id=pk,
            cart=cart
        )
        
        new_quantity = serializer.validated_data['quantity']
        
        # Check stock availability
        if cart_item.inventory.quantity < new_quantity:
            return Response(
                {
                    'error': 'Insufficient stock',
                    'available_quantity': float(cart_item.inventory.quantity)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
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

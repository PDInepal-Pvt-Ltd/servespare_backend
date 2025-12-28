from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.carts.models import Favorite
from apps.carts.serializers import (
    FavoriteSerializer,
    FavoriteListSerializer,
    AddToFavoriteSerializer,
    RemoveFromFavoriteSerializer,
)
from apps.stock_management.models import Inventory


class FavoriteViewSet(viewsets.ViewSet):
    """
    ViewSet for managing customer favorite products
    
    Endpoints:
    - GET /favorites/ - List all favorite products for current user
    - POST /favorites/add/ - Add product to favorites
    - DELETE /favorites/{id}/ - Remove favorite by ID
    - POST /favorites/remove/ - Remove product from favorites by product ID
    - GET /favorites/check/{inventory_id}/ - Check if product is favorited
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer
    
    def list(self, request):
        """
        Get all favorite products for the current user
        
        Returns:
            List of favorite products with inventory details
        """
        favorites = Favorite.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created')
        
        serializer = FavoriteListSerializer(
            favorites,
            many=True,
            context={'request': request}
        )
        return Response({
            'count': favorites.count(),
            'results': serializer.data,
            'message': 'Favorite products retrieved successfully.'
        }, status=status.HTTP_200_OK)
    
    def create(self, request):
        """
        Add product to favorites
        
        Expected payload:
        {
            "inventory_id": <int>
        }
        
        Returns:
            - 201 if product newly added
            - 200 if product was already favorited (returns message)
        """
        serializer = AddToFavoriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventory_id = serializer.validated_data['inventory_id']
        inventory = get_object_or_404(Inventory, id=inventory_id)
        
        # Use the model's method to add favorite with duplicate checking
        favorite, created, message = Favorite.add_to_favorites(
            request.user,
            inventory
        )
        
        response_serializer = FavoriteSerializer(
            favorite,
            context={'request': request}
        )
        
        if created:
            return Response({
                'data': response_serializer.data,
                'message': message,
                'newly_added': True
            }, status=status.HTTP_201_CREATED)
        else:
            # Product already exists in favorites
            return Response({
                'data': response_serializer.data,
                'message': message,
                'newly_added': False
            }, status=status.HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        """
        Remove favorite by favorite ID
        
        Args:
            pk: Favorite ID
        
        Returns:
            Success message
        """
        favorite = get_object_or_404(
            Favorite,
            id=pk,
            user=request.user,
            is_active=True
        )
        
        inventory_name = favorite.inventory.item_name
        favorite.is_active = False
        favorite.save()
        
        return Response({
            'message': f"'{inventory_name}' removed from your favorites.",
            'id': pk
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def add(self, request):
        """
        Add product to favorites (alternative endpoint)
        
        Expected payload:
        {
            "inventory_id": <int>
        }
        """
        return self.create(request)
    
    @action(detail=False, methods=['post'])
    def remove(self, request):
        """
        Remove product from favorites by inventory ID
        
        Expected payload:
        {
            "inventory_id": <int>
        }
        
        Returns:
            - 200: Successfully removed
            - 404: Product not in favorites
        """
        serializer = RemoveFromFavoriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventory_id = serializer.validated_data['inventory_id']
        inventory = get_object_or_404(Inventory, id=inventory_id)
        
        # Use the model's method to remove favorite
        success, message = Favorite.remove_from_favorites(
            request.user,
            inventory
        )
        
        if success:
            return Response({
                'message': message,
                'inventory_id': inventory_id
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': message,
                'inventory_id': inventory_id
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def check(self, request, inventory_id=None):
        """
        Check if a product is in user's favorites
        
        Query params:
        - inventory_id: Product ID to check
        
        Returns:
            {
                "is_favorite": true/false,
                "inventory_id": <int>
            }
        """
        inventory_id = request.query_params.get('inventory_id')
        
        if not inventory_id:
            return Response({
                'error': 'inventory_id query parameter is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            inventory_id = int(inventory_id)
        except ValueError:
            return Response({
                'error': 'inventory_id must be an integer.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        exists = Favorite.objects.filter(
            user=request.user,
            inventory_id=inventory_id,
            is_active=True
        ).exists()
        
        return Response({
            'is_favorite': exists,
            'inventory_id': inventory_id
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path=r'check/(?P<inventory_id>\d+)')
    def check_path_param(self, request, inventory_id=None):
        """
        Check if a product is in user's favorites (using URL path parameter)
        
        URL: /favorites/check/{inventory_id}/
        
        Returns:
            {
                "is_favorite": true/false,
                "inventory_id": <int>
            }
        """
        try:
            inventory_id = int(inventory_id)
        except (ValueError, TypeError):
            return Response({
                'error': 'inventory_id must be an integer.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify inventory exists
        get_object_or_404(Inventory, id=inventory_id)
        
        exists = Favorite.objects.filter(
            user=request.user,
            inventory_id=inventory_id,
            is_active=True
        ).exists()
        
        return Response({
            'is_favorite': exists,
            'inventory_id': inventory_id
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """
        Get the count of favorite products for current user
        
        Returns:
            {
                "count": <int>
            }
        """
        count = Favorite.objects.filter(
            user=request.user,
            is_active=True
        ).count()
        
        return Response({
            'count': count
        }, status=status.HTTP_200_OK)

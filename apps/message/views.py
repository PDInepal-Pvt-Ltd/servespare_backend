from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q

from apps.base.permissions import IsSuperAdmin, IsTenantAdmin
from .models import Message
from .serializers import MessageCreateSerializer, MessageListSerializer


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling messages from unauthorized users.
    
    - POST /api/messages/ : Create message (public, no authentication required)
    - GET /api/messages/ : List all messages (admin/support only)
    - GET /api/messages/{id}/ : Retrieve specific message (admin/support only)
    - PATCH /api/messages/{id}/ : Mark message as read (admin/support only)
    """
    queryset = Message.objects.all()
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageListSerializer
    
    def get_permissions(self):
        """
        Set permissions based on action:
        - create: Allow any (unauthenticated)
        - list, retrieve, update, partial_update, mark_as_read: Admin/Support only
        """
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            # Only super admin or tenant admin can view/manage messages
            permission_classes = [IsAuthenticated, IsSuperAdmin | IsTenantAdmin]
        
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """
        Create a new message. Public endpoint - no authentication required.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                'success': True,
                'message': 'Your message has been received. We will get back to you soon.',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, *args, **kwargs):
        """
        List all messages. Admin/Support only.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsSuperAdmin | IsTenantAdmin])
    def mark_as_read(self, request, pk=None):
        """
        Mark a message as read.
        """
        message = self.get_object()
        message.is_read = True
        message.save()
        serializer = self.get_serializer(message)
        return Response({
            'success': True,
            'message': 'Message marked as read.',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSuperAdmin | IsTenantAdmin])
    def unread_count(self, request):
        """
        Get count of unread messages.
        """
        unread_count = Message.objects.filter(is_read=False).count()
        return Response({
            'success': True,
            'unread_count': unread_count
        })


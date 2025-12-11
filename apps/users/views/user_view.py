from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_filters.rest_framework import DjangoFilterBackend

from apps.base.pagination import StandardResultsSetPagination
from apps.users.models import User
from apps.users.serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    FirstTimePasswordChangeSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserStatusUpdateSerializer,
    UserRoleUpdateSerializer,
    BulkUserActionSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional user data."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['role_display'] = user.get_role_display()
        token['full_name'] = user.full_name or user.username
        token['workspace_id'] = user.workspace_id
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Check if user must change password (except for customers)
        if self.user.must_change_password and self.user.role != 'customer':
            raise serializers.ValidationError({
                'detail': 'You must change your password before you can log in. Please use the password change endpoint first.',
                'must_change_password': True,
                'user_id': self.user.id,
                'username': self.user.username
            })
        
        # Update last login timestamp
        self.user.update_last_login()
        
        # Add user data to response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'full_name': self.user.full_name,
            'role': self.user.role,
            'role_display': self.user.get_role_display(),
            'status': self.user.status,
            'workspace_id': self.user.workspace_id,
            'must_change_password': self.user.must_change_password,
        }
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view."""
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User CRUD operations.
    
    Provides endpoints for:
    - list: Get all users
    - retrieve: Get single user
    - create: Create new user
    - update/partial_update: Update user
    - destroy: Delete user (soft delete)
    - me: Get current user profile
    - change_password: Change own password
    - reset_password: Admin reset user password
    - update_status: Update user status
    - update_role: Update user role
    - bulk_action: Perform bulk actions
    """
    
    queryset = User.objects.filter(is_removed=False)
    filterset_fields = ['role', 'status', 'is_active', 'tenant', 'workspace_id', 'is_staff']
    search_fields = ['username', 'email', 'full_name', 'phone']
    ordering_fields = ['created', 'username', 'email', 'last_login_at']
    ordering = ['-created']
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'me':
            return UserProfileSerializer
        elif self.action == 'update_profile':
            return UserProfileUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action == 'first_time_password_change':
            return FirstTimePasswordChangeSerializer
        elif self.action == 'reset_password':
            return ResetPasswordSerializer
        elif self.action == 'update_status':
            return UserStatusUpdateSerializer
        elif self.action == 'update_role':
            return UserRoleUpdateSerializer
        elif self.action == 'bulk_action':
            return BulkUserActionSerializer
        return UserDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['me', 'update_profile', 'change_password', 'first_time_password_change']:
            permission_classes = [IsAuthenticated]
        elif self.action == 'get_password_change_token':
            permission_classes = [AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy',
                             'reset_password', 'update_status', 'update_role', 'bulk_action']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Create user with created_by tracking."""
        serializer.save(created_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete user."""
        instance.is_removed = True
        instance.save(update_fields=['is_removed', 'modified'])
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current authenticated user's profile.
        
        GET /api/users/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Update current user's profile.
        
        PUT/PATCH /api/users/update_profile/
        """
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change current user's password.
        
        POST /api/users/change_password/
        Body: {old_password, new_password, new_password_confirm}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_password_change_token(self, request):
        """
        Get JWT token for password change without full login.
        
        For users with must_change_password=True who need to change their password
        before they can fully log in.
        
        POST /api/users/get_password_change_token/
        Body: {username, password}
        
        Returns JWT token that can be used with first_time_password_change endpoint.
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'User account is disabled.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user.status != User.Status.ACTIVE:
            return Response(
                {'error': f'User account is {user.get_status_display().lower()}.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is customer (customers don't use this endpoint)
        if user.role == User.Role.CUSTOMER:
            return Response(
                {'error': 'This endpoint is not for customer accounts. Use regular login.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user must change password
        if not user.must_change_password:
            return Response(
                {'error': 'You do not need to change your password. Use regular login endpoint.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate JWT token for password change
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.username
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['purpose'] = 'password_change'
        
        return Response({
            'message': 'Token issued. Use this token to change your password.',
            'token': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'role_display': user.get_role_display(),
                'must_change_password': True
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def first_time_password_change(self, request):
        """
        Change password using JWT authentication.
        
        This endpoint is used for:
        1. First-time login password change (after email with credentials)
        2. Password recovery after OTP verification
        
        User must provide JWT token (from OTP verification or special recovery token).
        
        POST /api/users/first_time_password_change/
        Headers: Authorization: Bearer <jwt_token>
        Body: {new_password, new_password_confirm}
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate fresh JWT tokens for the user after password change
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.username
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['role_display'] = user.get_role_display()
        refresh['workspace_id'] = user.workspace_id
        
        return Response({
            'message': 'Password changed successfully. You can now log in with your new password.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'role_display': user.get_role_display(),
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def reset_password(self, request, pk=None):
        """
        Admin resets user password.
        
        POST /api/users/{id}/reset_password/
        Body: {new_password, must_change_password}
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(
            {'message': f'Password reset successfully for user {user.username}.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def update_status(self, request, pk=None):
        """
        Update user status (active/inactive/suspended).
        
        POST /api/users/{id}/update_status/
        Body: {status}
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(
            {'message': f'User status updated to {user.get_status_display()}.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def update_role(self, request, pk=None):
        """
        Update user role.
        
        POST /api/users/{id}/update_role/
        Body: {role}
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(
            {'message': f'User role updated to {user.get_role_display()}.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def activate(self, request, pk=None):
        """
        Activate user account.
        
        POST /api/users/{id}/activate/
        """
        user = self.get_object()
        user.activate_account()
        return Response(
            {'message': f'User {user.username} activated successfully.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def deactivate(self, request, pk=None):
        """
        Deactivate user account.
        
        POST /api/users/{id}/deactivate/
        """
        user = self.get_object()
        user.deactivate_account()
        return Response(
            {'message': f'User {user.username} deactivated successfully.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def suspend(self, request, pk=None):
        """
        Suspend user account.
        
        POST /api/users/{id}/suspend/
        """
        user = self.get_object()
        user.suspend_account()
        return Response(
            {'message': f'User {user.username} suspended successfully.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def bulk_action(self, request):
        """
        Perform bulk actions on multiple users.
        
        POST /api/users/bulk_action/
        Body: {user_ids: [1,2,3], action: 'activate'|'deactivate'|'suspend'|'delete'}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_ids = serializer.validated_data['user_ids']
        action_type = serializer.validated_data['action']
        
        users = User.objects.filter(id__in=user_ids)
        count = users.count()
        
        if action_type == 'activate':
            users.update(status=User.Status.ACTIVE, is_active=True)
            message = f'{count} user(s) activated successfully.'
        elif action_type == 'deactivate':
            users.update(status=User.Status.INACTIVE, is_active=False)
            message = f'{count} user(s) deactivated successfully.'
        elif action_type == 'suspend':
            users.update(status=User.Status.SUSPENDED, is_active=False)
            message = f'{count} user(s) suspended successfully.'
        elif action_type == 'delete':
            users.update(is_removed=True)
            message = f'{count} user(s) deleted successfully.'
        
        return Response({'message': message}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request):
        """
        Get user statistics.
        
        GET /api/users/stats/
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total_users': queryset.count(),
            'active_users': queryset.filter(status=User.Status.ACTIVE).count(),
            'inactive_users': queryset.filter(status=User.Status.INACTIVE).count(),
            'suspended_users': queryset.filter(status=User.Status.SUSPENDED).count(),
            'by_role': {
                'super_admin': queryset.filter(role=User.Role.SUPER_ADMIN).count(),
                'admin': queryset.filter(role=User.Role.ADMIN).count(),
                'cashier': queryset.filter(role=User.Role.CASHIER).count(),
                'inventory_manager': queryset.filter(role=User.Role.INVENTORY_MANAGER).count(),
                'customer': queryset.filter(role=User.Role.CUSTOMER).count(),
            },
            'must_change_password': queryset.filter(must_change_password=True).count(),
        }
        
        return Response(stats)


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for authentication operations.
    
    Provides endpoints for:
    - register: User registration
    - login: User login with JWT
    - logout: User logout (blacklist token)
    - refresh: Refresh JWT token
    """
    
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register a new user.
        
        POST /api/auth/register/
        Body: {username, email, password, password_confirm, full_name, ...}
        """
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'User registered successfully.',
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Login user and return JWT tokens.
        
        POST /api/auth/login/
        Body: {username, password}
        """
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'User account is disabled.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user.status != User.Status.ACTIVE:
            return Response(
                {'error': f'User account is {user.get_status_display().lower()}.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If user must change password, do not issue JWT tokens; return guidance only
        if user.must_change_password:
            return Response({
                'message': 'User must change password.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'role_display': user.get_role_display(),
                    'status': user.status,
                    'workspace_id': user.workspace_id,
                    'must_change_password': user.must_change_password,
                }
            }, status=status.HTTP_200_OK)

        # Update last login
        user.update_last_login()
        
        # Generate JWT tokens with custom claims
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.username
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['role_display'] = user.get_role_display()
        refresh['workspace_id'] = user.workspace_id
        
        response_data = {
            'message': 'Login successful.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'role_display': user.get_role_display(),
                'status': user.status,
                'workspace_id': user.workspace_id,
                'must_change_password': user.must_change_password,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout user by blacklisting refresh token.
        
        POST /api/auth/logout/
        Body: {refresh_token}
        """
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Logout successful.'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Invalid token or token already blacklisted.'},
                status=status.HTTP_400_BAD_REQUEST
            )

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.users.models import User
from apps.users.utils import (
    send_password_change_notification_email,
    send_welcome_credentials_email,
)
from apps.tenant.serializers import TenantSerializer
from apps.base.serializer_mixins import ModelCleanValidationMixin


def _validate_branch_with_tenant(attrs, instance=None):
    """Ensure selected branch belongs to the provided tenant."""
    branch = attrs.get('branch')
    tenant = attrs.get('tenant')

    if instance:
        branch = branch or getattr(instance, 'branch', None)
        tenant = tenant or getattr(instance, 'tenant', None)

    # If a branch is provided without tenant, fall back to the branch's tenant
    if branch and tenant is None:
        attrs['tenant'] = branch.tenant
        tenant = branch.tenant

    if branch and tenant and branch.tenant_id != tenant.id:
        raise serializers.ValidationError({
            'branch': 'Branch must belong to the selected tenant.'
        })

    return attrs


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users (minimal fields)."""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'role', 'role_display',
            'status', 'status_display', 'is_active', 'tenant', 'branch', 'branch_name',
            'workspace_id', 'created', 'last_login_at'
        ]
        read_only_fields = ['id', 'created', 'last_login_at']


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed user information."""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    groups_list = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'first_name', 'last_name',
            'phone', 'location', 'avatar', 'tenant', 'branch', 'branch_name', 'workspace_id',
            'role', 'role_display', 'status', 'status_display',
            'is_active', 'is_staff', 'is_superuser',
            'must_change_password',
            'last_login', 'last_login_at', 'date_joined',
            'created', 'modified', 'created_by', 'created_by_username',
            'groups_list'
        ]
        read_only_fields = [
            'id', 'last_login', 'last_login_at', 'date_joined',
            'created', 'modified', 'is_removed'
        ]
    
    def get_groups_list(self, obj):
        """Get list of group names."""
        return list(obj.groups.values_list('name', flat=True))


class UserCreateSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """Serializer for creating new users by admin/super admin.
    
    Allows super admin/admin users to assign roles to newly created users.
    Users default to CUSTOMER role if not specified.
    Includes model-level validation from User.clean() method.
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'full_name', 'first_name', 'last_name', 'phone', 'location',
            'avatar', 'tenant', 'branch', 'workspace_id',
            'role', 'status', 'is_active', 'created_by'
        ]
        extra_kwargs = {
            'email': {'required': False},
            'role': {'required': False},
            'branch': {'required': False, 'allow_null': True},
        }
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Password fields do not match.'
            })
        return _validate_branch_with_tenant(attrs)
    
    def create(self, validated_data):
        """Create user with hashed password and send welcome email.
        
        Allows super admin/admin to assign roles. Defaults to CUSTOMER if not specified.
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Default role to CUSTOMER if not provided by admin/super admin
        role = validated_data.get('role', User.Role.CUSTOMER)
        if 'role' not in validated_data:
            validated_data['role'] = User.Role.CUSTOMER
        
        # Ensure customers and super admins do NOT need to change password on first login
        if role in [User.Role.CUSTOMER, User.Role.SUPER_ADMIN]:
            validated_data['must_change_password'] = False
        else:
            validated_data['must_change_password'] = True
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Send welcome email with credentials (not for customers)
        if user.role != User.Role.CUSTOMER and user.email:
            send_welcome_credentials_email(user, password)
        
        return user


class UserUpdateSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """Serializer for updating user information.
    Includes model-level validation from User.clean() method.
    """
    
    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'first_name', 'last_name', 'phone', 'location',
            'avatar', 'tenant', 'branch', 'workspace_id',
            'role', 'status', 'is_active', 'is_staff',
            'must_change_password'
        ]

    def validate(self, attrs):
        """Ensure branch belongs to the selected tenant when updating."""
        return _validate_branch_with_tenant(attrs, instance=self.instance)
    
    def update(self, instance, validated_data):
        """Update user and sync role to groups if changed."""
        role_changed = 'role' in validated_data and validated_data['role'] != instance.role
        
        instance = super().update(instance, validated_data)
        
        # Sync role to groups if role was changed
        if role_changed:
            instance._sync_role_to_group()
        
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """Validate old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value
    
    def validate(self, attrs):
        """Validate new password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Password fields do not match.'
            })
        return attrs
    
    def save(self, **kwargs):
        """Update user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password', 'modified'])
        send_password_change_notification_email(user)
        return user


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for admin resetting user password."""
    
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    must_change_password = serializers.BooleanField(default=True)
    
    def save(self, user, **kwargs):
        """Reset user password."""
        user.set_password(self.validated_data['new_password'])
        user.must_change_password = self.validated_data['must_change_password']
        user.save(update_fields=['password', 'must_change_password', 'modified'])
        return user


class FirstTimePasswordChangeSerializer(serializers.Serializer):
    """Serializer for first-time password change using JWT authentication.
    
    This endpoint is used for:
    1. First-time login password change (after receiving credentials email)
    2. Password recovery after OTP verification
    
    User must be authenticated via JWT token (from OTP verification or initial login attempt).
    """
    
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate passwords."""
        # Check if new passwords match
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Password fields do not match.'
            })
        
        # Get user from context (provided by view from JWT token)
        user = self.context.get('request').user
        
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({
                'detail': 'Authentication required.'
            })
        
        # Check if user is customer (customers don't have forced password change)
        if user.role == User.Role.CUSTOMER:
            raise serializers.ValidationError({
                'detail': 'This endpoint is not for customer accounts.'
            })
        
        attrs['user'] = user
        return attrs
    
    def save(self, **kwargs):
        """Update user password and clear must_change_password flag."""
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password', 'modified'])
        send_password_change_notification_email(user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user's own profile."""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'first_name', 'last_name',
            'phone', 'location', 'avatar', 'tenant', 'branch', 'branch_name', 'workspace_id',
            'role', 'role_display', 'status', 'status_display',
            'must_change_password',
            'last_login_at', 'date_joined', 'created'
        ]
        read_only_fields = [
            'id', 'username', 'role', 'status', 'branch',
            'must_change_password', 'last_login_at', 'date_joined', 'created'
        ]


class UserProfileUpdateSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """Serializer for users to update their own profile."""
    
    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'first_name', 'last_name',
            'phone', 'location', 'avatar', 'tenant'
        ]


class UserStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating user status."""
    
    status = serializers.ChoiceField(
        choices=User.Status.choices,
        required=True
    )
    
    def save(self, user, **kwargs):
        """Update user status."""
        status = self.validated_data['status']
        
        if status == User.Status.ACTIVE:
            user.activate_account()
        elif status == User.Status.INACTIVE:
            user.deactivate_account()
        elif status == User.Status.SUSPENDED:
            user.suspend_account()
        
        return user


class UserRoleUpdateSerializer(serializers.Serializer):
    """Serializer for updating user role."""
    
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        required=True
    )
    
    def save(self, user, **kwargs):
        """Update user role and sync to groups."""
        role = self.validated_data['role']
        user.set_role(role)
        return user


class BulkUserActionSerializer(serializers.Serializer):
    """Serializer for bulk user actions."""
    
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'suspend', 'delete'],
        required=True
    )
    
    def validate_user_ids(self, value):
        """Validate user IDs exist."""
        existing_ids = User.objects.filter(id__in=value).values_list('id', flat=True)
        existing_ids = list(existing_ids)
        
        if len(existing_ids) != len(value):
            invalid_ids = set(value) - set(existing_ids)
            raise serializers.ValidationError(
                f'Users with IDs {invalid_ids} do not exist.'
            )
        
        return value


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class UserRegistrationSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """Serializer for user self-registration."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'full_name', 'first_name', 'last_name', 'phone', 'location', 'role'
        ]
        extra_kwargs = {
            'role': {'required': False},
        }
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Password fields do not match.'
            })
        return attrs
    
    def create(self, validated_data):
        """Create user with default customer role or assigned role by super admin."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Default role for self-registration is CUSTOMER (if not provided)
        if 'role' not in validated_data:
            validated_data['role'] = User.Role.CUSTOMER

        # Ensure customers and super admins do NOT need to change password on first login
        if validated_data.get('role') in [User.Role.CUSTOMER, User.Role.SUPER_ADMIN]:
            validated_data['must_change_password'] = False
        else:
            validated_data['must_change_password'] = True

        validated_data['status'] = User.Status.ACTIVE
        validated_data['is_active'] = True

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class AdminAccountSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """
    Serializer for listing admin accounts with tenant and subscription information.
    Shows admin details along with their tenant's subscription package and user count.
    """
    tenant_detail = TenantSerializer(source='tenant', read_only=True)
    tenant_name = serializers.CharField(source='tenant.business_name', read_only=True)
    subscription_name = serializers.SerializerMethodField()
    tenant_user_count = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'phone',
            'role',
            'role_display',
            'status',
            'status_display',
            'tenant',
            'tenant_detail',
            'tenant_name',
            'branch',
            'branch_name',
            'subscription_name',
            'tenant_user_count',
            'is_active',
            'created',
            'last_login_at'
        ]
        read_only_fields = ['id', 'branch', 'branch_name', 'created', 'last_login_at']
    
    def get_subscription_name(self, obj):
        """Get the subscription/package name for the admin's tenant"""
        if obj.tenant and obj.tenant.package:
            return obj.tenant.package.plan_name
        return None
    
    def get_tenant_user_count(self, obj):
        """Get the total number of users in the admin's tenant"""
        if obj.tenant:
            return obj.tenant.get_user_count()
        return 0


class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for customer profile with order and favorites statistics.
    Provides total orders, active orders (excluding delivered and cancelled), and favorites count.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_orders = serializers.SerializerMethodField()
    active_orders = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'phone',
            'location',
            'avatar',
            'branch',
            'branch_name',
            'role',
            'role_display',
            'status',
            'status_display',
            'total_orders',
            'active_orders',
            'favorites_count',
            'last_login_at',
            'date_joined',
            'created'
        ]
        read_only_fields = [
            'id', 'username', 'role', 'status',
            'branch', 'branch_name',
            'last_login_at', 'date_joined', 'created',
            'total_orders', 'active_orders', 'favorites_count'
        ]
    
    def get_total_orders(self, obj):
        """Get total number of orders placed by customer"""
        return obj.sales_orders.count()
    
    def get_active_orders(self, obj):
        """Get count of active orders (excluding delivered and cancelled)"""
        return obj.sales_orders.exclude(
            order_status__in=['delivered', 'cancelled']
        ).count()
    
    def get_favorites_count(self, obj):
        """Get count of customer's favorite items"""
        return obj.favorites.filter(is_active=True).count()

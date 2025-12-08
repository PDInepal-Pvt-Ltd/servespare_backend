# User Model & Role-Based Access Control

## Overview

Custom User model with role-based access control using a choice field that syncs with Django Groups.

### Available Roles

1. **Super Admin** (`super_admin`) - Full system access with all permissions
2. **Admin** (`admin`) - Administrative access to manage users and settings
3. **Cashier** (`cashier`) - Access to sales and customer transactions
4. **Inventory Manager** (`inventory_manager`) - Manage inventory, stock, and suppliers

## Authentication

- Uses **username** for login (default Django behavior)
- Email is optional and not unique
- Username must be unique across all users

## User Model Fields

### Core Fields
- `username` - Unique username (used for login)
- `email` - Email address (optional, not unique)
- `password` - Hashed password
- `role` - User role (choice field): `super_admin`, `admin`, `cashier`, `inventory_manager`
- `full_name` - User's full name
- `first_name`, `last_name` - Optional name fields

### Contact & Workspace
- `phone` - Contact phone number
- `workspace_id` - Workspace identifier for multi-tenancy

### Status & Security
- `status` - User account status: `active`, `inactive`, `suspended`
- `is_active` - Boolean flag for account activation
- `must_change_password` - Force password change on next login
- `last_login_at` - Timestamp of last successful login

### Profile & Tracking
- `avatar` - URL or path to user avatar image
- `created_by` - Reference to user who created this account

## Setup & Migration

```powershell
# Create migrations
python manage.py makemigrations users

# Apply migrations (this will create role groups automatically)
python manage.py migrate

# Create superuser (requires username, email, and password)
python manage.py createsuperuser
```

## Role Management

### Using Management Commands

```powershell
# Assign a role to a user (by username)
python manage.py assign_role john_doe admin
python manage.py assign_role cashier1 cashier

# Available role values:
# - super_admin
# - admin
# - cashier
# - inventory_manager
```

### Programmatic Usage

```python
from apps.users.models import User

# Get or create user
user = User.objects.get(username='john_doe')

# Set role (automatically syncs with Django Groups)
user.set_role('admin')  # or User.Role.ADMIN
user.set_role(User.Role.CASHIER)

# Check roles
if user.is_admin():
    print("User is an admin")

if user.role == User.Role.CASHIER:
    print("User is a cashier")

# Get role information
role_display = user.get_role()  # Returns "Admin"
role_value = user.get_role_value()  # Returns "admin"
```

### Role Checking Methods

```python
user.is_super_admin()        # Check if Super Admin or superuser
user.is_admin()              # Check if Admin (or Super Admin)
user.is_cashier()            # Check if Cashier
user.is_inventory_manager()  # Check if Inventory Manager

# Direct role comparison
if user.role == User.Role.ADMIN:
    pass
```

## Permission System

Permissions are automatically assigned to groups during migration. The role field automatically syncs with Django Groups.

- **Super Admin**: All permissions
- **Admin**: User management (add, change, delete, view users)
- **Cashier**: View users + transaction permissions
- **Inventory Manager**: View users + inventory permissions

When you set a user's role, they are automatically added to the corresponding group with appropriate permissions.

### Using Permissions in Views

```python
from django.contrib.auth.decorators import permission_required, login_required

@login_required
@permission_required('users.change_user', raise_exception=True)
def edit_user(request, user_id):
    # Only users with 'change_user' permission can access
    pass
```

### Using Permissions in Templates

```django
{% if perms.users.add_user %}
    <a href="{% url 'add_user' %}">Add User</a>
{% endif %}
```

## Helper Methods

### Account Status
```python
user.is_account_active()      # Check if account is fully active
user.activate_account()        # Activate user account
user.deactivate_account()      # Deactivate user account
user.suspend_account()         # Suspend user account
```

### Login Tracking
```python
user.mark_first_login_complete()  # Mark first login as done
user.update_last_login()          # Update last login timestamp
```

### Workspace
```python
user.has_workspace()  # Check if user belongs to workspace
```

## Admin Interface

Access the Django admin to:
- Manage users and assign roles
- Bulk activate/deactivate/suspend users
- View audit trails
- Manage permissions

Admin URL: `/admin/users/user/`

## Creating Users

### Via Admin Panel
1. Go to `/admin/users/user/add/`
2. Enter username, email (optional), and password
3. Select role from dropdown
4. Fill additional fields
5. Save (role automatically syncs to groups)

### Programmatically
```python
from apps.users.models import User

# Create regular user
user = User.objects.create_user(
    username='john_doe',
    email='john@example.com',
    password='secure_password',
    full_name='John Doe',
    phone='+1234567890',
    role=User.Role.CASHIER
)

# Set role after creation
user.set_role(User.Role.ADMIN)

# Create superuser
admin = User.objects.create_superuser(
    username='admin',
    email='admin@example.com',
    password='admin_password',
    full_name='Admin User'
)
```

## Best Practices

1. **Use role field** - Set user.role to manage access levels
2. **Role auto-syncs with Groups** - Groups are automatically managed based on role field
3. **Use role checking methods** - `user.is_admin()` instead of checking role directly
4. **Track login activity** - Use `update_last_login()` in your authentication flow
5. **Force password changes** - Set `must_change_password=True` for security
6. **Workspace isolation** - Use `workspace_id` to filter data per tenant

## Security Considerations

- Passwords are automatically hashed using Django's password hashers
- Email validation is enforced at the database level
- Status constraints prevent invalid values
- Soft delete capability via `is_removed` field
- Audit trail with `created_by`, `created`, `modified` fields

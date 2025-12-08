# Quick Start Guide - User API with JWT

## Prerequisites

```powershell
# Install required packages (if not already installed)
pip install djangorestframework-simplejwt django-filter

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Test the API

### 1. Start Development Server
```powershell
python manage.py runserver
```

### 2. Test Endpoints

#### **Get JWT Token (Login)**
```powershell
# Using curl (PowerShell)
curl -X POST http://localhost:8000/api/token/ `
  -H "Content-Type: application/json" `
  -d '{\"username\": \"admin\", \"password\": \"your_password\"}'
```

#### **List Users**
```powershell
curl -X GET http://localhost:8000/api/users/ `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### **Get Current User Profile**
```powershell
curl -X GET http://localhost:8000/api/users/me/ `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### **Register New User**
```powershell
curl -X POST http://localhost:8000/api/auth/register/ `
  -H "Content-Type: application/json" `
  -d '{
    \"username\": \"testuser\",
    \"email\": \"test@example.com\",
    \"password\": \"SecurePass123!\",
    \"password_confirm\": \"SecurePass123!\",
    \"full_name\": \"Test User\"
  }'
```

#### **Create User (Admin Only)**
```powershell
curl -X POST http://localhost:8000/api/users/ `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{
    \"username\": \"newuser\",
    \"email\": \"new@example.com\",
    \"password\": \"SecurePass123!\",
    \"password_confirm\": \"SecurePass123!\",
    \"full_name\": \"New User\",
    \"role\": \"cashier\"
  }'
```

## Available Endpoints

### Authentication
- `POST /api/token/` - Login (get JWT tokens)
- `POST /api/token/refresh/` - Refresh access token
- `POST /api/token/verify/` - Verify token validity
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Alternative login endpoint
- `POST /api/auth/logout/` - Logout (blacklist token)

### User Management
- `GET /api/users/` - List users (with filters)
- `GET /api/users/{id}/` - Get user detail
- `POST /api/users/` - Create user (admin)
- `PUT /api/users/{id}/` - Update user (admin)
- `PATCH /api/users/{id}/` - Partial update (admin)
- `DELETE /api/users/{id}/` - Soft delete user (admin)

### Profile Management
- `GET /api/users/me/` - Get my profile
- `PUT /api/users/update_profile/` - Update my profile
- `PATCH /api/users/update_profile/` - Partial update profile

### Password Management
- `POST /api/users/change_password/` - Change own password
- `POST /api/users/{id}/reset_password/` - Reset user password (admin)

### User Actions (Admin Only)
- `POST /api/users/{id}/activate/` - Activate user
- `POST /api/users/{id}/deactivate/` - Deactivate user
- `POST /api/users/{id}/suspend/` - Suspend user
- `POST /api/users/{id}/update_status/` - Update status
- `POST /api/users/{id}/update_role/` - Update role
- `POST /api/users/bulk_action/` - Bulk actions

### Statistics
- `GET /api/users/stats/` - Get user statistics

## Query Parameters for List Users

```
/api/users/?role=admin&status=active&search=john&ordering=-created&page=1
```

- **role**: `super_admin`, `admin`, `cashier`, `inventory_manager`
- **status**: `active`, `inactive`, `suspended`
- **is_active**: `true`, `false`
- **workspace_id**: Filter by workspace
- **search**: Search in multiple fields
- **ordering**: Sort by field (prefix with `-` for descending)
- **page**: Page number
- **page_size**: Items per page

## Role Values

When creating/updating users, use these role values:
- `super_admin` - Super Admin
- `admin` - Admin
- `cashier` - Cashier
- `inventory_manager` - Inventory Manager

## Status Values

- `active` - Active
- `inactive` - Inactive
- `suspended` - Suspended

## JWT Token Structure

Access tokens include custom claims:
```json
{
  "token_type": "access",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "abc123",
  "user_id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "admin",
  "role_display": "Admin",
  "full_name": "John Doe",
  "workspace_id": "ws_123"
}
```

## Testing with Postman

1. **Import Collection**: Create requests for each endpoint
2. **Set Environment Variables**:
   - `base_url`: `http://localhost:8000`
   - `access_token`: (Set after login)
3. **Add Authorization**: Bearer Token with `{{access_token}}`

## Testing with Django Admin

Access: `http://localhost:8000/admin/`

- View/manage users
- Assign roles via groups
- View user statistics
- Perform bulk actions

## Common Issues

### Token Expired
**Error:** `Token is expired`
**Solution:** Use refresh token endpoint to get new access token

### Permission Denied
**Error:** `You do not have permission to perform this action`
**Solution:** Ensure user has admin privileges for admin-only endpoints

### Invalid Credentials
**Error:** `Invalid username or password`
**Solution:** Verify credentials are correct

### Account Disabled
**Error:** `User account is disabled`
**Solution:** Admin must activate the account

## Development Tips

1. **Always include Authorization header** for protected endpoints
2. **Use refresh token** to get new access token before expiry
3. **Logout properly** by blacklisting refresh token
4. **Filter and search** to optimize list queries
5. **Check user stats** endpoint for dashboard data
6. **Use bulk actions** for multiple user operations
7. **Role changes** automatically sync with Django Groups
8. **Soft delete** keeps user data for audit purposes

## Production Checklist

- [ ] Change SECRET_KEY in production
- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use secure JWT signing key
- [ ] Set appropriate token lifetimes
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Configure logging
- [ ] Set up monitoring

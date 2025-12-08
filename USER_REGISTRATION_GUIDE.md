# User Registration Guide

## Overview
This guide explains how to register new users in the ServeIQ system through the REST API.

---

## Registration Endpoint

### URL
```
POST /api/auth/register/
```

### Base URL
```
http://127.0.0.1:8000/api/auth/register/
```

### HTTP Method
- **POST**

---

## Required Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `username` | String | Unique username for login (3-150 chars) | ✅ Yes |
| `email` | Email | Valid email address | ✅ Yes |
| `password` | String | Password (minimum 8 chars, not numeric) | ✅ Yes |
| `password_confirm` | String | Password confirmation (must match password) | ✅ Yes |
| `full_name` | String | User's full name | ❌ Optional |
| `first_name` | String | User's first name | ❌ Optional |
| `last_name` | String | User's last name | ❌ Optional |
| `phone` | String | Contact phone number | ❌ Optional |
| `role` | String | User role (see roles below) | ❌ Optional (defaults to `cashier`) |

---

## Available Roles

```
- super_admin          → Super Admin (full system access)
- admin                → Admin (manage users and settings)
- cashier              → Cashier (sales and transactions)
- inventory_manager    → Inventory Manager (inventory management)
```

---

## Request Example

### Basic Registration (Minimal)
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

### Full Registration (All Fields)
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "full_name": "John Doe",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "role": "cashier"
  }'
```

### Registration with Admin Role
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin_user",
    "email": "admin@example.com",
    "password": "AdminPass123!",
    "password_confirm": "AdminPass123!",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

---

## Success Response (201 Created)

```json
{
  "message": "User registered successfully.",
  "user": {
    "id": 2,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "avatar": null,
    "tenant": null,
    "workspace_id": null,
    "role": "cashier",
    "role_display": "Cashier",
    "status": "active",
    "status_display": "Active",
    "must_change_password": true,
    "last_login_at": null,
    "date_joined": "2025-12-08T12:50:00.000000Z",
    "created": "2025-12-08T12:50:00.000000Z"
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

## Error Responses

### 400 Bad Request - Validation Error
```json
{
  "username": ["This field may not be blank."],
  "email": ["Enter a valid email address."],
  "password": ["This password is too short. It must contain at least 8 characters."]
}
```

### 400 Bad Request - Duplicate Username
```json
{
  "username": ["A user with that username already exists."]
}
```

### 400 Bad Request - Passwords Don't Match
```json
{
  "password_confirm": "Password fields do not match."
}
```

---

## Password Requirements

✅ **Valid Password Examples:**
- `SecurePass123!`
- `MyP@ssw0rd2025`
- `ComplexPassword99`

❌ **Invalid Passwords:**
- `password` (too common)
- `12345678` (entirely numeric)
- `short` (less than 8 characters)

---

## Important Notes

### Default Values
- **Status**: `active` (user can immediately access the system)
- **Role**: `cashier` (if not specified)
- **must_change_password**: `true` (user must change password on first login)
- **is_active**: `true`

### After Registration
1. User receives access and refresh JWT tokens
2. User can login with username and password
3. User MUST change their password on first login (due to `must_change_password: true`)
4. User belongs to a Django Group based on their role

### Token Usage
Use the `access` token in the Authorization header for subsequent API requests:

```bash
Authorization: Bearer {access_token}
```

---

## Using Registered Tokens

### Immediate Token Usage
```bash
curl -X GET http://127.0.0.1:8000/api/users/me/ \
  -H "Authorization: Bearer {access_token}"
```

### Token Refresh
```bash
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "{refresh_token}"
  }'
```

---

## Next Steps for New Users

1. **Change Password** (Required on first login)
   ```
   POST /api/users/change_password/
   Body: {old_password, new_password, new_password_confirm}
   ```

2. **Update Profile**
   ```
   PATCH /api/users/update_profile/
   Body: {email, full_name, phone, avatar, tenant}
   ```

3. **View Own Profile**
   ```
   GET /api/users/me/
   ```

---

## Admin Registration

Only admins with `IsAdminUser` permission can create users via:
```
POST /api/users/
```

This endpoint provides more control and bypasses some restrictions for admin-created accounts.

---

## Security Best Practices

1. ✅ Always use HTTPS in production
2. ✅ Never expose refresh tokens in logs
3. ✅ Store tokens securely in client (localStorage/sessionStorage with caution)
4. ✅ Implement token rotation
5. ✅ Use strong, unique passwords
6. ✅ Validate email addresses
7. ✅ Implement rate limiting for registration

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Username already exists" | Choose a unique username |
| "Invalid email address" | Provide a valid email format (user@example.com) |
| "Password too short" | Use at least 8 characters |
| "Passwords don't match" | Ensure password and password_confirm are identical |
| "This password is too common" | Choose a more complex password with numbers/symbols |

---

## Related Endpoints

- **Login**: `POST /api/auth/login/`
- **Token Obtain**: `POST /api/token/`
- **User List**: `GET /api/users/`
- **User Detail**: `GET /api/users/{id}/`
- **Update User**: `PATCH /api/users/{id}/`
- **Delete User**: `DELETE /api/users/{id}/`


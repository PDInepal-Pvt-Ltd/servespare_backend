# User API Documentation

## Base URL
```
http://localhost:8000/api/
```

## Authentication
All endpoints (except registration and login) require JWT authentication.

**Headers:**
```
Authorization: Bearer <access_token>
```

---

## JWT Token Endpoints

### 1. Login (Get JWT Tokens)
**Endpoint:** `POST /api/token/`

**Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbG...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbG...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "admin",
    "role_display": "Admin",
    "status": "active",
    "workspace_id": "ws_123",
    "must_change_password": false
  }
}
```

### 2. Refresh Token
**Endpoint:** `POST /api/token/refresh/`

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbG..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbG..."
}
```

### 3. Verify Token
**Endpoint:** `POST /api/token/verify/`

**Body:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbG..."
}
```

**Response:**
```json
{}
```

---

## Auth Endpoints

### 1. Register
**Endpoint:** `POST /api/auth/register/`

**Permission:** Public (No authentication required)

**Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "full_name": "John Doe",
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "message": "User registered successfully.",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "cashier",
    "role_display": "Cashier"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbG...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbG..."
  }
}
```

### 2. Login
**Endpoint:** `POST /api/auth/login/`

**Permission:** Public (No authentication required)

**Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response:** Same as token endpoint

### 3. Logout
**Endpoint:** `POST /api/auth/logout/`

**Permission:** Authenticated users

**Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbG..."
}
```

**Response:**
```json
{
  "message": "Logout successful."
}
```

---

## User Endpoints

### 1. List Users
**Endpoint:** `GET /api/users/`

**Permission:** Authenticated users

**Query Parameters:**
- `role`: Filter by role (`super_admin`, `admin`, `cashier`, `inventory_manager`)
- `status`: Filter by status (`active`, `inactive`, `suspended`)
- `is_active`: Filter by active status (`true`, `false`)
- `workspace_id`: Filter by workspace
- `search`: Search in username, email, full_name, phone, business_name
- `ordering`: Order by field (`created`, `-created`, `username`, `email`, etc.)
- `page`: Page number
- `page_size`: Items per page

**Example:**
```
GET /api/users/?role=admin&status=active&search=john&ordering=-created
```

**Response:**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "full_name": "John Doe",
      "role": "admin",
      "role_display": "Admin",
      "status": "active",
      "status_display": "Active",
      "is_active": true,
      "workspace_id": "ws_123",
      "created": "2025-12-08T10:00:00Z",
      "last_login_at": "2025-12-08T15:30:00Z"
    }
  ]
}
```

### 2. Get User Detail
**Endpoint:** `GET /api/users/{id}/`

**Permission:** Authenticated users

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "avatar": "https://example.com/avatar.jpg",
  "workspace_id": "ws_123",
  "role": "admin",
  "role_display": "Admin",
  "status": "active",
  "status_display": "Active",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "must_change_password": false,
  "last_login": "2025-12-08T15:30:00Z",
  "last_login_at": "2025-12-08T15:30:00Z",
  "date_joined": "2025-12-01T10:00:00Z",
  "created": "2025-12-01T10:00:00Z",
  "modified": "2025-12-08T15:30:00Z",
  "created_by": 2,
  "created_by_username": "admin",
  "groups_list": ["Admin"]
}
```

### 3. Create User
**Endpoint:** `POST /api/users/`

**Permission:** Admin users only

**Body:**
```json
{
  "username": "jane_doe",
  "email": "jane@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "full_name": "Jane Doe",
  "phone": "+1234567890",
  "role": "cashier",
  "status": "active",
  "workspace_id": "ws_123"
}
```

**Response:** User detail object

### 4. Update User
**Endpoint:** `PUT /api/users/{id}/` or `PATCH /api/users/{id}/`

**Permission:** Admin users only

**Body:**
```json
{
  "full_name": "Jane Smith",
  "phone": "+9876543210",
  "role": "admin",
  "status": "active"
}
```

**Response:** Updated user detail object

### 5. Delete User (Soft Delete)
**Endpoint:** `DELETE /api/users/{id}/`

**Permission:** Admin users only

**Response:** `204 No Content`

---

## Profile Endpoints

### 1. Get My Profile
**Endpoint:** `GET /api/users/me/`

**Permission:** Authenticated users

**Response:** Current user's profile

### 2. Update My Profile
**Endpoint:** `PUT /api/users/update_profile/` or `PATCH /api/users/update_profile/`

**Permission:** Authenticated users

**Body:**
```json
{
  "full_name": "John Smith",
  "phone": "+1234567890",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

**Response:** Updated profile

---

## Password Endpoints

### 1. Change Password
**Endpoint:** `POST /api/users/change_password/`

**Permission:** Authenticated users

**Body:**
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!",
  "new_password_confirm": "NewPass123!"
}
```

**Response:**
```json
{
  "message": "Password changed successfully."
}
```

### 2. Reset User Password (Admin)
**Endpoint:** `POST /api/users/{id}/reset_password/`

**Permission:** Admin users only

**Body:**
```json
{
  "new_password": "TempPass123!",
  "must_change_password": true
}
```

**Response:**
```json
{
  "message": "Password reset successfully for user john_doe."
}
```

---

## User Management Endpoints

### 1. Update User Status
**Endpoint:** `POST /api/users/{id}/update_status/`

**Permission:** Admin users only

**Body:**
```json
{
  "status": "suspended"
}
```

**Options:** `active`, `inactive`, `suspended`

**Response:**
```json
{
  "message": "User status updated to Suspended."
}
```

### 2. Update User Role
**Endpoint:** `POST /api/users/{id}/update_role/`

**Permission:** Admin users only

**Body:**
```json
{
  "role": "admin"
}
```

**Options:** `super_admin`, `admin`, `cashier`, `inventory_manager`

**Response:**
```json
{
  "message": "User role updated to Admin."
}
```

### 3. Activate User
**Endpoint:** `POST /api/users/{id}/activate/`

**Permission:** Admin users only

**Response:**
```json
{
  "message": "User john_doe activated successfully."
}
```

### 4. Deactivate User
**Endpoint:** `POST /api/users/{id}/deactivate/`

**Permission:** Admin users only

**Response:**
```json
{
  "message": "User john_doe deactivated successfully."
}
```

### 5. Suspend User
**Endpoint:** `POST /api/users/{id}/suspend/`

**Permission:** Admin users only

**Response:**
```json
{
  "message": "User john_doe suspended successfully."
}
```

---

## Bulk Actions

### Bulk User Action
**Endpoint:** `POST /api/users/bulk_action/`

**Permission:** Admin users only

**Body:**
```json
{
  "user_ids": [1, 2, 3, 4],
  "action": "activate"
}
```

**Actions:** `activate`, `deactivate`, `suspend`, `delete`

**Response:**
```json
{
  "message": "4 user(s) activated successfully."
}
```

---

## Statistics

### Get User Statistics
**Endpoint:** `GET /api/users/stats/`

**Permission:** Authenticated users

**Response:**
```json
{
  "total_users": 150,
  "active_users": 120,
  "inactive_users": 20,
  "suspended_users": 10,
  "by_role": {
    "super_admin": 2,
    "admin": 10,
    "cashier": 100,
    "inventory_manager": 38
  },
  "first_time_users": 5,
  "must_change_password": 3
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Usage Examples

### Using cURL

**Login:**
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "password": "SecurePass123!"}'
```

**Get Users:**
```bash
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbG..."
```

**Create User:**
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbG..." \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_doe",
    "email": "jane@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "full_name": "Jane Doe",
    "role": "cashier"
  }'
```

### Using Python requests

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/token/',
    json={'username': 'john_doe', 'password': 'SecurePass123!'}
)
tokens = response.json()
access_token = tokens['access']

# Get users
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://localhost:8000/api/users/', headers=headers)
users = response.json()
```

### Using JavaScript fetch

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/token/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'john_doe',
    password: 'SecurePass123!'
  })
});
const { access } = await loginResponse.json();

// Get users
const usersResponse = await fetch('http://localhost:8000/api/users/', {
  headers: { 'Authorization': `Bearer ${access}` }
});
const users = await usersResponse.json();
```

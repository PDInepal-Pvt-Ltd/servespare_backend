# Tenant API Documentation

## Base URL
```
/api/tenant/
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

---

## Endpoints

### 1. List Tenants
**GET** `/api/tenant/tenants/`

Get a list of all tenants.

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `inactive`, `suspended`, `trial`)
- `package` (optional): Filter by subscription plan ID
- `is_active` (optional): Filter by active status (`true`/`false`)
- `search` (optional): Search by business name or email

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "business_name": "ABC Corporation",
    "email": "contact@abccorp.com",
    "phone": "+1234567890",
    "package": 1,
    "package_detail": {
      "id": 1,
      "plan_name": "Premium Plan",
      "plan_price": "99.99",
      "no_of_user": 10,
      "no_of_branch": 5,
      "support_type": "email",
      "is_active": true,
      "created": "2025-12-08T10:00:00Z",
      "modified": "2025-12-08T10:00:00Z"
    },
    "status": "active",
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  }
]
```

---

### 2. Create Tenant
**POST** `/api/tenant/tenants/`

Create a new tenant.

**Request Body:**
```json
{
  "business_name": "ABC Corporation",
  "email": "contact@abccorp.com",
  "phone": "+1234567890",
  "package": 1,
  "status": "active"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "business_name": "ABC Corporation",
  "email": "contact@abccorp.com",
  "phone": "+1234567890",
  "package": 1,
  "package_detail": {
    "id": 1,
    "plan_name": "Premium Plan",
    "plan_price": "99.99",
    "no_of_user": 10,
    "no_of_branch": 5,
    "support_type": "email",
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  },
  "status": "active",
  "is_active": true,
  "created": "2025-12-08T10:00:00Z",
  "modified": "2025-12-08T10:00:00Z"
}
```

**Field Descriptions:**
- `business_name` (required): Name of the business/tenant
- `email` (required, unique): Email address
- `phone` (optional): Phone number
- `package` (optional): Subscription plan ID (Foreign Key)
- `status` (optional): Status - `active`, `inactive`, `suspended`, `trial` (default: `trial`)

---

### 3. Get Tenant
**GET** `/api/tenant/tenants/{id}/`

Get details of a specific tenant.

**Response:** `200 OK`
```json
{
  "id": 1,
  "business_name": "ABC Corporation",
  "email": "contact@abccorp.com",
  "phone": "+1234567890",
  "package": 1,
  "package_detail": {
    "id": 1,
    "plan_name": "Premium Plan",
    "plan_price": "99.99",
    "no_of_user": 10,
    "no_of_branch": 5,
    "support_type": "email",
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  },
  "status": "active",
  "is_active": true,
  "created": "2025-12-08T10:00:00Z",
  "modified": "2025-12-08T10:00:00Z"
}
```

---

### 4. Update Tenant
**PUT** `/api/tenant/tenants/{id}/` (Full update)
**PATCH** `/api/tenant/tenants/{id}/` (Partial update)

Update tenant information.

**Request Body (PATCH):**
```json
{
  "status": "active",
  "phone": "+1234567891"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "business_name": "ABC Corporation",
  "email": "contact@abccorp.com",
  "phone": "+1234567891",
  "package": 1,
  "package_detail": { ... },
  "status": "active",
  "is_active": true,
  "created": "2025-12-08T10:00:00Z",
  "modified": "2025-12-08T11:00:00Z"
}
```

---

### 5. Delete Tenant
**DELETE** `/api/tenant/tenants/{id}/`

Delete a tenant (soft delete).

**Response:** `204 No Content`

---

### 6. Get Active Tenants
**GET** `/api/tenant/tenants/active/`

Get all active tenants (is_active=true and status=active).

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "business_name": "ABC Corporation",
    "email": "contact@abccorp.com",
    ...
  }
]
```

---

### 7. Get Tenants by Status
**GET** `/api/tenant/tenants/by_status/?status={status}`

Get tenants filtered by status.

**Query Parameters:**
- `status` (required): `active`, `inactive`, `suspended`, or `trial`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "business_name": "ABC Corporation",
    "status": "active",
    ...
  }
]
```

---

### 8. Get Trial Tenants
**GET** `/api/tenant/tenants/trial/`

Get all tenants with trial status.

**Response:** `200 OK`
```json
[
  {
    "id": 2,
    "business_name": "XYZ Ltd",
    "status": "trial",
    ...
  }
]
```

---

## Data Format

### Tenant Object
```json
{
  "id": 1,
  "business_name": "string (required, max 255 chars)",
  "email": "string (required, unique, email format)",
  "phone": "string (optional, max 20 chars)",
  "package": "integer (optional, FK to SubscriptionPlan)",
  "package_detail": {
    "id": 1,
    "plan_name": "string",
    "plan_price": "decimal",
    "no_of_user": "integer",
    "no_of_branch": "integer",
    "support_type": "string (email|phone|chat|ticket)",
    "is_active": "boolean",
    "created": "datetime",
    "modified": "datetime"
  },
  "status": "string (active|inactive|suspended|trial, default: trial)",
  "is_active": "boolean (default: true)",
  "created": "datetime (read-only)",
  "modified": "datetime (read-only)"
}
```

---

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Validation Rules

- `business_name`: Required, cannot be empty
- `email`: Required, must be unique, valid email format
- `status`: Must be one of: `active`, `inactive`, `suspended`, `trial`


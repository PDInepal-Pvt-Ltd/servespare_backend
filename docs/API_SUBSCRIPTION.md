# Subscription API Documentation

## Base URL
```
/api/subscription/
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

---

## Endpoints Overview

### Subscription Plans
- `/api/subscription/subscription-plans/` - Manage subscription plans

### Subscriptions
- `/api/subscription/subscriptions/` - Manage tenant subscriptions

---

## 1. SUBSCRIPTION PLANS API

### List Subscription Plans
**GET** `/api/subscription/subscription-plans/`

Get a list of all subscription plans.

**Query Parameters:**
- `is_active` (optional): Filter by active status (`true`/`false`)
- `search` (optional): Search by plan name

**Response:** `200 OK`
```json
[
  {
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
  {
    "id": 2,
    "plan_name": "Basic Plan",
    "plan_price": "49.99",
    "no_of_user": 5,
    "no_of_branch": 2,
    "support_type": "email",
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  }
]
```

---

### Create Subscription Plan
**POST** `/api/subscription/subscription-plans/`

Create a new subscription plan.

**Request Body:**
```json
{
  "plan_name": "Premium Plan",
  "plan_price": "99.99",
  "no_of_user": 10,
  "no_of_branch": 5,
  "support_type": "email"
}
```

**Field Descriptions:**
- `plan_name` (required): Name of the subscription plan (unique)
- `plan_price` (required): Price of the plan (must be > 0)
- `no_of_user` (required): Maximum number of users (must be > 0)
- `no_of_branch` (required): Maximum number of branches (must be > 0)
- `support_type` (required): Type of support - `email`, `phone`, `chat`, `ticket` (default: `email`)

**Response:** `201 Created`
```json
{
  "id": 1,
  "plan_name": "Premium Plan",
  "plan_price": "99.99",
  "no_of_user": 10,
  "no_of_branch": 5,
  "support_type": "email",
  "is_active": true,
  "created": "2025-12-08T10:00:00Z",
  "modified": "2025-12-08T10:00:00Z"
}
```

---

### Get Subscription Plan
**GET** `/api/subscription/subscription-plans/{id}/`

Get details of a specific subscription plan.

**Response:** `200 OK`
```json
{
  "id": 1,
  "plan_name": "Premium Plan",
  "plan_price": "99.99",
  "no_of_user": 10,
  "no_of_branch": 5,
  "support_type": "email",
  "is_active": true,
  "created": "2025-12-08T10:00:00Z",
  "modified": "2025-12-08T10:00:00Z"
}
```

---

### Update Subscription Plan
**PUT** `/api/subscription/subscription-plans/{id}/` (Full update)
**PATCH** `/api/subscription/subscription-plans/{id}/` (Partial update)

Update subscription plan information.

**Request Body (PATCH):**
```json
{
  "plan_price": "89.99",
  "no_of_user": 15
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "plan_name": "Premium Plan",
  "plan_price": "89.99",
  "no_of_user": 15,
  "no_of_branch": 5,
  "support_type": "email",
  "is_active": true,
  "created": "2025-12-08T10:00:00Z",
  "modified": "2025-12-08T11:00:00Z"
}
```

---

### Delete Subscription Plan
**DELETE** `/api/subscription/subscription-plans/{id}/`

Delete a subscription plan (soft delete).

**Response:** `204 No Content`

---

### Get Active Subscription Plans
**GET** `/api/subscription/subscription-plans/active/`

Get all active subscription plans.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "plan_name": "Premium Plan",
    "plan_price": "99.99",
    ...
  }
]
```

---

## 2. SUBSCRIPTIONS API

### List Subscriptions
**GET** `/api/subscription/subscriptions/`

Get a list of all subscriptions.

**Query Parameters:**
- `tenant` (optional): Filter by tenant ID
- `plan` (optional): Filter by subscription plan ID
- `is_active` (optional): Filter by active status (`true`/`false`)
- `active_only` (optional): `true` to get only non-expired subscriptions

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "tenant": 1,
    "tenant_detail": {
      "id": 1,
      "business_name": "ABC Corporation",
      "email": "contact@abccorp.com"
    },
    "subscription_plan": 1,
    "subscription_plan_detail": {
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
    "subscription_date": "2025-12-01",
    "finish_date": "2025-12-31",
    "renew_date": "2026-01-01",
    "is_active": true,
    "created": "2025-12-08T10:00:00Z",
    "modified": "2025-12-08T10:00:00Z"
  }
]
```

---

### Create Subscription
**POST** `/api/subscription/subscriptions/`

Create a new subscription linking a tenant to a subscription plan.

**Request Body:**
```json
{
  "tenant": 1,
  "subscription_plan": 1,
  "subscription_date": "2025-12-01",
  "finish_date": "2025-12-31",
  "renew_date": "2026-01-01"
}
```

**Field Descriptions:**
- `tenant` (required): Tenant ID (Foreign Key)
- `subscription_plan` (required): Subscription Plan ID (Foreign Key)
- `subscription_date` (required): Date when subscription starts
- `finish_date` (required): Date when subscription ends (must be after subscription_date)
- `renew_date` (optional): Date for renewal (should be on or after finish_date)

**Response:** `201 Created`
```json
{
  "id": 1,
  "tenant": 1,
  "tenant_detail": {
    "id": 1,
    "business_name": "ABC Corporation",
    "email": "contact@abccorp.com"
  },
  "subscription_plan": 1,
  "subscription_plan_detail": {
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
  "subscription_date": "2025-12-01",
  "finish_date": "2025-12-31",
  "renew_date": "2026-01-01",
  "is_active": true,
  "created": "2025-12-08T10:00:00Z",
  "modified": "2025-12-08T10:00:00Z"
}
```

**Validation Rules:**
- `finish_date` must be after `subscription_date`
- `renew_date` should be on or after `finish_date`
- Unique constraint: tenant + subscription_plan + subscription_date

---

### Get Subscription
**GET** `/api/subscription/subscriptions/{id}/`

Get details of a specific subscription.

**Response:** `200 OK`
```json
{
  "id": 1,
  "tenant": 1,
  "tenant_detail": {
    "id": 1,
    "business_name": "ABC Corporation",
    "email": "contact@abccorp.com"
  },
  "subscription_plan": 1,
  "subscription_plan_detail": {
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
  "subscription_date": "2025-12-01",
  "finish_date": "2025-12-31",
  "renew_date": "2026-01-01",
  "is_active": true,
  "created": "2025-12-08T10:00:00Z",
  "modified": "2025-12-08T10:00:00Z"
}
```

---

### Update Subscription
**PUT** `/api/subscription/subscriptions/{id}/` (Full update)
**PATCH** `/api/subscription/subscriptions/{id}/` (Partial update)

Update subscription information.

**Request Body (PATCH):**
```json
{
  "finish_date": "2026-01-31",
  "renew_date": "2026-02-01"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "tenant": 1,
  "subscription_plan": 1,
  "subscription_date": "2025-12-01",
  "finish_date": "2026-01-31",
  "renew_date": "2026-02-01",
  "is_active": true,
  "created": "2025-12-08T10:00:00Z",
  "modified": "2025-12-08T11:00:00Z"
}
```

---

### Delete Subscription
**DELETE** `/api/subscription/subscriptions/{id}/`

Delete a subscription (soft delete).

**Response:** `204 No Content`

---

### Get Active Subscriptions
**GET** `/api/subscription/subscriptions/active/`

Get all active (non-expired) subscriptions where current date is between subscription_date and finish_date.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "tenant": 1,
    "subscription_plan": 1,
    "subscription_date": "2025-12-01",
    "finish_date": "2025-12-31",
    ...
  }
]
```

---

### Get Expired Subscriptions
**GET** `/api/subscription/subscriptions/expired/`

Get all expired subscriptions where finish_date < current date.

**Response:** `200 OK`
```json
[
  {
    "id": 2,
    "tenant": 2,
    "subscription_plan": 1,
    "subscription_date": "2025-11-01",
    "finish_date": "2025-11-30",
    ...
  }
]
```

---

### Get Subscriptions by Tenant
**GET** `/api/subscription/subscriptions/by_tenant/?tenant_id={id}`

Get all subscriptions for a specific tenant.

**Query Parameters:**
- `tenant_id` (required): Tenant ID

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "tenant": 1,
    "subscription_plan": 1,
    "subscription_date": "2025-12-01",
    "finish_date": "2025-12-31",
    ...
  }
]
```

---

## Data Formats

### Subscription Plan Object
```json
{
  "id": 1,
  "plan_name": "string (required, unique, max 255 chars)",
  "plan_price": "decimal (required, must be > 0)",
  "no_of_user": "integer (required, must be > 0)",
  "no_of_branch": "integer (required, must be > 0)",
  "support_type": "string (required, email|phone|chat|ticket, default: email)",
  "is_active": "boolean (default: true)",
  "created": "datetime (read-only)",
  "modified": "datetime (read-only)"
}
```

### Subscription Object
```json
{
  "id": 1,
  "tenant": "integer (required, FK to Tenant)",
  "tenant_detail": {
    "id": 1,
    "business_name": "string",
    "email": "string"
  },
  "subscription_plan": "integer (required, FK to SubscriptionPlan)",
  "subscription_plan_detail": {
    "id": 1,
    "plan_name": "string",
    "plan_price": "decimal",
    "no_of_user": "integer",
    "no_of_branch": "integer",
    "support_type": "string",
    "is_active": "boolean",
    "created": "datetime",
    "modified": "datetime"
  },
  "subscription_date": "date (required, format: YYYY-MM-DD)",
  "finish_date": "date (required, must be after subscription_date)",
  "renew_date": "date (optional, should be >= finish_date)",
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

### Subscription Plan
- `plan_name`: Required, must be unique, max 255 characters
- `plan_price`: Required, must be greater than zero
- `no_of_user`: Required, must be greater than zero
- `no_of_branch`: Required, must be greater than zero
- `support_type`: Required, must be one of: `email`, `phone`, `chat`, `ticket`

### Subscription
- `tenant`: Required, must be a valid tenant ID
- `subscription_plan`: Required, must be a valid subscription plan ID
- `subscription_date`: Required, valid date format
- `finish_date`: Required, must be after `subscription_date`
- `renew_date`: Optional, should be on or after `finish_date`
- Unique constraint: Cannot have duplicate subscription for same tenant, plan, and subscription_date


# Updated Password Change Flow - JWT Token Based

## Overview

The password change system now uses **JWT token-based authentication** instead of username/password for better security and consistency with OTP verification flow.

---

## Complete User Flows

### Flow 1: New User First-Time Login (After Receiving Credentials Email)

```
1. Admin creates user
   ↓
2. User receives email with username & temporary password
   ↓
3. User tries regular login → BLOCKED ❌
   ↓
4. User requests password change token
   POST /api/users/get_password_change_token/
   Body: {username, password: temporary_password}
   ↓
5. Receives JWT token
   ↓
6. User changes password using JWT token
   POST /api/users/first_time_password_change/
   Headers: Authorization: Bearer <token>
   Body: {new_password, new_password_confirm}
   ↓
7. Receives new JWT tokens + password changed ✅
   ↓
8. User can now login normally
```

### Flow 2: Password Recovery via OTP

```
1. User requests OTP
   POST /api/otp/request/
   Body: {identifier: username_or_email}
   ↓
2. User receives OTP via email
   ↓
3. User verifies OTP
   POST /api/otp/verify/
   Body: {otp: code}
   ↓
4. Receives JWT token for password reset
   ↓
5. User changes password using JWT token
   POST /api/users/first_time_password_change/
   Headers: Authorization: Bearer <token>
   Body: {new_password, new_password_confirm}
   ↓
6. Receives new JWT tokens + password changed ✅
   ↓
7. User can now login normally
```

---

## API Endpoints

### 1. Get Password Change Token (New Endpoint)

**Endpoint:** `POST /api/users/get_password_change_token/`

**Authentication:** None required (public endpoint)

**Purpose:** Get JWT token for users with `must_change_password=True` so they can change their password

**Request:**
```json
{
  "username": "john_doe",
  "password": "TemporaryPass123!"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Token issued. Use this token to change your password.",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 123,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "cashier",
    "role_display": "Cashier",
    "must_change_password": true
  }
}
```

**Error Responses:**

Invalid credentials (401):
```json
{
  "error": "Invalid username or password."
}
```

User doesn't need password change (400):
```json
{
  "error": "You do not need to change your password. Use regular login endpoint."
}
```

Customer account (400):
```json
{
  "error": "This endpoint is not for customer accounts. Use regular login."
}
```

---

### 2. First-Time Password Change (Updated)

**Endpoint:** `POST /api/users/first_time_password_change/`

**Authentication:** **Required** - JWT token (from `get_password_change_token` or OTP verification)

**Purpose:** Change password for first-time login or after OTP verification

**Request:**
```http
POST /api/users/first_time_password_change/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

{
  "new_password": "NewSecurePass@456",
  "new_password_confirm": "NewSecurePass@456"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Password changed successfully. You can now log in with your new password.",
  "user": {
    "id": 123,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "cashier",
    "role_display": "Cashier"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Error Responses:**

No authentication (401):
```json
{
  "detail": "Authentication credentials were not provided."
}
```

Passwords don't match (400):
```json
{
  "new_password_confirm": ["Password fields do not match."]
}
```

Customer account (400):
```json
{
  "detail": "This endpoint is not for customer accounts."
}
```

---

### 3. OTP Verification (Existing)

**Endpoint:** `POST /api/otp/verify/`

**Authentication:** None required

**Request:**
```json
{
  "otp": "123456"
}
```

**Success Response (200 OK):**
```json
{
  "message": "OTP verified successfully. Use the token to reset your password.",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_at": "2025-12-09T12:30:00Z",
  "expires_in": 900
}
```

**Note:** This token can be used with the `first_time_password_change` endpoint.

---

### 4. Regular Login (Existing - Blocks if must_change_password=true)

**Endpoint:** `POST /api/token/`

**Request:**
```json
{
  "username": "john_doe",
  "password": "password"
}
```

**Blocked Response (400 Bad Request) - if must_change_password=true:**
```json
{
  "detail": "You must change your password before you can log in. Please use the password change endpoint first.",
  "must_change_password": true,
  "user_id": 123,
  "username": "john_doe"
}
```

---

## Complete Testing Examples

### Scenario 1: New User First-Time Login

```bash
# Step 1: Admin creates user (you'll need admin token)
curl -X POST http://localhost:8000/api/users/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_cashier",
    "email": "cashier@example.com",
    "password": "TempPass123!",
    "password_confirm": "TempPass123!",
    "role": "cashier",
    "full_name": "New Cashier"
  }'

# Step 2: User tries to login (WILL FAIL)
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_cashier",
    "password": "TempPass123!"
  }'

# Step 3: User gets password change token
curl -X POST http://localhost:8000/api/users/get_password_change_token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_cashier",
    "password": "TempPass123!"
  }'
# Save the "token" from response

# Step 4: User changes password with token
curl -X POST http://localhost:8000/api/users/first_time_password_change/ \
  -H "Authorization: Bearer YOUR_TOKEN_FROM_STEP_3" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "MyNewSecure@Pass456",
    "new_password_confirm": "MyNewSecure@Pass456"
  }'

# Step 5: User can now login normally
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_cashier",
    "password": "MyNewSecure@Pass456"
  }'
```

### Scenario 2: Password Recovery via OTP

```bash
# Step 1: Request OTP
curl -X POST http://localhost:8000/api/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "john_doe"
  }'

# Step 2: Check console/email for OTP code

# Step 3: Verify OTP
curl -X POST http://localhost:8000/api/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "otp": "123456"
  }'
# Save the "token" from response

# Step 4: Change password with OTP token
curl -X POST http://localhost:8000/api/users/first_time_password_change/ \
  -H "Authorization: Bearer YOUR_TOKEN_FROM_STEP_3" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "MyNewSecure@Pass789",
    "new_password_confirm": "MyNewSecure@Pass789"
  }'

# Step 5: Login with new password
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "MyNewSecure@Pass789"
  }'
```

---

## Frontend Implementation Guide

### First-Time Login Flow

```javascript
// 1. User submits login form
async function handleLogin(username, password) {
  try {
    const response = await fetch('/api/token/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    if (response.ok) {
      // Normal login success
      const data = await response.json();
      saveTokens(data.tokens);
      redirectToDashboard();
    } else {
      const error = await response.json();
      
      // Check if password change required
      if (error.must_change_password) {
        // Get password change token
        const tokenResponse = await fetch('/api/users/get_password_change_token/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        
        const tokenData = await tokenResponse.json();
        
        // Redirect to password change page with token
        redirectToPasswordChange(tokenData.token);
      }
    }
  } catch (error) {
    console.error('Login failed:', error);
  }
}

// 2. User changes password
async function handlePasswordChange(token, newPassword, confirmPassword) {
  try {
    const response = await fetch('/api/users/first_time_password_change/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        new_password: newPassword,
        new_password_confirm: confirmPassword
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      saveTokens(data.tokens);
      showSuccess('Password changed successfully!');
      redirectToDashboard();
    } else {
      const error = await response.json();
      showError(error.detail || 'Password change failed');
    }
  } catch (error) {
    console.error('Password change failed:', error);
  }
}
```

### Password Recovery Flow

```javascript
// 1. Request OTP
async function requestOTP(identifier) {
  const response = await fetch('/api/otp/request/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ identifier })
  });
  
  if (response.ok) {
    showMessage('OTP sent to your email');
    showOTPVerificationForm();
  }
}

// 2. Verify OTP
async function verifyOTP(otpCode) {
  const response = await fetch('/api/otp/verify/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ otp: otpCode })
  });
  
  if (response.ok) {
    const data = await response.json();
    // Use the token for password change
    redirectToPasswordChange(data.token);
  }
}

// 3. Change password (same function as above)
// Use handlePasswordChange(token, newPassword, confirmPassword)
```

---

## Key Changes from Previous Version

| Aspect | Old Approach | New Approach |
|--------|-------------|--------------|
| **Authentication** | Username + current password | JWT token |
| **Endpoint Access** | Public (AllowAny) | Requires JWT authentication |
| **Token Source** | N/A | `get_password_change_token` or OTP verification |
| **Request Body** | `username`, `current_password`, `new_password`, `new_password_confirm` | `new_password`, `new_password_confirm` |
| **Security** | Password sent in every request | Token-based, password sent once |
| **OTP Integration** | Separate flow | Unified flow |

---

## Benefits of JWT Token Approach

1. **Better Security** - Password sent only once to get token
2. **Consistent Flow** - Same endpoint for both first-time and OTP recovery
3. **Token Expiry** - OTP tokens expire after 15 minutes
4. **Stateless** - No session management needed
5. **Mobile-Friendly** - Token can be stored securely in mobile apps
6. **Audit Trail** - Token contains user info and purpose

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Authentication credentials were not provided" | No Bearer token in header | Include `Authorization: Bearer <token>` header |
| "Invalid username or password" | Wrong credentials | Verify username and password |
| "You do not need to change your password" | `must_change_password=false` | Use regular login endpoint |
| "This endpoint is not for customer accounts" | Customer role | Customers use regular login |
| "Token has expired" | OTP token expired (>15 min) | Request new OTP |
| "Password fields do not match" | Passwords don't match | Ensure both passwords are identical |

---

## Security Considerations

### Token Lifetimes

- **Password Change Token:** Uses default JWT expiry (usually 5 minutes)
- **OTP Verification Token:** 15 minutes
- **Regular Access Token:** 5 minutes (configurable)
- **Refresh Token:** 24 hours (configurable)

### Best Practices

1. **Store tokens securely** - Use httpOnly cookies or secure storage
2. **Clear tokens after use** - Delete password change tokens after successful change
3. **Implement rate limiting** - Prevent brute force on `get_password_change_token`
4. **Log password changes** - Track all password change attempts
5. **Notify users** - Send email notification after password change

---

## Files Modified

1. **`apps/users/serializers/user_serializers.py`**
   - Updated `FirstTimePasswordChangeSerializer` to use JWT authentication
   - Removed username/current_password fields
   - Added request context validation

2. **`apps/users/views/user_view.py`**
   - Added `get_password_change_token` endpoint
   - Updated `first_time_password_change` to require authentication
   - Updated permissions configuration

---

For the complete previous documentation, see `PASSWORD_MANAGEMENT_GUIDE.md`

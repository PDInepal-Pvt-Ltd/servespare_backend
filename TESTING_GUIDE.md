# Test Guide: OTP Password Change System

## ✅ System is Ready!

All code is implemented. Follow these steps to test:

---

## Test Scenario 1: Password Recovery via OTP

### Step 1: Request OTP
```bash
curl -X POST http://localhost:8000/api/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test_user@example.com"
  }'
```

**Expected Response:**
```json
{
  "message": "If an account exists, a recovery code has been sent."
}
```

**Check console** for OTP code (development mode prints to console)

---

### Step 2: Verify OTP
```bash
curl -X POST http://localhost:8000/api/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "otp": "123456"
  }'
```

**Expected Response:**
```json
{
  "message": "OTP verified successfully. Use the token to reset your password.",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_at": "2025-12-09T12:30:00Z",
  "expires_in": 900
}
```

**Save the token!**

---

### Step 3: Change Password with JWT Token
```bash
curl -X POST http://localhost:8000/api/users/first_time_password_change/ \
  -H "Authorization: Bearer YOUR_TOKEN_FROM_STEP_2" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "MyNewSecure@Pass123",
    "new_password_confirm": "MyNewSecure@Pass123"
  }'
```

**Expected Response:**
```json
{
  "message": "Password changed successfully. You can now log in with your new password.",
  "user": {
    "id": 1,
    "username": "test_user",
    "email": "test_user@example.com",
    "full_name": "Test User",
    "role": "cashier",
    "role_display": "Cashier"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### Step 4: Login with New Password
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "MyNewSecure@Pass123"
  }'
```

**Expected Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}
```

✅ **SUCCESS!**

---

## Test Scenario 2: First-Time User Login

### Step 1: Admin Creates User
```bash
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
```

**Check console** for welcome email with credentials

---

### Step 2: User Tries Login (Will Fail)
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_cashier",
    "password": "TempPass123!"
  }'
```

**Expected Response (Error):**
```json
{
  "detail": "You must change your password before you can log in. Please use the password change endpoint first.",
  "must_change_password": true,
  "user_id": 2,
  "username": "new_cashier"
}
```

---

### Step 3: Get Password Change Token
```bash
curl -X POST http://localhost:8000/api/users/get_password_change_token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_cashier",
    "password": "TempPass123!"
  }'
```

**Expected Response:**
```json
{
  "message": "Token issued. Use this token to change your password.",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 2,
    "username": "new_cashier",
    "email": "cashier@example.com",
    "full_name": "New Cashier",
    "role": "cashier",
    "role_display": "Cashier",
    "must_change_password": true
  }
}
```

---

### Step 4: Change Password
```bash
curl -X POST http://localhost:8000/api/users/first_time_password_change/ \
  -H "Authorization: Bearer YOUR_TOKEN_FROM_STEP_3" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "MyNewSecure@Pass456",
    "new_password_confirm": "MyNewSecure@Pass456"
  }'
```

**Expected Response:**
```json
{
  "message": "Password changed successfully. You can now log in with your new password.",
  "user": {...},
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

---

### Step 5: Login with New Password
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_cashier",
    "password": "MyNewSecure@Pass456"
  }'
```

✅ **SUCCESS!**

---

## Quick Python Test Script

```python
import requests

BASE_URL = "http://localhost:8000"

def test_otp_flow():
    # Step 1: Request OTP
    response = requests.post(f"{BASE_URL}/api/otp/request/", json={
        "identifier": "test@example.com"
    })
    print("OTP Request:", response.json())
    
    # Step 2: Get OTP from console and verify
    otp_code = input("Enter OTP code from console: ")
    response = requests.post(f"{BASE_URL}/api/otp/verify/", json={
        "otp": otp_code
    })
    data = response.json()
    print("OTP Verify:", data)
    token = data['token']
    
    # Step 3: Change password
    response = requests.post(
        f"{BASE_URL}/api/users/first_time_password_change/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "new_password": "NewPass@123",
            "new_password_confirm": "NewPass@123"
        }
    )
    print("Password Change:", response.json())
    
    # Step 4: Login
    response = requests.post(f"{BASE_URL}/api/token/", json={
        "username": "test_user",
        "password": "NewPass@123"
    })
    print("Login:", response.json())

if __name__ == "__main__":
    test_otp_flow()
```

---

## Status Check

✅ **OTP Request** - Checks email in database, sends OTP  
✅ **OTP Verify** - Validates OTP, returns JWT token  
✅ **Password Change** - Uses JWT, changes password  
✅ **New User Flow** - Blocks login, requires password change  
✅ **Email Notifications** - Welcome email sent to new users  

---

## All Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/otp/request/` | None | Request OTP |
| POST | `/api/otp/verify/` | None | Verify OTP, get JWT |
| POST | `/api/users/get_password_change_token/` | None | Get JWT for new users |
| POST | `/api/users/first_time_password_change/` | JWT | Change password |
| POST | `/api/token/` | None | Regular login |
| POST | `/api/users/` | Admin | Create user |

---

## 🚀 Ready to Test!

Run the Django server and try the test scenarios above.

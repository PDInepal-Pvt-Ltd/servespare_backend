# Quick Reference: JWT-Based Password Change

## Two Main Flows

### 🔐 Flow 1: First-Time User Login

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Admin Creates User                                       │
│    POST /api/users/                                         │
│    → Email sent with username + temp password               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. User Tries Login (BLOCKED ❌)                            │
│    POST /api/token/                                         │
│    Response: "must change password first"                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. User Gets Password Change Token                          │
│    POST /api/users/get_password_change_token/               │
│    Body: {username, password}                               │
│    → Returns JWT token                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. User Changes Password                                    │
│    POST /api/users/first_time_password_change/              │
│    Headers: Authorization: Bearer <token>                   │
│    Body: {new_password, new_password_confirm}               │
│    → Returns new JWT tokens                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. User Logs In Normally ✅                                 │
│    POST /api/token/                                         │
│    Body: {username, new_password}                           │
│    → Success!                                               │
└─────────────────────────────────────────────────────────────┘
```

---

### 🔓 Flow 2: Password Recovery (OTP)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Requests OTP                                        │
│    POST /api/otp/request/                                   │
│    Body: {identifier: "username_or_email"}                  │
│    → OTP sent to email                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. User Verifies OTP                                        │
│    POST /api/otp/verify/                                    │
│    Body: {otp: "123456"}                                    │
│    → Returns JWT token (15 min expiry)                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. User Changes Password                                    │
│    POST /api/users/first_time_password_change/              │
│    Headers: Authorization: Bearer <token_from_otp>          │
│    Body: {new_password, new_password_confirm}               │
│    → Returns new JWT tokens                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. User Logs In with New Password ✅                        │
│    POST /api/token/                                         │
│    Body: {username, new_password}                           │
│    → Success!                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick API Reference

### Get Password Change Token
```http
POST /api/users/get_password_change_token/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "TempPass123!"
}
```
**Returns:** JWT token for password change

---

### Change Password (with JWT)
```http
POST /api/users/first_time_password_change/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "new_password": "NewSecure@Pass456",
  "new_password_confirm": "NewSecure@Pass456"
}
```
**Returns:** New JWT tokens + success message

---

### Verify OTP
```http
POST /api/otp/verify/
Content-Type: application/json

{
  "otp": "123456"
}
```
**Returns:** JWT token (valid 15 minutes)

---

## Key Points

✅ **Both flows use the same password change endpoint**  
✅ **JWT token required for password change**  
✅ **Token sources:**
   - First-time: `get_password_change_token`
   - Recovery: `otp/verify`
   
✅ **After password change:**
   - New JWT tokens issued immediately
   - `must_change_password` flag cleared
   - User can login normally

---

## Frontend Checklist

- [ ] Handle "must_change_password" error from login
- [ ] Request password change token on first login
- [ ] Store token securely (not in localStorage for sensitive apps)
- [ ] Include Bearer token in password change request
- [ ] Handle new tokens after password change
- [ ] Redirect to dashboard after successful change

---

## Testing Commands

```bash
# 1. Get token for new user
curl -X POST http://localhost:8000/api/users/get_password_change_token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_doe", "password": "TempPass123!"}'

# 2. Change password
curl -X POST http://localhost:8000/api/users/first_time_password_change/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "NewPass@456", "new_password_confirm": "NewPass@456"}'
```

---

## Common Errors

| Status | Error | Reason |
|--------|-------|--------|
| 401 | Invalid credentials | Wrong username/password |
| 400 | Must change password | Use `get_password_change_token` |
| 400 | Passwords don't match | Check confirm password |
| 401 | Token invalid | Token expired or malformed |

---

**Full Documentation:** See `JWT_PASSWORD_CHANGE_FLOW.md`

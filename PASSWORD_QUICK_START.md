# Quick Start: User Password Management

## Summary

New users (except customers) receive login credentials via email and **must change their password** on first login.

## Key Points

✅ **Admins create users** → Email sent with username/password  
✅ **First login blocked** → Must change password first  
✅ **Change password** → Get JWT tokens immediately  
✅ **Customers exempt** → Can login directly (no forced change)  

---

## API Endpoints Quick Reference

### 1. Create User (Admin Only)
```http
POST /api/users/
Authorization: Bearer {admin_token}

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "TempPass123!",
  "password_confirm": "TempPass123!",
  "role": "cashier",
  "full_name": "John Doe"
}
```

**Result:** 
- User created with `must_change_password=true`
- Email sent with credentials (if not customer)

---

### 2. First-Time Password Change (Public)
```http
POST /api/users/first_time_password_change/
No Authentication Required

{
  "username": "john_doe",
  "current_password": "TempPass123!",
  "new_password": "NewSecure@Pass456",
  "new_password_confirm": "NewSecure@Pass456"
}
```

**Result:**
- Password changed
- `must_change_password` set to `false`
- JWT tokens returned immediately

---

### 3. Regular Login
```http
POST /api/token/

{
  "username": "john_doe",
  "password": "NewSecure@Pass456"
}
```

**Before password change:** ❌ Blocked with error  
**After password change:** ✅ Returns JWT tokens

---

## User Flow Diagram

```
Admin Creates User
      ↓
Email Sent (username + password)
      ↓
User Tries to Login
      ↓
Login BLOCKED ❌
      ↓
User Uses First-Time Password Change Endpoint
      ↓
Password Changed ✅
      ↓
JWT Tokens Issued Immediately
      ↓
User Can Login Normally
```

---

## Role-Based Behavior

| Role | must_change_password | Email Sent | Can Login Immediately |
|------|---------------------|------------|----------------------|
| **Super Admin** | ✅ True | ✅ Yes | ❌ No (must change) |
| **Admin** | ✅ True | ✅ Yes | ❌ No (must change) |
| **Sub Admin** | ✅ True | ✅ Yes | ❌ No (must change) |
| **Cashier** | ✅ True | ✅ Yes | ❌ No (must change) |
| **Inventory Manager** | ✅ True | ✅ Yes | ❌ No (must change) |
| **Customer** | ❌ False | ❌ No | ✅ Yes |

---

## Common Scenarios

### Scenario 1: New Cashier Account
1. Admin creates cashier with password "Temp123!"
2. Cashier receives email with credentials
3. Cashier tries to login → **BLOCKED**
4. Cashier uses `/first_time_password_change/` → **SUCCESS + JWT tokens**
5. Cashier can now login normally

### Scenario 2: New Customer Account
1. Admin creates customer with password "Cust123!"
2. **No email sent** (customer exempt)
3. Customer logs in immediately → **SUCCESS**

---

## Testing in Development

Email output is printed to console. Check terminal for:
```
Content-Type: text/plain; charset="utf-8"
...
Username: john_doe
Temporary Password: TempPass123!
...
```

---

## Configuration

### Development (Default)
```python
# core/settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@serveiq.com'
```

### Production
```python
# core/settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@serveiq.com'
```

---

## Files Created/Modified

```
✅ templates/email/welcome_credentials.html     (new email template)
✅ apps/users/utils.py                          (email utility)
✅ apps/users/serializers/user_serializers.py   (FirstTimePasswordChangeSerializer)
✅ apps/users/views/user_view.py                (first_time_password_change endpoint)
```

---

## Security Notes

⚠️ **Temporary passwords sent via email** - Users should:
- Change password immediately
- Delete credentials email after changing password
- Use strong, unique passwords

🔒 **Best Practices:**
- Generate strong temporary passwords
- Use SMTP with TLS in production
- Monitor users who haven't changed passwords

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Login blocked | Use `/first_time_password_change/` endpoint |
| Email not received | Check console (dev) or SMTP config (prod) |
| Password too weak | Must meet Django validation requirements |
| Customer can't use endpoint | Customers use regular login, not forced change |

---

For detailed documentation, see: `PASSWORD_MANAGEMENT_GUIDE.md`

# User Password Management System

## Overview

This document describes the forced password change system for newly created users (excluding customers). When an admin creates a new user, the system:

1. Sends an email with username and password to the user
2. Sets `must_change_password=True` flag
3. Blocks login with JWT tokens until password is changed
4. Provides a special endpoint for first-time password change

## Features

### 1. Automatic Email Notification

When a new user is created (except customers):
- An email is sent with their username and temporary password
- Email includes security instructions and next steps
- Template: `templates/email/welcome_credentials.html`

### 2. Forced Password Change

- Users with `must_change_password=True` cannot log in with regular login endpoints
- JWT token generation is blocked until password is changed
- Customers are exempt from this requirement

### 3. First-Time Password Change Endpoint

A dedicated endpoint allows users to change their password without authentication:
- No authentication required (uses username and current password)
- Automatically issues JWT tokens after successful password change
- Only works for users with `must_change_password=True`

## API Endpoints

### 1. Login Endpoint (Modified Behavior)

**Endpoint:** `POST /api/token/` or `POST /api/auth/login/`

**Request:**
```json
{
  "username": "john_doe",
  "password": "temporary_password"
}
```

**Response (if must_change_password=true):**
```json
{
  "detail": "You must change your password before you can log in. Please use the password change endpoint first.",
  "must_change_password": true,
  "user_id": 123,
  "username": "john_doe"
}
```

**HTTP Status:** `400 Bad Request`

### 2. First-Time Password Change

**Endpoint:** `POST /api/users/first_time_password_change/`

**Authentication:** None required (public endpoint)

**Request:**
```json
{
  "username": "john_doe",
  "current_password": "temporary_password",
  "new_password": "NewSecure@Password123",
  "new_password_confirm": "NewSecure@Password123"
}
```

**Response (Success):**
```json
{
  "message": "Password changed successfully. You can now log in.",
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

**HTTP Status:** `200 OK`

**Validations:**
- Username must exist
- Current password must be correct
- New passwords must match
- User must have `must_change_password=True`
- User must not be a customer
- Password must meet Django's password validation requirements

### 3. Create User (Admin)

**Endpoint:** `POST /api/users/`

**Authentication:** Required (Admin only)

**Request:**
```json
{
  "username": "new_user",
  "email": "user@example.com",
  "password": "TemporaryPass123!",
  "password_confirm": "TemporaryPass123!",
  "full_name": "New User",
  "role": "cashier"
}
```

**Behavior:**
- Automatically sets `must_change_password=True` for non-customer users
- Sends welcome email with credentials
- Customers get `must_change_password=False`

### 4. Regular Password Change

**Endpoint:** `POST /api/users/change_password/`

**Authentication:** Required

**Request:**
```json
{
  "old_password": "current_password",
  "new_password": "NewPassword123!",
  "new_password_confirm": "NewPassword123!"
}
```

**Behavior:**
- Requires authentication
- Validates old password
- Sets `must_change_password=False` after successful change

## User Flow

### For New Users (Non-Customers)

1. **Admin creates user account**
   - Admin submits user creation form with username, email, password, and role
   - System sets `must_change_password=True`
   - Email sent to user with credentials

2. **User receives email**
   - Email contains username and temporary password
   - Email includes security instructions
   - User advised to change password immediately

3. **User attempts first login**
   - User tries to log in with temporary password
   - Login is blocked with error message
   - Error response includes `must_change_password: true` flag

4. **User changes password**
   - User visits first-time password change endpoint
   - Provides username, current password, and new password
   - System validates and updates password
   - `must_change_password` flag set to `false`
   - JWT tokens immediately issued in response

5. **User can now log in normally**
   - User can use regular login endpoint
   - JWT tokens are issued successfully

### For Customers

- Customers are exempt from forced password change
- `must_change_password` defaults to `false`
- No credentials email sent
- Can log in immediately after account creation

## Email Configuration

### Development

Emails are printed to console (default setting):
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@serveiq.com'
```

### Production

Configure SMTP settings in `core/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@serveiq.com'
```

## Email Template

The welcome email template is located at:
```
templates/email/welcome_credentials.html
```

**Template Variables:**
- `username` - User's username
- `password` - Temporary password (plain text)
- `full_name` - User's full name
- `role_display` - User's role (display format)
- `domain` - Site domain
- `protocol` - http or https

## Security Considerations

### Password Security

1. **Temporary passwords should be strong**
   - Admins should generate strong temporary passwords
   - Consider using password generator tools

2. **Email security**
   - Credentials are sent via email (inherent risk)
   - Users instructed to delete email after password change
   - Consider implementing password expiration for temporary passwords

3. **Password validation**
   - Django's password validation is applied
   - Minimum length, complexity requirements enforced

### Best Practices

1. **For Admins:**
   - Generate strong temporary passwords
   - Inform users about the email
   - Monitor users who haven't changed passwords

2. **For Users:**
   - Change password immediately upon receipt
   - Choose strong, unique passwords
   - Delete credentials email after password change

3. **For System:**
   - Configure SMTP with TLS/SSL in production
   - Use application-specific passwords for email services
   - Consider adding password expiration feature
   - Log password change attempts

## Code Structure

### Files Modified/Created

1. **`apps/users/utils.py`** (New)
   - `send_welcome_credentials_email()` - Sends credentials email

2. **`apps/users/serializers/user_serializers.py`**
   - `UserCreateSerializer.create()` - Sets must_change_password and sends email
   - `FirstTimePasswordChangeSerializer` - New serializer for first-time password change
   - `ChangePasswordSerializer.save()` - Sets must_change_password to False

3. **`apps/users/views/user_view.py`**
   - `CustomTokenObtainPairSerializer.validate()` - Blocks login if must_change_password
   - `UserViewSet.first_time_password_change()` - New endpoint for password change

4. **`templates/email/welcome_credentials.html`** (New)
   - Professional email template for credentials

## Testing

### Test Scenarios

1. **Create non-customer user**
   - Verify `must_change_password=True`
   - Verify email sent

2. **Create customer user**
   - Verify `must_change_password=False`
   - Verify no credentials email sent

3. **Login with must_change_password=True**
   - Verify login blocked
   - Verify error message received

4. **First-time password change**
   - Verify successful password change
   - Verify JWT tokens issued
   - Verify `must_change_password=False` after change

5. **Login after password change**
   - Verify login successful
   - Verify JWT tokens issued

### Sample Test Commands

```bash
# Create a user (as admin)
curl -X POST http://localhost:8000/api/users/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com",
    "password": "TempPass123!",
    "password_confirm": "TempPass123!",
    "role": "cashier",
    "full_name": "Test User"
  }'

# Try to login (should fail)
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "TempPass123!"
  }'

# Change password (first time)
curl -X POST http://localhost:8000/api/users/first_time_password_change/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "current_password": "TempPass123!",
    "new_password": "NewSecure@Pass456",
    "new_password_confirm": "NewSecure@Pass456"
  }'

# Login with new password (should succeed)
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "NewSecure@Pass456"
  }'
```

## Error Handling

### Common Errors

1. **Login blocked due to must_change_password**
   ```json
   {
     "detail": "You must change your password before you can log in...",
     "must_change_password": true,
     "user_id": 123,
     "username": "john_doe"
   }
   ```

2. **Invalid current password**
   ```json
   {
     "current_password": ["Current password is incorrect."]
   }
   ```

3. **Password mismatch**
   ```json
   {
     "new_password_confirm": ["Password fields do not match."]
   }
   ```

4. **User not found**
   ```json
   {
     "username": ["User not found."]
   }
   ```

5. **Customer trying to use endpoint**
   ```json
   {
     "detail": "This endpoint is not for customer accounts."
   }
   ```

6. **User without must_change_password flag**
   ```json
   {
     "detail": "You do not need to use this endpoint. Use the regular password change endpoint."
   }
   ```

## Future Enhancements

1. **Password Expiration**
   - Add expiration date for temporary passwords
   - Automatically block old temporary passwords

2. **Password History**
   - Prevent reuse of recent passwords
   - Track password change history

3. **Email Notifications**
   - Send email confirmation after password change
   - Send alerts for suspicious password change attempts

4. **Multi-factor Authentication**
   - Add MFA for enhanced security
   - Require MFA setup after first password change

5. **Password Strength Meter**
   - Frontend integration for password strength
   - Real-time validation feedback

## Support

For issues or questions:
- Check Django admin for user's `must_change_password` status
- Review email logs in console (development) or email service (production)
- Check user model fields: `must_change_password`, `is_active`, `status`, `role`

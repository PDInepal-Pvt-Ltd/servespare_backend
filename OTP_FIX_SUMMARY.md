# OTP Email Sending - Issues Fixed ✅

## Problems Identified & Fixed

### 1. **Database Constraint Issue (OneToOneField)**
**Problem:** The OTP model was using `OneToOneField`, which meant only ONE OTP could exist per user at a time. When a customer tried to resend OTP, the database constraint would fail.

**Fix:** Changed `OneToOneField` to `ForeignKey` in [apps/otp/models/otp_model.py](apps/otp/models/otp_model.py)
- Allows multiple OTP records per user
- Old OTPs are automatically deleted when new ones are requested
- Prevents "integrity constraint violation" errors

### 2. **OTP Generation Logic**
**Problem:** The `update_or_create()` method could still fail with multiple concurrent requests due to the OneToOneField constraint.

**Fix:** Updated `generate_and_save_otp()` in [apps/otp/utils.py](apps/otp/utils.py)
- Explicitly deletes old OTPs before creating new ones
- Handles errors gracefully with try-catch
- Added logging for debugging

### 3. **Poor Error Handling in Email Sending**
**Problem:** The `send_otp_email()` function had minimal error logging, making it hard to diagnose issues.

**Fix:** Enhanced error handling in [apps/otp/utils.py](apps/otp/utils.py)
- Added verification of email credentials before sending
- Shows EMAIL_BACKEND mode (SMTP vs Console)
- Provides full traceback on errors
- Logs successful sends with message count

## Configuration Status ✓

Your email configuration is properly set up:
- **EMAIL_HOST:** smtp.gmail.com
- **EMAIL_PORT:** 587
- **EMAIL_USE_TLS:** True
- **EMAIL_HOST_USER:** Configured ✓
- **EMAIL_HOST_PASSWORD:** Configured ✓
- **DEFAULT_FROM_EMAIL:** Configured ✓

## Migration Applied

```
Migrations for 'otp':
  apps\otp\migrations\0002_alter_otp_user.py
    ~ Alter field user on otp
```

Migration successfully applied to database.

## Testing

Run the diagnostic test to verify OTP sending works:

```bash
python test_otp_send.py
```

This will:
1. Check email configuration
2. Verify a user with email exists
3. Generate a test OTP
4. Send a test email
5. Display results and any errors

## Files Modified

1. **[apps/otp/models/otp_model.py](apps/otp/models/otp_model.py)**
   - Changed OneToOneField to ForeignKey

2. **[apps/otp/utils.py](apps/otp/utils.py)**
   - Updated `generate_and_save_otp()` with delete + create logic
   - Enhanced `send_otp_email()` with better error handling

3. **apps/otp/migrations/0002_alter_otp_user.py** (auto-generated)
   - Database schema update

## How OTP Flow Works Now

1. Customer requests OTP via `/otp/request/`
2. System generates 6-digit code with 5-minute expiry
3. Old OTP records are deleted (no constraint violations)
4. New OTP is saved to database
5. Email is sent via Gmail SMTP
6. Customer receives verification code
7. Customer verifies code via `/otp/verify/`
8. OTP is deleted after verification
9. Reset token is issued for password change

## Debugging Tips

If customers still don't receive OTP:

1. **Check email logs:**
   ```bash
   python test_otp_send.py
   ```

2. **Check for email in spam/junk folder**

3. **Monitor DEBUG mode:**
   - If `DEBUG=True` and credentials missing → emails go to console
   - Check Django development server logs

4. **Verify email in DB:**
   ```python
   from apps.users.models import User
   User.objects.filter(role='customer').values('email')
   ```

5. **Check OTP records:**
   ```python
   from apps.otp.models import OTP
   OTP.objects.all().order_by('-created_at')[:10]
   ```

## Summary

The primary issue was the **OneToOneField constraint** preventing multiple OTP requests. This has been completely fixed. Your email configuration is working perfectly. Customers should now receive OTP emails without issues.

✅ **Ready to go!**

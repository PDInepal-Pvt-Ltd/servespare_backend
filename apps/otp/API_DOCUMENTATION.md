# OTP API Documentation

Source: [apps/otp/views/otp_views.py](apps/otp/views/otp_views.py)

This document describes the OTP (one-time-password) endpoints implemented in the `RequestOtpViewSet`, `VerifyOtpViewSet`, and `OTPViewSet`.

---

## Summary

- Purpose: Provide password recovery OTP issuance and verification plus an admin listing endpoint.
- Token: Successful OTP verification returns a short-lived recovery token issued by `create_recovery_token(purpose='password_reset', expires_in=15)`.
- Safety: The request endpoint intentionally returns a generic message to avoid account enumeration.

---

## Endpoints

Note: Exact URL prefixes depend on how the viewsets are registered in your router (see your project's `urls.py`). The documented `path` values below use the `request` and `verify` action url_paths and assume a base like `/api/otp/` — adjust to match your routes.

### 1) Request OTP

- Path (example): POST `/api/otp/request/`
- View: `RequestOtpViewSet.trigger_otp`
- Permission: `AllowAny`
- Throttle: `OTPResendRateThrottle`

Request body (JSON):

{
  "identifier": "<username_or_email>"
}

Behavior:
- Validates `identifier` with `RecoveryRequestSerializer`.
- Attempts to find `User` by `username` or `email`.
- If user found: generates and stores an `OTP` via `generate_and_save_otp(user)` and emails it via `send_otp_email(user, code)`.
- If user not found: responds the same (generic success) to prevent enumeration.

Responses:
- 200 OK — { "message": "If an account exists, a recovery code has been sent." }
- 500 Internal Server Error — { "error": "Failed to send OTP." } (if email sending fails)

Example curl:

```bash
curl -X POST https://example.com/api/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"alice@example.com"}'
```

---

### 2) Verify OTP

- Path (example): POST `/api/otp/verify/`
- View: `VerifyOtpViewSet.verify_otp`
- Permission: `AllowAny`

Request body (JSON):

{
  "identifier": "<username_or_email>",
  "otp": "<code>"
}

Behavior:
- Validates fields with `OTPVerificationSerializer`.
- Finds matching `User` by `username` or `email`.
- Looks up `OTP` with `OTP.objects.filter(user=user, code=code).first()`.
- If OTP missing or `otp.is_valid()` is False: deletes OTP (if present) and returns error.
- If OTP valid: deletes the OTP and issues a recovery token with a 15-minute expiry.

Responses:
- 200 OK —
  {
    "message": "OTP verified successfully. Use the token to reset your password.",
    "token": "<access_token>",
    "expires_at": "<ISO datetime>",
    "expires_in": 15
  }
- 400 Bad Request — { "error": "Invalid or expired code." }

Example curl:

```bash
curl -X POST https://example.com/api/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"alice@example.com","otp":"123456"}'
```

---

### 3) List OTPs (admin)

- Path (example): GET `/api/otp/` (provided by `OTPViewSet.list`)
- View: `OTPViewSet` (list)
- Permission: `IsAdminUser`
- Pagination: `StandardResultsSetPagination`

Query parameters:
- `user_id` (optional) — integer user id to filter OTPs.
- `valid` (optional) — string `"true"` or `"false"` to filter by current validity. Note: filtering is applied in Python by calling `otp.is_valid()` on each OTP returned from the DB; this may load objects into memory.

Responses:
- 200 OK — paginated list of serialized OTP objects (uses `OTPSerializer`).

Example curl (admin):

```bash
curl -X GET "https://example.com/api/otp/?user_id=42&valid=true" \
  -H "Authorization: Bearer <admin_token>"
```

---

## Serializers & Models (references)

- `RecoveryRequestSerializer` — validates the `identifier` used for requesting OTPs.
- `OTPVerificationSerializer` — validates `identifier` and `otp` fields for verification.
- `OTPSerializer` — used to serialize OTP objects for admin listing.
- `OTP` model — includes `created_at` and an `is_valid()` method used to check expiry/validity.

Check implementations in:
- [apps/otp/serializers.py](apps/otp/serializers.py)
- [apps/otp/models.py](apps/otp/models.py)

---

## Implementation notes & recommendations

- The request endpoint intentionally returns a generic 200 message for both found and not-found users to avoid leaking account existence.
- The `verify` endpoint deletes OTPs after verification or when expired/invalid to prevent reuse.
- The admin `valid` filter evaluates `is_valid()` in Python; consider pushing validity logic into the database (e.g., filter by `expires_at__gt=timezone.now()`) for large datasets.
- Confirm exact route prefixes by inspecting the router registration in your `urls.py`.

---

## Next steps you might want me to do

- Scan `urls.py` and return the exact registered routes for these viewsets.
- Include the serializer field definitions in this doc.
- Add OpenAPI (Swagger) examples or generate a Postman collection.




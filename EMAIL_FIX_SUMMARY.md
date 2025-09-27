# Email Configuration Fix Summary

## Problem Identified

The issue was that **OTP emails and other tenant-specific emails were not working in production**, while **password reset emails were working fine**. This was due to a critical bug in the `send_tenant_email()` function in `apps/core/utils.py`.

## Root Cause

1. **Password Reset Emails Work**: Django's built-in `PasswordResetView` uses Django's standard `send_mail()` function, which uses the global email settings directly.

2. **OTP Emails Don't Work**: The OTP system uses `send_tenant_email()` from `apps/core/utils.py`, which had a **critical bug** in the SSL/TLS configuration logic.

3. **The Bug**: The `send_tenant_email()` function was not applying the **mutual exclusivity logic** between SSL and TLS that was present in production settings. This caused conflicts when both SSL and TLS were enabled.

## Changes Made

### 1. Fixed SSL/TLS Mutual Exclusivity in `apps/core/utils.py`

**File**: `apps/core/utils.py`
**Lines**: 95-97, 109-111

Added the same mutual exclusivity logic that exists in production settings:
```python
# Enforce mutual exclusivity to prevent Django errors (same logic as production.py)
if use_ssl:
    use_tls = False
```

This ensures that when SSL is enabled, TLS is automatically disabled, preventing SMTP connection conflicts.

### 2. Added Missing Tenant Email SSL Setting

**File**: `config/settings/tenants.py`
**Line**: 185

Added the missing `TENANT_EMAIL_USE_SSL` setting:
```python
# Whether to use SSL for tenant-specific emails
TENANT_EMAIL_USE_SSL = os.getenv('TENANT_EMAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
```

### 3. Enhanced Error Logging and Debugging

**File**: `apps/core/utils.py`
**Lines**: 125-126, 149-150

Added comprehensive logging to help debug email issues:
```python
# Log email configuration for debugging (without sensitive data)
logger.debug(f"Email config: host={host}, port={port}, use_tls={use_tls}, use_ssl={use_ssl}, timeout={timeout}")
```

### 4. Added Fallback Mechanism for OTP Emails

**File**: `apps/users/models.py`
**Lines**: 284-307

Added fallback to Django's standard `send_mail` if tenant email fails:
```python
# Try tenant email first, fallback to standard Django send_mail
try:
    send_mail(...)
except Exception as e:
    # Fallback to Django's standard send_mail
    from django.core.mail import send_mail as django_send_mail
    django_send_mail(...)
```

### 5. Added Fallback for Welcome Emails

**File**: `apps/users/tasks.py`
**Lines**: 24-48

Applied the same fallback mechanism to welcome emails sent via Celery tasks.

### 6. Created Email Testing Command

**File**: `apps/users/management/commands/test_email.py`

Created a management command to test email functionality:
```bash
python manage.py test_email --email test@example.com
```

## How to Test the Fix

### 1. Test Email Configuration
```bash
python manage.py test_email --email your-email@example.com
```

### 2. Test OTP Functionality
1. Create a new user account
2. Check if OTP email is received during onboarding
3. Check application logs for any email errors

### 3. Test Other Email Functions
- Welcome emails (sent after user registration)
- Any other tenant-specific emails in your application

## Environment Variables to Check

Ensure these environment variables are properly set in production:

```bash
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=587  # or 465 for SSL
EMAIL_USE_TLS=True  # if using port 587
EMAIL_USE_SSL=False  # if using port 587, or True if using port 465
EMAIL_HOST_USER=your-email@oreno.tech
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=info@oreno.tech
```

## Expected Results

After applying this fix:

1. ✅ **OTP emails should work** during user onboarding
2. ✅ **Welcome emails should work** after user registration  
3. ✅ **Password reset emails should continue working** (no regression)
4. ✅ **All tenant-specific emails should work** consistently
5. ✅ **Better error logging** for debugging any future email issues

## Non-Destructive Nature

This fix is **completely non-destructive**:
- ✅ No database changes required
- ✅ No breaking changes to existing functionality
- ✅ Backward compatible with existing email configurations
- ✅ Includes fallback mechanisms to ensure emails are sent even if tenant email fails
- ✅ Enhanced logging for better debugging without affecting performance

## Files Modified

1. `apps/core/utils.py` - Fixed SSL/TLS logic and added logging
2. `config/settings/tenants.py` - Added missing TENANT_EMAIL_USE_SSL setting
3. `apps/users/models.py` - Added fallback mechanism for OTP emails
4. `apps/users/tasks.py` - Added fallback mechanism for welcome emails
5. `apps/users/management/commands/test_email.py` - New testing command

The fix addresses the core issue while maintaining robustness and providing better debugging capabilities.

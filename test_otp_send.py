"""
OTP Email Sending Test Script
This script tests the OTP email sending functionality to diagnose issues.
Run this to verify email configuration and sending.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from apps.users.models import User
from apps.otp.utils import generate_and_save_otp, send_otp_email
from apps.otp.models import OTP

def test_email_configuration():
    """Test if email configuration is correct"""
    print("\n" + "="*60)
    print("EMAIL CONFIGURATION TEST")
    print("="*60)
    
    print(f"DEBUG Mode: {settings.DEBUG}")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else '[NOT SET]'}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else '[NOT SET]'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Check if credentials are missing
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n⚠️  WARNING: Email credentials not configured!")
        print("   Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env file")
        if settings.DEBUG:
            print("   DEBUG mode is ON - emails will be sent to console")
        return False
    
    print("\n✓ Email configuration looks good")
    return True

def test_user_email():
    """Test if a test user exists with valid email"""
    print("\n" + "="*60)
    print("USER EMAIL TEST")
    print("="*60)
    
    users = User.objects.filter(email__isnull=False).exclude(email='')
    
    if not users.exists():
        print("❌ No users found with email addresses")
        return None
    
    test_user = users.first()
    print(f"✓ Found user: {test_user.username}")
    print(f"  Email: {test_user.email}")
    print(f"  Role: {test_user.role}")
    
    return test_user

def test_otp_generation(user):
    """Test OTP generation"""
    print("\n" + "="*60)
    print("OTP GENERATION TEST")
    print("="*60)
    
    try:
        # Clear old OTPs
        OTP.objects.filter(user=user).delete()
        
        otp = generate_and_save_otp(user)
        print(f"✓ OTP generated successfully")
        print(f"  Code: {otp.code}")
        print(f"  Expires at: {otp.expires_at}")
        print(f"  Is valid: {otp.is_valid()}")
        
        return otp
    except Exception as e:
        print(f"❌ Failed to generate OTP: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_otp_email_send(user, otp):
    """Test OTP email sending"""
    print("\n" + "="*60)
    print("OTP EMAIL SENDING TEST")
    print("="*60)
    
    try:
        result = send_otp_email(user, otp.code)
        if result:
            print(f"✓ OTP email sent successfully to {user.email}")
        else:
            print(f"❌ Failed to send OTP email")
        return result
    except Exception as e:
        print(f"❌ Exception while sending OTP: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "🔍 " + "="*56 + " 🔍")
    print("   OTP EMAIL SENDING DIAGNOSTIC TEST")
    print("🔍 " + "="*56 + " 🔍")
    
    # Step 1: Check email config
    config_ok = test_email_configuration()
    
    # Step 2: Get test user
    test_user = test_user_email()
    if not test_user:
        print("\n❌ Cannot proceed without a user with email")
        return
    
    # Step 3: Generate OTP
    otp = test_otp_generation(test_user)
    if not otp:
        print("\n❌ Cannot proceed without OTP generation")
        return
    
    # Step 4: Send OTP email
    email_sent = test_otp_email_send(test_user, otp)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if config_ok and otp and email_sent:
        print("✓ All tests passed! OTP email sending should work.")
        print(f"\n📧 OTP email sent to: {test_user.email}")
        print(f"   Code: {otp.code}")
        print(f"   Valid for 5 minutes")
    else:
        print("❌ Some tests failed. Check the logs above.")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()

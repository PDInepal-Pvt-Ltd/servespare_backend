#!/usr/bin/env python
"""
Simple test script to send a test email to verify email configuration
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_test_email():
    """Send a simple test email"""
    recipient_email = 'anishkumal0202@gmail.com'
    subject = 'Test Email from ServeSpare Backend'
    
    plain_message = '''
Hello,

This is a test email from the ServeSpare backend to verify that the email configuration is working correctly.

If you received this, the email system is functioning properly!

Best regards,
ServeSpare Team
    '''
    
    html_message = '''
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #667eea;">Test Email from ServeSpare Backend</h2>
                <p>Hello,</p>
                <p>This is a test email from the ServeSpare backend to verify that the email configuration is working correctly.</p>
                <p style="color: #28a745; font-weight: bold;">✓ If you received this, the email system is functioning properly!</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p>Best regards,<br><strong>ServeSpare Team</strong></p>
            </div>
        </body>
    </html>
    '''
    
    try:
        print(f"Email Configuration:")
        print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        print(f"  EMAIL_HOST_USER: {'*' * 10 if settings.EMAIL_HOST_USER else 'NOT SET'}")
        print()
        
        email = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
        )
        
        email.attach_alternative(html_message, "text/html")
        
        result = email.send(fail_silently=False)
        
        print(f"✓ Email sent successfully to {recipient_email}")
        print(f"  Message ID count: {result}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send email. Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("ServeSpare Test Email Script")
    print("=" * 60)
    print()
    
    success = send_test_email()
    
    print()
    print("=" * 60)
    exit(0 if success else 1)

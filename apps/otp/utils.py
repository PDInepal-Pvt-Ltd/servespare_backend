import secrets
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from .models import OTP # Assuming this is your OTP model

# Note: You need to have 'django.contrib.sites' in INSTALLED_APPS 
# and the domain for Site ID 1 set to '127.0.0.1:8000' in your Django Admin.

def generate_and_save_otp(user):
    """
    Generates a 6-digit code securely, calculates expiry, and saves/updates the OTP record.
    Returns the OTP instance.
    """
    code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = timezone.now() + timedelta(minutes=5)
    
    otp, _ = OTP.objects.update_or_create(
        user=user, 
        defaults={'code': code, 'expires_at': expires_at}
    )
    return otp


def send_otp_email(user, otp_code):
    """
    Sends the OTP code to the user's email as a multi-part email (HTML and plain text).
    Includes logic for absolute URLs (necessary for images in emails).
    """
    
    if not user.email:
        print(f"Error: User {user.get_username()} has no email address.")
        return False
        
    subject = 'Your Verification Code'
    
    # Get the current site's domain for absolute URLs (Works with 127.0.0.1:8000 locally)
    try:
        current_site = Site.objects.get_current()
        domain = current_site.domain
        protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
    except Exception as e:
        # Fall back to localhost instead of aborting so email still sends
        print(f"Failed to get site domain; using localhost fallback. Error: {e}")
        domain = 'localhost:8000'
        protocol = 'http'

    # 1. Define the context for the template
    context = {
        'user': user,
        'otp_code': otp_code,
        'domain': domain,       # Used for absolute image path
        'protocol': protocol,   # Used for absolute image path (http://localhost)
    }

    # 2. Render the HTML content from the template
    try:
        # Assumes 'otp.html' is in your templates directory
        html_message = render_to_string('email/otp.html', context)
    except Exception as e:
        print(f"Failed to render OTP HTML template. Error: {e}")
        return False

    # 3. Create a plain text fallback
    plain_message = (
        f'Hello {user.get_username()},\n\n'
        f'Your verification code is: {otp_code}\n'
        f'This code is valid for 5 minutes. Do not share this code.\n\n'
    )
    
    try:
        # 4. Use EmailMultiAlternatives to send the email
        email = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        
        # 5. Attach the HTML version
        email.attach_alternative(html_message, "text/html")
        
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Failed to send OTP email. Error: {e}")
        return False
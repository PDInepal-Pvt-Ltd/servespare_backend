"""
Utility functions for user management including email notifications.
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.utils import timezone


def send_welcome_credentials_email(user, raw_password):
    """
    Sends a welcome email with username and password to newly created users.
    
    Args:
        user: User instance
        raw_password: The plain text password to send (before hashing)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    if not user.email:
        print(f"Error: User {user.username} has no email address.")
        return False
    
    # Don't send credentials email to customers
    if user.role == 'customer':
        print(f"Skipping credentials email for customer: {user.username}")
        return True
        
    subject = 'Welcome to ServeSpare - Your Account Credentials'
    
    # Get the current site's domain for absolute URLs
    try:
        current_site = Site.objects.get_current()
        domain = current_site.domain
        protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
    except Exception as e:
        print(f"Failed to get site domain. Using default. Error: {e}")
        domain = 'localhost:8000'
        protocol = 'http'

    # Define the context for the template
    context = {
        'username': user.username,
        'password': raw_password,
        'full_name': user.full_name or user.username,
        'role_display': user.get_role_display(),
        'domain': domain,
        'protocol': protocol,
    }

    # Render the HTML content from the template
    try:
        html_message = render_to_string('email/welcome_credentials.html', context)
    except Exception as e:
        print(f"Failed to render welcome credentials HTML template. Error: {e}")
        return False

    # Create a plain text fallback
    plain_message = (
        f'Welcome to ServeSpare!\n\n'
        f'Hello {context["full_name"]},\n\n'
        f'Your account has been successfully created.\n\n'
        f'Login Credentials:\n'
        f'Username: {user.username}\n'
        f'Temporary Password: {raw_password}\n'
        f'Role: {user.get_role_display()}\n\n'
        f'IMPORTANT: You must change your password on your first login for security reasons.\n\n'
        f'Security Reminders:\n'
        f'- Do not share your credentials with anyone\n'
        f'- Change your password immediately after first login\n'
        f'- Choose a strong password with letters, numbers, and symbols\n'
        f'- Delete this email after changing your password\n\n'
        f'If you have any questions, please contact your system administrator.\n\n'
        f'Best regards,\n'
        f'ServeSpare Team\n'
    )
    
    try:
        # Use EmailMultiAlternatives to send the email
        email = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        
        # Attach the HTML version
        email.attach_alternative(html_message, "text/html")
        
        email.send(fail_silently=False)
        print(f"Welcome credentials email sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f"Failed to send welcome credentials email. Error: {e}")
        return False


def send_password_change_notification_email(user):
    """
    Sends a notification email when a user changes their password.
    """

    if not user.email:
        print(f"Skipping password change email for {user.username}; no email on file.")
        return False

    subject = 'Your ServeSpare password was changed'

    try:
        current_site = Site.objects.get_current()
        domain = current_site.domain
        protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
    except Exception as e:
        print(f"Failed to get site domain. Using default. Error: {e}")
        domain = 'localhost:8000'
        protocol = 'http'

    changed_at = timezone.localtime(timezone.now())

    context = {
        'full_name': user.get_full_name(),
        'username': user.username,
        'timestamp': changed_at.strftime('%Y-%m-%d %H:%M %Z'),
        'login_url': f"{protocol}://{domain}/login",
        'domain_display': domain,
    }

    plain_message = (
        f"Hello {context['full_name']},\n\n"
        f"Your ServeSpare password was changed on {context['timestamp']} for account {context['username']}.\n\n"
        "If this was you, no further action is needed. If you did not make this change, reset your password immediately or contact an administrator.\n\n"
        f"Sign in: {context['login_url']}\n\n"
        "Best regards,\n"
        "ServeSpare Team\n"
    )

    try:
        html_message = render_to_string('email/password_changed.html', context)
    except Exception as e:
        print(f"Failed to render password change HTML template. Using plain fallback. Error: {e}")
        html_message = (
            f"<p>Hello {context['full_name']},</p>"
            f"<p>Your ServeSpare password was changed on <strong>{context['timestamp']}</strong> for account <strong>{context['username']}</strong>.</p>"
            "<p>If this was you, no further action is needed. If you did not make this change, reset your password immediately or contact an administrator.</p>"
            f"<p><a href=\"{context['login_url']}\">Sign in</a></p>"
            "<p>Best regards,<br>ServeSpare Team</p>"
        )

    try:
        email = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        print(f"Password change notification email sent to {user.email}")
        return True
    except Exception as e:
        print(f"Failed to send password change notification email. Error: {e}")
        return False


def send_two_factor_otp_email(user, otp_code):
    """
    Sends a two-factor authentication OTP code to the user's email.
    
    Args:
        user: User instance
        otp_code: The 6-digit OTP code to send
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    if not user.email:
        print(f"Error: User {user.username} has no email address.")
        return False
    
    subject = 'Your Two-Factor Authentication Code'
    
    try:
        current_site = Site.objects.get_current()
        domain = current_site.domain
        protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
    except Exception as e:
        print(f"Failed to get site domain. Using default. Error: {e}")
        domain = 'localhost:8000'
        protocol = 'http'

    context = {
        'full_name': user.full_name or user.username,
        'otp_code': otp_code,
        'domain': domain,
        'protocol': protocol,
    }

    try:
        html_message = render_to_string('email/two_factor_otp.html', context)
    except Exception as e:
        print(f"Failed to render 2FA OTP HTML template. Using plain fallback. Error: {e}")
        html_message = (
            f"<p>Hello {context['full_name']},</p>"
            f"<p>Your two-factor authentication code is: <strong>{context['otp_code']}</strong></p>"
            "<p>This code is valid for 5 minutes. Do not share this code with anyone.</p>"
            "<p>If you did not request this code, please ignore this email.</p>"
            "<p>Best regards,<br>ServeSpare Team</p>"
        )

    plain_message = (
        f"Hello {context['full_name']},\n\n"
        f"Your two-factor authentication code is: {context['otp_code']}\n"
        "This code is valid for 5 minutes. Do not share this code with anyone.\n"
        "If you did not request this code, please ignore this email.\n\n"
        "Best regards,\nServeSpare Team"
    )

    try:
        email = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        print(f"Two-factor authentication OTP email sent to {user.email}")
        return True
    except Exception as e:
        print(f"Failed to send 2FA OTP email. Error: {e}")
        return False

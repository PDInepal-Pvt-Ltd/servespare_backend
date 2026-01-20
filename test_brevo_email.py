import os
import django

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
 
from django.core.mail import send_mail

try:
    send_mail(
        subject="Brevo SMTP Test",
        message="This is a test email to check Brevo SMTP configuration.",
        from_email="no-reply@servespare.xyz",
        recipient_list=["iamcsubedi@gmail.com"],
        fail_silently=False,
    )
    print("✅ Email sent successfully! Brevo SMTP is working.")
except Exception as e:
    print("❌ Email failed!")
    print(str(e))

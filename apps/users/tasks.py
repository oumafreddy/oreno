from core.utils import send_tenant_email as send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from celery import shared_task
from datetime import datetime, timedelta

from .models import OTP

@shared_task
def send_welcome_email(user_id, email, username):
    """
    Send a welcome email to newly registered users.
    """
    subject = _("Welcome to Oreno!")
    context = {
        'username': username,
        'support_email': settings.DEFAULT_FROM_EMAIL,
    }
    message = render_to_string('users/email/welcome.txt', context)
    html_message = render_to_string('users/email/welcome.html', context)
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )

@shared_task
def cleanup_old_otps(user_id):
    """
    Clean up old unverified OTP records that are older than 24 hours.
    """
    expiration_time = datetime.now() - timedelta(hours=24)
    OTP.objects.filter(
        created_at__lt=expiration_time,
        is_verified=False,
        user_id=user_id
    ).delete() 
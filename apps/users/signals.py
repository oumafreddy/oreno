# apps/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OTP
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from .models import Profile, OTP
User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=User)
def create_user_related_profiles(sender, instance, created, **kwargs):
    """
    Signal to auto-create Profile and initial OTP whenever a new user is created.
    """
    if created:
        # 1) Create the one-to-one Profile
        Profile.objects.create(user=instance)

        # 2) Optionally, generate an OTP for email verification / 2FA
        OTP.objects.create(user=instance)


@receiver(post_save, sender=OTP)
def cleanup_otps(sender, instance, **kwargs):
    """Cleanup expired OTPs when new ones are created"""
    OTP.cleanup_expired()
    # Delete verified OTPs older than 1 hour
    OTP.objects.filter(
        is_verified=True,
        created_at__lte=timezone.now() - timedelta(hours=1)
    ).delete()
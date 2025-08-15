# apps/users/signals.py
from django.db.models.signals import (
    post_save, pre_save, post_delete,
    m2m_changed, pre_delete
)
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.sessions.models import Session
from django_tenants.utils import tenant_context
from django.db.models import Q

from .models import Profile, OTP, OrganizationRole
from .tasks import send_welcome_email, cleanup_old_otps
from organizations.models import Organization

User = get_user_model()

def safe_delete_pattern(pattern):
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(pattern)
    else:
        # Optionally log or skip
        pass

@receiver(post_save, sender=User)
def create_user_related_profiles(sender, instance, created, **kwargs):
    """
    Signal to auto-create Profile and initial OTP whenever a new user is created.
    Also handles organization context and welcome email.
    """
    if created:
        # Use a transaction block for DB-related operations (profile and OTP creation)
        with transaction.atomic():
            # Create the one-to-one Profile
            Profile.objects.create(user=instance)

            # Generate an OTP for email verification (but not inside transaction block)
            OTP.objects.create(user=instance)

        # After DB changes are committed, handle async tasks independently
        # Send welcome email asynchronously outside the transaction block
        send_welcome_email.delay(instance.id, instance.email, instance.username)

        # Cleanup OTPs asynchronously, outside transaction
        cleanup_old_otps.delay(instance.id)

        # Clear any cached user data
        safe_delete_pattern(f'user_{instance.id}_*')

@receiver(pre_save, sender=User)
def handle_user_state_changes(sender, instance, **kwargs):
    """
    Handle user state changes and organization updates.
    """
    if not instance.pk:  # New user
        return

    try:
        old_instance = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    # Handle organization changes
    if old_instance.organization != instance.organization:
        # Clear old organization roles
        OrganizationRole.objects.filter(user=instance).delete()
        # Clear cached data
        safe_delete_pattern(f'user_{instance.id}_*')
        safe_delete_pattern(f'org_{old_instance.organization_id}_*')

    # Handle active state changes
    if old_instance.is_active != instance.is_active:
        if not instance.is_active:
            # Deactivate all OTPs (set expires_at to now instead of is_expired)
            OTP.objects.filter(user=instance).update(expires_at=timezone.now())
            # Delete all sessions for this user
            for session in Session.objects.all():
                data = session.get_decoded()
                if data.get('_auth_user_id') == str(instance.pk):
                    session.delete()

@receiver(post_save, sender=OTP)
def handle_otp_creation(sender, instance, created, **kwargs):
    """
    Handle OTP creation and cleanup.
    """
    if created:
        # Cleanup old OTPs asynchronously
        cleanup_old_otps.delay(instance.user.id)
        
        # Send OTP via email
        subject = _("Your OTP Code")
        message = render_to_string('users/email/otp.txt', {
            'user': instance.user,
            'otp': instance.otp,
            'expires_at': instance.expires_at
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=False
        )

@receiver(post_save, sender=OrganizationRole)
def handle_role_changes(sender, instance, created, **kwargs):
    """
    Handle organization role changes and cache updates.
    """
    # Clear cached user and organization data
    safe_delete_pattern(f'user_{instance.user_id}_*')
    safe_delete_pattern(f'org_{instance.organization_id}_*')

    if created:
        # Send notification email for new role assignment
        subject = _("New Organization Role Assigned")
        message = render_to_string('users/email/new_role.txt', {
            'user': instance.user,
            'organization': instance.organization,
            'role': instance.get_role_display()
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=False
        )

@receiver(pre_delete, sender=User)
def handle_user_deletion(sender, instance, **kwargs):
    """
    Handle cleanup and anonymization before user deletion.
    """
    # Clear all related data in the public schema
    try:
        if hasattr(instance, 'profile'):
            instance.profile.delete()
    except Profile.DoesNotExist:
        pass  # Profile doesn't exist, which is fine
    
    # Delete OTPs
    instance.otps.all().delete()
    
    # Delete organization roles
    instance.user_roles.all().delete()
    
    # Clear cached data
    safe_delete_pattern(f'user_{instance.id}_*')
    if instance.organization:
        safe_delete_pattern(f'org_{instance.organization_id}_*')
        # Switch to tenant schema and anonymize/delete tenant data
        with tenant_context(instance.organization):
            try:
                from audit.models import Approval, Engagement, Issue, AuditWorkplan
                # Anonymize audit records
                Approval.objects.filter(Q(requester=instance) | Q(approver=instance)).update(requester=None, approver=None, comments='[ANONYMIZED]')
                Engagement.objects.filter(assigned_to=instance).update(assigned_to=None)
                Issue.objects.filter(issue_owner=instance).update(issue_owner=None, issue_owner_title='[ANONYMIZED]')
                AuditWorkplan.objects.filter(created_by=instance).update(created_by=None)
            except Exception:
                pass  # Table may not exist in public schema

@receiver(m2m_changed, sender=User.groups.through)
def handle_group_changes(sender, instance, action, **kwargs):
    """
    Handle user group membership changes.
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Clear cached user data
        safe_delete_pattern(f'user_{instance.id}_*')
        
        # Update user permissions
        instance.user_permissions.clear()
        for group in instance.groups.all():
            instance.user_permissions.add(*group.permissions.all())

@receiver(post_save, sender=Profile)
def handle_profile_changes(sender, instance, created, **kwargs):
    """
    Handle profile updates and cache management.
    """
    safe_delete_pattern(f'user_{instance.user_id}_*')
    if not created and hasattr(instance, 'get_dirty_fields'):
        if 'avatar' in instance.get_dirty_fields():
            old_avatar = instance.get_dirty_fields().get('avatar')
            if old_avatar:
                old_avatar.delete(save=False)

@receiver(pre_delete, sender=Organization)
def handle_organization_deletion(sender, instance, **kwargs):
    """
    Handle cleanup and anonymization before organization deletion.
    Applies to all users in the organization.
    """
    from audit.models import Approval, Engagement, Issue, AuditWorkplan
    from users.models import CustomUser
    from django.db.models import Q
    # Clear cached data
    safe_delete_pattern(f'org_{instance.id}_*')
    with tenant_context(instance):
        # Anonymize or delete all tenant data for all users in this org
        for user in CustomUser.objects.filter(organization=instance):
            try:
                Approval.objects.filter(Q(requester=user) | Q(approver=user)).update(requester=None, approver=None, comments='[ANONYMIZED]')
                Engagement.objects.filter(assigned_to=user).update(assigned_to=None)
                Issue.objects.filter(issue_owner=user).update(issue_owner=None, issue_owner_title='[ANONYMIZED]')
                AuditWorkplan.objects.filter(created_by=user).update(created_by=None)
            except Exception:
                pass  # Table may not exist in schema

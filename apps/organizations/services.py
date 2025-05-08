# apps/organizations/services.py

from django.db import transaction
from django.core.exceptions import ValidationError

# import your core models
from .models import (
    Organization,
    OrganizationSettings,
    Subscription,
    ArchivedOrganization,
    OrganizationUser,
)

# import the CustomUser model
from users.models import CustomUser

def create_organization(data, created_by):
    """
    Application service to create an organization and its related entities.
    """
    with transaction.atomic():
        org = Organization.objects.create(
            customer_code=data['customer_code'],
            customer_name=data['customer_name'],
            financial_year_end_date=data['financial_year_end_date'],
            customer_industry=data.get('customer_industry', '')
        )
        org.created_by = created_by
        org.save(update_fields=['created_by'])

        # Initialize settings & subscription
        OrganizationSettings.objects.create(
            organization=org,
            subscription_plan=data.get('subscription_plan', 'basic'),
            is_active=True
        )
        Subscription.objects.create(
            organization=org,
            subscription_plan=data.get('subscription_plan', 'basic'),
            start_date=data.get('start_date'),
            billing_cycle=data.get('billing_cycle', 'monthly')
        )
        return org

def update_organization(org: Organization, data: dict):
    """
    Application service to update an existing organization.
    """
    if 'customer_code' in data and len(data['customer_code']) != 8:
        raise ValidationError("Customer code must be exactly 8 characters")

    with transaction.atomic():
        for field in ['customer_code', 'customer_name', 'financial_year_end_date', 'customer_industry']:
            if field in data:
                setattr(org, field, data[field])
        org.save(update_fields=[f for f in data.keys()])
    return org

def archive_organization(org: Organization, archived_by: CustomUser, reason: str = ""):
    """
    Archives an organization and deactivates its users.
    """
    with transaction.atomic():
        ArchivedOrganization.objects.create(
            original_org_id=org.id,
            customer_code=org.customer_code,
            customer_name=org.customer_name,
            archived_reason=reason,
            archived_by_user=archived_by,
            financial_year_end_date=org.financial_year_end_date,
            customer_industry=org.customer_industry,
            was_active=org.is_active,
        )
        org.is_active = False
        org.save(update_fields=['is_active'])
        org.users.update(is_active=False)
    return org

def restore_organization(archived: ArchivedOrganization, restored_by: CustomUser):
    """
    Restores an archived organization back into active status.
    """
    with transaction.atomic():
        data = archived.restore_context()
        org = Organization.objects.create(**data)
        org.created_by = restored_by
        org.save(update_fields=['created_by'])
        archived.delete()
    return org

def renew_subscription(subscription: Subscription, new_end_date):
    """
    Renews the subscription by updating its end date.
    """
    if subscription.status != Subscription.STATUS_ACTIVE:
        raise ValidationError("Cannot renew a non-active subscription")
    subscription.end_date = new_end_date
    subscription.save(update_fields=['end_date'])
    return subscription

def pause_subscription(subscription: Subscription):
    """
    Pauses an active subscription.
    """
    if subscription.status != Subscription.STATUS_ACTIVE:
        raise ValidationError("Only active subscriptions can be paused")
    subscription.status = Subscription.STATUS_PAUSED
    subscription.save(update_fields=['status'])
    return subscription

def cancel_subscription(subscription: Subscription):
    """
    Cancels a subscription.
    """
    if subscription.status == Subscription.STATUS_CANCELLED:
        raise ValidationError("Subscription already cancelled")
    subscription.status = Subscription.STATUS_CANCELLED
    subscription.auto_renew = False
    subscription.save(update_fields=['status', 'auto_renew'])
    return subscription

def get_org_setting(org: Organization, key: str, default=None):
    """
    Retrieve a specific additional setting.
    """
    return org.settings.get_setting(key, default)

def set_org_setting(org: Organization, key: str, value):
    """
    Update an additional setting in the organization's settings.
    """
    settings_obj = org.settings
    settings_obj.set_setting(key, value)
    return settings_obj

def add_user_to_org(org: Organization, user: CustomUser, role: str = CustomUser.ROLE_STAFF):
    """
    Adds a user to an organization with a specific role.
    """
    if OrganizationUser.objects.filter(organization=org, user=user).exists():
        raise ValidationError("User already a member of this organization")
    return OrganizationUser.objects.create(organization=org, user=user, role=role)

def remove_user_from_org(org: Organization, user: CustomUser):
    """
    Removes a user from an organization.
    """
    membership = OrganizationUser.objects.filter(organization=org, user=user)
    if not membership.exists():
        raise ValidationError("User is not a member of this organization")
    membership.delete()
    return True

def resolve_tenant(request):
    """
    Resolves the organization for the current request.
    """
    if hasattr(request, 'organization') and request.organization:
        return request.organization
    raise ValidationError("No organization could be resolved for this request")

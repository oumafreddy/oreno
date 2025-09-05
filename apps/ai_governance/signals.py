"""
AI Governance audit signals and logging.
"""

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from core.models.audit import AuditLog
from core.signals import log_change
from django.db.utils import ProgrammingError, OperationalError, DatabaseError
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='ai_governance.ModelAsset')
def log_model_asset_changes(sender, instance, created, **kwargs):
    """Log changes to ModelAsset instances."""
    try:
        action = 'create' if created else 'update'
        log_change(instance, action)
        
        # Additional AI governance specific logging
        if created:
            logger.info(f"New AI model registered: {instance.name} ({instance.model_type}) in organization {instance.organization}")
        else:
            logger.info(f"AI model updated: {instance.name} in organization {instance.organization}")
            
    except Exception as e:
        logger.warning(f"Failed to log ModelAsset change: {str(e)}")


@receiver(post_save, sender='ai_governance.DatasetAsset')
def log_dataset_asset_changes(sender, instance, created, **kwargs):
    """Log changes to DatasetAsset instances."""
    try:
        action = 'create' if created else 'update'
        log_change(instance, action)
        
        # Additional AI governance specific logging
        if created:
            logger.info(f"New dataset registered: {instance.name} ({instance.role}) in organization {instance.organization}")
        else:
            logger.info(f"Dataset updated: {instance.name} in organization {instance.organization}")
            
    except Exception as e:
        logger.warning(f"Failed to log DatasetAsset change: {str(e)}")


@receiver(post_save, sender='ai_governance.TestPlan')
def log_test_plan_changes(sender, instance, created, **kwargs):
    """Log changes to TestPlan instances."""
    try:
        action = 'create' if created else 'update'
        log_change(instance, action)
        
        # Additional AI governance specific logging
        if created:
            logger.info(f"New test plan created: {instance.name} ({instance.model_type}) in organization {instance.organization}")
        else:
            logger.info(f"Test plan updated: {instance.name} in organization {instance.organization}")
            
    except Exception as e:
        logger.warning(f"Failed to log TestPlan change: {str(e)}")


@receiver(post_save, sender='ai_governance.TestRun')
def log_test_run_changes(sender, instance, created, **kwargs):
    """Log changes to TestRun instances."""
    try:
        action = 'create' if created else 'update'
        log_change(instance, action)
        
        # Additional AI governance specific logging
        if created:
            logger.info(f"New test run started: {instance.id} for model {instance.model_asset.name} in organization {instance.organization}")
        elif instance.status == 'completed':
            logger.info(f"Test run completed: {instance.id} for model {instance.model_asset.name} in organization {instance.organization}")
        elif instance.status == 'failed':
            logger.warning(f"Test run failed: {instance.id} for model {instance.model_asset.name} in organization {instance.organization}")
            
    except Exception as e:
        logger.warning(f"Failed to log TestRun change: {str(e)}")


@receiver(post_save, sender='ai_governance.TestResult')
def log_test_result_changes(sender, instance, created, **kwargs):
    """Log changes to TestResult instances."""
    try:
        action = 'create' if created else 'update'
        log_change(instance, action)
        
        # Additional AI governance specific logging
        if created:
            status = "PASSED" if instance.passed else "FAILED"
            logger.info(f"Test result: {instance.test_name} {status} for test run {instance.test_run.id} in organization {instance.organization}")
            
    except Exception as e:
        logger.warning(f"Failed to log TestResult change: {str(e)}")


@receiver(post_save, sender='ai_governance.Framework')
def log_framework_changes(sender, instance, created, **kwargs):
    """Log changes to Framework instances."""
    try:
        action = 'create' if created else 'update'
        log_change(instance, action)
        
        # Additional AI governance specific logging
        if created:
            logger.info(f"New compliance framework added: {instance.title} ({instance.code}) in organization {instance.organization}")
        else:
            logger.info(f"Compliance framework updated: {instance.title} in organization {instance.organization}")
            
    except Exception as e:
        logger.warning(f"Failed to log Framework change: {str(e)}")


@receiver(post_save, sender='ai_governance.ComplianceMapping')
def log_compliance_mapping_changes(sender, instance, created, **kwargs):
    """Log changes to ComplianceMapping instances."""
    try:
        action = 'create' if created else 'update'
        log_change(instance, action)
        
        # Additional AI governance specific logging
        if created:
            logger.info(f"New compliance mapping created: {instance.test_name} -> {instance.clause.clause_code} in organization {instance.organization}")
        else:
            logger.info(f"Compliance mapping updated: {instance.test_name} in organization {instance.organization}")
            
    except Exception as e:
        logger.warning(f"Failed to log ComplianceMapping change: {str(e)}")


@receiver(post_save, sender='ai_governance.ConnectorConfig')
def log_connector_config_changes(sender, instance, created, **kwargs):
    """Log changes to ConnectorConfig instances."""
    try:
        action = 'create' if created else 'update'
        log_change(instance, action)
        
        # Additional AI governance specific logging
        if created:
            logger.info(f"New connector configured: {instance.name} ({instance.connector_type}) in organization {instance.organization}")
        else:
            logger.info(f"Connector configuration updated: {instance.name} in organization {instance.organization}")
            
    except Exception as e:
        logger.warning(f"Failed to log ConnectorConfig change: {str(e)}")


@receiver(post_delete, sender='ai_governance.ModelAsset')
def log_model_asset_deletion(sender, instance, **kwargs):
    """Log deletion of ModelAsset instances."""
    try:
        log_change(instance, 'delete')
        logger.warning(f"AI model deleted: {instance.name} from organization {instance.organization}")
    except Exception as e:
        logger.warning(f"Failed to log ModelAsset deletion: {str(e)}")


@receiver(post_delete, sender='ai_governance.DatasetAsset')
def log_dataset_asset_deletion(sender, instance, **kwargs):
    """Log deletion of DatasetAsset instances."""
    try:
        log_change(instance, 'delete')
        logger.warning(f"Dataset deleted: {instance.name} from organization {instance.organization}")
    except Exception as e:
        logger.warning(f"Failed to log DatasetAsset deletion: {str(e)}")


@receiver(post_delete, sender='ai_governance.TestPlan')
def log_test_plan_deletion(sender, instance, **kwargs):
    """Log deletion of TestPlan instances."""
    try:
        log_change(instance, 'delete')
        logger.warning(f"Test plan deleted: {instance.name} from organization {instance.organization}")
    except Exception as e:
        logger.warning(f"Failed to log TestPlan deletion: {str(e)}")


@receiver(post_delete, sender='ai_governance.Framework')
def log_framework_deletion(sender, instance, **kwargs):
    """Log deletion of Framework instances."""
    try:
        log_change(instance, 'delete')
        logger.warning(f"Compliance framework deleted: {instance.title} from organization {instance.organization}")
    except Exception as e:
        logger.warning(f"Failed to log Framework deletion: {str(e)}")


@receiver(post_delete, sender='ai_governance.ConnectorConfig')
def log_connector_config_deletion(sender, instance, **kwargs):
    """Log deletion of ConnectorConfig instances."""
    try:
        log_change(instance, 'delete')
        logger.warning(f"Connector configuration deleted: {instance.name} from organization {instance.organization}")
    except Exception as e:
        logger.warning(f"Failed to log ConnectorConfig deletion: {str(e)}")


def log_ai_governance_activity(activity_type, details, user=None, organization=None):
    """
    Helper function to log AI governance specific activities.
    
    Args:
        activity_type: Type of activity (e.g., 'test_execution', 'model_registration')
        details: Dictionary with activity details
        user: User who performed the activity
        organization: Organization context
    """
    try:
        # Create a custom audit log entry for AI governance activities
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(AuditLog),  # Use AuditLog as content type for custom entries
            object_id=0,  # No specific object ID for custom activities
            action='create',  # Custom activities are treated as 'create' actions
            changes=details,
            object_repr=f"AI Governance Activity: {activity_type}",
            user=user,
            model="ai_governance.activity",
            details={
                'activity_type': activity_type,
                'organization_id': organization.id if organization else None,
                'organization_name': organization.name if organization else None,
                **details
            }
        )
        
        logger.info(f"AI Governance activity logged: {activity_type} by user {user} in organization {organization}")
        
    except Exception as e:
        logger.warning(f"Failed to log AI governance activity: {str(e)}")
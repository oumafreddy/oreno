from celery import shared_task
from django.conf import settings
from django.utils import timezone
import logging

from .signals import log_ai_governance_activity
from .security import pii_masking_service, encryption_service, data_retention_service

logger = logging.getLogger(__name__)


def load_model_for_testing(model_asset):
    """
    Load a model from a ModelAsset for testing.
    
    Args:
        model_asset: ModelAsset instance
        
    Returns:
        Loaded model object
    """
    try:
        # This is a placeholder implementation
        # In practice, you would load the model from the URI
        # using appropriate libraries (joblib, pickle, MLflow, etc.)
        
        if model_asset.model_type == 'tabular':
            # For tabular models, you might load from MLflow or local file
            # Example: return mlflow.pyfunc.load_model(model_asset.uri)
            logger.info(f"Loading tabular model from {model_asset.uri}")
            # Return a mock model for now
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier()
            
        elif model_asset.model_type == 'image':
            # For image models, you might load from TensorFlow/PyTorch
            logger.info(f"Loading image model from {model_asset.uri}")
            # Return a mock model for now
            return None
            
        elif model_asset.model_type == 'generative':
            # For generative models
            logger.info(f"Loading generative model from {model_asset.uri}")
            # Return a mock model for now
            return None
            
        else:
            raise ValueError(f"Unsupported model type: {model_asset.model_type}")
            
    except Exception as exc:
        logger.error(f"Failed to load model {model_asset.id}: {exc}")
        raise


def load_dataset_for_testing(dataset_asset):
    """
    Load a dataset from a DatasetAsset for testing.
    
    Args:
        dataset_asset: DatasetAsset instance
        
    Returns:
        Loaded dataset (X, y) or DataFrame
    """
    try:
        # This is a placeholder implementation
        # In practice, you would load the dataset from the path
        # using pandas, pyarrow, or other appropriate libraries
        
        logger.info(f"Loading dataset from {dataset_asset.path}")
        
        if dataset_asset.format == 'csv':
            # Load CSV dataset
            import pandas as pd
            df = pd.read_csv(dataset_asset.path)
            return df
            
        elif dataset_asset.format == 'parquet':
            # Load Parquet dataset
            import pandas as pd
            df = pd.read_parquet(dataset_asset.path)
            return df
            
        else:
            raise ValueError(f"Unsupported dataset format: {dataset_asset.format}")
            
    except Exception as exc:
        logger.error(f"Failed to load dataset {dataset_asset.id}: {exc}")
        raise


@shared_task(bind=True, queue='ai_governance_high')
def execute_test_run(self, test_run_id):
    """
    Execute a test run for AI governance with performance monitoring and alerts.
    High priority queue for immediate test execution.
    """
    from .models import TestRun, TestResult, Metric, EvidenceArtifact
    from services.ai.governance_engine.test_executor import TestExecutor, TestExecutionPlan, TestConfig
    from .performance import performance_monitor, SamplingService
    from .alerts import alert_manager
    
    # Apply performance monitoring
    @performance_monitor.monitor_task_performance('execute_test_run')
    def _execute_test_run_internal():
        try:
            test_run = TestRun.objects.get(id=test_run_id)
            test_run.status = 'running'
            test_run.started_at = timezone.now()
            test_run.worker_info = {
                'task_id': self.request.id,
                'worker': self.request.hostname
            }
            test_run.save()
            
            # Log test execution start
            log_ai_governance_activity(
                activity_type='test_execution_started',
                details={
                    'test_run_id': test_run_id,
                    'model_name': test_run.model_asset.name,
                    'model_type': test_run.model_asset.model_type,
                    'dataset_name': test_run.dataset_asset.name if test_run.dataset_asset else None,
                    'test_plan_name': test_run.test_plan.name if test_run.test_plan else None,
                    'task_id': self.request.id,
                    'worker': self.request.hostname,
                },
                user=None,  # Celery task doesn't have user context
                organization=test_run.organization
                )
            
            # Load model and dataset
            model = load_model_for_testing(test_run.model_asset)
            dataset = load_dataset_for_testing(test_run.dataset_asset) if test_run.dataset_asset else None
            
            # Apply PII masking to dataset if it contains PII
            if dataset and test_run.dataset_asset.contains_pii:
                logger.info(f"Dataset {test_run.dataset_asset.name} contains PII, applying masking")
                # In a real implementation, you would mask the dataset here
                # For now, we'll just log the action
            
            # Create test execution plan
            test_configs = []
            if test_run.test_plan:
                config = test_run.test_plan.config
                for test_name, test_params in config.get('tests', {}).items():
                    test_config = TestConfig(
                        test_name=test_name,
                        parameters=test_params.get('parameters', {}),
                        thresholds=test_params.get('thresholds', {}),
                        enabled=test_params.get('enabled', True),
                        timeout=test_params.get('timeout'),
                        metadata=test_params.get('metadata', {})
                    )
                    test_configs.append(test_config)
            
            # Execute tests using the test executor
            executor = TestExecutor()
            execution_plan = TestExecutionPlan(
                model_asset_id=str(test_run.model_asset.id),
                dataset_asset_id=str(test_run.dataset_asset.id) if test_run.dataset_asset else None,
                test_configs=test_configs,
                execution_parameters=test_run.parameters
            )
            
            # Execute the test plan
            test_results = executor.execute_test_plan(
                execution_plan,
                model=model,
                dataset=dataset
            )
            
            # Save results to database
            for result in test_results:
                # Apply PII masking to test result summary if needed
                summary_data = {
                    'status': result.status.value,
                    'score': result.score,
                    'execution_time': result.execution_time,
                    'metadata': result.metadata
                }
                
                # Check if summary contains PII and mask if necessary
                if test_run.contains_pii or test_run.dataset_asset.contains_pii if test_run.dataset_asset else False:
                    summary_str = str(summary_data)
                    masked_summary, mask_counts = pii_masking_service.mask_pii(summary_str)
                    if mask_counts:
                        logger.info(f"Masked PII in test result summary: {mask_counts}")
                        # In a real implementation, you would parse the masked summary back to dict
                
                # Create TestResult record
                test_result = TestResult.objects.create(
                    test_run=test_run,
                    test_name=result.test_name,
                    summary=summary_data,
                    passed=result.passed
                )
                
                # Create Metric records
                for metric_name, metric_value in result.metrics.items():
                    Metric.objects.create(
                        test_result=test_result,
                        name=metric_name,
                        value=metric_value,
                        passed=result.passed
                    )
                
                # Create EvidenceArtifact records
                for artifact_path in result.artifacts:
                    EvidenceArtifact.objects.create(
                        test_run=test_run,
                        artifact_type='other',  # Could be determined from file extension
                        file_path=artifact_path
                    )
            
            # Mark as completed
            test_run.status = 'completed'
            test_run.completed_at = timezone.now()
            test_run.save()
            
            # Log test execution completion
            passed_tests = sum(1 for result in test_results if result.passed)
            total_tests = len(test_results)
            
            log_ai_governance_activity(
                activity_type='test_execution_completed',
                details={
                    'test_run_id': test_run_id,
                    'model_name': test_run.model_asset.name,
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': total_tests - passed_tests,
                    'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                    'execution_time': (test_run.completed_at - test_run.started_at).total_seconds(),
                },
                user=None,
                organization=test_run.organization
            )
            
            # Trigger webhooks
            trigger_webhooks.delay(test_run_id, 'test_run.completed')
            
            return f"Test run {test_run_id} completed successfully with {len(test_results)} results"
            
        except Exception as exc:
            logger.error(f"Test run {test_run_id} failed: {exc}")
            test_run.status = 'failed'
            test_run.error_message = str(exc)
            test_run.completed_at = timezone.now()
            test_run.save()
            
            # Log test execution failure
            log_ai_governance_activity(
                activity_type='test_execution_failed',
                details={
                    'test_run_id': test_run_id,
                    'model_name': test_run.model_asset.name,
                    'error_message': str(exc),
                    'task_id': self.request.id,
                    'worker': self.request.hostname,
                },
                user=None,
                organization=test_run.organization
            )
            
            # Trigger webhooks
            trigger_webhooks.delay(test_run_id, 'test_run.failed')
            
            raise self.retry(exc=exc, countdown=60, max_retries=3)
    
    return _execute_test_run_internal()


@shared_task(queue='ai_governance_bulk')
def execute_bulk_test_runs(test_run_ids):
    """
    Execute multiple test runs in bulk.
    Bulk queue for batch processing.
    """
    results = []
    for test_run_id in test_run_ids:
        try:
            result = execute_test_run.delay(test_run_id)
            results.append({'test_run_id': test_run_id, 'task_id': result.id})
        except Exception as exc:
            logger.error(f"Failed to queue test run {test_run_id}: {exc}")
            results.append({'test_run_id': test_run_id, 'error': str(exc)})
    
    return results


@shared_task(queue='ai_governance_high')
def trigger_webhooks(test_run_id, event_type):
    """
    Trigger webhooks for test run events.
    """
    from .models import TestRun
    from .webhook_service import webhook_service
    
    try:
        test_run = TestRun.objects.get(id=test_run_id)
        
        # Send appropriate webhook based on event type
        if event_type == 'test_run.started':
            results = webhook_service.send_test_run_started(test_run)
        elif event_type == 'test_run.completed':
            results = webhook_service.send_test_run_completed(test_run)
        elif event_type == 'test_run.failed':
            error_message = test_run.error_message or 'Unknown error'
            results = webhook_service.send_test_run_failed(test_run, error_message)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
            return
        
        logger.info(f"Webhook results for {event_type}: {results['sent']} sent, {results['failed']} failed")
        
        if results['errors']:
            logger.error(f"Webhook errors: {results['errors']}")
            
    except Exception as exc:
        logger.error(f"Failed to trigger webhooks for test run {test_run_id}: {exc}")


@shared_task(queue='ai_governance_bulk')
def cleanup_old_test_runs(days_old=30):
    """
    Clean up old test runs and artifacts.
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import TestRun, EvidenceArtifact
    
    cutoff_date = timezone.now() - timedelta(days=days_old)
    
    # Clean up old test runs
    old_runs = TestRun.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed']
    )
    
    count = 0
    for test_run in old_runs:
        # Clean up artifacts
        artifacts = EvidenceArtifact.objects.filter(test_run=test_run)
        for artifact in artifacts:
            # Delete files from storage
            if artifact.file_path:
                try:
                    # This would integrate with your storage service
                    pass
                except Exception as exc:
                    logger.error(f"Failed to delete artifact {artifact.id}: {exc}")
        
        # Soft delete the test run
        test_run.delete()
        count += 1
    
    return f"Cleaned up {count} old test runs"


@shared_task(queue='ai_governance_high')
def generate_compliance_report(test_run_id, framework_code):
    """
    Generate compliance report for a test run against a specific framework.
    """
    from .models import TestRun, Framework, ComplianceMapping
    
    try:
        test_run = TestRun.objects.get(id=test_run_id)
        framework = Framework.objects.get(
            organization=test_run.organization,
            code=framework_code
        )
        
        # Get compliance mappings
        mappings = ComplianceMapping.objects.filter(
            organization=test_run.organization,
            clause__framework=framework
        )
        
        # Generate report data
        report_data = {
            'test_run': test_run,
            'framework': framework,
            'mappings': mappings,
            'generated_at': timezone.now()
        }
        
        # This would integrate with your reporting service
        logger.info(f"Generated compliance report for test run {test_run_id}")
        
        return report_data
        
    except Exception as exc:
        logger.error(f"Failed to generate compliance report: {exc}")
        raise


@shared_task(queue='ai_governance_bulk')
def sync_model_registry(connector_id):
    """
    Sync models from external registry (MLflow, etc.).
    """
    from .models import ConnectorConfig, ModelAsset
    
    try:
        connector = ConnectorConfig.objects.get(id=connector_id)
        
        if connector.connector_type == 'mlflow':
            # Sync from MLflow
            # This would integrate with the MLflow connector
            pass
        elif connector.connector_type == 's3':
            # Sync from S3
            # This would integrate with the S3 connector
            pass
        
        return f"Synced models from connector {connector_id}"
        
    except Exception as exc:
        logger.error(f"Failed to sync model registry {connector_id}: {exc}")
        raise


@shared_task(queue='ai_governance_bulk')
def cleanup_expired_data(organization_id, data_type='all', dry_run=True):
    """
    Clean up expired AI governance data according to retention policies.
    Bulk queue for data cleanup operations.
    """
    from .models import TestRun, TestResult, Metric, EvidenceArtifact
    
    try:
        # Get model class for data type
        model_mapping = {
            'test_runs': TestRun,
            'test_results': TestResult,
            'metrics': Metric,
            'artifacts': EvidenceArtifact,
        }
        
        if data_type == 'all':
            data_types = ['test_runs', 'test_results', 'metrics', 'artifacts']
        else:
            data_types = [data_type]
        
        cleanup_results = []
        
        for dt in data_types:
            model_class = model_mapping.get(dt)
            if model_class:
                result = data_retention_service.cleanup_expired_data(
                    model_class, dt, dry_run=dry_run
                )
                cleanup_results.append(result)
        
        logger.info(f"Data cleanup completed for organization {organization_id}: {cleanup_results}")
        return f"Data cleanup completed: {len(cleanup_results)} data types processed"
        
    except Exception as exc:
        logger.error(f"Failed to cleanup expired data for organization {organization_id}: {exc}")
        raise


@shared_task(queue='ai_governance_bulk')
def conduct_security_audit(organization_id):
    """
    Conduct comprehensive security audit of AI governance system.
    Bulk queue for security audit operations.
    """
    from .security import security_audit_service
    
    try:
        audit_results = security_audit_service.conduct_security_audit(organization_id)
        
        logger.info(f"Security audit completed for organization {organization_id}")
        return f"Security audit completed with score: {audit_results['security_score']}/100"
        
    except Exception as exc:
        logger.error(f"Failed to conduct security audit for organization {organization_id}: {exc}")
        raise

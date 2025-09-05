from celery import shared_task
from django.conf import settings
from django.utils import timezone
import logging

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
    Execute a test run for AI governance.
    High priority queue for immediate test execution.
    """
    from .models import TestRun, TestResult, Metric, EvidenceArtifact
    from services.ai.governance_engine.test_executor import TestExecutor, TestExecutionPlan, TestConfig
    
    try:
        test_run = TestRun.objects.get(id=test_run_id)
        test_run.status = 'running'
        test_run.started_at = timezone.now()
        test_run.worker_info = {
            'task_id': self.request.id,
            'worker': self.request.hostname
        }
        test_run.save()
        
        # Load model and dataset
        model = load_model_for_testing(test_run.model_asset)
        dataset = load_dataset_for_testing(test_run.dataset_asset) if test_run.dataset_asset else None
        
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
            # Create TestResult record
            test_result = TestResult.objects.create(
                test_run=test_run,
                test_name=result.test_name,
                summary={
                    'status': result.status.value,
                    'score': result.score,
                    'execution_time': result.execution_time,
                    'metadata': result.metadata
                },
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
        
        # Trigger webhooks
        trigger_webhooks.delay(test_run_id, 'test_run.completed')
        
        return f"Test run {test_run_id} completed successfully with {len(test_results)} results"
        
    except Exception as exc:
        logger.error(f"Test run {test_run_id} failed: {exc}")
        test_run.status = 'failed'
        test_run.error_message = str(exc)
        test_run.completed_at = timezone.now()
        test_run.save()
        
        # Trigger webhooks
        trigger_webhooks.delay(test_run_id, 'test_run.failed')
        
        raise self.retry(exc=exc, countdown=60, max_retries=3)


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
    from .models import TestRun, WebhookSubscription
    
    try:
        test_run = TestRun.objects.get(id=test_run_id)
        webhooks = WebhookSubscription.objects.filter(
            organization=test_run.organization,
            is_active=True,
            events__contains=[event_type]
        )
        
        for webhook in webhooks:
            # Send webhook notification
            # This would integrate with your webhook service
            logger.info(f"Triggering webhook {webhook.url} for event {event_type}")
            
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

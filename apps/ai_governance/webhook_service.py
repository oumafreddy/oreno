"""
Webhook service for AI governance events.
Handles sending webhook notifications for test run events and compliance alerts.
Follows the same patterns as other services in the project.
"""

import json
import logging
import requests
import hashlib
import hmac
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import WebhookSubscription, TestRun, TestResult

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Service for sending webhook notifications for AI governance events.
    """
    
    def __init__(self):
        self.timeout = getattr(settings, 'WEBHOOK_TIMEOUT', 30)
        self.max_retries = getattr(settings, 'WEBHOOK_MAX_RETRIES', 3)
    
    def send_test_run_started(self, test_run: TestRun) -> Dict[str, Any]:
        """Send webhook notification for test run started event."""
        payload = self._build_test_run_payload(test_run, 'test_run.started')
        return self._send_webhooks('test_run.started', payload, test_run.organization)
    
    def send_test_run_completed(self, test_run: TestRun) -> Dict[str, Any]:
        """Send webhook notification for test run completed event."""
        payload = self._build_test_run_payload(test_run, 'test_run.completed')
        
        # Add test results summary
        results = TestResult.objects.filter(test_run=test_run)
        payload['test_results'] = {
            'total_tests': results.count(),
            'passed_tests': results.filter(passed=True).count(),
            'failed_tests': results.filter(passed=False).count(),
            'success_rate': (results.filter(passed=True).count() / results.count() * 100) if results.count() > 0 else 0
        }
        
        return self._send_webhooks('test_run.completed', payload, test_run.organization)
    
    def send_test_run_failed(self, test_run: TestRun, error_message: str) -> Dict[str, Any]:
        """Send webhook notification for test run failed event."""
        payload = self._build_test_run_payload(test_run, 'test_run.failed')
        payload['error_message'] = error_message
        return self._send_webhooks('test_run.failed', payload, test_run.organization)
    
    def send_threshold_breached(self, test_run: TestRun, metric_name: str, threshold: float, actual_value: float) -> Dict[str, Any]:
        """Send webhook notification for threshold breach event."""
        payload = self._build_test_run_payload(test_run, 'thresholds.breached')
        payload['threshold_breach'] = {
            'metric_name': metric_name,
            'threshold': threshold,
            'actual_value': actual_value,
            'breach_severity': self._calculate_breach_severity(threshold, actual_value)
        }
        return self._send_webhooks('thresholds.breached', payload, test_run.organization)
    
    def send_evidence_published(self, test_run: TestRun, artifact_count: int) -> Dict[str, Any]:
        """Send webhook notification for evidence published event."""
        payload = self._build_test_run_payload(test_run, 'evidence.published')
        payload['evidence'] = {
            'artifact_count': artifact_count,
            'published_at': timezone.now().isoformat()
        }
        return self._send_webhooks('evidence.published', payload, test_run.organization)
    
    def _build_test_run_payload(self, test_run: TestRun, event_type: str) -> Dict[str, Any]:
        """Build standard payload for test run events."""
        return {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'organization': {
                'id': test_run.organization.id,
                'name': test_run.organization.name,
                'code': getattr(test_run.organization, 'code', None)
            },
            'test_run': {
                'id': test_run.id,
                'status': test_run.status,
                'created_at': test_run.created_at.isoformat(),
                'started_at': test_run.started_at.isoformat() if test_run.started_at else None,
                'completed_at': test_run.completed_at.isoformat() if test_run.completed_at else None,
                'parameters': test_run.parameters
            },
            'model_asset': {
                'id': test_run.model_asset.id,
                'name': test_run.model_asset.name,
                'model_type': test_run.model_asset.model_type,
                'version': test_run.model_asset.version
            },
            'dataset_asset': {
                'id': test_run.dataset_asset.id,
                'name': test_run.dataset_asset.name,
                'role': test_run.dataset_asset.role
            } if test_run.dataset_asset else None,
            'test_plan': {
                'id': test_run.test_plan.id,
                'name': test_run.test_plan.name
            } if test_run.test_plan else None
        }
    
    def _send_webhooks(self, event_type: str, payload: Dict[str, Any], organization) -> Dict[str, Any]:
        """Send webhooks to all active subscriptions for the event type."""
        webhooks = WebhookSubscription.objects.filter(
            organization=organization,
            is_active=True,
            events__contains=[event_type]
        )
        
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for webhook in webhooks:
            try:
                success = self._send_webhook(webhook, payload)
                if success:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f'Webhook {webhook.url}: {str(e)}')
                logger.error(f'Failed to send webhook to {webhook.url}: {e}')
        
        return results
    
    def _send_webhook(self, webhook: WebhookSubscription, payload: Dict[str, Any]) -> bool:
        """Send webhook to a specific subscription."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Oreno-AI-Governance/1.0'
        }
        
        # Add signature if secret is configured
        if webhook.secret:
            signature = self._generate_signature(payload, webhook.secret)
            headers['X-Webhook-Signature'] = f'sha256={signature}'
        
        try:
            response = requests.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Consider 2xx status codes as success
            if 200 <= response.status_code < 300:
                logger.info(f'Webhook sent successfully to {webhook.url}')
                return True
            else:
                logger.warning(f'Webhook failed with status {response.status_code}: {response.text}')
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Webhook request failed to {webhook.url}: {e}')
            return False
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _calculate_breach_severity(self, threshold: float, actual_value: float) -> str:
        """Calculate severity of threshold breach."""
        if threshold == 0:
            return 'high' if actual_value > 0 else 'low'
        
        ratio = abs(actual_value - threshold) / abs(threshold)
        
        if ratio >= 0.5:  # 50% or more deviation
            return 'high'
        elif ratio >= 0.2:  # 20% or more deviation
            return 'medium'
        else:
            return 'low'
    
    def test_webhook(self, webhook: WebhookSubscription) -> Dict[str, Any]:
        """Test webhook endpoint with a sample payload."""
        test_payload = {
            'event_type': 'webhook.test',
            'timestamp': timezone.now().isoformat(),
            'message': 'This is a test webhook from Oreno AI Governance',
            'organization': {
                'id': webhook.organization.id,
                'name': webhook.organization.name
            }
        }
        
        try:
            success = self._send_webhook(webhook, test_payload)
            return {
                'success': success,
                'message': 'Webhook test completed' if success else 'Webhook test failed'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Webhook test failed: {str(e)}'
            }


# Global webhook service instance
webhook_service = WebhookService()

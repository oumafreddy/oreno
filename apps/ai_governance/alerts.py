"""
Alert and notification system for AI governance.
Follows the same patterns as other apps in the project.
"""

import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from core.utils import send_tenant_email as send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import TestRun, TestResult, Metric, WebhookSubscription
from .webhook_service import webhook_service

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alerts and notifications for AI governance events.
    """
    
    def __init__(self):
        self.alert_cooldown = getattr(settings, 'AI_GOVERNANCE_ALERT_COOLDOWN', 300)  # 5 minutes
        self.max_alerts_per_hour = getattr(settings, 'AI_GOVERNANCE_MAX_ALERTS_PER_HOUR', 10)
    
    def send_test_failure_alert(self, test_run: TestRun, failed_tests: List[TestResult]) -> Dict[str, Any]:
        """Send alert for test failures."""
        alert_data = {
            'alert_type': 'test_failure',
            'test_run_id': test_run.id,
            'model_name': test_run.model_asset.name,
            'failed_tests': [
                {
                    'test_name': test.name,
                    'error_message': test.summary.get('error', 'Unknown error')
                }
                for test in failed_tests
            ],
            'organization': test_run.organization.name,
            'timestamp': timezone.now().isoformat()
        }
        
        # Send webhook notifications
        webhook_results = webhook_service.send_test_run_failed(
            test_run, 
            f"{len(failed_tests)} tests failed"
        )
        
        # Send email notifications (if configured)
        email_results = self._send_email_alert('test_failure', alert_data, test_run.organization)
        
        return {
            'webhook_results': webhook_results,
            'email_results': email_results,
            'alert_sent': True
        }
    
    def send_threshold_breach_alert(self, test_run: TestRun, metric: Metric) -> Dict[str, Any]:
        """Send alert for threshold breaches."""
        alert_data = {
            'alert_type': 'threshold_breach',
            'test_run_id': test_run.id,
            'model_name': test_run.model_asset.name,
            'metric_name': metric.name,
            'metric_value': metric.value,
            'threshold': metric.threshold,
            'breach_severity': self._calculate_breach_severity(metric.threshold, metric.value),
            'organization': test_run.organization.name,
            'timestamp': timezone.now().isoformat()
        }
        
        # Send webhook notifications
        webhook_results = webhook_service.send_threshold_breached(
            test_run,
            metric.name,
            metric.threshold,
            metric.value
        )
        
        # Send email notifications (if configured)
        email_results = self._send_email_alert('threshold_breach', alert_data, test_run.organization)
        
        return {
            'webhook_results': webhook_results,
            'email_results': email_results,
            'alert_sent': True
        }
    
    def send_compliance_violation_alert(self, test_run: TestRun, violation_details: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert for compliance violations."""
        alert_data = {
            'alert_type': 'compliance_violation',
            'test_run_id': test_run.id,
            'model_name': test_run.model_asset.name,
            'violation_details': violation_details,
            'organization': test_run.organization.name,
            'timestamp': timezone.now().isoformat()
        }
        
        # Send webhook notifications
        webhook_results = webhook_service.send_test_run_failed(
            test_run,
            f"Compliance violation: {violation_details.get('framework', 'Unknown framework')}"
        )
        
        # Send email notifications (if configured)
        email_results = self._send_email_alert('compliance_violation', alert_data, test_run.organization)
        
        return {
            'webhook_results': webhook_results,
            'email_results': email_results,
            'alert_sent': True
        }
    
    def send_performance_degradation_alert(self, test_run: TestRun, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert for performance degradation."""
        alert_data = {
            'alert_type': 'performance_degradation',
            'test_run_id': test_run.id,
            'model_name': test_run.model_asset.name,
            'performance_metrics': performance_metrics,
            'organization': test_run.organization.name,
            'timestamp': timezone.now().isoformat()
        }
        
        # Send webhook notifications
        webhook_results = webhook_service.send_test_run_failed(
            test_run,
            f"Performance degradation detected: {performance_metrics.get('degradation_percent', 0)}%"
        )
        
        # Send email notifications (if configured)
        email_results = self._send_email_alert('performance_degradation', alert_data, test_run.organization)
        
        return {
            'webhook_results': webhook_results,
            'email_results': email_results,
            'alert_sent': True
        }
    
    def _send_email_alert(self, alert_type: str, alert_data: Dict[str, Any], organization) -> Dict[str, Any]:
        """Send email alert to organization administrators."""
        try:
            # Get organization administrators
            admin_emails = self._get_admin_emails(organization)
            
            if not admin_emails:
                return {'sent': 0, 'failed': 0, 'errors': ['No admin emails found']}
            
            # Prepare email content
            subject = f"AI Governance Alert: {alert_type.replace('_', ' ').title()}"
            context = {
                'alert_data': alert_data,
                'organization': organization,
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
            }
            
            # Render email template
            html_message = render_to_string('ai_governance/emails/alert.html', context)
            plain_message = render_to_string('ai_governance/emails/alert.txt', context)
            
            # Send email
            sent_count = send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@oreno.com'),
                recipient_list=admin_emails,
                html_message=html_message,
                fail_silently=False
            )
            
            return {
                'sent': sent_count,
                'failed': len(admin_emails) - sent_count,
                'errors': []
            }
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return {
                'sent': 0,
                'failed': 1,
                'errors': [str(e)]
            }
    
    def _get_admin_emails(self, organization) -> List[str]:
        """Get admin email addresses for an organization."""
        try:
            from users.models import CustomUser
            
            admin_users = CustomUser.objects.filter(
                organization=organization,
                role='admin',
                is_active=True
            ).values_list('email', flat=True)
            
            return list(admin_users)
            
        except Exception as e:
            logger.error(f"Failed to get admin emails: {e}")
            return []
    
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


class SLOMonitor:
    """
    Service Level Objective monitoring for AI governance.
    """
    
    def __init__(self):
        self.slo_targets = {
            'test_execution_time': 300,  # 5 minutes
            'test_success_rate': 95.0,  # 95%
            'compliance_score': 90.0,   # 90%
            'alert_response_time': 60,  # 1 minute
        }
    
    def check_slo_compliance(self, organization_id: int) -> Dict[str, Any]:
        """Check SLO compliance for an organization."""
        from .models import TestRun, TestResult
        
        # Get recent test runs (last 24 hours)
        recent_runs = TestRun.objects.filter(
            organization_id=organization_id,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        )
        
        slo_results = {}
        
        # Test execution time SLO
        execution_times = []
        for run in recent_runs.filter(status='completed'):
            if run.started_at and run.completed_at:
                execution_time = (run.completed_at - run.started_at).total_seconds()
                execution_times.append(execution_time)
        
        if execution_times:
            avg_execution_time = sum(execution_times) / len(execution_times)
            slo_results['test_execution_time'] = {
                'current': avg_execution_time,
                'target': self.slo_targets['test_execution_time'],
                'compliant': avg_execution_time <= self.slo_targets['test_execution_time'],
                'percentage': (avg_execution_time / self.slo_targets['test_execution_time']) * 100
            }
        
        # Test success rate SLO
        total_runs = recent_runs.count()
        successful_runs = recent_runs.filter(status='completed').count()
        
        if total_runs > 0:
            success_rate = (successful_runs / total_runs) * 100
            slo_results['test_success_rate'] = {
                'current': success_rate,
                'target': self.slo_targets['test_success_rate'],
                'compliant': success_rate >= self.slo_targets['test_success_rate'],
                'percentage': (success_rate / self.slo_targets['test_success_rate']) * 100
            }
        
        # Overall SLO compliance
        compliant_slos = sum(1 for slo in slo_results.values() if slo['compliant'])
        total_slos = len(slo_results)
        
        slo_results['overall_compliance'] = {
            'compliant_slos': compliant_slos,
            'total_slos': total_slos,
            'compliance_percentage': (compliant_slos / total_slos * 100) if total_slos > 0 else 0
        }
        
        return slo_results
    
    def get_slo_metrics(self, organization_id: int) -> Dict[str, Any]:
        """Get SLO metrics for dashboard display."""
        slo_results = self.check_slo_compliance(organization_id)
        
        return {
            'slo_status': slo_results,
            'last_checked': timezone.now().isoformat(),
            'next_check': (timezone.now() + timezone.timedelta(hours=1)).isoformat()
        }


# Global instances
alert_manager = AlertManager()
slo_monitor = SLOMonitor()

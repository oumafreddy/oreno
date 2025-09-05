"""
Performance monitoring and caching utilities for AI governance.
Follows the same patterns as other apps in the project.
"""

import time
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.db import connection
from django.core.cache.utils import make_template_fragment_key

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance monitoring utilities for AI governance operations.
    """
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'AI_GOVERNANCE_CACHE_TIMEOUT', 300)  # 5 minutes
        self.slow_query_threshold = getattr(settings, 'AI_GOVERNANCE_SLOW_QUERY_THRESHOLD', 1.0)  # 1 second
    
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key for AI governance data."""
        key_parts = [f'ai_gov_{prefix}']
        
        # Add organization ID if available
        if 'organization_id' in kwargs:
            key_parts.append(f'org_{kwargs["organization_id"]}')
        
        # Add other key components
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))
        
        return ':'.join(key_parts)
    
    def get_cached_metrics(self, organization_id: int, metric_type: str) -> Optional[Dict[str, Any]]:
        """Get cached metrics for an organization."""
        cache_key = self.cache_key('metrics', metric_type, organization_id=organization_id)
        return cache.get(cache_key)
    
    def set_cached_metrics(self, organization_id: int, metric_type: str, data: Dict[str, Any], timeout: Optional[int] = None):
        """Cache metrics for an organization."""
        cache_key = self.cache_key('metrics', metric_type, organization_id=organization_id)
        cache.set(cache_key, data, timeout or self.cache_timeout)
    
    def invalidate_metrics_cache(self, organization_id: int, metric_type: Optional[str] = None):
        """Invalidate cached metrics."""
        if metric_type:
            cache_key = self.cache_key('metrics', metric_type, organization_id=organization_id)
            cache.delete(cache_key)
        else:
            # Invalidate all metrics for organization
            cache_key_pattern = self.cache_key('metrics', '*', organization_id=organization_id)
            cache.delete_many(cache.keys(cache_key_pattern))
    
    def monitor_query_performance(self, query_name: str):
        """Decorator to monitor database query performance."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_queries = len(connection.queries)
                
                try:
                    result = func(*args, **kwargs)
                    
                    execution_time = time.time() - start_time
                    query_count = len(connection.queries) - start_queries
                    
                    # Log slow queries
                    if execution_time > self.slow_query_threshold:
                        logger.warning(
                            f'Slow AI governance query: {query_name} took {execution_time:.2f}s '
                            f'with {query_count} queries'
                        )
                    
                    # Log performance metrics
                    logger.info(
                        f'AI governance query: {query_name} - '
                        f'Time: {execution_time:.3f}s, Queries: {query_count}'
                    )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(
                        f'AI governance query failed: {query_name} - '
                        f'Time: {execution_time:.3f}s, Error: {str(e)}'
                    )
                    raise
                    
            return wrapper
        return decorator
    
    def monitor_task_performance(self, task_name: str):
        """Decorator to monitor Celery task performance."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    execution_time = time.time() - start_time
                    
                    # Log task performance
                    logger.info(
                        f'AI governance task: {task_name} - '
                        f'Time: {execution_time:.3f}s, Status: completed'
                    )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(
                        f'AI governance task failed: {task_name} - '
                        f'Time: {execution_time:.3f}s, Error: {str(e)}'
                    )
                    raise
                    
            return wrapper
        return decorator


class MetricsCollector:
    """
    Collect and aggregate AI governance metrics.
    """
    
    def __init__(self, organization_id: int):
        self.organization_id = organization_id
        self.monitor = PerformanceMonitor()
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get cached dashboard metrics or compute if not cached."""
        cached_metrics = self.monitor.get_cached_metrics(self.organization_id, 'dashboard')
        if cached_metrics:
            return cached_metrics
        
        # Compute metrics
        from .models import ModelAsset, TestRun, TestResult, Metric
        
        metrics = {
            'total_models': ModelAsset.objects.filter(organization_id=self.organization_id).count(),
            'total_test_runs': TestRun.objects.filter(organization_id=self.organization_id).count(),
            'recent_test_runs': TestRun.objects.filter(
                organization_id=self.organization_id,
                created_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).count(),
            'total_metrics': Metric.objects.filter(organization_id=self.organization_id).count(),
            'computed_at': timezone.now().isoformat()
        }
        
        # Cache the results
        self.monitor.set_cached_metrics(self.organization_id, 'dashboard', metrics)
        
        return metrics
    
    def get_test_performance_metrics(self) -> Dict[str, Any]:
        """Get test execution performance metrics."""
        cached_metrics = self.monitor.get_cached_metrics(self.organization_id, 'test_performance')
        if cached_metrics:
            return cached_metrics
        
        from .models import TestRun, TestResult
        
        # Get recent test runs
        recent_runs = TestRun.objects.filter(
            organization_id=self.organization_id,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        )
        
        metrics = {
            'total_runs': recent_runs.count(),
            'completed_runs': recent_runs.filter(status='completed').count(),
            'failed_runs': recent_runs.filter(status='failed').count(),
            'avg_execution_time': self._calculate_avg_execution_time(recent_runs),
            'success_rate': self._calculate_success_rate(recent_runs),
            'computed_at': timezone.now().isoformat()
        }
        
        # Cache the results
        self.monitor.set_cached_metrics(self.organization_id, 'test_performance', metrics)
        
        return metrics
    
    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance framework metrics."""
        cached_metrics = self.monitor.get_cached_metrics(self.organization_id, 'compliance')
        if cached_metrics:
            return cached_metrics
        
        from .models import Framework, ComplianceMapping, TestResult
        
        # Get framework compliance scores
        frameworks = Framework.objects.filter(organization_id=self.organization_id)
        compliance_scores = {}
        
        for framework in frameworks:
            # Get test results for this framework
            mappings = ComplianceMapping.objects.filter(
                organization_id=self.organization_id,
                clause__framework=framework
            )
            
            if mappings.exists():
                # Calculate compliance score based on test results
                total_tests = 0
                passed_tests = 0
                
                for mapping in mappings:
                    test_results = TestResult.objects.filter(
                        test_run__organization_id=self.organization_id,
                        test_name=mapping.test_name,
                        created_at__gte=timezone.now() - timezone.timedelta(days=30)
                    )
                    
                    total_tests += test_results.count()
                    passed_tests += test_results.filter(passed=True).count()
                
                compliance_scores[framework.code] = {
                    'score': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                    'total_tests': total_tests,
                    'passed_tests': passed_tests
                }
        
        metrics = {
            'frameworks': compliance_scores,
            'overall_score': sum(s['score'] for s in compliance_scores.values()) / len(compliance_scores) if compliance_scores else 0,
            'computed_at': timezone.now().isoformat()
        }
        
        # Cache the results
        self.monitor.set_cached_metrics(self.organization_id, 'compliance', metrics)
        
        return metrics
    
    def _calculate_avg_execution_time(self, test_runs) -> float:
        """Calculate average execution time for test runs."""
        completed_runs = test_runs.filter(
            status='completed',
            started_at__isnull=False,
            completed_at__isnull=False
        )
        
        if not completed_runs.exists():
            return 0.0
        
        total_time = 0
        count = 0
        
        for run in completed_runs:
            if run.started_at and run.completed_at:
                execution_time = (run.completed_at - run.started_at).total_seconds()
                total_time += execution_time
                count += 1
        
        return total_time / count if count > 0 else 0.0
    
    def _calculate_success_rate(self, test_runs) -> float:
        """Calculate success rate for test runs."""
        total_runs = test_runs.count()
        if total_runs == 0:
            return 0.0
        
        successful_runs = test_runs.filter(status='completed').count()
        return (successful_runs / total_runs) * 100


class SamplingService:
    """
    Service for intelligent sampling of test data to improve performance.
    """
    
    def __init__(self):
        self.default_sample_size = getattr(settings, 'AI_GOVERNANCE_DEFAULT_SAMPLE_SIZE', 1000)
        self.max_sample_size = getattr(settings, 'AI_GOVERNANCE_MAX_SAMPLE_SIZE', 10000)
    
    def get_sample_size(self, total_size: int, test_type: str) -> int:
        """Determine appropriate sample size based on total data size and test type."""
        if total_size <= self.default_sample_size:
            return total_size
        
        # Adjust sample size based on test type
        if test_type in ['fairness', 'explainability']:
            # These tests need more data for reliable results
            return min(total_size, self.max_sample_size)
        elif test_type in ['robustness', 'privacy']:
            # These tests can work with smaller samples
            return min(total_size, self.default_sample_size)
        else:
            return min(total_size, self.default_sample_size)
    
    def should_sample(self, total_size: int, test_type: str) -> bool:
        """Determine if sampling should be used."""
        return total_size > self.get_sample_size(total_size, test_type)
    
    def get_sampling_strategy(self, test_type: str) -> str:
        """Get sampling strategy for test type."""
        strategies = {
            'fairness': 'stratified',  # Maintain demographic balance
            'explainability': 'random',  # Random sampling for generalizability
            'robustness': 'adversarial',  # Focus on edge cases
            'privacy': 'sensitive'  # Focus on sensitive data points
        }
        return strategies.get(test_type, 'random')


# Global instances
performance_monitor = PerformanceMonitor()

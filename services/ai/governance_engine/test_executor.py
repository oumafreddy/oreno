"""
Test execution engine for AI governance testing.
Orchestrates test adapters and manages test execution workflow.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import time

from test_adapters import (
    BaseTestAdapter,
    TestResult,
    TestConfig,
    FairnessTestAdapter,
    ExplainabilityTestAdapter,
    RobustnessTestAdapter,
    PrivacyTestAdapter
)

logger = logging.getLogger(__name__)


@dataclass
class TestExecutionPlan:
    """Plan for executing multiple tests."""
    model_asset_id: str
    dataset_asset_id: Optional[str]
    test_configs: List[TestConfig]
    execution_parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.execution_parameters is None:
            self.execution_parameters = {}


class TestExecutor:
    """
    Main test execution engine for AI governance.
    
    Manages test adapters, coordinates test execution,
    and handles result aggregation.
    """

    def __init__(self):
        """Initialize the test executor with available adapters."""
        self.adapters = {
            'fairness': FairnessTestAdapter(),
            'explainability': ExplainabilityTestAdapter(),
            'robustness': RobustnessTestAdapter(),
            'privacy': PrivacyTestAdapter()
        }
        self.logger = logging.getLogger(__name__)

    def get_available_tests(self, model_type: str) -> Dict[str, List[str]]:
        """
        Get all available tests for a given model type.
        
        Args:
            model_type: Type of model (tabular, image, generative)
            
        Returns:
            Dictionary mapping adapter names to available tests
        """
        available_tests = {}
        
        for adapter_name, adapter in self.adapters.items():
            if model_type in adapter.supported_model_types:
                available_tests[adapter_name] = adapter.get_available_tests()
        
        return available_tests

    def validate_test_plan(self, test_plan: TestExecutionPlan) -> Dict[str, Any]:
        """
        Validate a test execution plan.
        
        Args:
            test_plan: Test execution plan to validate
            
        Returns:
            Validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "adapter_availability": {}
        }
        
        # Check if adapters are available for each test
        for test_config in test_plan.test_configs:
            adapter_name = self._get_adapter_name_from_test(test_config.test_name)
            
            if adapter_name not in self.adapters:
                validation_results["errors"].append(
                    f"No adapter available for test: {test_config.test_name}"
                )
                validation_results["valid"] = False
                continue
            
            adapter = self.adapters[adapter_name]
            
            # Validate test configuration
            if not adapter.validate_config(test_config):
                validation_results["errors"].append(
                    f"Invalid configuration for test: {test_config.test_name}"
                )
                validation_results["valid"] = False
            
            # Check adapter availability
            validation_results["adapter_availability"][adapter_name] = True
        
        return validation_results

    def execute_test_plan(
        self,
        test_plan: TestExecutionPlan,
        model: Any,
        dataset: Any = None,
        progress_callback: Optional[callable] = None
    ) -> List[TestResult]:
        """
        Execute a complete test plan.
        
        Args:
            test_plan: Test execution plan
            model: Model to test
            dataset: Dataset to use for testing
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of test results
        """
        self.logger.info(f"Starting test execution for model {test_plan.model_asset_id}")
        
        # Validate test plan
        validation = self.validate_test_plan(test_plan)
        if not validation["valid"]:
            raise ValueError(f"Invalid test plan: {validation['errors']}")
        
        # Group tests by adapter for efficient execution
        tests_by_adapter = self._group_tests_by_adapter(test_plan.test_configs)
        
        all_results = []
        total_tests = len(test_plan.test_configs)
        completed_tests = 0
        
        # Execute tests by adapter
        for adapter_name, test_configs in tests_by_adapter.items():
            adapter = self.adapters[adapter_name]
            
            self.logger.info(f"Executing {len(test_configs)} tests with {adapter_name} adapter")
            
            try:
                # Execute tests with this adapter
                results = adapter.execute_tests(
                    model=model,
                    dataset=dataset,
                    test_configs=test_configs,
                    **test_plan.execution_parameters
                )
                
                all_results.extend(results)
                completed_tests += len(test_configs)
                
                # Update progress
                if progress_callback:
                    progress_callback(completed_tests, total_tests, adapter_name)
                
            except Exception as exc:
                self.logger.error(f"Adapter {adapter_name} failed: {exc}")
                
                # Create failed results for all tests in this adapter
                for test_config in test_configs:
                    failed_result = TestResult(
                        test_name=test_config.test_name,
                        status="failed",
                        passed=False,
                        error_message=f"Adapter execution failed: {str(exc)}"
                    )
                    all_results.append(failed_result)
                    completed_tests += 1
                    
                    if progress_callback:
                        progress_callback(completed_tests, total_tests, adapter_name)
        
        self.logger.info(f"Test execution completed. {len(all_results)} results generated.")
        
        return all_results

    def execute_single_test(
        self,
        test_name: str,
        model: Any,
        dataset: Any,
        test_config: TestConfig,
        **kwargs
    ) -> TestResult:
        """
        Execute a single test.
        
        Args:
            test_name: Name of the test to execute
            model: Model to test
            dataset: Dataset to use for testing
            test_config: Test configuration
            **kwargs: Additional parameters
            
        Returns:
            Test result
        """
        adapter_name = self._get_adapter_name_from_test(test_name)
        
        if adapter_name not in self.adapters:
            return TestResult(
                test_name=test_name,
                status="failed",
                passed=False,
                error_message=f"No adapter available for test: {test_name}"
            )
        
        adapter = self.adapters[adapter_name]
        
        try:
            return adapter.execute_test(
                model=model,
                dataset=dataset,
                test_config=test_config,
                **kwargs
            )
        except Exception as exc:
            self.logger.error(f"Single test execution failed: {exc}")
            return TestResult(
                test_name=test_name,
                status="failed",
                passed=False,
                error_message=str(exc)
            )

    def get_test_summary(self, results: List[TestResult]) -> Dict[str, Any]:
        """
        Generate a summary of test results.
        
        Args:
            results: List of test results
            
        Returns:
            Test summary dictionary
        """
        if not results:
            return {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0,
                "overall_score": 0.0,
                "execution_time": 0.0,
                "by_adapter": {}
            }
        
        # Calculate overall statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = sum(1 for r in results if not r.passed and r.status != "skipped")
        skipped_tests = sum(1 for r in results if r.status == "skipped")
        
        # Calculate overall score
        scores = [r.score for r in results if r.score is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        # Calculate total execution time
        execution_times = [r.execution_time for r in results if r.execution_time is not None]
        total_execution_time = sum(execution_times) if execution_times else 0.0
        
        # Group by adapter
        by_adapter = {}
        for result in results:
            adapter_name = self._get_adapter_name_from_test(result.test_name)
            if adapter_name not in by_adapter:
                by_adapter[adapter_name] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "avg_score": 0.0
                }
            
            by_adapter[adapter_name]["total"] += 1
            if result.passed:
                by_adapter[adapter_name]["passed"] += 1
            elif result.status == "skipped":
                by_adapter[adapter_name]["skipped"] += 1
            else:
                by_adapter[adapter_name]["failed"] += 1
        
        # Calculate average scores by adapter
        for adapter_name in by_adapter:
            adapter_results = [r for r in results if self._get_adapter_name_from_test(r.test_name) == adapter_name]
            adapter_scores = [r.score for r in adapter_results if r.score is not None]
            by_adapter[adapter_name]["avg_score"] = sum(adapter_scores) / len(adapter_scores) if adapter_scores else 0.0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "overall_score": overall_score,
            "execution_time": total_execution_time,
            "by_adapter": by_adapter
        }

    def _get_adapter_name_from_test(self, test_name: str) -> str:
        """Determine which adapter should handle a test based on test name."""
        # Map test names to adapters
        test_to_adapter = {
            # Fairness tests
            "demographic_parity": "fairness",
            "equal_opportunity": "fairness",
            "equalized_odds": "fairness",
            "disparate_impact": "fairness",
            "statistical_parity": "fairness",
            "comprehensive_fairness": "fairness",
            
            # Explainability tests
            "shap_feature_importance": "explainability",
            "shap_local_explanations": "explainability",
            "lime_explanations": "explainability",
            "permutation_importance": "explainability",
            "partial_dependence": "explainability",
            "comprehensive_explainability": "explainability",
            
            # Robustness tests
            "adversarial_noise": "robustness",
            "input_perturbation": "robustness",
            "feature_perturbation": "robustness",
            "stability_test": "robustness",
            "boundary_test": "robustness",
            "comprehensive_robustness": "robustness",
            
            # Privacy tests
            "differential_privacy": "privacy",
            "membership_inference": "privacy",
            "data_leakage": "privacy",
            "attribute_inference": "privacy",
            "model_inversion": "privacy",
            "comprehensive_privacy": "privacy"
        }
        
        return test_to_adapter.get(test_name, "unknown")

    def _group_tests_by_adapter(self, test_configs: List[TestConfig]) -> Dict[str, List[TestConfig]]:
        """Group test configurations by their respective adapters."""
        grouped = {}
        
        for test_config in test_configs:
            adapter_name = self._get_adapter_name_from_test(test_config.test_name)
            
            if adapter_name not in grouped:
                grouped[adapter_name] = []
            
            grouped[adapter_name].append(test_config)
        
        return grouped

    def register_adapter(self, name: str, adapter: BaseTestAdapter):
        """Register a new test adapter."""
        self.adapters[name] = adapter
        self.logger.info(f"Registered test adapter: {name}")

    def get_adapter_info(self, adapter_name: str) -> Dict[str, Any]:
        """Get information about a specific adapter."""
        if adapter_name not in self.adapters:
            return {"error": f"Adapter {adapter_name} not found"}
        
        adapter = self.adapters[adapter_name]
        
        return {
            "name": adapter.adapter_name,
            "supported_model_types": adapter.supported_model_types,
            "available_tests": adapter.get_available_tests()
        }
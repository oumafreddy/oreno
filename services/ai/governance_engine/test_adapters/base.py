"""
Base test adapter and common interfaces for AI governance testing.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """Standardized test result structure."""
    test_name: str
    status: TestStatus
    passed: bool
    score: Optional[float] = None
    threshold: Optional[float] = None
    metrics: Dict[str, Any] = None
    artifacts: List[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
        if self.artifacts is None:
            self.artifacts = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TestConfig:
    """Configuration for test execution."""
    test_name: str
    parameters: Dict[str, Any] = None
    thresholds: Dict[str, float] = None
    enabled: bool = True
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.thresholds is None:
            self.thresholds = {}
        if self.metadata is None:
            self.metadata = {}


class BaseTestAdapter(ABC):
    """
    Abstract base class for all AI governance test adapters.
    
    Each test adapter implements specific testing capabilities like fairness,
    explainability, robustness, or privacy testing.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the test adapter.
        
        Args:
            config: Configuration dictionary for the adapter
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Return the name of this test adapter."""
        pass

    @property
    @abstractmethod
    def supported_model_types(self) -> List[str]:
        """Return list of supported model types (e.g., ['tabular', 'image'])."""
        pass

    @abstractmethod
    def get_available_tests(self) -> List[str]:
        """
        Return list of available test names for this adapter.
        
        Returns:
            List of test names that can be executed
        """
        pass

    @abstractmethod
    def validate_config(self, test_config: TestConfig) -> bool:
        """
        Validate test configuration.
        
        Args:
            test_config: Test configuration to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    @abstractmethod
    def execute_test(
        self,
        model: Any,
        dataset: Any,
        test_config: TestConfig,
        **kwargs
    ) -> TestResult:
        """
        Execute a specific test.
        
        Args:
            model: The model to test
            dataset: The dataset to use for testing
            test_config: Configuration for the test
            **kwargs: Additional parameters
            
        Returns:
            TestResult object with test outcomes
        """
        pass

    def execute_tests(
        self,
        model: Any,
        dataset: Any,
        test_configs: List[TestConfig],
        **kwargs
    ) -> List[TestResult]:
        """
        Execute multiple tests.
        
        Args:
            model: The model to test
            dataset: The dataset to use for testing
            test_configs: List of test configurations
            **kwargs: Additional parameters
            
        Returns:
            List of TestResult objects
        """
        results = []
        
        for test_config in test_configs:
            if not test_config.enabled:
                self.logger.info(f"Skipping disabled test: {test_config.test_name}")
                results.append(TestResult(
                    test_name=test_config.test_name,
                    status=TestStatus.SKIPPED,
                    passed=True,
                    metadata={"reason": "test_disabled"}
                ))
                continue

            if not self.validate_config(test_config):
                self.logger.error(f"Invalid configuration for test: {test_config.test_name}")
                results.append(TestResult(
                    test_name=test_config.test_name,
                    status=TestStatus.FAILED,
                    passed=False,
                    error_message="Invalid test configuration"
                ))
                continue

            try:
                self.logger.info(f"Executing test: {test_config.test_name}")
                result = self.execute_test(model, dataset, test_config, **kwargs)
                results.append(result)
                
            except Exception as exc:
                self.logger.error(f"Test {test_config.test_name} failed with exception: {exc}")
                results.append(TestResult(
                    test_name=test_config.test_name,
                    status=TestStatus.FAILED,
                    passed=False,
                    error_message=str(exc)
                ))

        return results

    def _create_artifact_path(self, test_name: str, artifact_type: str, extension: str = None) -> str:
        """
        Create a standardized artifact path.
        
        Args:
            test_name: Name of the test
            artifact_type: Type of artifact (e.g., 'plot', 'report')
            extension: File extension (e.g., 'png', 'json')
            
        Returns:
            Artifact path string
        """
        import time
        timestamp = int(time.time())
        
        if extension:
            return f"artifacts/{test_name}_{artifact_type}_{timestamp}.{extension}"
        else:
            return f"artifacts/{test_name}_{artifact_type}_{timestamp}"

    def _log_test_start(self, test_name: str, model_type: str):
        """Log test execution start."""
        self.logger.info(f"Starting {self.adapter_name} test '{test_name}' for {model_type} model")

    def _log_test_complete(self, test_name: str, passed: bool, execution_time: float):
        """Log test execution completion."""
        status = "PASSED" if passed else "FAILED"
        self.logger.info(f"Completed {self.adapter_name} test '{test_name}': {status} ({execution_time:.2f}s)")

    def _calculate_pass_fail(self, score: float, threshold: float, higher_is_better: bool = True) -> bool:
        """
        Calculate pass/fail based on score and threshold.
        
        Args:
            score: Test score
            threshold: Pass/fail threshold
            higher_is_better: Whether higher scores are better
            
        Returns:
            True if test passed, False otherwise
        """
        if higher_is_better:
            return score >= threshold
        else:
            return score <= threshold
"""
Fairness testing adapter for AI governance.
Implements demographic parity, equal opportunity, and other fairness metrics.
"""

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .base import BaseTestAdapter, TestResult, TestConfig, TestStatus

logger = logging.getLogger(__name__)


@dataclass
class FairnessMetrics:
    """Container for fairness metrics."""
    demographic_parity: float
    equal_opportunity: float
    equalized_odds: float
    disparate_impact: float
    statistical_parity: float


class FairnessTestAdapter(BaseTestAdapter):
    """
    Test adapter for fairness testing using fairlearn and AIF360.
    
    Supports demographic parity, equal opportunity, equalized odds,
    and other fairness metrics for tabular models.
    """

    @property
    def adapter_name(self) -> str:
        return "fairness"

    @property
    def supported_model_types(self) -> List[str]:
        return ["tabular"]

    def get_available_tests(self) -> List[str]:
        """Return available fairness tests."""
        return [
            "demographic_parity",
            "equal_opportunity", 
            "equalized_odds",
            "disparate_impact",
            "statistical_parity",
            "comprehensive_fairness"
        ]

    def validate_config(self, test_config: TestConfig) -> bool:
        """Validate fairness test configuration."""
        required_params = ["sensitive_attribute", "privileged_group"]
        
        for param in required_params:
            if param not in test_config.parameters:
                self.logger.error(f"Missing required parameter: {param}")
                return False
        
        return True

    def execute_test(
        self,
        model: Any,
        dataset: Any,
        test_config: TestConfig,
        **kwargs
    ) -> TestResult:
        """
        Execute fairness test.
        
        Args:
            model: Trained model to test
            dataset: Test dataset with features and labels
            test_config: Test configuration
            **kwargs: Additional parameters
            
        Returns:
            TestResult with fairness metrics
        """
        import time
        start_time = time.time()
        
        self._log_test_start(test_config.test_name, "tabular")
        
        try:
            # Extract parameters
            sensitive_attribute = test_config.parameters["sensitive_attribute"]
            privileged_group = test_config.parameters["privileged_group"]
            
            # Prepare data
            X_test, y_test = self._prepare_dataset(dataset, sensitive_attribute)
            
            # Get model predictions
            y_pred = self._get_predictions(model, X_test)
            
            # Calculate fairness metrics based on test type
            if test_config.test_name == "demographic_parity":
                metrics = self._calculate_demographic_parity(
                    y_test, y_pred, X_test[sensitive_attribute], privileged_group
                )
            elif test_config.test_name == "equal_opportunity":
                metrics = self._calculate_equal_opportunity(
                    y_test, y_pred, X_test[sensitive_attribute], privileged_group
                )
            elif test_config.test_name == "equalized_odds":
                metrics = self._calculate_equalized_odds(
                    y_test, y_pred, X_test[sensitive_attribute], privileged_group
                )
            elif test_config.test_name == "disparate_impact":
                metrics = self._calculate_disparate_impact(
                    y_test, y_pred, X_test[sensitive_attribute], privileged_group
                )
            elif test_config.test_name == "statistical_parity":
                metrics = self._calculate_statistical_parity(
                    y_test, y_pred, X_test[sensitive_attribute], privileged_group
                )
            elif test_config.test_name == "comprehensive_fairness":
                metrics = self._calculate_comprehensive_fairness(
                    y_test, y_pred, X_test[sensitive_attribute], privileged_group
                )
            else:
                raise ValueError(f"Unknown fairness test: {test_config.test_name}")
            
            # Determine pass/fail
            passed = self._evaluate_fairness_metrics(metrics, test_config.thresholds)
            
            execution_time = time.time() - start_time
            self._log_test_complete(test_config.test_name, passed, execution_time)
            
            return TestResult(
                test_name=test_config.test_name,
                status=TestStatus.COMPLETED,
                passed=passed,
                score=metrics.demographic_parity,  # Primary metric
                metrics={
                    "demographic_parity": metrics.demographic_parity,
                    "equal_opportunity": metrics.equal_opportunity,
                    "equalized_odds": metrics.equalized_odds,
                    "disparate_impact": metrics.disparate_impact,
                    "statistical_parity": metrics.statistical_parity,
                },
                execution_time=execution_time,
                metadata={
                    "sensitive_attribute": sensitive_attribute,
                    "privileged_group": privileged_group,
                    "test_type": "fairness"
                }
            )
            
        except Exception as exc:
            execution_time = time.time() - start_time
            self.logger.error(f"Fairness test failed: {exc}")
            
            return TestResult(
                test_name=test_config.test_name,
                status=TestStatus.FAILED,
                passed=False,
                error_message=str(exc),
                execution_time=execution_time
            )

    def _prepare_dataset(self, dataset: Any, sensitive_attribute: str) -> tuple:
        """Prepare dataset for fairness testing."""
        if isinstance(dataset, pd.DataFrame):
            # Assume last column is target
            X = dataset.drop(columns=[dataset.columns[-1]])
            y = dataset.iloc[:, -1]
        else:
            # Handle other dataset formats
            X, y = dataset
        
        # Ensure sensitive attribute exists
        if sensitive_attribute not in X.columns:
            raise ValueError(f"Sensitive attribute '{sensitive_attribute}' not found in dataset")
        
        return X, y

    def _get_predictions(self, model: Any, X: pd.DataFrame) -> np.ndarray:
        """Get model predictions."""
        try:
            # Try predict_proba first (for probability outputs)
            if hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X)
                # Use positive class probability
                if y_pred_proba.shape[1] > 1:
                    return y_pred_proba[:, 1]
                else:
                    return y_pred_proba[:, 0]
            else:
                # Fall back to predict
                return model.predict(X)
        except Exception as exc:
            self.logger.error(f"Error getting predictions: {exc}")
            raise

    def _calculate_demographic_parity(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series, 
        privileged_group: Any
    ) -> FairnessMetrics:
        """Calculate demographic parity difference."""
        # Convert predictions to binary if needed
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        # Calculate positive prediction rates for each group
        privileged_mask = sensitive_attr == privileged_group
        unprivileged_mask = ~privileged_mask
        
        privileged_rate = np.mean(y_pred_binary[privileged_mask])
        unprivileged_rate = np.mean(y_pred_binary[unprivileged_mask])
        
        demographic_parity = abs(privileged_rate - unprivileged_rate)
        
        return FairnessMetrics(
            demographic_parity=demographic_parity,
            equal_opportunity=0.0,  # Placeholder
            equalized_odds=0.0,     # Placeholder
            disparate_impact=0.0,   # Placeholder
            statistical_parity=demographic_parity
        )

    def _calculate_equal_opportunity(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series, 
        privileged_group: Any
    ) -> FairnessMetrics:
        """Calculate equal opportunity difference."""
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        # Calculate true positive rates for each group
        privileged_mask = sensitive_attr == privileged_group
        unprivileged_mask = ~privileged_mask
        
        # True positive rate = TP / (TP + FN)
        privileged_tp = np.sum((y_pred_binary[privileged_mask] == 1) & (y_true[privileged_mask] == 1))
        privileged_fn = np.sum((y_pred_binary[privileged_mask] == 0) & (y_true[privileged_mask] == 1))
        privileged_tpr = privileged_tp / (privileged_tp + privileged_fn) if (privileged_tp + privileged_fn) > 0 else 0
        
        unprivileged_tp = np.sum((y_pred_binary[unprivileged_mask] == 1) & (y_true[unprivileged_mask] == 1))
        unprivileged_fn = np.sum((y_pred_binary[unprivileged_mask] == 0) & (y_true[unprivileged_mask] == 1))
        unprivileged_tpr = unprivileged_tp / (unprivileged_tp + unprivileged_fn) if (unprivileged_tp + unprivileged_fn) > 0 else 0
        
        equal_opportunity = abs(privileged_tpr - unprivileged_tpr)
        
        return FairnessMetrics(
            demographic_parity=0.0,  # Placeholder
            equal_opportunity=equal_opportunity,
            equalized_odds=0.0,      # Placeholder
            disparate_impact=0.0,    # Placeholder
            statistical_parity=0.0   # Placeholder
        )

    def _calculate_equalized_odds(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series, 
        privileged_group: Any
    ) -> FairnessMetrics:
        """Calculate equalized odds difference."""
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        privileged_mask = sensitive_attr == privileged_group
        unprivileged_mask = ~privileged_mask
        
        # Calculate TPR and FPR for each group
        def calculate_rates(y_true_group, y_pred_group):
            tp = np.sum((y_pred_group == 1) & (y_true_group == 1))
            fp = np.sum((y_pred_group == 1) & (y_true_group == 0))
            fn = np.sum((y_pred_group == 0) & (y_true_group == 1))
            tn = np.sum((y_pred_group == 0) & (y_true_group == 0))
            
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            
            return tpr, fpr
        
        privileged_tpr, privileged_fpr = calculate_rates(
            y_true[privileged_mask], y_pred_binary[privileged_mask]
        )
        unprivileged_tpr, unprivileged_fpr = calculate_rates(
            y_true[unprivileged_mask], y_pred_binary[unprivileged_mask]
        )
        
        equalized_odds = max(
            abs(privileged_tpr - unprivileged_tpr),
            abs(privileged_fpr - unprivileged_fpr)
        )
        
        return FairnessMetrics(
            demographic_parity=0.0,  # Placeholder
            equal_opportunity=0.0,   # Placeholder
            equalized_odds=equalized_odds,
            disparate_impact=0.0,    # Placeholder
            statistical_parity=0.0   # Placeholder
        )

    def _calculate_disparate_impact(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series, 
        privileged_group: Any
    ) -> FairnessMetrics:
        """Calculate disparate impact ratio."""
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        privileged_mask = sensitive_attr == privileged_group
        unprivileged_mask = ~privileged_mask
        
        privileged_rate = np.mean(y_pred_binary[privileged_mask])
        unprivileged_rate = np.mean(y_pred_binary[unprivileged_mask])
        
        # Disparate impact ratio (should be close to 1.0)
        disparate_impact = unprivileged_rate / privileged_rate if privileged_rate > 0 else 0
        
        return FairnessMetrics(
            demographic_parity=0.0,  # Placeholder
            equal_opportunity=0.0,   # Placeholder
            equalized_odds=0.0,      # Placeholder
            disparate_impact=disparate_impact,
            statistical_parity=0.0   # Placeholder
        )

    def _calculate_statistical_parity(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series, 
        privileged_group: Any
    ) -> FairnessMetrics:
        """Calculate statistical parity difference (same as demographic parity)."""
        return self._calculate_demographic_parity(y_true, y_pred, sensitive_attr, privileged_group)

    def _calculate_comprehensive_fairness(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        sensitive_attr: pd.Series, 
        privileged_group: Any
    ) -> FairnessMetrics:
        """Calculate all fairness metrics."""
        dp_metrics = self._calculate_demographic_parity(y_true, y_pred, sensitive_attr, privileged_group)
        eo_metrics = self._calculate_equal_opportunity(y_true, y_pred, sensitive_attr, privileged_group)
        eod_metrics = self._calculate_equalized_odds(y_true, y_pred, sensitive_attr, privileged_group)
        di_metrics = self._calculate_disparate_impact(y_true, y_pred, sensitive_attr, privileged_group)
        
        return FairnessMetrics(
            demographic_parity=dp_metrics.demographic_parity,
            equal_opportunity=eo_metrics.equal_opportunity,
            equalized_odds=eod_metrics.equalized_odds,
            disparate_impact=di_metrics.disparate_impact,
            statistical_parity=dp_metrics.statistical_parity
        )

    def _evaluate_fairness_metrics(self, metrics: FairnessMetrics, thresholds: Dict[str, float]) -> bool:
        """Evaluate if fairness metrics pass thresholds."""
        default_thresholds = {
            "demographic_parity": 0.1,
            "equal_opportunity": 0.1,
            "equalized_odds": 0.1,
            "disparate_impact": 0.8,  # Should be >= 0.8 (80% rule)
        }
        
        # Use provided thresholds or defaults
        thresholds = {**default_thresholds, **thresholds}
        
        # Check each metric
        checks = []
        
        if "demographic_parity" in thresholds:
            checks.append(metrics.demographic_parity <= thresholds["demographic_parity"])
        
        if "equal_opportunity" in thresholds:
            checks.append(metrics.equal_opportunity <= thresholds["equal_opportunity"])
        
        if "equalized_odds" in thresholds:
            checks.append(metrics.equalized_odds <= thresholds["equalized_odds"])
        
        if "disparate_impact" in thresholds:
            checks.append(metrics.disparate_impact >= thresholds["disparate_impact"])
        
        # All checks must pass
        return all(checks) if checks else True
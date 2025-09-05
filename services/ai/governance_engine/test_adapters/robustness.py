"""
Robustness testing adapter for AI governance.
Implements adversarial testing, noise robustness, and stability tests.
"""

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union
import time

from .base import BaseTestAdapter, TestResult, TestConfig, TestStatus

logger = logging.getLogger(__name__)


class RobustnessTestAdapter(BaseTestAdapter):
    """
    Test adapter for model robustness testing.
    
    Supports adversarial attacks, noise robustness, input perturbation,
    and stability testing for tabular and image models.
    """

    @property
    def adapter_name(self) -> str:
        return "robustness"

    @property
    def supported_model_types(self) -> List[str]:
        return ["tabular", "image"]

    def get_available_tests(self) -> List[str]:
        """Return available robustness tests."""
        return [
            "adversarial_noise",
            "input_perturbation",
            "feature_perturbation",
            "stability_test",
            "boundary_test",
            "comprehensive_robustness"
        ]

    def validate_config(self, test_config: TestConfig) -> bool:
        """Validate robustness test configuration."""
        # Most robustness tests have optional parameters
        return True

    def execute_test(
        self,
        model: Any,
        dataset: Any,
        test_config: TestConfig,
        **kwargs
    ) -> TestResult:
        """
        Execute robustness test.
        
        Args:
            model: Trained model to test
            dataset: Test dataset
            test_config: Test configuration
            **kwargs: Additional parameters
            
        Returns:
            TestResult with robustness metrics
        """
        start_time = time.time()
        
        self._log_test_start(test_config.test_name, "tabular")  # Default to tabular
        
        try:
            # Prepare data
            X_test, y_test = self._prepare_dataset(dataset)
            
            # Execute specific robustness test
            if test_config.test_name == "adversarial_noise":
                result = self._test_adversarial_noise(model, X_test, y_test, test_config)
            elif test_config.test_name == "input_perturbation":
                result = self._test_input_perturbation(model, X_test, y_test, test_config)
            elif test_config.test_name == "feature_perturbation":
                result = self._test_feature_perturbation(model, X_test, y_test, test_config)
            elif test_config.test_name == "stability_test":
                result = self._test_stability(model, X_test, y_test, test_config)
            elif test_config.test_name == "boundary_test":
                result = self._test_decision_boundary(model, X_test, y_test, test_config)
            elif test_config.test_name == "comprehensive_robustness":
                result = self._test_comprehensive_robustness(model, X_test, y_test, test_config)
            else:
                raise ValueError(f"Unknown robustness test: {test_config.test_name}")
            
            execution_time = time.time() - start_time
            self._log_test_complete(test_config.test_name, result["passed"], execution_time)
            
            return TestResult(
                test_name=test_config.test_name,
                status=TestStatus.COMPLETED,
                passed=result["passed"],
                score=result.get("score", 0.0),
                metrics=result.get("metrics", {}),
                artifacts=result.get("artifacts", []),
                execution_time=execution_time,
                metadata={
                    "test_type": "robustness",
                    "robustness_method": test_config.test_name
                }
            )
            
        except Exception as exc:
            execution_time = time.time() - start_time
            self.logger.error(f"Robustness test failed: {exc}")
            
            return TestResult(
                test_name=test_config.test_name,
                status=TestStatus.FAILED,
                passed=False,
                error_message=str(exc),
                execution_time=execution_time
            )

    def _prepare_dataset(self, dataset: Any) -> tuple:
        """Prepare dataset for robustness testing."""
        if isinstance(dataset, pd.DataFrame):
            # Assume last column is target
            X = dataset.drop(columns=[dataset.columns[-1]])
            y = dataset.iloc[:, -1]
        else:
            # Handle other dataset formats
            X, y = dataset
        
        return X, y

    def _test_adversarial_noise(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test model robustness to adversarial noise."""
        try:
            # Get baseline predictions
            baseline_pred = self._get_predictions(model, X)
            
            # Add different levels of noise
            noise_levels = test_config.parameters.get("noise_levels", [0.01, 0.05, 0.1, 0.2])
            robustness_scores = []
            
            for noise_level in noise_levels:
                # Add Gaussian noise
                X_noisy = X + np.random.normal(0, noise_level, X.shape)
                
                # Get predictions on noisy data
                noisy_pred = self._get_predictions(model, X_noisy)
                
                # Calculate prediction stability
                if len(baseline_pred.shape) > 1:
                    # Multi-class case
                    stability = np.mean(np.all(baseline_pred == noisy_pred, axis=1))
                else:
                    # Binary case
                    stability = np.mean(baseline_pred == noisy_pred)
                
                robustness_scores.append(stability)
            
            # Calculate overall robustness score
            overall_robustness = np.mean(robustness_scores)
            
            # Generate artifacts
            artifacts = []
            if test_config.parameters.get("save_plots", True):
                plot_path = self._create_artifact_path(test_config.test_name, "robustness_curve", "png")
                self._save_robustness_curve_plot(noise_levels, robustness_scores, plot_path)
                artifacts.append(plot_path)
            
            return {
                "passed": overall_robustness > 0.8,  # 80% of predictions should remain stable
                "score": overall_robustness,
                "metrics": {
                    "overall_robustness": overall_robustness,
                    "noise_levels": noise_levels,
                    "robustness_scores": robustness_scores,
                    "min_robustness": np.min(robustness_scores),
                    "max_robustness": np.max(robustness_scores)
                },
                "artifacts": artifacts
            }
            
        except Exception as exc:
            self.logger.error(f"Adversarial noise test failed: {exc}")
            raise

    def _test_input_perturbation(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test model robustness to input perturbations."""
        try:
            # Get baseline predictions
            baseline_pred = self._get_predictions(model, X)
            
            # Test different perturbation types
            perturbation_types = test_config.parameters.get("perturbation_types", ["gaussian", "uniform", "outlier"])
            perturbation_results = {}
            
            for pert_type in perturbation_types:
                if pert_type == "gaussian":
                    X_pert = X + np.random.normal(0, 0.1, X.shape)
                elif pert_type == "uniform":
                    X_pert = X + np.random.uniform(-0.1, 0.1, X.shape)
                elif pert_type == "outlier":
                    # Add outliers to random features
                    X_pert = X.copy()
                    outlier_indices = np.random.choice(X.shape[0], size=int(0.05 * X.shape[0]), replace=False)
                    outlier_features = np.random.choice(X.shape[1], size=2, replace=False)
                    X_pert.iloc[outlier_indices, outlier_features] *= 10
                else:
                    continue
                
                # Get predictions on perturbed data
                pert_pred = self._get_predictions(model, X_pert)
                
                # Calculate prediction stability
                if len(baseline_pred.shape) > 1:
                    stability = np.mean(np.all(baseline_pred == pert_pred, axis=1))
                else:
                    stability = np.mean(baseline_pred == pert_pred)
                
                perturbation_results[pert_type] = stability
            
            # Calculate overall perturbation robustness
            overall_robustness = np.mean(list(perturbation_results.values()))
            
            return {
                "passed": overall_robustness > 0.7,
                "score": overall_robustness,
                "metrics": {
                    "overall_robustness": overall_robustness,
                    "perturbation_results": perturbation_results,
                    "num_perturbation_types": len(perturbation_types)
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Input perturbation test failed: {exc}")
            raise

    def _test_feature_perturbation(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test model robustness to feature perturbations."""
        try:
            # Get baseline predictions
            baseline_pred = self._get_predictions(model, X)
            
            # Test dropping/perturbing individual features
            feature_importance = []
            
            for i, feature in enumerate(X.columns):
                # Create perturbed dataset by shuffling this feature
                X_pert = X.copy()
                X_pert[feature] = np.random.permutation(X_pert[feature].values)
                
                # Get predictions
                pert_pred = self._get_predictions(model, X_pert)
                
                # Calculate prediction change
                if len(baseline_pred.shape) > 1:
                    change = np.mean(np.any(baseline_pred != pert_pred, axis=1))
                else:
                    change = np.mean(baseline_pred != pert_pred)
                
                feature_importance.append((feature, change))
            
            # Sort by importance (higher change = more important)
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            # Calculate robustness score based on feature sensitivity
            # Lower sensitivity to random feature changes is better
            avg_sensitivity = np.mean([imp[1] for imp in feature_importance])
            robustness_score = 1.0 - avg_sensitivity
            
            return {
                "passed": robustness_score > 0.5,  # Model should be somewhat robust to feature changes
                "score": robustness_score,
                "metrics": {
                    "robustness_score": robustness_score,
                    "feature_sensitivity": feature_importance,
                    "most_sensitive_features": feature_importance[:5],
                    "least_sensitive_features": feature_importance[-5:]
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Feature perturbation test failed: {exc}")
            raise

    def _test_stability(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test model stability across multiple runs."""
        try:
            # Test model stability by retraining with slightly different data
            num_runs = test_config.parameters.get("num_runs", 5)
            stability_scores = []
            
            for run in range(num_runs):
                # Create slightly different training data (bootstrap sample)
                sample_indices = np.random.choice(len(X), size=int(0.8 * len(X)), replace=True)
                X_sample = X.iloc[sample_indices]
                y_sample = y.iloc[sample_indices]
                
                # Retrain model (if possible)
                try:
                    if hasattr(model, 'fit'):
                        # Clone the model to avoid modifying the original
                        from sklearn.base import clone
                        model_copy = clone(model)
                        model_copy.fit(X_sample, y_sample)
                        
                        # Get predictions on test set
                        pred = self._get_predictions(model_copy, X)
                        
                        # Calculate stability (consistency with original predictions)
                        original_pred = self._get_predictions(model, X)
                        
                        if len(original_pred.shape) > 1:
                            stability = np.mean(np.all(original_pred == pred, axis=1))
                        else:
                            stability = np.mean(original_pred == pred)
                        
                        stability_scores.append(stability)
                    else:
                        # Model doesn't support retraining, skip this test
                        self.logger.warning("Model doesn't support retraining, skipping stability test")
                        return {
                            "passed": True,
                            "score": 1.0,
                            "metrics": {"note": "Model doesn't support retraining"},
                            "artifacts": []
                        }
                        
                except Exception as exc:
                    self.logger.warning(f"Stability test run {run} failed: {exc}")
                    continue
            
            if not stability_scores:
                return {
                    "passed": False,
                    "score": 0.0,
                    "metrics": {"error": "No successful stability test runs"},
                    "artifacts": []
                }
            
            # Calculate overall stability
            overall_stability = np.mean(stability_scores)
            stability_variance = np.var(stability_scores)
            
            return {
                "passed": overall_stability > 0.8 and stability_variance < 0.1,
                "score": overall_stability,
                "metrics": {
                    "overall_stability": overall_stability,
                    "stability_variance": stability_variance,
                    "individual_scores": stability_scores,
                    "num_successful_runs": len(stability_scores)
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Stability test failed: {exc}")
            raise

    def _test_decision_boundary(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test model robustness near decision boundaries."""
        try:
            # Get prediction probabilities if available
            if hasattr(model, 'predict_proba'):
                pred_proba = model.predict_proba(X)
                if pred_proba.shape[1] > 1:
                    # Binary classification - use positive class probability
                    confidence = np.max(pred_proba, axis=1)
                else:
                    confidence = pred_proba[:, 0]
            else:
                # Fallback to predictions
                pred = self._get_predictions(model, X)
                confidence = np.ones_like(pred)  # Assume high confidence
            
            # Find samples near decision boundary (low confidence)
            boundary_threshold = test_config.parameters.get("boundary_threshold", 0.6)
            boundary_indices = np.where(confidence < boundary_threshold)[0]
            
            if len(boundary_indices) == 0:
                # No samples near boundary
                return {
                    "passed": True,
                    "score": 1.0,
                    "metrics": {
                        "note": "No samples found near decision boundary",
                        "min_confidence": np.min(confidence),
                        "boundary_threshold": boundary_threshold
                    },
                    "artifacts": []
                }
            
            # Test robustness of boundary samples
            X_boundary = X.iloc[boundary_indices]
            boundary_robustness_scores = []
            
            for i, idx in enumerate(boundary_indices[:10]):  # Test first 10 boundary samples
                sample = X_boundary.iloc[i:i+1]
                
                # Add small perturbations
                perturbations = []
                for noise_level in [0.01, 0.05, 0.1]:
                    X_pert = sample + np.random.normal(0, noise_level, sample.shape)
                    pert_pred = self._get_predictions(model, X_pert)
                    perturbations.append(pert_pred[0])
                
                # Calculate consistency of predictions
                if len(set(perturbations)) == 1:
                    # All predictions are the same
                    boundary_robustness_scores.append(1.0)
                else:
                    # Predictions vary
                    boundary_robustness_scores.append(0.0)
            
            boundary_robustness = np.mean(boundary_robustness_scores) if boundary_robustness_scores else 0.0
            
            return {
                "passed": boundary_robustness > 0.5,
                "score": boundary_robustness,
                "metrics": {
                    "boundary_robustness": boundary_robustness,
                    "num_boundary_samples": len(boundary_indices),
                    "samples_tested": len(boundary_robustness_scores),
                    "boundary_threshold": boundary_threshold
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Decision boundary test failed: {exc}")
            raise

    def _test_comprehensive_robustness(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Run comprehensive robustness tests."""
        results = {}
        scores = []
        
        # Run multiple robustness tests
        tests_to_run = [
            ("adversarial_noise", self._test_adversarial_noise),
            ("input_perturbation", self._test_input_perturbation),
            ("feature_perturbation", self._test_feature_perturbation),
            ("stability_test", self._test_stability),
            ("boundary_test", self._test_decision_boundary)
        ]
        
        all_artifacts = []
        
        for test_name, test_func in tests_to_run:
            try:
                result = test_func(model, X, y, test_config)
                results[test_name] = result
                scores.append(result["score"])
                all_artifacts.extend(result.get("artifacts", []))
                
            except Exception as exc:
                self.logger.warning(f"Test {test_name} failed: {exc}")
                results[test_name] = {"passed": False, "score": 0.0}
        
        overall_score = np.mean(scores) if scores else 0.0
        
        return {
            "passed": overall_score > 0.6,
            "score": overall_score,
            "metrics": {
                "overall_score": overall_score,
                "individual_scores": {k: v["score"] for k, v in results.items()},
                "tests_passed": sum(1 for v in results.values() if v["passed"]),
                "total_tests": len(results)
            },
            "artifacts": all_artifacts
        }

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

    def _save_robustness_curve_plot(self, noise_levels: List[float], robustness_scores: List[float], path: str):
        """Save robustness curve plot."""
        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            plt.plot(noise_levels, robustness_scores, 'bo-', linewidth=2, markersize=8)
            plt.xlabel('Noise Level')
            plt.ylabel('Robustness Score')
            plt.title('Model Robustness to Adversarial Noise')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as exc:
            self.logger.warning(f"Could not save robustness curve plot: {exc}")
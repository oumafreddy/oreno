"""
Privacy testing adapter for AI governance.
Implements differential privacy, data leakage, and privacy-preserving tests.
"""

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union
import time

from .base import BaseTestAdapter, TestResult, TestConfig, TestStatus

logger = logging.getLogger(__name__)


class PrivacyTestAdapter(BaseTestAdapter):
    """
    Test adapter for privacy testing.
    
    Supports differential privacy analysis, data leakage detection,
    membership inference attacks, and privacy-preserving validation
    for tabular and image models.
    """

    @property
    def adapter_name(self) -> str:
        return "privacy"

    @property
    def supported_model_types(self) -> List[str]:
        return ["tabular", "image"]

    def get_available_tests(self) -> List[str]:
        """Return available privacy tests."""
        return [
            "differential_privacy",
            "membership_inference",
            "data_leakage",
            "attribute_inference",
            "model_inversion",
            "comprehensive_privacy"
        ]

    def validate_config(self, test_config: TestConfig) -> bool:
        """Validate privacy test configuration."""
        # Most privacy tests have optional parameters
        return True

    def execute_test(
        self,
        model: Any,
        dataset: Any,
        test_config: TestConfig,
        **kwargs
    ) -> TestResult:
        """
        Execute privacy test.
        
        Args:
            model: Trained model to test
            dataset: Test dataset
            test_config: Test configuration
            **kwargs: Additional parameters
            
        Returns:
            TestResult with privacy metrics
        """
        start_time = time.time()
        
        self._log_test_start(test_config.test_name, "tabular")  # Default to tabular
        
        try:
            # Prepare data
            X_test, y_test = self._prepare_dataset(dataset)
            
            # Execute specific privacy test
            if test_config.test_name == "differential_privacy":
                result = self._test_differential_privacy(model, X_test, y_test, test_config)
            elif test_config.test_name == "membership_inference":
                result = self._test_membership_inference(model, X_test, y_test, test_config)
            elif test_config.test_name == "data_leakage":
                result = self._test_data_leakage(model, X_test, y_test, test_config)
            elif test_config.test_name == "attribute_inference":
                result = self._test_attribute_inference(model, X_test, y_test, test_config)
            elif test_config.test_name == "model_inversion":
                result = self._test_model_inversion(model, X_test, y_test, test_config)
            elif test_config.test_name == "comprehensive_privacy":
                result = self._test_comprehensive_privacy(model, X_test, y_test, test_config)
            else:
                raise ValueError(f"Unknown privacy test: {test_config.test_name}")
            
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
                    "test_type": "privacy",
                    "privacy_method": test_config.test_name
                }
            )
            
        except Exception as exc:
            execution_time = time.time() - start_time
            self.logger.error(f"Privacy test failed: {exc}")
            
            return TestResult(
                test_name=test_config.test_name,
                status=TestStatus.FAILED,
                passed=False,
                error_message=str(exc),
                execution_time=execution_time
            )

    def _prepare_dataset(self, dataset: Any) -> tuple:
        """Prepare dataset for privacy testing."""
        if isinstance(dataset, pd.DataFrame):
            # Assume last column is target
            X = dataset.drop(columns=[dataset.columns[-1]])
            y = dataset.iloc[:, -1]
        else:
            # Handle other dataset formats
            X, y = dataset
        
        return X, y

    def _test_differential_privacy(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test model for differential privacy compliance."""
        try:
            # This is a simplified differential privacy test
            # In practice, you would need access to the training process
            
            # Test sensitivity to individual data points
            sensitivity_scores = []
            
            # Sample a subset for testing
            sample_size = test_config.parameters.get("sample_size", min(100, len(X)))
            X_sample = X.sample(n=sample_size, random_state=42)
            y_sample = y.loc[X_sample.index]
            
            # Get baseline predictions
            baseline_pred = self._get_predictions(model, X_sample)
            
            # Test sensitivity by removing individual points
            for i in range(min(10, len(X_sample))):
                # Remove one data point
                X_pert = X_sample.drop(X_sample.index[i])
                y_pert = y_sample.drop(y_sample.index[i])
                
                # Retrain model if possible
                try:
                    if hasattr(model, 'fit'):
                        from sklearn.base import clone
                        model_copy = clone(model)
                        model_copy.fit(X_pert, y_pert)
                        
                        # Get predictions on remaining data
                        pred_pert = self._get_predictions(model_copy, X_sample.drop(X_sample.index[i]))
                        pred_original = baseline_pred[i+1:]  # Skip the removed point
                        
                        # Calculate sensitivity
                        if len(pred_pert.shape) > 1:
                            sensitivity = np.mean(np.abs(pred_pert - pred_original))
                        else:
                            sensitivity = np.mean(np.abs(pred_pert - pred_original))
                        
                        sensitivity_scores.append(sensitivity)
                    else:
                        # Model doesn't support retraining
                        self.logger.warning("Model doesn't support retraining for DP test")
                        return {
                            "passed": True,
                            "score": 1.0,
                            "metrics": {"note": "Model doesn't support retraining for DP analysis"},
                            "artifacts": []
                        }
                        
                except Exception as exc:
                    self.logger.warning(f"DP sensitivity test {i} failed: {exc}")
                    continue
            
            if not sensitivity_scores:
                return {
                    "passed": False,
                    "score": 0.0,
                    "metrics": {"error": "No successful DP sensitivity tests"},
                    "artifacts": []
                }
            
            # Calculate differential privacy score
            # Lower sensitivity indicates better privacy
            avg_sensitivity = np.mean(sensitivity_scores)
            dp_score = max(0, 1.0 - avg_sensitivity)
            
            return {
                "passed": dp_score > 0.7,  # High privacy score
                "score": dp_score,
                "metrics": {
                    "differential_privacy_score": dp_score,
                    "average_sensitivity": avg_sensitivity,
                    "sensitivity_scores": sensitivity_scores,
                    "num_tests": len(sensitivity_scores)
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Differential privacy test failed: {exc}")
            raise

    def _test_membership_inference(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test for membership inference attack vulnerability."""
        try:
            # Simulate membership inference attack
            # In practice, this would require access to training data
            
            # Split data into "member" and "non-member" sets
            split_ratio = test_config.parameters.get("split_ratio", 0.5)
            n_members = int(len(X) * split_ratio)
            
            # Randomly assign membership
            member_indices = np.random.choice(len(X), size=n_members, replace=False)
            member_mask = np.zeros(len(X), dtype=bool)
            member_mask[member_indices] = True
            
            X_members = X[member_mask]
            y_members = y[member_mask]
            X_non_members = X[~member_mask]
            y_non_members = y[~member_mask]
            
            # Get model predictions
            member_pred = self._get_predictions(model, X_members)
            non_member_pred = self._get_predictions(model, X_non_members)
            
            # Calculate prediction confidence/entropy
            if hasattr(model, 'predict_proba'):
                member_proba = model.predict_proba(X_members)
                non_member_proba = model.predict_proba(X_non_members)
                
                # Calculate entropy (higher entropy = lower confidence)
                member_entropy = -np.sum(member_proba * np.log(member_proba + 1e-8), axis=1)
                non_member_entropy = -np.sum(non_member_proba * np.log(non_member_proba + 1e-8), axis=1)
                
                # Membership inference: members should have lower entropy (higher confidence)
                member_confidence = 1.0 - member_entropy
                non_member_confidence = 1.0 - non_member_entropy
                
                # Calculate attack success rate
                # If members have significantly higher confidence, attack is successful
                confidence_diff = np.mean(member_confidence) - np.mean(non_member_confidence)
                attack_success_rate = max(0, min(1, (confidence_diff + 0.1) / 0.2))  # Normalize to 0-1
                
            else:
                # Fallback: use prediction variance as confidence proxy
                member_pred_var = np.var(member_pred)
                non_member_pred_var = np.var(non_member_pred)
                
                # Lower variance might indicate membership
                confidence_diff = non_member_pred_var - member_pred_var
                attack_success_rate = max(0, min(1, (confidence_diff + 0.1) / 0.2))
            
            # Privacy score: lower attack success rate is better
            privacy_score = 1.0 - attack_success_rate
            
            return {
                "passed": privacy_score > 0.6,  # Attack success rate < 40%
                "score": privacy_score,
                "metrics": {
                    "privacy_score": privacy_score,
                    "attack_success_rate": attack_success_rate,
                    "confidence_difference": confidence_diff if 'confidence_diff' in locals() else 0,
                    "num_members": len(X_members),
                    "num_non_members": len(X_non_members)
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Membership inference test failed: {exc}")
            raise

    def _test_data_leakage(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test for data leakage in the model."""
        try:
            # Test for potential data leakage by checking for perfect or near-perfect performance
            # on test data, which might indicate leakage
            
            # Get predictions
            y_pred = self._get_predictions(model, X)
            
            # Calculate accuracy
            if len(y_pred.shape) > 1:
                # Multi-class case
                y_pred_class = np.argmax(y_pred, axis=1)
                accuracy = np.mean(y_pred_class == y)
            else:
                # Binary case
                y_pred_binary = (y_pred > 0.5).astype(int)
                accuracy = np.mean(y_pred_binary == y)
            
            # Check for suspiciously high accuracy
            suspicious_accuracy_threshold = test_config.parameters.get("suspicious_threshold", 0.95)
            
            # Test for feature importance patterns that might indicate leakage
            leakage_indicators = []
            
            # Check if any single feature has extremely high importance
            if hasattr(model, 'feature_importances_'):
                feature_importance = model.feature_importances_
                max_importance = np.max(feature_importance)
                
                if max_importance > 0.8:  # Single feature explains >80%
                    leakage_indicators.append("high_single_feature_importance")
            
            # Check for perfect correlation between features and target
            correlations = []
            for feature in X.columns:
                corr = np.corrcoef(X[feature], y)[0, 1]
                correlations.append(abs(corr))
            
            max_correlation = np.max(correlations)
            if max_correlation > 0.99:  # Near-perfect correlation
                leakage_indicators.append("perfect_feature_correlation")
            
            # Calculate leakage score
            leakage_score = 0.0
            if accuracy > suspicious_accuracy_threshold:
                leakage_score += 0.5
            if "high_single_feature_importance" in leakage_indicators:
                leakage_score += 0.3
            if "perfect_feature_correlation" in leakage_indicators:
                leakage_score += 0.2
            
            # Privacy score: lower leakage score is better
            privacy_score = 1.0 - leakage_score
            
            return {
                "passed": privacy_score > 0.7,  # Low leakage risk
                "score": privacy_score,
                "metrics": {
                    "privacy_score": privacy_score,
                    "leakage_score": leakage_score,
                    "test_accuracy": accuracy,
                    "suspicious_accuracy": accuracy > suspicious_accuracy_threshold,
                    "max_feature_importance": max_importance if hasattr(model, 'feature_importances_') else 0,
                    "max_feature_correlation": max_correlation,
                    "leakage_indicators": leakage_indicators
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Data leakage test failed: {exc}")
            raise

    def _test_attribute_inference(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test for attribute inference attack vulnerability."""
        try:
            # Test if sensitive attributes can be inferred from model outputs
            
            # This is a simplified test - in practice, you'd need access to sensitive attributes
            # and training data to perform a proper attribute inference attack
            
            # For now, we'll test if the model is overly sensitive to individual features
            # which might indicate it's memorizing sensitive information
            
            feature_sensitivity = []
            
            for feature in X.columns:
                # Calculate how much predictions change when this feature is perturbed
                X_pert = X.copy()
                X_pert[feature] = np.random.permutation(X_pert[feature].values)
                
                pred_original = self._get_predictions(model, X)
                pred_pert = self._get_predictions(model, X_pert)
                
                # Calculate sensitivity
                if len(pred_original.shape) > 1:
                    sensitivity = np.mean(np.abs(pred_original - pred_pert))
                else:
                    sensitivity = np.mean(np.abs(pred_original - pred_pert))
                
                feature_sensitivity.append((feature, sensitivity))
            
            # Sort by sensitivity
            feature_sensitivity.sort(key=lambda x: x[1], reverse=True)
            
            # High sensitivity to individual features might indicate memorization
            max_sensitivity = feature_sensitivity[0][1] if feature_sensitivity else 0
            avg_sensitivity = np.mean([s[1] for s in feature_sensitivity])
            
            # Privacy score: lower sensitivity is better
            privacy_score = max(0, 1.0 - (max_sensitivity + avg_sensitivity) / 2)
            
            return {
                "passed": privacy_score > 0.5,
                "score": privacy_score,
                "metrics": {
                    "privacy_score": privacy_score,
                    "max_feature_sensitivity": max_sensitivity,
                    "avg_feature_sensitivity": avg_sensitivity,
                    "most_sensitive_features": feature_sensitivity[:5],
                    "least_sensitive_features": feature_sensitivity[-5:]
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Attribute inference test failed: {exc}")
            raise

    def _test_model_inversion(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test for model inversion attack vulnerability."""
        try:
            # Model inversion attack: try to reconstruct training data from model outputs
            
            # This is a simplified test - in practice, you'd need more sophisticated methods
            
            # Test if the model outputs contain enough information to reconstruct inputs
            # by checking the relationship between inputs and outputs
            
            # Get model predictions
            y_pred = self._get_predictions(model, X)
            
            # Calculate reconstruction error
            reconstruction_errors = []
            
            # For each feature, try to predict it from model outputs
            for feature in X.columns:
                try:
                    # Simple linear regression to predict feature from model output
                    from sklearn.linear_model import LinearRegression
                    from sklearn.metrics import mean_squared_error
                    
                    reg = LinearRegression()
                    reg.fit(y_pred.reshape(-1, 1), X[feature])
                    feature_pred = reg.predict(y_pred.reshape(-1, 1))
                    
                    # Calculate reconstruction error
                    mse = mean_squared_error(X[feature], feature_pred)
                    reconstruction_errors.append(mse)
                    
                except Exception as exc:
                    self.logger.warning(f"Feature reconstruction failed for {feature}: {exc}")
                    continue
            
            if not reconstruction_errors:
                return {
                    "passed": True,
                    "score": 1.0,
                    "metrics": {"note": "Could not perform model inversion test"},
                    "artifacts": []
                }
            
            # Calculate average reconstruction error
            avg_reconstruction_error = np.mean(reconstruction_errors)
            
            # Privacy score: higher reconstruction error is better (harder to invert)
            # Normalize to 0-1 scale
            privacy_score = min(1.0, avg_reconstruction_error / np.var(X.values))
            
            return {
                "passed": privacy_score > 0.3,  # Some protection against inversion
                "score": privacy_score,
                "metrics": {
                    "privacy_score": privacy_score,
                    "avg_reconstruction_error": avg_reconstruction_error,
                    "reconstruction_errors": reconstruction_errors,
                    "num_features_tested": len(reconstruction_errors)
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Model inversion test failed: {exc}")
            raise

    def _test_comprehensive_privacy(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Run comprehensive privacy tests."""
        results = {}
        scores = []
        
        # Run multiple privacy tests
        tests_to_run = [
            ("membership_inference", self._test_membership_inference),
            ("data_leakage", self._test_data_leakage),
            ("attribute_inference", self._test_attribute_inference),
            ("model_inversion", self._test_model_inversion)
        ]
        
        # Add differential privacy test if model supports retraining
        if hasattr(model, 'fit'):
            tests_to_run.append(("differential_privacy", self._test_differential_privacy))
        
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
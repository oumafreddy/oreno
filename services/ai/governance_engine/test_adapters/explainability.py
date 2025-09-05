"""
Explainability testing adapter for AI governance.
Implements SHAP, LIME, and other explainability methods.
"""

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union
import time

from .base import BaseTestAdapter, TestResult, TestConfig, TestStatus

logger = logging.getLogger(__name__)


class ExplainabilityTestAdapter(BaseTestAdapter):
    """
    Test adapter for model explainability using SHAP, LIME, and other methods.
    
    Supports feature importance, local explanations, and global model
    interpretability for tabular and image models.
    """

    @property
    def adapter_name(self) -> str:
        return "explainability"

    @property
    def supported_model_types(self) -> List[str]:
        return ["tabular", "image"]

    def get_available_tests(self) -> List[str]:
        """Return available explainability tests."""
        return [
            "shap_feature_importance",
            "shap_local_explanations",
            "lime_explanations",
            "permutation_importance",
            "partial_dependence",
            "comprehensive_explainability"
        ]

    def validate_config(self, test_config: TestConfig) -> bool:
        """Validate explainability test configuration."""
        # Most explainability tests don't require specific parameters
        # but some might need sample size or explanation parameters
        return True

    def execute_test(
        self,
        model: Any,
        dataset: Any,
        test_config: TestConfig,
        **kwargs
    ) -> TestResult:
        """
        Execute explainability test.
        
        Args:
            model: Trained model to explain
            dataset: Test dataset
            test_config: Test configuration
            **kwargs: Additional parameters
            
        Returns:
            TestResult with explainability metrics
        """
        start_time = time.time()
        
        self._log_test_start(test_config.test_name, "tabular")  # Default to tabular
        
        try:
            # Prepare data
            X_test, y_test = self._prepare_dataset(dataset)
            
            # Execute specific explainability test
            if test_config.test_name == "shap_feature_importance":
                result = self._test_shap_feature_importance(model, X_test, test_config)
            elif test_config.test_name == "shap_local_explanations":
                result = self._test_shap_local_explanations(model, X_test, test_config)
            elif test_config.test_name == "lime_explanations":
                result = self._test_lime_explanations(model, X_test, test_config)
            elif test_config.test_name == "permutation_importance":
                result = self._test_permutation_importance(model, X_test, y_test, test_config)
            elif test_config.test_name == "partial_dependence":
                result = self._test_partial_dependence(model, X_test, test_config)
            elif test_config.test_name == "comprehensive_explainability":
                result = self._test_comprehensive_explainability(model, X_test, y_test, test_config)
            else:
                raise ValueError(f"Unknown explainability test: {test_config.test_name}")
            
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
                    "test_type": "explainability",
                    "explanation_method": test_config.test_name
                }
            )
            
        except Exception as exc:
            execution_time = time.time() - start_time
            self.logger.error(f"Explainability test failed: {exc}")
            
            return TestResult(
                test_name=test_config.test_name,
                status=TestStatus.FAILED,
                passed=False,
                error_message=str(exc),
                execution_time=execution_time
            )

    def _prepare_dataset(self, dataset: Any) -> tuple:
        """Prepare dataset for explainability testing."""
        if isinstance(dataset, pd.DataFrame):
            # Assume last column is target
            X = dataset.drop(columns=[dataset.columns[-1]])
            y = dataset.iloc[:, -1]
        else:
            # Handle other dataset formats
            X, y = dataset
        
        return X, y

    def _test_shap_feature_importance(self, model: Any, X: pd.DataFrame, test_config: TestConfig) -> Dict[str, Any]:
        """Test SHAP feature importance."""
        try:
            # Try to import SHAP
            import shap
            
            # Create SHAP explainer
            if hasattr(model, 'predict_proba'):
                # For models with probability outputs
                explainer = shap.TreeExplainer(model) if hasattr(model, 'tree_') else shap.Explainer(model)
            else:
                explainer = shap.Explainer(model)
            
            # Calculate SHAP values for a sample
            sample_size = test_config.parameters.get("sample_size", min(100, len(X)))
            X_sample = X.sample(n=sample_size, random_state=42)
            
            shap_values = explainer.shap_values(X_sample)
            
            # Calculate feature importance (mean absolute SHAP values)
            if isinstance(shap_values, list):
                # Multi-class case - use first class
                feature_importance = np.mean(np.abs(shap_values[0]), axis=0)
            else:
                feature_importance = np.mean(np.abs(shap_values), axis=0)
            
            # Create feature importance ranking
            feature_names = X.columns.tolist()
            importance_ranking = list(zip(feature_names, feature_importance))
            importance_ranking.sort(key=lambda x: x[1], reverse=True)
            
            # Calculate explainability score (how well we can explain the model)
            # Higher is better - based on consistency of explanations
            explanation_consistency = self._calculate_explanation_consistency(shap_values)
            
            # Generate artifacts
            artifacts = []
            if test_config.parameters.get("save_plots", True):
                plot_path = self._create_artifact_path(test_config.test_name, "shap_summary", "png")
                self._save_shap_summary_plot(explainer, X_sample, shap_values, plot_path)
                artifacts.append(plot_path)
            
            return {
                "passed": explanation_consistency > 0.7,  # Threshold for good explanations
                "score": explanation_consistency,
                "metrics": {
                    "explanation_consistency": explanation_consistency,
                    "top_features": importance_ranking[:5],  # Top 5 features
                    "feature_importance_variance": np.var(feature_importance),
                    "sample_size": sample_size
                },
                "artifacts": artifacts
            }
            
        except ImportError:
            self.logger.warning("SHAP not available, using fallback method")
            return self._fallback_feature_importance(model, X, test_config)
        except Exception as exc:
            self.logger.error(f"SHAP test failed: {exc}")
            raise

    def _test_shap_local_explanations(self, model: Any, X: pd.DataFrame, test_config: TestConfig) -> Dict[str, Any]:
        """Test SHAP local explanations."""
        try:
            import shap
            
            # Create explainer
            explainer = shap.Explainer(model)
            
            # Test on a few instances
            num_instances = test_config.parameters.get("num_instances", 5)
            X_sample = X.sample(n=num_instances, random_state=42)
            
            shap_values = explainer.shap_values(X_sample)
            
            # Calculate local explanation quality metrics
            local_consistency = self._calculate_local_explanation_consistency(shap_values, X_sample)
            
            # Generate artifacts
            artifacts = []
            if test_config.parameters.get("save_plots", True):
                for i in range(min(3, num_instances)):  # Save plots for first 3 instances
                    plot_path = self._create_artifact_path(
                        test_config.test_name, f"local_explanation_{i}", "png"
                    )
                    self._save_shap_waterfall_plot(explainer, X_sample.iloc[i], shap_values[i], plot_path)
                    artifacts.append(plot_path)
            
            return {
                "passed": local_consistency > 0.6,
                "score": local_consistency,
                "metrics": {
                    "local_consistency": local_consistency,
                    "num_instances_tested": num_instances,
                    "explanation_variance": np.var(shap_values) if isinstance(shap_values, np.ndarray) else 0
                },
                "artifacts": artifacts
            }
            
        except ImportError:
            return {"passed": False, "score": 0.0, "metrics": {}, "artifacts": []}
        except Exception as exc:
            self.logger.error(f"SHAP local explanations test failed: {exc}")
            raise

    def _test_lime_explanations(self, model: Any, X: pd.DataFrame, test_config: TestConfig) -> Dict[str, Any]:
        """Test LIME explanations."""
        try:
            from lime import lime_tabular
            
            # Create LIME explainer
            explainer = lime_tabular.LimeTabularExplainer(
                X.values,
                feature_names=X.columns,
                class_names=['class_0', 'class_1'],  # Assume binary classification
                mode='classification'
            )
            
            # Test on a few instances
            num_instances = test_config.parameters.get("num_instances", 5)
            X_sample = X.sample(n=num_instances, random_state=42)
            
            lime_scores = []
            artifacts = []
            
            for i, instance in X_sample.iterrows():
                # Generate LIME explanation
                explanation = explainer.explain_instance(
                    instance.values,
                    model.predict_proba if hasattr(model, 'predict_proba') else model.predict,
                    num_features=min(10, len(X.columns))
                )
                
                # Calculate explanation quality
                explanation_score = self._calculate_lime_explanation_quality(explanation)
                lime_scores.append(explanation_score)
                
                # Save explanation if requested
                if test_config.parameters.get("save_explanations", True):
                    explanation_path = self._create_artifact_path(
                        test_config.test_name, f"lime_explanation_{i}", "html"
                    )
                    explanation.save_to_file(explanation_path)
                    artifacts.append(explanation_path)
            
            avg_lime_score = np.mean(lime_scores)
            
            return {
                "passed": avg_lime_score > 0.5,
                "score": avg_lime_score,
                "metrics": {
                    "average_lime_score": avg_lime_score,
                    "lime_score_variance": np.var(lime_scores),
                    "num_instances_tested": num_instances
                },
                "artifacts": artifacts
            }
            
        except ImportError:
            self.logger.warning("LIME not available")
            return {"passed": False, "score": 0.0, "metrics": {}, "artifacts": []}
        except Exception as exc:
            self.logger.error(f"LIME test failed: {exc}")
            raise

    def _test_permutation_importance(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Test permutation feature importance."""
        try:
            from sklearn.inspection import permutation_importance
            
            # Calculate permutation importance
            perm_importance = permutation_importance(
                model, X, y,
                n_repeats=test_config.parameters.get("n_repeats", 5),
                random_state=42
            )
            
            # Calculate importance metrics
            importance_scores = perm_importance.importances_mean
            importance_std = perm_importance.importances_std
            
            # Calculate stability (lower std is better)
            stability_score = 1.0 - (np.mean(importance_std) / (np.mean(importance_scores) + 1e-8))
            
            # Create feature ranking
            feature_names = X.columns.tolist()
            importance_ranking = list(zip(feature_names, importance_scores, importance_std))
            importance_ranking.sort(key=lambda x: x[1], reverse=True)
            
            return {
                "passed": stability_score > 0.7,
                "score": stability_score,
                "metrics": {
                    "stability_score": stability_score,
                    "top_features": importance_ranking[:5],
                    "importance_variance": np.var(importance_scores),
                    "n_repeats": test_config.parameters.get("n_repeats", 5)
                },
                "artifacts": []
            }
            
        except Exception as exc:
            self.logger.error(f"Permutation importance test failed: {exc}")
            raise

    def _test_partial_dependence(self, model: Any, X: pd.DataFrame, test_config: TestConfig) -> Dict[str, Any]:
        """Test partial dependence plots."""
        try:
            from sklearn.inspection import PartialDependenceDisplay
            
            # Select top features for partial dependence
            num_features = test_config.parameters.get("num_features", 3)
            top_features = X.columns[:num_features].tolist()
            
            # Calculate partial dependence
            pd_display = PartialDependenceDisplay.from_estimator(
                model, X, top_features, grid_resolution=20
            )
            
            # Calculate smoothness of partial dependence curves
            smoothness_scores = []
            for i, feature in enumerate(top_features):
                pd_values = pd_display.pd_results_[i]['values'][0]
                smoothness = self._calculate_curve_smoothness(pd_values)
                smoothness_scores.append(smoothness)
            
            avg_smoothness = np.mean(smoothness_scores)
            
            # Generate artifacts
            artifacts = []
            if test_config.parameters.get("save_plots", True):
                plot_path = self._create_artifact_path(test_config.test_name, "partial_dependence", "png")
                pd_display.figure_.savefig(plot_path, dpi=300, bbox_inches='tight')
                artifacts.append(plot_path)
            
            return {
                "passed": avg_smoothness > 0.6,
                "score": avg_smoothness,
                "metrics": {
                    "average_smoothness": avg_smoothness,
                    "smoothness_scores": smoothness_scores,
                    "features_analyzed": top_features
                },
                "artifacts": artifacts
            }
            
        except Exception as exc:
            self.logger.error(f"Partial dependence test failed: {exc}")
            raise

    def _test_comprehensive_explainability(self, model: Any, X: pd.DataFrame, y: pd.Series, test_config: TestConfig) -> Dict[str, Any]:
        """Run comprehensive explainability tests."""
        results = {}
        scores = []
        
        # Run multiple explainability tests
        tests_to_run = [
            ("permutation_importance", self._test_permutation_importance),
            ("partial_dependence", self._test_partial_dependence)
        ]
        
        # Add SHAP and LIME if available
        try:
            import shap
            tests_to_run.append(("shap_feature_importance", self._test_shap_feature_importance))
        except ImportError:
            pass
        
        try:
            from lime import lime_tabular
            tests_to_run.append(("lime_explanations", self._test_lime_explanations))
        except ImportError:
            pass
        
        all_artifacts = []
        
        for test_name, test_func in tests_to_run:
            try:
                if test_name == "permutation_importance":
                    result = test_func(model, X, y, test_config)
                else:
                    result = test_func(model, X, test_config)
                
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

    def _fallback_feature_importance(self, model: Any, X: pd.DataFrame, test_config: TestConfig) -> Dict[str, Any]:
        """Fallback feature importance when SHAP is not available."""
        try:
            # Use built-in feature importance if available
            if hasattr(model, 'feature_importances_'):
                importance_scores = model.feature_importances_
                feature_names = X.columns.tolist()
                
                # Calculate importance metrics
                importance_ranking = list(zip(feature_names, importance_scores))
                importance_ranking.sort(key=lambda x: x[1], reverse=True)
                
                # Calculate score based on how concentrated the importance is
                concentration_score = np.max(importance_scores) / np.sum(importance_scores)
                
                return {
                    "passed": concentration_score > 0.1,  # At least some features are important
                    "score": concentration_score,
                    "metrics": {
                        "concentration_score": concentration_score,
                        "top_features": importance_ranking[:5],
                        "method": "built_in_importance"
                    },
                    "artifacts": []
                }
            else:
                return {
                    "passed": False,
                    "score": 0.0,
                    "metrics": {"error": "No feature importance method available"},
                    "artifacts": []
                }
                
        except Exception as exc:
            self.logger.error(f"Fallback feature importance failed: {exc}")
            raise

    def _calculate_explanation_consistency(self, shap_values: np.ndarray) -> float:
        """Calculate consistency of SHAP explanations."""
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Calculate variance in SHAP values across samples
        # Lower variance indicates more consistent explanations
        variance = np.var(shap_values)
        consistency = 1.0 / (1.0 + variance)
        
        return min(consistency, 1.0)

    def _calculate_local_explanation_consistency(self, shap_values: np.ndarray, X_sample: pd.DataFrame) -> float:
        """Calculate consistency of local explanations."""
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Calculate how well explanations align with feature values
        # This is a simplified metric
        feature_importance = np.mean(np.abs(shap_values), axis=0)
        feature_variance = np.var(X_sample.values, axis=0)
        
        # Higher importance should correlate with higher variance (more informative features)
        correlation = np.corrcoef(feature_importance, feature_variance)[0, 1]
        
        return max(0, correlation)  # Return positive correlation

    def _calculate_lime_explanation_quality(self, explanation) -> float:
        """Calculate quality of LIME explanation."""
        # Extract explanation scores
        explanation_list = explanation.as_list()
        
        if not explanation_list:
            return 0.0
        
        # Calculate quality based on explanation strength and diversity
        scores = [abs(score) for _, score in explanation_list]
        
        # Quality based on how strong and diverse the explanations are
        max_score = max(scores) if scores else 0
        score_diversity = len([s for s in scores if s > 0.1 * max_score])
        
        quality = min(1.0, (max_score * score_diversity) / len(explanation_list))
        
        return quality

    def _calculate_curve_smoothness(self, values: np.ndarray) -> float:
        """Calculate smoothness of a curve (partial dependence)."""
        if len(values) < 2:
            return 0.0
        
        # Calculate second derivative (curvature)
        second_derivative = np.diff(values, n=2)
        
        # Smoothness is inverse of curvature variance
        curvature_variance = np.var(second_derivative)
        smoothness = 1.0 / (1.0 + curvature_variance)
        
        return min(smoothness, 1.0)

    def _save_shap_summary_plot(self, explainer, X_sample, shap_values, path: str):
        """Save SHAP summary plot."""
        try:
            import shap
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 8))
            shap.summary_plot(shap_values, X_sample, show=False)
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as exc:
            self.logger.warning(f"Could not save SHAP summary plot: {exc}")

    def _save_shap_waterfall_plot(self, explainer, instance, shap_values, path: str):
        """Save SHAP waterfall plot."""
        try:
            import shap
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            shap.waterfall_plot(explainer.expected_value, shap_values, instance, show=False)
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as exc:
            self.logger.warning(f"Could not save SHAP waterfall plot: {exc}")
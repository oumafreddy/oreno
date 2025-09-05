#!/usr/bin/env python3
"""
Test script for AI governance test adapters.
This script demonstrates the test adapters functionality.
"""

import os
import sys
import django
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'ai', 'governance_engine'))

from test_adapters import (
    FairnessTestAdapter,
    ExplainabilityTestAdapter,
    RobustnessTestAdapter,
    PrivacyTestAdapter,
    TestConfig
)
from test_executor import TestExecutor


def create_sample_data():
    """Create sample data for testing."""
    # Generate synthetic dataset
    X, y = make_classification(
        n_samples=1000,
        n_features=10,
        n_informative=8,
        n_redundant=2,
        n_classes=2,
        random_state=42
    )
    
    # Convert to DataFrame
    feature_names = [f'feature_{i}' for i in range(X.shape[1])]
    X_df = pd.DataFrame(X, columns=feature_names)
    
    # Add a sensitive attribute (simulated)
    np.random.seed(42)
    X_df['sensitive_attribute'] = np.random.choice(['group_a', 'group_b'], size=len(X_df))
    
    # Add target to DataFrame
    X_df['target'] = y
    
    return X_df


def train_sample_model(X, y):
    """Train a sample model for testing."""
    # Remove non-numeric columns for training
    X_numeric = X.select_dtypes(include=[np.number])
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_numeric, y)
    return model


def test_fairness_adapter():
    """Test the fairness adapter."""
    print("Testing Fairness Adapter...")
    
    # Create sample data
    data = create_sample_data()
    X = data.drop(['target'], axis=1)
    y = data['target']
    
    # Train model on numeric features only
    X_numeric = X.select_dtypes(include=[np.number])
    model = train_sample_model(X_numeric, y)
    
    # Create test configuration
    test_config = TestConfig(
        test_name='demographic_parity',
        parameters={
            'sensitive_attribute': 'sensitive_attribute',
            'privileged_group': 'group_a'
        },
        thresholds={'demographic_parity': 0.1}
    )
    
    # Test fairness adapter with full dataset (including sensitive attribute)
    adapter = FairnessTestAdapter()
    result = adapter.execute_test(model, data, test_config)
    
    print(f"  Test: {result.test_name}")
    print(f"  Passed: {result.passed}")
    print(f"  Score: {result.score}")
    print(f"  Metrics: {result.metrics}")
    print()


def test_explainability_adapter():
    """Test the explainability adapter."""
    print("Testing Explainability Adapter...")
    
    # Create sample data
    data = create_sample_data()
    X = data.drop(['target'], axis=1)
    y = data['target']
    
    # Train model on numeric features only
    X_numeric = X.select_dtypes(include=[np.number])
    model = train_sample_model(X_numeric, y)
    
    # Create test configuration
    test_config = TestConfig(
        test_name='permutation_importance',
        parameters={'n_repeats': 3}
    )
    
    # Test explainability adapter with numeric features only
    adapter = ExplainabilityTestAdapter()
    result = adapter.execute_test(model, X_numeric, test_config)
    
    print(f"  Test: {result.test_name}")
    print(f"  Passed: {result.passed}")
    print(f"  Score: {result.score}")
    print(f"  Metrics: {result.metrics}")
    print()


def test_robustness_adapter():
    """Test the robustness adapter."""
    print("Testing Robustness Adapter...")
    
    # Create sample data
    data = create_sample_data()
    X = data.drop(['target'], axis=1)
    y = data['target']
    
    # Train model on numeric features only
    X_numeric = X.select_dtypes(include=[np.number])
    model = train_sample_model(X_numeric, y)
    
    # Create test configuration
    test_config = TestConfig(
        test_name='adversarial_noise',
        parameters={'noise_levels': [0.01, 0.05, 0.1]}
    )
    
    # Test robustness adapter with numeric features only
    adapter = RobustnessTestAdapter()
    result = adapter.execute_test(model, X_numeric, test_config)
    
    print(f"  Test: {result.test_name}")
    print(f"  Passed: {result.passed}")
    print(f"  Score: {result.score}")
    print(f"  Metrics: {result.metrics}")
    print()


def test_privacy_adapter():
    """Test the privacy adapter."""
    print("Testing Privacy Adapter...")
    
    # Create sample data
    data = create_sample_data()
    X = data.drop(['target'], axis=1)
    y = data['target']
    
    # Train model on numeric features only
    X_numeric = X.select_dtypes(include=[np.number])
    model = train_sample_model(X_numeric, y)
    
    # Create test configuration
    test_config = TestConfig(
        test_name='data_leakage',
        parameters={'suspicious_threshold': 0.95}
    )
    
    # Test privacy adapter with numeric features only
    adapter = PrivacyTestAdapter()
    result = adapter.execute_test(model, X_numeric, test_config)
    
    print(f"  Test: {result.test_name}")
    print(f"  Passed: {result.passed}")
    print(f"  Score: {result.score}")
    print(f"  Metrics: {result.metrics}")
    print()


def test_executor():
    """Test the test executor."""
    print("Testing Test Executor...")
    
    # Create sample data
    data = create_sample_data()
    X = data.drop(['target'], axis=1)
    y = data['target']
    
    # Train model on numeric features only
    X_numeric = X.select_dtypes(include=[np.number])
    model = train_sample_model(X_numeric, y)
    
    # Create test configurations
    test_configs = [
        TestConfig(
            test_name='demographic_parity',
            parameters={
                'sensitive_attribute': 'sensitive_attribute',
                'privileged_group': 'group_a'
            },
            thresholds={'demographic_parity': 0.1}
        ),
        TestConfig(
            test_name='permutation_importance',
            parameters={'n_repeats': 3}
        ),
        TestConfig(
            test_name='adversarial_noise',
            parameters={'noise_levels': [0.01, 0.05]}
        )
    ]
    
    # Test executor
    executor = TestExecutor()
    
    # Get available tests
    available_tests = executor.get_available_tests('tabular')
    print(f"  Available tests for tabular models: {available_tests}")
    
    # Execute tests
    results = []
    for test_config in test_configs:
        # Use full dataset for fairness test, numeric only for others
        dataset = data if test_config.test_name == 'demographic_parity' else X_numeric
        result = executor.execute_single_test(
            test_config.test_name,
            model,
            dataset,
            test_config
        )
        results.append(result)
    
    # Generate summary
    summary = executor.get_test_summary(results)
    print(f"  Test Summary:")
    print(f"    Total tests: {summary['total_tests']}")
    print(f"    Passed: {summary['passed_tests']}")
    print(f"    Failed: {summary['failed_tests']}")
    print(f"    Overall score: {summary['overall_score']:.2f}")
    print()


def main():
    """Run all tests."""
    print("AI Governance Test Adapters Demo")
    print("=" * 50)
    print()
    
    try:
        test_fairness_adapter()
        test_explainability_adapter()
        test_robustness_adapter()
        test_privacy_adapter()
        test_executor()
        
        print("All tests completed successfully!")
        
    except Exception as exc:
        print(f"Error during testing: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
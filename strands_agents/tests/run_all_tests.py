"""
Test runner for all Strands Agents tests
Runs unit tests, integration tests, and performance tests
"""

import unittest
import sys
import os
from datetime import datetime
import json

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def run_test_suite():
    """Run the complete test suite"""
    print("=" * 70)
    print("AWS STRANDS AGENTS TEST SUITE")
    print("=" * 70)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.splitlines()[-1] if traceback else 'No details'}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.splitlines()[-1] if traceback else 'No details'}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    print(f"Completed at: {datetime.now().isoformat()}")
    
    # Return True if all tests passed
    return len(result.failures) == 0 and len(result.errors) == 0

def run_unit_tests_only():
    """Run only unit tests"""
    print("Running Unit Tests Only...")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add unit tests
    unit_test_dir = os.path.join(os.path.dirname(__file__), 'unit')
    if os.path.exists(unit_test_dir):
        unit_suite = loader.discover(unit_test_dir, pattern='test_*.py')
        suite.addTest(unit_suite)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0

def run_integration_tests_only():
    """Run only integration tests"""
    print("Running Integration Tests Only...")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add integration tests
    integration_test_dir = os.path.join(os.path.dirname(__file__), 'integration')
    if os.path.exists(integration_test_dir):
        integration_suite = loader.discover(integration_test_dir, pattern='test_*.py')
        suite.addTest(integration_suite)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0

def generate_test_report(result):
    """Generate a detailed test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": result.testsRun,
            "passed": result.testsRun - len(result.failures) - len(result.errors),
            "failed": len(result.failures),
            "errors": len(result.errors),
            "success_rate": ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        },
        "failures": [
            {
                "test": str(test),
                "traceback": traceback
            }
            for test, traceback in result.failures
        ],
        "errors": [
            {
                "test": str(test),
                "traceback": traceback
            }
            for test, traceback in result.errors
        ]
    }
    
    # Save report to file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path = os.path.join(os.path.dirname(__file__), report_file)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed test report saved to: {report_path}")
    return report

if __name__ == '__main__':
    # Check command line arguments for specific test types
    if len(sys.argv) > 1:
        if sys.argv[1] == 'unit':
            success = run_unit_tests_only()
        elif sys.argv[1] == 'integration':
            success = run_integration_tests_only()
        else:
            print(f"Unknown test type: {sys.argv[1]}")
            print("Usage: python run_all_tests.py [unit|integration]")
            sys.exit(1)
    else:
        success = run_test_suite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
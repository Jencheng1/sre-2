import os
import sys
import json
import logging
import pytest
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_tests():
    """Run the SRE Copilot agent tests and generate a report."""
    try:
        # Create test results directory if it doesn't exist
        test_results_dir = Path('test_results')
        test_results_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for the test run
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = test_results_dir / f'test_report_{timestamp}.json'
        
        # Run pytest with JSON output
        pytest_args = [
            'test_agents.py',
            '-v',
            '--json-report',
            f'--json-report-file={report_file}'
        ]
        
        logger.info("Starting SRE Copilot agent tests...")
        exit_code = pytest.main(pytest_args)
        
        # Read and process the test report
        if report_file.exists():
            with open(report_file, 'r') as f:
                report = json.load(f)
            
            # Calculate test statistics
            total_tests = report['summary']['total']
            passed_tests = report['summary']['passed']
            failed_tests = report['summary']['failed']
            skipped_tests = report['summary']['skipped']
            
            # Print test summary
            logger.info("\nTest Summary:")
            logger.info(f"Total Tests: {total_tests}")
            logger.info(f"Passed: {passed_tests}")
            logger.info(f"Failed: {failed_tests}")
            logger.info(f"Skipped: {skipped_tests}")
            
            # Print detailed results for failed tests
            if failed_tests > 0:
                logger.info("\nFailed Tests:")
                for test in report['tests']:
                    if test['outcome'] == 'failed':
                        logger.error(f"{test['nodeid']}: {test['call']['longrepr']}")
            
            # Generate HTML report
            html_report = test_results_dir / f'test_report_{timestamp}.html'
            pytest.main([
                'test_agents.py',
                '--html-report',
                f'--html-report-file={html_report}'
            ])
            
            logger.info(f"\nTest reports generated:")
            logger.info(f"JSON Report: {report_file}")
            logger.info(f"HTML Report: {html_report}")
            
            return exit_code
        else:
            logger.error("Test report file not found")
            return 1
            
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests()) 
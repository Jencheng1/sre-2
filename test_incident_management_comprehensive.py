#!/usr/bin/env python3
"""
Comprehensive test suite for Incident Management functionality.
Tests all aspects of incident generation, analysis, and management.
"""

import json
import time
import boto3
from datetime import datetime, timedelta
import requests
from colorama import init, Fore, Style

init(autoreset=True)

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name='us-east-1')
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
ssm = boto3.client('ssm', region_name='us-east-1')
logs_client = boto3.client('logs', region_name='us-east-1')

# Test configuration
STREAMLIT_URL = "http://localhost:8501"
SUPERVISOR_LAMBDA = 'sre-supervisor-lambda'
KNOWLEDGE_BASE_LAMBDA = 'sre-knowledge-base-agent-lambda'

class IncidentManagementTester:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
        
    def print_header(self, text):
        """Print a formatted header."""
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.CYAN}{text.center(60)}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
        
    def print_test_result(self, test_name, passed, details=""):
        """Print test result with color coding."""
        if passed:
            print(f"{Fore.GREEN}✓ {test_name} - PASSED{Style.RESET_ALL}")
            self.passed_tests += 1
        else:
            print(f"{Fore.RED}✗ {test_name} - FAILED{Style.RESET_ALL}")
            if details:
                print(f"  {Fore.YELLOW}Details: {details}{Style.RESET_ALL}")
            self.failed_tests += 1
            
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        
    def test_supervisor_lambda_ai(self):
        """Test supervisor Lambda with AI-powered analysis."""
        test_name = "Supervisor Lambda AI Analysis"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # Test with performance incident
            payload = {
                'action': 'analyze',
                'incident_description': 'Application experiencing severe performance degradation with high CPU usage',
                'service': 'demo-app',
                'environment': 'production',
                'enable_kb': True
            }
            
            response = lambda_client.invoke(
                FunctionName=SUPERVISOR_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            if result['StatusCode'] == 200:
                # Parse the response properly
            payload_data = response['Payload'].read()
            body = json.loads(payload_data)
                
                # Check if AI analysis is present
                root_cause = body.get('body', {})
                if isinstance(root_cause, str):
                    root_cause = json.loads(root_cause)
                
                analysis = root_cause.get('root_cause_analysis', '')
                
                # Check for AI-generated content indicators
                ai_indicators = [
                    'Root Cause Analysis',
                    'Impact Assessment',
                    'Immediate Mitigation Steps',
                    'Long-term Recommendations'
                ]
                
                ai_powered = all(indicator in analysis for indicator in ai_indicators)
                
                if ai_powered and 'Under investigation' not in analysis:
                    self.print_test_result(test_name, True)
                    print(f"  {Fore.GREEN}✓ AI analysis detected with all required sections")
                else:
                    self.print_test_result(test_name, False, "AI analysis not detected or incomplete")
                    print(f"  {Fore.YELLOW}Analysis preview: {analysis[:200]}...")
                    
            else:
                self.print_test_result(test_name, False, f"Lambda returned status {result['StatusCode']}")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_incident_types(self):
        """Test different incident types for proper analysis."""
        test_name = "Incident Type Analysis"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        incident_types = [
            {
                'type': 'performance',
                'description': 'Application response time exceeding 5 seconds, users experiencing slowness',
                'expected_keywords': ['CPU', 'memory', 'response time', 'performance']
            },
            {
                'type': 'security',
                'description': 'Multiple unauthorized access attempts detected from unknown IP addresses',
                'expected_keywords': ['security', 'unauthorized', 'authentication', 'access']
            },
            {
                'type': 'outage',
                'description': 'Complete service outage, application is down and not responding',
                'expected_keywords': ['outage', 'availability', 'error rate', 'service failure']
            }
        ]
        
        all_passed = True
        
        for incident in incident_types:
            try:
                payload = {
                    'action': 'analyze',
                    'incident_description': incident['description'],
                    'service': 'test-service',
                    'environment': 'test'
                }
                
                response = lambda_client.invoke(
                    FunctionName=SUPERVISOR_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                result = json.loads(response['Payload'].read())
                body = json.loads(result['body'])
                
                # Check if incident type was correctly identified
                detected_type = body.get('incident_type', '')
                analysis = body.get('root_cause_analysis', '').lower()
                
                # Check for expected keywords in analysis
                keywords_found = sum(1 for keyword in incident['expected_keywords'] if keyword.lower() in analysis)
                
                if detected_type == incident['type'] and keywords_found >= 2:
                    print(f"  {Fore.GREEN}✓ {incident['type']} incident: Correctly analyzed")
                else:
                    print(f"  {Fore.RED}✗ {incident['type']} incident: Analysis incomplete")
                    all_passed = False
                    
            except Exception as e:
                print(f"  {Fore.RED}✗ {incident['type']} incident: {str(e)}")
                all_passed = False
                
        self.print_test_result(test_name, all_passed)
        
    def test_metrics_generation(self):
        """Test CloudWatch metrics generation."""
        test_name = "CloudWatch Metrics Generation"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # Put test metrics
            namespace = 'SREDemo/Application'
            metrics = [
                {'name': 'CPUUtilization', 'value': 85.5},
                {'name': 'MemoryUtilization', 'value': 72.3},
                {'name': 'ErrorRate', 'value': 2.1},
                {'name': 'ResponseTime', 'value': 1250}
            ]
            
            for metric in metrics:
                cloudwatch.put_metric_data(
                    Namespace=namespace,
                    MetricData=[
                        {
                            'MetricName': metric['name'],
                            'Value': metric['value'],
                            'Timestamp': datetime.utcnow(),
                            'Dimensions': [
                                {'Name': 'Environment', 'Value': 'demo'},
                                {'Name': 'Service', 'Value': 'sre-demo-app'}
                            ]
                        }
                    ]
                )
                
            # Wait for metrics to be available
            time.sleep(2)
            
            # Verify metrics were created
            response = cloudwatch.list_metrics(
                Namespace=namespace,
                Dimensions=[
                    {'Name': 'Environment', 'Value': 'demo'},
                    {'Name': 'Service', 'Value': 'sre-demo-app'}
                ]
            )
            
            created_metrics = [m['MetricName'] for m in response.get('Metrics', [])]
            all_created = all(m['name'] in created_metrics for m in metrics)
            
            self.print_test_result(test_name, all_created)
            if all_created:
                print(f"  {Fore.GREEN}✓ All {len(metrics)} metrics created successfully")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_log_generation(self):
        """Test CloudWatch logs generation."""
        test_name = "CloudWatch Logs Generation"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            log_group = '/aws/lambda/sre-supervisor-lambda'  # Use existing log group
            log_stream = f'test-stream-{int(time.time())}'
            
            # Create log stream
            try:
                logs_client.create_log_stream(
                    logGroupName=log_group,
                    logStreamName=log_stream
                )
            except logs_client.exceptions.ResourceAlreadyExistsException:
                pass
                
            # Put test log events
            test_events = [
                {'level': 'ERROR', 'message': 'Database connection timeout after 30 seconds'},
                {'level': 'WARNING', 'message': 'Memory usage approaching threshold: 85%'},
                {'level': 'INFO', 'message': 'Health check completed successfully'},
                {'level': 'ERROR', 'message': 'Failed to process user request: NullPointerException'}
            ]
            
            events = []
            for event in test_events:
                events.append({
                    'timestamp': int(time.time() * 1000),
                    'message': f"[{event['level']}] {event['message']}"
                })
                
            logs_client.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                logEvents=events
            )
            
            # Verify logs were created
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                logStreamNames=[log_stream],
                limit=10
            )
            
            created_events = len(response.get('events', []))
            
            self.print_test_result(test_name, created_events == len(test_events))
            if created_events == len(test_events):
                print(f"  {Fore.GREEN}✓ All {len(test_events)} log events created successfully")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_knowledge_base_integration(self):
        """Test Knowledge Base integration with incident analysis."""
        test_name = "Knowledge Base Integration"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # First, create a test incident in KB
            kb_payload = {
                'action': 'add_item',
                'item': {
                    'id': f'test-incident-{int(time.time())}',
                    'type': 'incident',
                    'title': 'Test Database Connection Failure',
                    'description': 'Database connection pool exhausted causing application errors',
                    'resolution': 'Increased connection pool size from 50 to 100 connections',
                    'tags': ['database', 'connection', 'performance'],
                    'severity': 'high'
                }
            }
            
            kb_response = lambda_client.invoke(
                FunctionName=KNOWLEDGE_BASE_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(kb_payload)
            )
            
            # Now test incident analysis with KB context
            incident_payload = {
                'action': 'analyze',
                'incident_description': 'Database connection errors, unable to connect to RDS instance',
                'service': 'api-service',
                'environment': 'production',
                'enable_kb': True
            }
            
            response = lambda_client.invoke(
                FunctionName=SUPERVISOR_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(incident_payload)
            )
            
            result = json.loads(response['Payload'].read())
            body = json.loads(result['body'])
            
            kb_insights = body.get('knowledge_base_insights', {})
            similar_found = kb_insights.get('similar_incidents_found', 0) > 0
            has_resolution = kb_insights.get('has_suggested_resolution', False)
            
            self.print_test_result(test_name, similar_found or has_resolution)
            if similar_found:
                print(f"  {Fore.GREEN}✓ Found {kb_insights.get('similar_incidents_found', 0)} similar incidents in KB")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_streamlit_api(self):
        """Test Streamlit API endpoints if available."""
        test_name = "Streamlit API Endpoints"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # Check if Streamlit is running
            response = requests.get(STREAMLIT_URL, timeout=5)
            
            if response.status_code == 200:
                self.print_test_result(test_name, True)
                print(f"  {Fore.GREEN}✓ Streamlit dashboard is accessible at {STREAMLIT_URL}")
            else:
                self.print_test_result(test_name, False, f"Status code: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.print_test_result(test_name, False, "Streamlit not running or not accessible")
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_incident_correlation(self):
        """Test incident correlation capabilities."""
        test_name = "Incident Correlation"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # Generate multiple related incidents
            incidents = [
                'High CPU usage on application servers exceeding 90%',
                'Database query response time increased to 5 seconds',
                'Memory utilization reaching critical levels at 95%'
            ]
            
            analyses = []
            
            for desc in incidents:
                payload = {
                    'action': 'analyze',
                    'incident_description': desc,
                    'service': 'correlation-test',
                    'environment': 'test'
                }
                
                response = lambda_client.invoke(
                    FunctionName=SUPERVISOR_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                result = json.loads(response['Payload'].read())
                body = json.loads(result['body'])
                analyses.append(body)
                
            # Check if incidents are properly analyzed
            all_analyzed = all(a.get('root_cause_analysis', '') != '' for a in analyses)
            
            self.print_test_result(test_name, all_analyzed)
            if all_analyzed:
                print(f"  {Fore.GREEN}✓ All {len(incidents)} incidents analyzed successfully")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_error_handling(self):
        """Test error handling and edge cases."""
        test_name = "Error Handling"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        edge_cases = [
            {
                'name': 'Empty description',
                'payload': {'action': 'analyze', 'incident_description': ''}
            },
            {
                'name': 'Missing parameters',
                'payload': {'action': 'analyze'}
            },
            {
                'name': 'Very long description',
                'payload': {'action': 'analyze', 'incident_description': 'A' * 5000}
            }
        ]
        
        all_handled = True
        
        for case in edge_cases:
            try:
                response = lambda_client.invoke(
                    FunctionName=SUPERVISOR_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(case['payload'])
                )
                
                # Should handle gracefully without throwing exceptions
                result = json.loads(response['Payload'].read())
                if result.get('StatusCode', result.get('statusCode', 0)) in [200, 500]:
                    print(f"  {Fore.GREEN}✓ {case['name']}: Handled gracefully")
                else:
                    print(f"  {Fore.RED}✗ {case['name']}: Unexpected response")
                    all_handled = False
                    
            except Exception as e:
                print(f"  {Fore.RED}✗ {case['name']}: Exception thrown - {str(e)}")
                all_handled = False
                
        self.print_test_result(test_name, all_handled)
        
    def generate_summary_report(self):
        """Generate a summary report of all tests."""
        self.print_header("TEST SUMMARY REPORT")
        
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"{Fore.CYAN}Total Tests Run: {total_tests}")
        print(f"{Fore.GREEN}Passed: {self.passed_tests}")
        print(f"{Fore.RED}Failed: {self.failed_tests}")
        print(f"{Fore.YELLOW}Pass Rate: {pass_rate:.1f}%\n")
        
        if self.failed_tests > 0:
            print(f"{Fore.RED}Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}")
                    if result['details']:
                        print(f"    {Fore.YELLOW}{result['details']}")
                        
        # Save report to file
        report_file = f"incident_management_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tests': total_tests,
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'pass_rate': pass_rate,
                'results': self.test_results
            }, f, indent=2)
            
        print(f"\n{Fore.CYAN}Report saved to: {report_file}")
        
def main():
    """Run all incident management tests."""
    tester = IncidentManagementTester()
    
    tester.print_header("INCIDENT MANAGEMENT TEST SUITE")
    
    print(f"{Fore.YELLOW}Starting comprehensive incident management tests...")
    print(f"{Fore.YELLOW}This will test AI analysis, metrics, logs, KB integration, and more.\n")
    
    # Run all tests
    tester.test_supervisor_lambda_ai()
    tester.test_incident_types()
    tester.test_metrics_generation()
    tester.test_log_generation()
    tester.test_knowledge_base_integration()
    tester.test_streamlit_api()
    tester.test_incident_correlation()
    tester.test_error_handling()
    
    # Generate summary
    tester.generate_summary_report()
    
if __name__ == "__main__":
    main()
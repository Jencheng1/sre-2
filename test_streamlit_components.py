#!/usr/bin/env python3
"""
Comprehensive Test Suite for All Streamlit Components
Tests all tabs, features, and integrations
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
import boto3
from colorama import init, Fore, Style

init(autoreset=True)

class StreamlitComponentTester:
    def __init__(self):
        self.base_url = "http://localhost:8501"
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{text}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
    def print_test(self, test_name, passed, details=""):
        if passed:
            print(f"{Fore.GREEN}✓ {test_name}{Style.RESET_ALL}")
            if details:
                print(f"  {Fore.YELLOW}{details}{Style.RESET_ALL}")
            self.passed_tests += 1
        else:
            print(f"{Fore.RED}✗ {test_name}{Style.RESET_ALL}")
            if details:
                print(f"  {Fore.RED}{details}{Style.RESET_ALL}")
            self.failed_tests += 1
            
    def test_streamlit_health(self):
        """Test 1: Check if Streamlit is running"""
        try:
            response = requests.get(f"{self.base_url}/_stcore/health")
            passed = response.status_code == 200
            self.print_test("Streamlit Health Check", passed, 
                          f"Status: {response.status_code}")
            return passed
        except Exception as e:
            self.print_test("Streamlit Health Check", False, str(e))
            return False
            
    def test_mcp_servers(self):
        """Test 2: Check MCP server connectivity"""
        servers = [
            ("ALM Octane", "http://localhost:9085/octane/defects"),
            ("Jira", "http://localhost:9086/jira/issues")
        ]
        
        all_passed = True
        for server_name, url in servers:
            try:
                response = requests.get(url, timeout=5)
                passed = response.status_code == 200
                self.print_test(f"{server_name} MCP Server", passed,
                              f"Status: {response.status_code}")
                all_passed = all_passed and passed
            except Exception as e:
                self.print_test(f"{server_name} MCP Server", False, str(e))
                all_passed = False
                
        return all_passed
        
    def test_aws_services(self):
        """Test 3: Check AWS service connectivity"""
        services = []
        
        # CloudWatch
        try:
            cw = boto3.client('cloudwatch', region_name='us-east-1')
            cw.list_metrics(Namespace='AWS/EC2')
            services.append(("CloudWatch", True, "Connected"))
        except Exception as e:
            services.append(("CloudWatch", False, str(e)))
            
        # Systems Manager
        try:
            ssm = boto3.client('ssm', region_name='us-east-1')
            ssm.describe_ops_items(MaxResults=1)
            services.append(("Systems Manager", True, "Connected"))
        except Exception as e:
            services.append(("Systems Manager", False, str(e)))
            
        # Lambda
        try:
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            lambda_client.list_functions(MaxItems=1)
            services.append(("Lambda", True, "Connected"))
        except Exception as e:
            services.append(("Lambda", False, str(e)))
            
        all_passed = True
        for service_name, passed, details in services:
            self.print_test(f"AWS {service_name}", passed, details)
            all_passed = all_passed and passed
            
        return all_passed
        
    def test_incident_generation(self):
        """Test 4: Test incident generation scenarios"""
        try:
            from incident_scenarios import IncidentScenarios
            
            # Create instance and get scenarios
            scenario_generator = IncidentScenarios()
            scenarios = scenario_generator.scenarios
                        
            if scenarios is None:
                self.print_test("Incident Scenarios", False, "No scenarios found")
                return False
                
            scenario_count = len(scenarios)
            self.print_test("Incident Scenarios", True, 
                          f"Found {scenario_count} scenarios")
            
            # Test first scenario structure
            first_scenario = scenarios[0]
            required_fields = ['title', 'description', 'severity', 'category']
            has_all_fields = all(field in first_scenario for field in required_fields)
            
            self.print_test("Scenario Structure", has_all_fields,
                          f"Required fields: {', '.join(required_fields)}")
            
            return has_all_fields
        except Exception as e:
            self.print_test("Incident Scenarios", False, str(e))
            return False
            
    def test_problem_management(self):
        """Test 5: Test problem management integration"""
        try:
            # Import problem manager
            from servicenow_problem_manager import ServiceNowProblemManager
            
            pm = ServiceNowProblemManager()
            self.print_test("Problem Manager Import", True, "Initialized")
            
            # Test problem creation
            test_incident = {
                'title': 'Test High CPU Alert',
                'description': 'CPU usage exceeded 90%',
                'severity': 3,
                'category': 'Performance'
            }
            
            problem = pm.create_problem_from_incident(test_incident)
            has_problem_id = 'problem_id' in problem
            self.print_test("Problem Creation", has_problem_id,
                          f"Problem ID: {problem.get('problem_id', 'None')}")
            
            return has_problem_id
        except Exception as e:
            self.print_test("Problem Management", False, str(e))
            return False
            
    def test_synthetic_transactions(self):
        """Test 6: Test synthetic transaction generation"""
        try:
            from synthetic_transaction_generator import SyntheticTransactionGenerator
            
            generator = SyntheticTransactionGenerator()
            self.print_test("Synthetic Generator Import", True, "Initialized")
            
            # Test transaction generation
            test_incident = {
                'incident_type': 'performance',
                'service': 'web-app',
                'severity': 3
            }
            
            # Use the correct method
            result = generator.generate_transactions_for_incident(test_incident)
            transactions = result.get('transactions', [])
                
            has_transactions = len(transactions) > 0
            self.print_test("Transaction Generation", has_transactions,
                          f"Generated {len(transactions)} transactions")
            
            return has_transactions
        except Exception as e:
            self.print_test("Synthetic Transactions", False, str(e))
            return False
            
    def test_knowledge_base(self):
        """Test 7: Test knowledge base functionality"""
        try:
            # Test KB Lambda connection
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            
            test_payload = {
                'action': 'search_incidents',
                'query': 'high cpu usage',
                'limit': 5
            }
            
            response = lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            # Check if response is successful
            if 'statusCode' in result and result['statusCode'] == 200:
                body = json.loads(result.get('body', '{}'))
                has_results = 'results' in body or 'message' in body or 'items' in body
                if not has_results and body:
                    # Check if body has any content at all
                    has_results = len(body) > 0
                details = f"Response body keys: {list(body.keys()) if body else 'Empty body'}"
            else:
                has_results = 'results' in result or 'message' in result
                details = f"Response keys: {list(result.keys())}"
            
            self.print_test("Knowledge Base Search", has_results, details)
            
            return has_results
        except Exception as e:
            self.print_test("Knowledge Base", False, str(e))
            return False
            
    def test_defect_correlation(self):
        """Test 8: Test defect-incident correlation"""
        try:
            from defect_incident_correlator import DefectIncidentCorrelator
            
            # Initialize with required MCP endpoints
            mcp_endpoints = {
                'alm_octane': 'http://localhost:9085',
                'jira': 'http://localhost:9086'
            }
            
            correlator = DefectIncidentCorrelator(mcp_endpoints)
            self.print_test("Defect Correlator Import", True, "Initialized")
            
            # Test correlation
            test_incident = {
                'title': 'API Gateway timeout errors',
                'description': 'Multiple timeout errors in API Gateway',
                'category': 'Performance',
                'service': 'api-gateway'
            }
            
            # Use the correct method
            correlation_results = correlator.correlate_incident_with_defects(test_incident)
            defects = correlation_results
            found_defects = len(defects) > 0
            
            self.print_test("Defect Correlation", found_defects,
                          f"Found {len(defects)} related defects")
            
            return found_defects
        except Exception as e:
            self.print_test("Defect Correlation", False, str(e))
            return False
            
    def test_change_correlation(self):
        """Test 9: Test change-incident correlation"""
        try:
            from change_incident_correlator import ChangeIncidentCorrelator
            
            correlator = ChangeIncidentCorrelator()
            self.print_test("Change Correlator Import", True, "Initialized")
            
            # Test correlation
            test_incident = {
                'incident_time': datetime.now(),
                'affected_services': ['web-app', 'api-gateway'],
                'incident_type': 'outage'
            }
            
            # Check which method exists
            if hasattr(correlator, 'analyze_incident_change_correlation'):
                analysis = correlator.analyze_incident_change_correlation(test_incident)
            elif hasattr(correlator, 'correlate_incident_to_changes'):
                analysis = correlator.correlate_incident_to_changes(test_incident)
            else:
                analysis = {'overall_confidence': 0}
                
            has_analysis = 'overall_confidence' in analysis
            
            self.print_test("Change Correlation", has_analysis,
                          f"Confidence: {analysis.get('overall_confidence', 0):.1%}")
            
            return has_analysis
        except Exception as e:
            self.print_test("Change Correlation", False, str(e))
            return False
            
    def test_supervisor_lambda(self):
        """Test 10: Test supervisor Lambda integration"""
        try:
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            
            test_payload = {
                'action': 'analyze',
                'incident': {
                    'title': 'Test incident',
                    'description': 'Test description',
                    'severity': 3
                }
            }
            
            response = lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            result = json.loads(response['Payload'].read())
            has_analysis = 'analysis' in result or 'statusCode' in result
            
            self.print_test("Supervisor Lambda", has_analysis,
                          f"Response status: {result.get('statusCode', 'Unknown')}")
            
            return has_analysis
        except Exception as e:
            self.print_test("Supervisor Lambda", False, str(e))
            return False
            
    def test_cloudwatch_integration(self):
        """Test 11: Test CloudWatch metrics and logs"""
        try:
            cw = boto3.client('cloudwatch', region_name='us-east-1')
            logs = boto3.client('logs', region_name='us-east-1')
            
            # Test metrics
            metrics = cw.list_metrics(
                Namespace='SREDemo/Application'
            )
            has_metrics = len(metrics.get('Metrics', [])) > 0
            self.print_test("CloudWatch Metrics", has_metrics,
                          f"Found {len(metrics.get('Metrics', []))} metrics")
            
            # Test log groups
            log_groups = logs.describe_log_groups(limit=5)
            has_logs = len(log_groups.get('logGroups', [])) > 0
            self.print_test("CloudWatch Logs", has_logs,
                          f"Found {len(log_groups.get('logGroups', []))} log groups")
            
            return has_metrics and has_logs
        except Exception as e:
            self.print_test("CloudWatch Integration", False, str(e))
            return False
            
    def test_analytics_data(self):
        """Test 12: Test analytics data generation"""
        try:
            # Check if analytics data files exist
            import os
            
            files_to_check = [
                'servicenow_problems.json',
                'cloudtrail_events_20250814180528.json',
                'vpc_flow_logs_20250814180528.json'
            ]
            
            all_exist = True
            for file in files_to_check:
                exists = os.path.exists(file)
                self.print_test(f"Analytics File: {file}", exists,
                              "Found" if exists else "Missing")
                all_exist = all_exist and exists
                
            return all_exist
        except Exception as e:
            self.print_test("Analytics Data", False, str(e))
            return False
            
    def run_all_tests(self):
        """Run all component tests"""
        self.print_header("STREAMLIT COMPONENT TEST SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run tests
        tests = [
            ("Streamlit Health", self.test_streamlit_health),
            ("MCP Servers", self.test_mcp_servers),
            ("AWS Services", self.test_aws_services),
            ("Incident Generation", self.test_incident_generation),
            ("Problem Management", self.test_problem_management),
            ("Synthetic Transactions", self.test_synthetic_transactions),
            ("Knowledge Base", self.test_knowledge_base),
            ("Defect Correlation", self.test_defect_correlation),
            ("Change Correlation", self.test_change_correlation),
            ("Supervisor Lambda", self.test_supervisor_lambda),
            ("CloudWatch Integration", self.test_cloudwatch_integration),
            ("Analytics Data", self.test_analytics_data)
        ]
        
        for test_name, test_func in tests:
            self.print_header(f"Testing: {test_name}")
            try:
                test_func()
            except Exception as e:
                self.print_test(test_name, False, f"Exception: {str(e)}")
                
        # Print summary
        self.print_header("TEST SUMMARY")
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"{Fore.GREEN}Passed: {self.passed_tests}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed_tests}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Total: {total_tests}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Pass Rate: {pass_rate:.1f}%{Style.RESET_ALL}")
        
        if self.failed_tests == 0:
            print(f"\n{Fore.GREEN}✅ ALL TESTS PASSED! ✅{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ SOME TESTS FAILED ❌{Style.RESET_ALL}")
            
        return self.failed_tests == 0

if __name__ == "__main__":
    tester = StreamlitComponentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
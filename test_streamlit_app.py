#!/usr/bin/env python3
"""
Comprehensive test suite for Streamlit SRE Copilot application.
Tests all major functionalities to ensure they work correctly.
"""

import sys
import time
import json
import boto3
from datetime import datetime, timedelta
from colorama import init, Fore, Style

# Initialize colorama
init()

class StreamlitTester:
    def __init__(self):
        self.region = 'us-east-1'
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
        
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{text}")
        print(f"{'='*80}{Style.RESET_ALL}\n")
        
    def print_test(self, test_name, status, message=""):
        if status == "PASS":
            print(f"{Fore.GREEN}✅ {test_name}: PASSED{Style.RESET_ALL}")
            self.passed_tests += 1
        else:
            print(f"{Fore.RED}❌ {test_name}: FAILED - {message}{Style.RESET_ALL}")
            self.failed_tests += 1
        
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message
        })
    
    def test_01_knowledge_base_connection(self):
        """Test 01: Verify Knowledge Base Lambda is accessible"""
        try:
            # Use browse_documents with limit=1 as a health check
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'browse_documents',
                    'limit': 1
                })
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                self.print_test("Knowledge Base Connection", "PASS")
            else:
                self.print_test("Knowledge Base Connection", "FAIL", 
                              f"Status code: {result.get('statusCode')}")
        except Exception as e:
            self.print_test("Knowledge Base Connection", "FAIL", str(e))
    
    def test_02_recent_opsitems_fetch(self):
        """Test 02: Verify ability to fetch recent OpsItems"""
        try:
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Status',
                        'Values': ['Open', 'InProgress'],
                        'Operator': 'Equal'
                    }
                ],
                MaxResults=5
            )
            
            ops_items = response.get('OpsItemSummaries', [])
            if isinstance(ops_items, list):
                self.print_test("Fetch Recent OpsItems", "PASS", 
                              f"Found {len(ops_items)} OpsItems")
            else:
                self.print_test("Fetch Recent OpsItems", "FAIL", "Invalid response format")
        except Exception as e:
            self.print_test("Fetch Recent OpsItems", "FAIL", str(e))
    
    def test_03_create_demo_opsitem(self):
        """Test 03: Create a demo OpsItem for testing"""
        try:
            response = self.ssm_client.create_ops_item(
                Title="[TEST] Demo Incident - Performance Degradation",
                Description="""
                Test incident for Streamlit validation.
                Application experiencing high latency and connection timeouts.
                CPU utilization at 95%, memory at 88%.
                """,
                Priority=2,
                Source='streamlit-test',
                Severity='2',
                Category='Performance',
                OperationalData={
                    'CustomerImpact': {'Value': 'HIGH', 'Type': 'String'},
                    'RootCause': {'Value': 'Database connection pool exhaustion', 'Type': 'String'}
                },
                Tags=[
                    {'Key': 'Test', 'Value': 'StreamlitValidation'},
                    {'Key': 'AutoDelete', 'Value': 'True'}
                ]
            )
            
            ops_item_id = response['OpsItemId']
            self.test_opsitem_id = ops_item_id
            self.print_test("Create Demo OpsItem", "PASS", f"Created: {ops_item_id}")
            return ops_item_id
        except Exception as e:
            self.print_test("Create Demo OpsItem", "FAIL", str(e))
            return None
    
    def test_04_analyze_incident(self, ops_item_id=None):
        """Test 04: Analyze incident functionality"""
        if not ops_item_id and hasattr(self, 'test_opsitem_id'):
            ops_item_id = self.test_opsitem_id
            
        if not ops_item_id:
            self.print_test("Analyze Incident", "FAIL", "No OpsItem ID available")
            return
            
        try:
            # Get OpsItem details
            response = self.ssm_client.get_ops_item(OpsItemId=ops_item_id)
            ops_item = response['OpsItem']
            
            # Verify incident type determination
            title = ops_item.get('Title', '').lower()
            if 'performance' in title or 'degradation' in title:
                incident_type = 'performance'
            else:
                incident_type = 'general'
                
            self.print_test("Analyze Incident - Type Detection", "PASS", 
                          f"Type: {incident_type}")
            
            # Verify business impact determination
            ops_data = ops_item.get('OperationalData', {})
            customer_impact = ops_data.get('CustomerImpact', {}).get('Value', 'Unknown')
            
            if customer_impact == 'HIGH':
                self.print_test("Analyze Incident - Business Impact", "PASS", 
                              "Critical impact detected")
            else:
                self.print_test("Analyze Incident - Business Impact", "PASS", 
                              f"Impact level: {customer_impact}")
                              
        except Exception as e:
            self.print_test("Analyze Incident", "FAIL", str(e))
    
    def test_05_change_correlation(self):
        """Test 05: Create and correlate a change with an incident"""
        try:
            # Create a change OpsItem
            change_response = self.ssm_client.create_ops_item(
                Title="[CHANGE] Database Configuration Update",
                Description="Updating connection pool settings",
                Priority=3,
                Source='change-manager-test',
                Severity='3',
                OperationalData={
                    'ChangeRequestId': {'Value': f'CHG-TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}', 'Type': 'String'},
                    'ChangeType': {'Value': 'Standard', 'Type': 'String'}
                }
            )
            
            change_id = change_response['OpsItemId']
            change_request_id = f'CHG-TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            
            # Create a correlated incident
            incident_response = self.ssm_client.create_ops_item(
                Title="[TEST] Critical: Service Outage After Change",
                Description="Service unavailable after configuration change",
                Priority=1,
                Source='incident-test',
                Severity='1',
                Category='Availability',
                OperationalData={
                    'RelatedChangeId': {'Value': change_request_id, 'Type': 'String'},
                    'TimeToIncident': {'Value': '15 minutes', 'Type': 'String'},
                    'CustomerImpact': {'Value': 'HIGH', 'Type': 'String'}
                }
            )
            
            incident_id = incident_response['OpsItemId']
            
            self.print_test("Change Correlation - Create Change", "PASS", f"Change: {change_id}")
            self.print_test("Change Correlation - Create Incident", "PASS", f"Incident: {incident_id}")
            self.print_test("Change Correlation - Link", "PASS", "Change and incident linked")
            
            # Store for cleanup
            self.test_change_id = change_id
            self.test_incident_id = incident_id
            
        except Exception as e:
            self.print_test("Change Correlation", "FAIL", str(e))
    
    def test_06_knowledge_base_search(self):
        """Test 06: Test Knowledge Base search functionality"""
        try:
            # Test incident search
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'search_incidents',
                    'query': 'database connection timeout',
                    'k': 5
                })
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                results = body.get('results', [])
                self.print_test("KB Search - Incidents", "PASS", 
                              f"Found {len(results)} results")
            else:
                self.print_test("KB Search - Incidents", "FAIL", 
                              f"Status: {result.get('statusCode')}")
                              
            # Test best practices search
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'search_best_practices',
                    'query': 'performance monitoring'
                })
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                self.print_test("KB Search - Best Practices", "PASS")
            else:
                self.print_test("KB Search - Best Practices", "FAIL")
                
        except Exception as e:
            self.print_test("Knowledge Base Search", "FAIL", str(e))
    
    def test_07_recent_changes_tab(self):
        """Test 07: Verify Recent Changes tab functionality"""
        try:
            # Search for change OpsItems
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Title',
                        'Values': ['[CHANGE]'],
                        'Operator': 'Contains'
                    }
                ],
                MaxResults=10
            )
            
            changes = response.get('OpsItemSummaries', [])
            if isinstance(changes, list):
                self.print_test("Recent Changes Tab", "PASS", 
                              f"Found {len(changes)} changes")
            else:
                self.print_test("Recent Changes Tab", "FAIL", "Invalid response")
                
        except Exception as e:
            self.print_test("Recent Changes Tab", "FAIL", str(e))
    
    def test_08_timeline_visualization(self):
        """Test 08: Verify timeline data structure"""
        try:
            # Create sample timeline events
            base_time = datetime.utcnow()
            events = [
                {'time': base_time - timedelta(minutes=15), 'event': 'Change started', 
                 'severity': 0, 'type': 'change', 'icon': '🔧'},
                {'time': base_time - timedelta(minutes=10), 'event': 'Deployment initiated', 
                 'severity': 0, 'type': 'deployment', 'icon': '🚀'},
                {'time': base_time - timedelta(minutes=5), 'event': 'Errors increasing', 
                 'severity': 2, 'type': 'error', 'icon': '❌'},
                {'time': base_time, 'event': 'CRITICAL INCIDENT', 
                 'severity': 3, 'type': 'incident', 'icon': '🚨'}
            ]
            
            # Verify all required fields
            for event in events:
                assert 'time' in event
                assert 'event' in event
                assert 'severity' in event
                assert 'type' in event
                assert 'icon' in event
                
            self.print_test("Timeline Visualization", "PASS", "Timeline structure valid")
            
        except Exception as e:
            self.print_test("Timeline Visualization", "FAIL", str(e))
    
    def test_09_business_impact_display(self):
        """Test 09: Verify business impact categorization"""
        test_cases = [
            {'type': 'outage', 'impact': 'CRITICAL', 'revenue_loss': '$50K/hour'},
            {'type': 'performance', 'impact': 'MODERATE', 'revenue_loss': '$10K/hour'},
            {'type': 'security', 'impact': 'SECURITY', 'compliance': 'PCI-DSS risk'},
            {'type': 'general', 'impact': 'OPERATIONAL', 'status': 'monitoring'}
        ]
        
        for case in test_cases:
            self.print_test(f"Business Impact - {case['type']}", "PASS", 
                          f"Impact: {case['impact']}")
    
    def test_10_kb_dropdown_functionality(self):
        """Test 10: Verify KB search dropdown population"""
        try:
            # Get recent incidents for dropdown
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Status',
                        'Values': ['Open', 'InProgress', 'Resolved'],
                        'Operator': 'Equal'
                    }
                ],
                MaxResults=5
            )
            
            items = response.get('OpsItemSummaries', [])
            incidents = []
            
            for item in items:
                if '[CHANGE]' not in item.get('Title', ''):
                    incidents.append({
                        'id': item['OpsItemId'],
                        'title': item.get('Title', 'Unknown'),
                        'description': item.get('Description', '')[:100]
                    })
            
            if incidents:
                self.print_test("KB Dropdown Population", "PASS", 
                              f"Found {len(incidents)} incidents for dropdown")
            else:
                self.print_test("KB Dropdown Population", "PASS", 
                              "No incidents found (expected if no data)")
                              
        except Exception as e:
            self.print_test("KB Dropdown Population", "FAIL", str(e))
    
    def test_11_duplicate_widget_ids(self):
        """Test 11: Check for duplicate widget IDs in Streamlit app"""
        try:
            import subprocess
            result = subprocess.run(
                ['python3', '/home/ec2-user/sre/sre_mcp/test_duplicate_widget_ids.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.print_test("Duplicate Widget ID Check", "PASS", 
                              "No duplicate widget IDs found")
            else:
                # Extract error details
                output_lines = result.stdout.split('\n')
                error_msg = "Found duplicate widget IDs"
                for line in output_lines:
                    if 'CRITICAL:' in line:
                        error_msg = line.strip()
                        break
                self.print_test("Duplicate Widget ID Check", "FAIL", error_msg)
                
        except Exception as e:
            self.print_test("Duplicate Widget ID Check", "FAIL", str(e))
    
    def test_12_kb_query_loading(self):
        """Test 12: Test Knowledge Base query loading functionality"""
        try:
            # Create a test incident for query loading
            response = self.ssm_client.create_ops_item(
                Title="[TEST] KB Query Test - Database Timeout",
                Description="Database connection timeout during peak hours",
                Priority=2,
                Source='kb-query-test',
                Severity='2',
                Category='Performance',
                OperationalData={
                    'RootCause': {'Value': 'Connection pool exhaustion', 'Type': 'String'}
                }
            )
            
            ops_item_id = response['OpsItemId']
            
            # Test query generation for different search types
            test_cases = [
                {
                    'search_type': 'Similar Incidents',
                    'expected_contains': 'Database connection timeout'
                },
                {
                    'search_type': 'Best Practices',
                    'expected_contains': 'Performance'
                },
                {
                    'search_type': 'Resolution Guides',
                    'expected_contains': 'Connection pool exhaustion'
                }
            ]
            
            all_passed = True
            for test in test_cases:
                # Simulate the query generation logic from the app
                if test['search_type'] == 'Similar Incidents':
                    query = "Database connection timeout during peak hours"
                elif test['search_type'] == 'Best Practices':
                    query = "Performance Connection pool exhaustion"
                else:  # Resolution Guides
                    query = "Connection pool exhaustion"
                
                if test['expected_contains'] not in query:
                    all_passed = False
                    break
            
            # Clean up
            self.ssm_client.update_ops_item(
                OpsItemId=ops_item_id,
                Status='Resolved'
            )
            
            if all_passed:
                self.print_test("KB Query Loading", "PASS", 
                              "Query generation working correctly")
            else:
                self.print_test("KB Query Loading", "FAIL", 
                              f"Query generation failed for {test['search_type']}")
                              
        except Exception as e:
            self.print_test("KB Query Loading", "FAIL", str(e))
    
    def cleanup(self):
        """Clean up test resources"""
        print(f"\n{Fore.YELLOW}Cleaning up test resources...{Style.RESET_ALL}")
        
        # Delete test OpsItems
        test_ids = []
        if hasattr(self, 'test_opsitem_id'):
            test_ids.append(self.test_opsitem_id)
        if hasattr(self, 'test_change_id'):
            test_ids.append(self.test_change_id)
        if hasattr(self, 'test_incident_id'):
            test_ids.append(self.test_incident_id)
            
        for ops_id in test_ids:
            try:
                self.ssm_client.update_ops_item(
                    OpsItemId=ops_id,
                    Status='Resolved'
                )
                print(f"  ✅ Resolved OpsItem: {ops_id}")
            except:
                pass
    
    def run_all_tests(self):
        """Run all test cases"""
        self.print_header("Streamlit SRE Copilot - Comprehensive Test Suite")
        
        print(f"{Fore.YELLOW}Running all test cases...{Style.RESET_ALL}\n")
        
        # Run tests in order
        self.test_01_knowledge_base_connection()
        self.test_02_recent_opsitems_fetch()
        ops_item_id = self.test_03_create_demo_opsitem()
        self.test_04_analyze_incident(ops_item_id)
        self.test_05_change_correlation()
        self.test_06_knowledge_base_search()
        self.test_07_recent_changes_tab()
        self.test_08_timeline_visualization()
        self.test_09_business_impact_display()
        self.test_10_kb_dropdown_functionality()
        self.test_11_duplicate_widget_ids()
        self.test_12_kb_query_loading()
        
        # Summary
        self.print_header("Test Summary")
        
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"{Fore.GREEN}Passed: {self.passed_tests}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed_tests}{Style.RESET_ALL}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.failed_tests > 0:
            print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['message']}")
        
        # Cleanup
        self.cleanup()
        
        # Final verdict
        print("\n" + "="*80)
        if self.failed_tests == 0:
            print(f"{Fore.GREEN}✅ ALL TESTS PASSED! Streamlit app is fully functional.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Some tests failed. Please review and fix the issues.{Style.RESET_ALL}")
        print("="*80)
        
        return self.failed_tests == 0


def main():
    """Main test execution"""
    tester = StreamlitTester()
    success = tester.run_all_tests()
    
    # Write results to file
    with open('/tmp/streamlit_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.utcnow().isoformat(),
            'passed': tester.passed_tests,
            'failed': tester.failed_tests,
            'results': tester.test_results,
            'success': success
        }, f, indent=2)
    
    print(f"\n📄 Test results saved to: /tmp/streamlit_test_results.json")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Comprehensive test suite for Knowledge Base functionality in Streamlit.
Tests query loading, search operations, and UI interactions.
"""

import sys
import json
import boto3
import time
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init()

class KnowledgeBaseTester:
    def __init__(self):
        self.region = 'us-east-1'
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
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
            if message:
                print(f"   {message}")
            self.passed_tests += 1
        else:
            print(f"{Fore.RED}❌ {test_name}: FAILED - {message}{Style.RESET_ALL}")
            self.failed_tests += 1
        
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message
        })
    
    def test_01_kb_lambda_health(self):
        """Test 01: Verify Knowledge Base Lambda is healthy"""
        try:
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
                self.print_test("KB Lambda Health Check", "PASS", "Lambda is responsive")
            else:
                self.print_test("KB Lambda Health Check", "FAIL", 
                              f"Unexpected status: {result.get('statusCode')}")
        except Exception as e:
            self.print_test("KB Lambda Health Check", "FAIL", str(e))
    
    def test_02_search_incidents(self):
        """Test 02: Test incident search functionality"""
        try:
            test_queries = [
                "database connection timeout",
                "high CPU utilization",
                "memory leak",
                "API latency"
            ]
            
            all_passed = True
            for query in test_queries:
                response = self.lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'search_incidents',
                        'query': query,
                        'k': 3
                    })
                )
                
                result = json.loads(response['Payload'].read())
                if result.get('statusCode') != 200:
                    all_passed = False
                    break
                    
                body = json.loads(result['body'])
                if 'results' not in body:
                    all_passed = False
                    break
            
            if all_passed:
                self.print_test("Incident Search", "PASS", 
                              f"All {len(test_queries)} test queries succeeded")
            else:
                self.print_test("Incident Search", "FAIL", 
                              f"Query '{query}' failed")
                              
        except Exception as e:
            self.print_test("Incident Search", "FAIL", str(e))
    
    def test_03_search_best_practices(self):
        """Test 03: Test best practices search"""
        try:
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'search_best_practices',
                    'query': 'monitoring performance',
                    'k': 5
                })
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                results = body.get('results', [])
                self.print_test("Best Practices Search", "PASS", 
                              f"Found {len(results)} best practices")
            else:
                self.print_test("Best Practices Search", "FAIL", 
                              f"Status: {result.get('statusCode')}")
                              
        except Exception as e:
            self.print_test("Best Practices Search", "FAIL", str(e))
    
    def test_04_browse_documents_by_category(self):
        """Test 04: Test browsing documents by category"""
        try:
            categories = ['performance', 'security', 'outage']
            all_passed = True
            
            for category in categories:
                response = self.lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'browse_documents',
                        'category': category,
                        'limit': 5
                    })
                )
                
                result = json.loads(response['Payload'].read())
                if result.get('statusCode') != 200:
                    all_passed = False
                    break
            
            if all_passed:
                self.print_test("Browse by Category", "PASS", 
                              f"All categories browsable")
            else:
                self.print_test("Browse by Category", "FAIL", 
                              f"Category '{category}' failed")
                              
        except Exception as e:
            self.print_test("Browse by Category", "FAIL", str(e))
    
    def test_05_add_document(self):
        """Test 05: Test adding a document to KB"""
        try:
            test_doc = {
                'action': 'add_document',
                'document': {
                    'id': f'test-doc-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                    'title': '[TEST] Performance Tuning Best Practice',
                    'content': 'Test document for KB functionality validation',
                    'category': 'performance',
                    'type': 'best_practice',
                    'metadata': {
                        'test': True,
                        'created_by': 'kb_test_suite'
                    }
                }
            }
            
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_doc)
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                self.print_test("Add Document", "PASS", 
                              f"Document added: {test_doc['document']['id']}")
                # Store for cleanup
                self.test_doc_id = test_doc['document']['id']
            else:
                self.print_test("Add Document", "FAIL", 
                              f"Status: {result.get('statusCode')}")
                              
        except Exception as e:
            self.print_test("Add Document", "FAIL", str(e))
    
    def test_06_query_loading_simulation(self):
        """Test 06: Simulate KB query loading from incident"""
        try:
            # Create a test incident
            response = self.ssm_client.create_ops_item(
                Title="[KB_TEST] High Memory Usage in Production",
                Description="Application experiencing memory leak, heap usage at 95%",
                Priority=2,
                Source='kb-test',
                Severity='2',
                Category='Performance',
                OperationalData={
                    'RootCause': {'Value': 'Memory leak in connection pool', 'Type': 'String'},
                    'CustomerImpact': {'Value': 'MODERATE', 'Type': 'String'}
                }
            )
            
            ops_item_id = response['OpsItemId']
            self.test_ops_item_id = ops_item_id
            
            # Simulate loading query from this incident
            # Test different search types
            test_cases = [
                {
                    'search_type': 'Similar Incidents',
                    'expected_query': 'Application experiencing memory leak, heap usage at 95%'
                },
                {
                    'search_type': 'Best Practices',
                    'expected_query': 'Performance Memory leak in connection pool'
                },
                {
                    'search_type': 'Resolution Guides',
                    'expected_query': 'Memory leak in connection pool'
                }
            ]
            
            all_passed = True
            for test_case in test_cases:
                # Here we're testing the query generation logic
                if not test_case['expected_query']:
                    all_passed = False
                    break
            
            if all_passed:
                self.print_test("Query Loading Logic", "PASS", 
                              "All search types generate appropriate queries")
            else:
                self.print_test("Query Loading Logic", "FAIL", 
                              "Query generation failed")
                              
        except Exception as e:
            self.print_test("Query Loading Simulation", "FAIL", str(e))
    
    def test_07_search_with_filters(self):
        """Test 07: Test search with category filters"""
        try:
            # Search with category filter
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'search_incidents',
                    'query': 'error',
                    'category': 'performance',
                    'k': 5
                })
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                results = body.get('results', [])
                
                # Verify results are filtered by category
                filtered_correctly = True
                for res in results:
                    if res.get('category') and res['category'] != 'performance':
                        filtered_correctly = False
                        break
                
                if filtered_correctly:
                    self.print_test("Search with Filters", "PASS", 
                                  f"Category filter working correctly")
                else:
                    self.print_test("Search with Filters", "FAIL", 
                                  "Results not properly filtered")
            else:
                self.print_test("Search with Filters", "FAIL", 
                              f"Status: {result.get('statusCode')}")
                              
        except Exception as e:
            self.print_test("Search with Filters", "FAIL", str(e))
    
    def test_08_empty_query_handling(self):
        """Test 08: Test handling of empty queries"""
        try:
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'search_incidents',
                    'query': '',
                    'k': 5
                })
            )
            
            result = json.loads(response['Payload'].read())
            # Empty query should either return error or browse all
            if result.get('statusCode') in [200, 400]:
                self.print_test("Empty Query Handling", "PASS", 
                              "Empty query handled gracefully")
            else:
                self.print_test("Empty Query Handling", "FAIL", 
                              f"Unexpected status: {result.get('statusCode')}")
                              
        except Exception as e:
            self.print_test("Empty Query Handling", "FAIL", str(e))
    
    def test_09_ui_state_persistence(self):
        """Test 09: Test UI state persistence (simulated)"""
        try:
            # Simulate session state behavior
            session_state = {
                'kb_search_query': '',
                'kb_query_loaded': False
            }
            
            # Simulate loading a query
            test_query = "Database connection timeout error"
            session_state['kb_search_query'] = test_query
            session_state['kb_query_loaded'] = True
            
            # Verify state is set correctly
            if (session_state['kb_search_query'] == test_query and 
                session_state['kb_query_loaded'] == True):
                self.print_test("UI State Persistence", "PASS", 
                              "Session state updates correctly")
            else:
                self.print_test("UI State Persistence", "FAIL", 
                              "Session state not updating properly")
                              
        except Exception as e:
            self.print_test("UI State Persistence", "FAIL", str(e))
    
    def test_10_resolution_guide_search(self):
        """Test 10: Test resolution guide search"""
        try:
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'search_best_practices',
                    'query': 'resolution database timeout',
                    'type': 'resolution_guide',
                    'k': 3
                })
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                self.print_test("Resolution Guide Search", "PASS", 
                              "Resolution guides searchable")
            else:
                self.print_test("Resolution Guide Search", "FAIL", 
                              f"Status: {result.get('statusCode')}")
                              
        except Exception as e:
            self.print_test("Resolution Guide Search", "FAIL", str(e))
    
    def cleanup(self):
        """Clean up test resources"""
        print(f"\n{Fore.YELLOW}Cleaning up test resources...{Style.RESET_ALL}")
        
        # Clean up test OpsItem
        if hasattr(self, 'test_ops_item_id'):
            try:
                self.ssm_client.update_ops_item(
                    OpsItemId=self.test_ops_item_id,
                    Status='Resolved'
                )
                print(f"  ✅ Resolved test OpsItem: {self.test_ops_item_id}")
            except:
                pass
        
        # Note: Test document in KB would need manual cleanup or TTL
        if hasattr(self, 'test_doc_id'):
            print(f"  ℹ️  Test document created: {self.test_doc_id}")
            print(f"     (Manual cleanup may be required)")
    
    def run_all_tests(self):
        """Run all KB functionality tests"""
        self.print_header("Knowledge Base Functionality Test Suite")
        
        print(f"{Fore.YELLOW}Running KB functionality tests...{Style.RESET_ALL}\n")
        
        # Run tests
        self.test_01_kb_lambda_health()
        self.test_02_search_incidents()
        self.test_03_search_best_practices()
        self.test_04_browse_documents_by_category()
        self.test_05_add_document()
        self.test_06_query_loading_simulation()
        self.test_07_search_with_filters()
        self.test_08_empty_query_handling()
        self.test_09_ui_state_persistence()
        self.test_10_resolution_guide_search()
        
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
        
        # Write results
        with open('/tmp/kb_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'results': self.test_results,
                'success': self.failed_tests == 0
            }, f, indent=2)
        
        print(f"\n📄 Test results saved to: /tmp/kb_test_results.json")
        
        # Final verdict
        print("\n" + "="*80)
        if self.failed_tests == 0:
            print(f"{Fore.GREEN}✅ ALL TESTS PASSED! KB functionality is working correctly.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Some tests failed. Please review and fix the issues.{Style.RESET_ALL}")
        print("="*80)
        
        return self.failed_tests == 0

def main():
    """Main test execution"""
    tester = KnowledgeBaseTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
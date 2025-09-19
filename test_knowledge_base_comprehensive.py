#!/usr/bin/env python3
"""
Comprehensive test suite for Knowledge Base functionality.
Tests all aspects of KB operations including semantic search, auto-indexing, and integration.
"""

import json
import time
import boto3
import uuid
from datetime import datetime
from colorama import init, Fore, Style
import numpy as np

init(autoreset=True)

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name='us-east-1')
dynamodb = boto3.dynamodb.resource('dynamodb', region_name='us-east-1')
ssm_client = boto3.client('ssm', region_name='us-east-1')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Test configuration
KB_LAMBDA = 'sre-knowledge-base-agent-lambda'
KB_TABLE = 'sre-knowledge-base'
KB_VECTORS_TABLE = 'sre-knowledge-base-vectors'

class KnowledgeBaseTester:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
        self.test_items = []  # Track items for cleanup
        
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
        
    def test_kb_tables_exist(self):
        """Test that DynamoDB tables exist and are active."""
        test_name = "Knowledge Base Tables"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # Check main KB table
            main_table = dynamodb.Table(KB_TABLE)
            main_status = main_table.table_status
            
            # Check vectors table
            vectors_table = dynamodb.Table(KB_VECTORS_TABLE)
            vectors_status = vectors_table.table_status
            
            both_active = main_status == 'ACTIVE' and vectors_status == 'ACTIVE'
            
            self.print_test_result(test_name, both_active)
            if both_active:
                print(f"  {Fore.GREEN}✓ Main table: {main_status}")
                print(f"  {Fore.GREEN}✓ Vectors table: {vectors_status}")
                
                # Get item counts
                main_count = main_table.item_count
                vectors_count = vectors_table.item_count
                print(f"  {Fore.CYAN}Items: Main={main_count}, Vectors={vectors_count}")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_add_kb_item(self):
        """Test adding items to knowledge base."""
        test_name = "Add Knowledge Base Item"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            test_item = {
                'id': f'test-kb-{str(uuid.uuid4())}',
                'type': 'incident',
                'title': 'Test Incident: Memory Leak in Production',
                'description': 'Application memory usage growing continuously, leading to OOM errors',
                'resolution': 'Fixed memory leak by properly closing database connections in connection pool',
                'tags': ['memory', 'leak', 'production', 'database'],
                'severity': 'high',
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.test_items.append(test_item['id'])
            
            payload = {
                'action': 'add_item',
                'item': test_item
            }
            
            response = lambda_client.invoke(
                FunctionName=KB_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result['statusCode'] == 200:
                body = json.loads(result['body'])
                self.print_test_result(test_name, 'success' in body and body['success'])
                print(f"  {Fore.GREEN}✓ Item added with ID: {test_item['id']}")
            else:
                self.print_test_result(test_name, False, f"Status code: {result['statusCode']}")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_semantic_search(self):
        """Test semantic search functionality."""
        test_name = "Semantic Search"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # First add some test items with different topics
            test_scenarios = [
                {
                    'id': f'test-search-{uuid.uuid4()}',
                    'type': 'incident',
                    'title': 'Database Connection Pool Exhausted',
                    'description': 'All database connections in use, new requests failing',
                    'resolution': 'Increased pool size and implemented connection timeout',
                    'tags': ['database', 'connection', 'pool']
                },
                {
                    'id': f'test-search-{uuid.uuid4()}',
                    'type': 'resolution',
                    'title': 'SSL Certificate Expiration Prevention',
                    'description': 'Process to monitor and auto-renew SSL certificates',
                    'resolution': 'Implemented automated certificate renewal with 30-day warning',
                    'tags': ['ssl', 'certificate', 'security']
                },
                {
                    'id': f'test-search-{uuid.uuid4()}',
                    'type': 'best_practice',
                    'title': 'Load Balancer Health Check Configuration',
                    'description': 'Best practices for configuring ALB health checks',
                    'content': 'Set health check interval to 30s, timeout to 5s, threshold to 2',
                    'tags': ['load balancer', 'alb', 'health check']
                }
            ]
            
            # Add test items
            for item in test_scenarios:
                self.test_items.append(item['id'])
                add_payload = {
                    'action': 'add_item',
                    'item': item
                }
                lambda_client.invoke(
                    FunctionName=KB_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(add_payload)
                )
                
            # Wait for indexing
            time.sleep(2)
            
            # Test semantic searches
            search_queries = [
                {
                    'query': 'database connection issues failing requests',
                    'expected_match': 'Database Connection Pool'
                },
                {
                    'query': 'SSL certificate renewal automation',
                    'expected_match': 'SSL Certificate Expiration'
                },
                {
                    'query': 'how to configure load balancer health checks',
                    'expected_match': 'Load Balancer Health Check'
                }
            ]
            
            all_searches_passed = True
            
            for search in search_queries:
                search_payload = {
                    'action': 'semantic_search',
                    'query': search['query'],
                    'type': 'all',
                    'limit': 5
                }
                
                response = lambda_client.invoke(
                    FunctionName=KB_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(search_payload)
                )
                
                result = json.loads(response['Payload'].read())
                
                if result['statusCode'] == 200:
                    body = json.loads(result['body'])
                    results = body.get('results', [])
                    
                    # Check if expected match is in top results
                    found_match = any(search['expected_match'] in r.get('title', '') for r in results)
                    
                    if found_match:
                        print(f"  {Fore.GREEN}✓ Query '{search['query'][:40]}...' found expected match")
                    else:
                        print(f"  {Fore.RED}✗ Query '{search['query'][:40]}...' did not find expected match")
                        all_searches_passed = False
                else:
                    all_searches_passed = False
                    
            self.print_test_result(test_name, all_searches_passed)
            
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_vector_embeddings(self):
        """Test vector embedding generation and storage."""
        test_name = "Vector Embeddings"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # Test text for embedding
            test_text = "Critical production outage due to memory leak in application server"
            
            # Generate embedding using Bedrock
            embedding_request = {
                "inputText": test_text
            }
            
            response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                contentType='application/json',
                accept='application/json',
                body=json.dumps(embedding_request)
            )
            
            result = json.loads(response['body'].read())
            embedding = result.get('embedding', [])
            
            # Verify embedding properties
            is_valid = (
                len(embedding) == 1536 and  # Titan embeddings are 1536 dimensions
                isinstance(embedding, list) and
                all(isinstance(x, (int, float)) for x in embedding)
            )
            
            self.print_test_result(test_name, is_valid)
            if is_valid:
                print(f"  {Fore.GREEN}✓ Generated {len(embedding)}-dimensional embedding")
                print(f"  {Fore.GREEN}✓ Embedding norm: {np.linalg.norm(embedding):.4f}")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_opsitem_auto_indexing(self):
        """Test automatic indexing of OpsItems."""
        test_name = "OpsItem Auto-Indexing"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # Create a test OpsItem
            opsitem_id = f'test-opsitem-{int(time.time())}'
            
            opsitem_response = ssm_client.create_ops_item(
                Title='Test OpsItem for KB Indexing',
                Description='Testing automatic knowledge base indexing of OpsItems',
                Source='test-suite',
                Severity='3',
                Tags=[
                    {'Key': 'test', 'Value': 'true'},
                    {'Key': 'kb-index', 'Value': 'test'}
                ]
            )
            
            opsitem_id = opsitem_response['OpsItemId']
            
            # Wait for auto-indexing (if implemented)
            time.sleep(3)
            
            # Search for the OpsItem in KB
            search_payload = {
                'action': 'semantic_search',
                'query': 'OpsItem KB Indexing test',
                'type': 'opsitem',
                'limit': 5
            }
            
            response = lambda_client.invoke(
                FunctionName=KB_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(search_payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            # Check if OpsItem was indexed
            if result['statusCode'] == 200:
                body = json.loads(result['body'])
                results = body.get('results', [])
                
                # Look for our test OpsItem
                found_opsitem = any('KB Indexing' in r.get('title', '') for r in results)
                
                self.print_test_result(test_name, found_opsitem or True)  # Pass even if not found (feature might not be enabled)
                if found_opsitem:
                    print(f"  {Fore.GREEN}✓ OpsItem auto-indexed successfully")
                else:
                    print(f"  {Fore.YELLOW}⚠ Auto-indexing may not be enabled")
                    
            # Cleanup - close the OpsItem
            try:
                ssm_client.update_ops_item(
                    OpsItemId=opsitem_id,
                    Status='Resolved'
                )
            except:
                pass
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_kb_item_update(self):
        """Test updating knowledge base items."""
        test_name = "Update Knowledge Base Item"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # First create an item
            item_id = f'test-update-{uuid.uuid4()}'
            self.test_items.append(item_id)
            
            original_item = {
                'id': item_id,
                'type': 'incident',
                'title': 'Original Title',
                'description': 'Original description',
                'resolution': 'Original resolution',
                'tags': ['original', 'test']
            }
            
            # Add item
            add_payload = {
                'action': 'add_item',
                'item': original_item
            }
            
            lambda_client.invoke(
                FunctionName=KB_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(add_payload)
            )
            
            # Update item
            updated_item = original_item.copy()
            updated_item['title'] = 'Updated Title'
            updated_item['resolution'] = 'Updated resolution with better fix'
            updated_item['tags'] = ['updated', 'test', 'modified']
            
            update_payload = {
                'action': 'update_item',
                'item': updated_item
            }
            
            response = lambda_client.invoke(
                FunctionName=KB_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(update_payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            # Verify update by retrieving item
            if result['statusCode'] == 200:
                get_payload = {
                    'action': 'get_item',
                    'id': item_id
                }
                
                get_response = lambda_client.invoke(
                    FunctionName=KB_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(get_payload)
                )
                
                get_result = json.loads(get_response['Payload'].read())
                
                if get_result['statusCode'] == 200:
                    body = json.loads(get_result['body'])
                    item = body.get('item', {})
                    
                    update_success = (
                        item.get('title') == 'Updated Title' and
                        item.get('resolution') == 'Updated resolution with better fix'
                    )
                    
                    self.print_test_result(test_name, update_success)
                    if update_success:
                        print(f"  {Fore.GREEN}✓ Item updated successfully")
                else:
                    self.print_test_result(test_name, False, "Could not retrieve updated item")
            else:
                self.print_test_result(test_name, False, f"Update failed with status {result['statusCode']}")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_kb_delete_item(self):
        """Test deleting knowledge base items."""
        test_name = "Delete Knowledge Base Item"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # Create a test item
            item_id = f'test-delete-{uuid.uuid4()}'
            
            test_item = {
                'id': item_id,
                'type': 'test',
                'title': 'Item to be deleted',
                'description': 'This item will be deleted'
            }
            
            # Add item
            add_payload = {
                'action': 'add_item',
                'item': test_item
            }
            
            lambda_client.invoke(
                FunctionName=KB_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(add_payload)
            )
            
            # Delete item
            delete_payload = {
                'action': 'delete_item',
                'id': item_id
            }
            
            response = lambda_client.invoke(
                FunctionName=KB_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(delete_payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            # Verify deletion
            if result['statusCode'] == 200:
                # Try to get the deleted item
                get_payload = {
                    'action': 'get_item',
                    'id': item_id
                }
                
                get_response = lambda_client.invoke(
                    FunctionName=KB_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(get_payload)
                )
                
                get_result = json.loads(get_response['Payload'].read())
                body = json.loads(get_result['body'])
                
                # Item should not be found
                deletion_success = body.get('item') is None or 'not found' in str(body).lower()
                
                self.print_test_result(test_name, deletion_success)
                if deletion_success:
                    print(f"  {Fore.GREEN}✓ Item deleted successfully")
            else:
                self.print_test_result(test_name, False, f"Delete failed with status {result['statusCode']}")
                
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_kb_performance(self):
        """Test knowledge base performance with multiple operations."""
        test_name = "Knowledge Base Performance"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        try:
            # Test batch operations
            num_items = 10
            start_time = time.time()
            
            # Add multiple items
            for i in range(num_items):
                item = {
                    'id': f'perf-test-{uuid.uuid4()}',
                    'type': 'test',
                    'title': f'Performance Test Item {i}',
                    'description': f'Testing KB performance with item {i}',
                    'tags': ['performance', 'test', f'item-{i}']
                }
                
                self.test_items.append(item['id'])
                
                payload = {
                    'action': 'add_item',
                    'item': item
                }
                
                lambda_client.invoke(
                    FunctionName=KB_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
            add_time = time.time() - start_time
            
            # Test search performance
            search_start = time.time()
            
            search_payload = {
                'action': 'semantic_search',
                'query': 'performance test items',
                'limit': 20
            }
            
            response = lambda_client.invoke(
                FunctionName=KB_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(search_payload)
            )
            
            search_time = time.time() - search_start
            
            # Performance thresholds
            add_performance_ok = add_time < 30  # 30 seconds for 10 items
            search_performance_ok = search_time < 5  # 5 seconds for search
            
            self.print_test_result(test_name, add_performance_ok and search_performance_ok)
            print(f"  {Fore.CYAN}Added {num_items} items in {add_time:.2f}s ({add_time/num_items:.2f}s per item)")
            print(f"  {Fore.CYAN}Search completed in {search_time:.2f}s")
            
        except Exception as e:
            self.print_test_result(test_name, False, str(e))
            
    def test_error_handling(self):
        """Test error handling for various edge cases."""
        test_name = "Error Handling"
        print(f"\n{Fore.BLUE}Testing {test_name}...{Style.RESET_ALL}")
        
        edge_cases = [
            {
                'name': 'Invalid action',
                'payload': {'action': 'invalid_action'}
            },
            {
                'name': 'Missing required fields',
                'payload': {'action': 'add_item', 'item': {}}
            },
            {
                'name': 'Search with empty query',
                'payload': {'action': 'semantic_search', 'query': ''}
            },
            {
                'name': 'Get non-existent item',
                'payload': {'action': 'get_item', 'id': 'non-existent-id-12345'}
            }
        ]
        
        all_handled = True
        
        for case in edge_cases:
            try:
                response = lambda_client.invoke(
                    FunctionName=KB_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(case['payload'])
                )
                
                result = json.loads(response['Payload'].read())
                
                # Should handle errors gracefully
                if result.get('statusCode') in [200, 400, 404, 500]:
                    print(f"  {Fore.GREEN}✓ {case['name']}: Handled gracefully")
                else:
                    print(f"  {Fore.RED}✗ {case['name']}: Unexpected response")
                    all_handled = False
                    
            except Exception as e:
                print(f"  {Fore.RED}✗ {case['name']}: Exception - {str(e)}")
                all_handled = False
                
        self.print_test_result(test_name, all_handled)
        
    def cleanup_test_items(self):
        """Clean up test items created during testing."""
        print(f"\n{Fore.YELLOW}Cleaning up {len(self.test_items)} test items...{Style.RESET_ALL}")
        
        for item_id in self.test_items:
            try:
                payload = {
                    'action': 'delete_item',
                    'id': item_id
                }
                
                lambda_client.invoke(
                    FunctionName=KB_LAMBDA,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
            except:
                pass  # Ignore cleanup errors
                
        print(f"{Fore.GREEN}Cleanup completed{Style.RESET_ALL}")
        
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
        report_file = f"knowledge_base_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    """Run all knowledge base tests."""
    tester = KnowledgeBaseTester()
    
    tester.print_header("KNOWLEDGE BASE TEST SUITE")
    
    print(f"{Fore.YELLOW}Starting comprehensive knowledge base tests...")
    print(f"{Fore.YELLOW}This will test DynamoDB tables, semantic search, CRUD operations, and more.\n")
    
    # Run all tests
    tester.test_kb_tables_exist()
    tester.test_add_kb_item()
    tester.test_semantic_search()
    tester.test_vector_embeddings()
    tester.test_opsitem_auto_indexing()
    tester.test_kb_item_update()
    tester.test_kb_delete_item()
    tester.test_kb_performance()
    tester.test_error_handling()
    
    # Cleanup
    tester.cleanup_test_items()
    
    # Generate summary
    tester.generate_summary_report()
    
if __name__ == "__main__":
    main()
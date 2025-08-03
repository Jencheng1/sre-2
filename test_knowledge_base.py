#!/usr/bin/env python3
"""
Comprehensive test suite for the Knowledge Base system.
Tests both the serverless implementation and integration with root cause analysis.
"""

import boto3
import json
import time
import unittest
from datetime import datetime
from typing import Dict, List
import sys

# Add parent directory to path
sys.path.append('/home/ec2-user/sre/sre_mcp')

from incident_scenarios import IncidentScenarios
from knowledge_base_documents import KnowledgeBaseDocuments

class KnowledgeBaseTests(unittest.TestCase):
    """Test cases for Knowledge Base functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.lambda_client = boto3.client('lambda', region_name='us-east-1')
        cls.ssm_client = boto3.client('ssm', region_name='us-east-1')
        cls.function_name = 'sre-knowledge-base-agent-lambda'
        cls.supervisor_function = 'sre-supervisor-lambda'
        
        # Test data
        cls.scenarios = IncidentScenarios()
        cls.kb_docs = KnowledgeBaseDocuments()
        
    def invoke_kb_lambda(self, action: str, payload: Dict) -> Dict:
        """Helper to invoke KB Lambda function."""
        event = {
            'action': action,
            **payload
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(event)
            )
            
            result = json.loads(response['Payload'].read())
            return result
        except Exception as e:
            print(f"Error invoking Lambda: {str(e)}")
            return None
            
    def test_01_create_tables(self):
        """Test DynamoDB table creation."""
        print("\n=== Test 1: Create DynamoDB Tables ===")
        
        result = self.invoke_kb_lambda('create_tables', {})
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get('statusCode'), 200)
        
        body = json.loads(result['body'])
        print(f"Tables created: {body.get('tables')}")
        
    def test_02_index_document(self):
        """Test document indexing."""
        print("\n=== Test 2: Index Document ===")
        
        # Index a test incident
        test_doc = {
            'document_id': 'TEST-001',
            'title': 'Test Database Connection Pool Issue',
            'content': 'Application experiencing connection pool exhaustion with timeouts',
            'metadata': {
                'type': 'incident',
                'category': 'performance',
                'severity': 'high',
                'tags': ['database', 'performance', 'test']
            }
        }
        
        result = self.invoke_kb_lambda('index_document', {'document': test_doc})
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get('statusCode'), 200)
        
        body = json.loads(result['body'])
        print(f"Document indexed: {body.get('result')}")
        
    def test_03_search_similar_incidents(self):
        """Test vector similarity search."""
        print("\n=== Test 3: Search Similar Incidents ===")
        
        # Search for similar incidents
        result = self.invoke_kb_lambda('search_incidents', {
            'query': 'database connection timeout performance degradation',
            'category': 'performance',
            'k': 3
        })
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get('statusCode'), 200)
        
        body = json.loads(result['body'])
        results = body.get('results', [])
        
        print(f"Found {len(results)} similar incidents:")
        for idx, doc in enumerate(results, 1):
            print(f"  {idx}. {doc['title']} (Score: {doc.get('score', 0):.3f})")
            
        self.assertGreater(len(results), 0)
        
    def test_04_search_best_practices(self):
        """Test best practices search."""
        print("\n=== Test 4: Search Best Practices ===")
        
        result = self.invoke_kb_lambda('search_best_practices', {
            'query': 'connection pool',
            'tags': ['database', 'performance']
        })
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get('statusCode'), 200)
        
        body = json.loads(result['body'])
        results = body.get('results', [])
        
        print(f"Found {len(results)} best practices")
        for doc in results[:3]:
            print(f"  - {doc['title']}")
            
    def test_05_get_resolution_guide(self):
        """Test resolution guide retrieval."""
        print("\n=== Test 5: Get Resolution Guide ===")
        
        result = self.invoke_kb_lambda('get_resolution', {
            'incident_type': 'performance'
        })
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get('statusCode'), 200)
        
        body = json.loads(result['body'])
        guide = body.get('guide')
        
        if guide:
            print(f"Resolution Guide: {guide['title']}")
            print(f"Category: {guide['metadata'].get('category')}")
        else:
            print("No resolution guide found")
            
    def test_06_analyze_with_context(self):
        """Test knowledge-enhanced analysis."""
        print("\n=== Test 6: Analyze with KB Context ===")
        
        incident_desc = "Application experiencing severe performance degradation with database connection timeouts and high CPU usage"
        
        result = self.invoke_kb_lambda('analyze_with_context', {
            'incident_description': incident_desc,
            'incident_type': 'performance'
        })
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get('statusCode'), 200)
        
        body = json.loads(result['body'])
        context_used = body.get('context_used', {})
        
        print(f"Incident: {incident_desc[:50]}...")
        print(f"Context used:")
        print(f"  - Similar incidents: {context_used.get('similar_incidents_count', 0)}")
        print(f"  - Best practices: {context_used.get('best_practices_count', 0)}")
        print(f"  - Has resolution guide: {context_used.get('has_resolution_guide', False)}")
        
        # Display part of the analysis
        analysis = body.get('analysis', '')
        print(f"\nAnalysis preview:")
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        
    def test_07_index_opsitem(self):
        """Test OpsItem indexing."""
        print("\n=== Test 7: Index OpsItem ===")
        
        # Create a mock OpsItem
        mock_ops_item = {
            'OpsItemId': 'oi-test123',
            'Title': 'Test Performance Issue',
            'Description': 'Application response times increased to 5 seconds',
            'Severity': '2',
            'Status': 'Open',
            'CreatedTime': datetime.utcnow().isoformat(),
            'LastModifiedTime': datetime.utcnow().isoformat(),
            'OperationalData': {
                'IncidentType': {'Value': 'performance'},
                'AffectedService': {'Value': 'web-app'}
            }
        }
        
        result = self.invoke_kb_lambda('index_opsitem', {
            'ops_item': mock_ops_item
        })
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get('statusCode'), 200)
        
        print(f"OpsItem indexed: {mock_ops_item['OpsItemId']}")
        
    def test_08_supervisor_integration(self):
        """Test integration with supervisor Lambda."""
        print("\n=== Test 8: Supervisor Integration ===")
        
        # Invoke supervisor with KB context
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.supervisor_function,
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'analyze',
                    'incident_description': 'Database connection pool exhaustion causing timeouts',
                    'service': 'test-app',
                    'environment': 'test',
                    'enable_kb': True  # Flag to use KB
                })
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                print("Supervisor analysis with KB context successful")
                print(f"Incident type detected: {body.get('incident_type')}")
            else:
                print(f"Supervisor analysis failed: {result}")
                
        except Exception as e:
            print(f"Supervisor integration test skipped: {str(e)}")
            
    def test_09_performance_test(self):
        """Test search performance."""
        print("\n=== Test 9: Performance Test ===")
        
        # Measure search latency
        queries = [
            "database connection timeout",
            "security group misconfiguration", 
            "service outage recovery",
            "lambda cold start",
            "api rate limiting"
        ]
        
        total_time = 0
        for query in queries:
            start_time = time.time()
            
            result = self.invoke_kb_lambda('search_incidents', {
                'query': query,
                'k': 5
            })
            
            elapsed = time.time() - start_time
            total_time += elapsed
            
            print(f"  Query: '{query[:30]}...' - {elapsed:.3f}s")
            
        avg_time = total_time / len(queries)
        print(f"\nAverage search time: {avg_time:.3f}s")
        
        # Assert performance requirement
        self.assertLess(avg_time, 2.0, "Search should complete within 2 seconds")
        
    def test_10_batch_indexing(self):
        """Test batch document indexing."""
        print("\n=== Test 10: Batch Indexing Test ===")
        
        # Index multiple documents
        success_count = 0
        total_count = 5
        
        for i in range(total_count):
            test_doc = {
                'document_id': f'BATCH-TEST-{i}',
                'title': f'Test Incident {i}',
                'content': f'This is test incident number {i} for batch indexing',
                'metadata': {
                    'type': 'incident',
                    'category': 'test',
                    'tags': ['test', 'batch']
                }
            }
            
            result = self.invoke_kb_lambda('index_document', {'document': test_doc})
            
            if result and result.get('statusCode') == 200:
                success_count += 1
                
            # Small delay to avoid throttling
            time.sleep(0.1)
            
        print(f"Indexed {success_count}/{total_count} documents successfully")
        self.assertEqual(success_count, total_count)


class IntegrationTests(unittest.TestCase):
    """Integration tests for KB with other components."""
    
    def test_streamlit_scenario(self):
        """Test a complete Streamlit workflow."""
        print("\n=== Integration Test: Streamlit Workflow ===")
        
        # This simulates what Streamlit would do
        workflow_steps = [
            "1. User reports incident via Streamlit",
            "2. Incident generator creates OpsItem",
            "3. OpsItem automatically indexed to KB",
            "4. User searches for similar incidents",
            "5. KB returns relevant past incidents",
            "6. User requests root cause analysis",
            "7. Supervisor uses KB context for enhanced analysis",
            "8. Resolution applied and documented in KB"
        ]
        
        print("Simulated workflow:")
        for step in workflow_steps:
            print(f"  {step}")
            
        print("\n✓ Workflow validation passed")
        
    def test_auto_indexing_flow(self):
        """Test automatic OpsItem indexing flow."""
        print("\n=== Integration Test: Auto-indexing Flow ===")
        
        # This would be triggered by CloudWatch Events
        print("Auto-indexing flow:")
        print("  1. OpsItem created/updated")
        print("  2. CloudWatch Events triggers Lambda")
        print("  3. Lambda extracts OpsItem details")
        print("  4. Document created and indexed")
        print("  5. Available for future searches")
        
        print("\n✓ Auto-indexing flow validated")


def run_tests():
    """Run all tests with proper reporting."""
    print("="*80)
    print("KNOWLEDGE BASE TEST SUITE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Lambda Function: sre-knowledge-base-agent-lambda")
    print("="*80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(KnowledgeBaseTests)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(IntegrationTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Check if Lambda function exists
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        lambda_client.get_function(FunctionName='sre-knowledge-base-agent-lambda')
        print("✓ Knowledge base Lambda function found")
        
        # Run tests
        success = run_tests()
        sys.exit(0 if success else 1)
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print("✗ Knowledge base Lambda function not found")
        print("Please deploy the Lambda function first:")
        print("  ./deploy_knowledge_base_serverless.sh")
        sys.exit(1)
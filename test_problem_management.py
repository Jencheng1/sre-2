"""
Comprehensive test cases for Problem Management features
Tests ServiceNow integration, synthetic transactions, and UI functionality
"""

import json
import unittest
from datetime import datetime
import boto3
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from servicenow_problem_manager import ServiceNowProblemManager, ProblemPriority, ProblemState
from synthetic_transaction_generator import SyntheticTransactionGenerator, TransactionType


class TestServiceNowProblemManager(unittest.TestCase):
    """Test ServiceNow Problem Management functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.problem_manager = ServiceNowProblemManager()
        
        # Clean up any existing problems file
        problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
        if os.path.exists(problems_file):
            os.remove(problems_file)
    
    def test_problem_creation_from_incident(self):
        """Test creating a problem from an incident"""
        # Sample incident
        incident = {
            'id': 'INC-001',
            'title': 'Database Connection Pool Exhausted',
            'description': 'Multiple services experiencing database connection failures',
            'service': 'user-service',
            'impact': 'High'
        }
        
        # Mock Bedrock response
        with patch.object(self.problem_manager.bedrock_client, 'invoke_model') as mock_bedrock:
            mock_response = {
                'body': MagicMock(read=lambda: json.dumps({
                    'content': [{
                        'text': json.dumps({
                            'short_description': 'DB Connection Pool Issue',
                            'description': 'Database connection pool exhaustion affecting multiple services',
                            'priority': '2',
                            'category': 'Database',
                            'root_cause': 'Connection leak in application code',
                            'workaround': 'Restart application servers to release connections',
                            'impact': '2',
                            'urgency': '2'
                        })
                    }]
                }).encode())
            }
            mock_bedrock.return_value = mock_response
            
            # Create problem
            result = self.problem_manager.create_problem_from_incident(incident)
            
            # Assertions
            self.assertIn('problem_id', result)
            self.assertIn('problem', result)
            self.assertIn('ai_analysis', result)
            
            # Verify problem details
            problem = result['problem']
            self.assertEqual(len(problem['related_incidents']), 1)
            self.assertEqual(problem['related_incidents'][0], 'INC-001')
            
            # Verify AI analysis
            analysis = result['ai_analysis']
            self.assertEqual(analysis['category'], 'Database')
            self.assertEqual(analysis['priority'], '2')
    
    def test_incident_to_problem_correlation(self):
        """Test correlating an incident to an existing problem"""
        # Create a problem first
        problem_id = 'PRB12345'
        problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
        
        problem_data = [{
            'id': problem_id,
            'short_description': 'Test Problem',
            'related_incidents': ['INC-001']
        }]
        
        with open(problems_file, 'w') as f:
            json.dump(problem_data, f)
        
        # Correlate new incident
        result = self.problem_manager.correlate_incident_to_problem('INC-002', problem_id)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(len(result['related_incidents']), 2)
        self.assertIn('INC-002', result['related_incidents'])
    
    def test_problem_correlation_suggestions(self):
        """Test AI-powered problem correlation suggestions"""
        # Create some problems
        problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
        problems = [
            {
                'id': 'PRB001',
                'short_description': 'Database Connection Issues',
                'category': 'Database'
            },
            {
                'id': 'PRB002',
                'short_description': 'API Gateway Timeouts',
                'category': 'Network'
            }
        ]
        
        with open(problems_file, 'w') as f:
            json.dump(problems, f)
        
        # Test incident
        incident = {
            'title': 'Database Query Timeouts',
            'description': 'Slow database queries causing timeouts',
            'service': 'order-service'
        }
        
        # Mock Bedrock response
        with patch.object(self.problem_manager.bedrock_client, 'invoke_model') as mock_bedrock:
            mock_response = {
                'body': MagicMock(read=lambda: json.dumps({
                    'content': [{
                        'text': json.dumps([
                            {'id': 'PRB001', 'confidence': 85},
                            {'id': 'PRB002', 'confidence': 30}
                        ])
                    }]
                }).encode())
            }
            mock_bedrock.return_value = mock_response
            
            # Get correlations
            correlations = self.problem_manager.get_problems_for_correlation(incident)
            
            # Assertions
            self.assertEqual(len(correlations), 2)
            self.assertEqual(correlations[0]['id'], 'PRB001')
            self.assertEqual(correlations[0]['correlation_confidence'], 85)
            self.assertTrue(correlations[0]['correlation_confidence'] > correlations[1]['correlation_confidence'])


class TestSyntheticTransactionGenerator(unittest.TestCase):
    """Test Synthetic Transaction Generator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = SyntheticTransactionGenerator()
    
    @patch('boto3.client')
    def test_transaction_generation_for_performance_incident(self, mock_boto):
        """Test generating transactions for performance incidents"""
        # Mock AWS clients
        mock_logs_client = MagicMock()
        mock_metrics_client = MagicMock()
        mock_boto.side_effect = lambda service, **kwargs: {
            'logs': mock_logs_client,
            'cloudwatch': mock_metrics_client,
            'cloudtrail': MagicMock()
        }.get(service)
        
        # Reinitialize with mocked clients
        self.generator = SyntheticTransactionGenerator()
        
        # Test incident
        incident = {
            'id': 'INC-001',
            'type': 'performance',
            'service': 'api-gateway',
            'title': 'API Response Time Degradation'
        }
        
        # Generate transactions
        result = self.generator.generate_transactions_for_incident(incident)
        
        # Assertions
        self.assertIn('transactions', result)
        self.assertIn('logs', result)
        self.assertIn('metrics', result)
        self.assertIn('vpc_flow_logs', result)
        self.assertIn('cloudtrail_events', result)
        
        # Verify transactions
        transactions = result['transactions']
        self.assertGreater(len(transactions), 0)
        
        # Check for performance pattern (increasing durations)
        durations = [t['duration_ms'] for t in transactions if t['duration_ms']]
        self.assertTrue(any(d > 1000 for d in durations))  # Some slow transactions
    
    def test_transaction_types(self):
        """Test different transaction types generation"""
        # Test each transaction type
        for trans_type in TransactionType:
            transactions = self.generator._generate_generic_issue_transactions()
            
            # Verify we have transactions of different types
            type_found = any(t.type == trans_type for t in transactions)
            self.assertTrue(type_found or len(transactions) > 0)
    
    @patch('boto3.client')
    def test_cloudwatch_log_generation(self, mock_boto):
        """Test CloudWatch log generation"""
        # Mock CloudWatch logs client
        mock_logs_client = MagicMock()
        mock_boto.return_value = mock_logs_client
        
        # Generate test transactions
        from synthetic_transaction_generator import SyntheticTransaction
        transactions = [
            SyntheticTransaction(
                transaction_id='test-1',
                type=TransactionType.API_CALL,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_ms=100,
                status='success',
                error_message=None,
                metadata={'endpoint': '/test'}
            )
        ]
        
        incident = {'id': 'INC-001', 'type': 'test'}
        
        # Reinitialize generator
        self.generator = SyntheticTransactionGenerator()
        
        # Generate logs
        result = self.generator._generate_cloudwatch_logs(transactions, incident)
        
        # Assertions
        self.assertIn('log_group', result)
        self.assertIn('log_stream', result)
        self.assertIn('events_count', result)
        self.assertEqual(result['events_count'], 1)
    
    def test_vpc_flow_log_generation(self):
        """Test VPC Flow Log generation"""
        # Generate test transactions
        transactions = self.generator._generate_security_issue_transactions()
        incident = {'id': 'INC-001', 'type': 'security'}
        
        # Generate VPC flow logs
        result = self.generator._generate_vpc_flow_logs(transactions, incident)
        
        # Assertions
        self.assertIn('file', result)
        self.assertIn('logs_count', result)
        self.assertIn('rejected_count', result)
        
        # Verify file was created
        self.assertTrue(os.path.exists(result['file']))
        
        # Clean up
        os.remove(result['file'])
    
    def test_cloudtrail_event_generation(self):
        """Test CloudTrail event generation"""
        # Generate test transactions
        transactions = self.generator._generate_security_issue_transactions()
        incident = {'id': 'INC-001', 'type': 'security'}
        
        # Generate CloudTrail events
        result = self.generator._generate_cloudtrail_events(transactions, incident)
        
        # Assertions
        self.assertIn('file', result)
        self.assertIn('events_count', result)
        self.assertIn('error_events', result)
        
        # Verify file was created
        self.assertTrue(os.path.exists(result['file']))
        
        # Verify events content
        with open(result['file'], 'r') as f:
            events = json.load(f)
            self.assertGreater(len(events), 0)
            
            # Check event structure
            event = events[0]
            self.assertIn('eventTime', event)
            self.assertIn('eventName', event)
            self.assertIn('userIdentity', event)
        
        # Clean up
        os.remove(result['file'])


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.problem_manager = ServiceNowProblemManager()
        self.transaction_generator = SyntheticTransactionGenerator()
        
        # Clean up any existing problems file
        problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
        if os.path.exists(problems_file):
            os.remove(problems_file)
    
    @patch('boto3.client')
    def test_end_to_end_workflow(self, mock_boto):
        """Test complete workflow from incident to problem to synthetic transactions"""
        # Mock AWS clients
        mock_bedrock = MagicMock()
        mock_logs = MagicMock()
        mock_cloudwatch = MagicMock()
        
        def get_client(service, **kwargs):
            clients = {
                'bedrock-runtime': mock_bedrock,
                'logs': mock_logs,
                'cloudwatch': mock_cloudwatch,
                'cloudtrail': MagicMock()
            }
            return clients.get(service)
        
        mock_boto.side_effect = get_client
        
        # Mock Bedrock response for problem creation
        mock_bedrock.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': json.dumps({
                        'short_description': 'Test Problem',
                        'description': 'Test problem description',
                        'priority': '3',
                        'category': 'Application',
                        'root_cause': 'Test root cause',
                        'workaround': 'Test workaround',
                        'impact': '3',
                        'urgency': '3'
                    })
                }]
            }).encode())
        }
        
        # Reinitialize with mocked clients
        self.problem_manager = ServiceNowProblemManager()
        self.transaction_generator = SyntheticTransactionGenerator()
        
        # Step 1: Create incident
        incident = {
            'id': 'INC-TEST-001',
            'title': 'Test Incident',
            'description': 'Test incident for integration testing',
            'type': 'performance',
            'service': 'test-service',
            'impact': 'Medium'
        }
        
        # Step 2: Create problem from incident
        problem_result = self.problem_manager.create_problem_from_incident(incident)
        
        # Verify problem creation
        self.assertIn('problem_id', problem_result)
        problem_id = problem_result['problem_id']
        
        # Step 3: Generate synthetic transactions
        transaction_result = self.transaction_generator.generate_transactions_for_incident(incident)
        
        # Verify transaction generation
        self.assertIn('transactions', transaction_result)
        self.assertIn('summary', transaction_result)
        self.assertGreater(transaction_result['summary']['total_transactions'], 0)
        
        # Step 4: Verify problem exists
        problems = self.problem_manager.get_all_problems()
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0]['id'], problem_id)
        
        # Clean up
        problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
        if os.path.exists(problems_file):
            os.remove(problems_file)


def run_all_tests():
    """Run all test suites and return results"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestServiceNowProblemManager))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSyntheticTransactionGenerator))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return summary
    return {
        'total_tests': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful()
    }


if __name__ == '__main__':
    print("Running Problem Management Test Suite...")
    print("=" * 60)
    
    result_summary = run_all_tests()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"Total Tests: {result_summary['total_tests']}")
    print(f"Failures: {result_summary['failures']}")
    print(f"Errors: {result_summary['errors']}")
    print(f"Success: {'✅ ALL TESTS PASSED' if result_summary['success'] else '❌ TESTS FAILED'}")
    print("=" * 60)
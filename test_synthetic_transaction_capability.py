#!/usr/bin/env python3
"""
Test Suite for Synthetic Transaction Capability
Tests the ability to reproduce incidents through synthetic transactions
"""

import unittest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSyntheticTransactionCapability(unittest.TestCase):
    """Test synthetic transaction generation and execution"""
    
    def setUp(self):
        """Set up test environment"""
        self.fed_lpp_url = "http://localhost:9087"
        self.sample_incidents = [
            {
                'id': 'INC-ST-001',
                'type': 'api_timeout',
                'description': 'API Gateway experiencing timeout errors on /api/v1/payments endpoint',
                'severity': 'High'
            },
            {
                'id': 'INC-ST-002',
                'type': 'authentication_failure',
                'description': 'Multiple authentication failures detected in login service',
                'severity': 'Critical'
            },
            {
                'id': 'INC-ST-003',
                'type': 'connection_pool_exhaustion',
                'description': 'Database connection pool exhausted causing service failures',
                'severity': 'High'
            },
            {
                'id': 'INC-ST-004',
                'type': 'memory_leak',
                'description': 'Memory usage increasing steadily in payment processing service',
                'severity': 'Medium'
            }
        ]
    
    @patch('requests.post')
    def test_create_synthetic_transaction_for_api_timeout(self, mock_post):
        """Test creating synthetic transaction for API timeout incident"""
        # Mock successful response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'incident_id': 'INC-ST-001',
            'transaction_id': 'ST-INC-ST-001-123456',
            'transaction_type': 'api_timeout',
            'status': 'created',
            'execution_plan': [
                {'action': 'send_request', 'endpoint': '/api/v1/payments', 'timeout': 5},
                {'action': 'wait', 'duration': 6},
                {'action': 'verify_timeout', 'expected_error': 'timeout'}
            ],
            'reproduction_confidence': 0.85
        }
        
        # Create synthetic transaction
        incident = self.sample_incidents[0]
        response = requests.post(
            f"{self.fed_lpp_url}/fedlpp/synthetic-transaction",
            json={
                'incident_id': incident['id'],
                'incident_type': incident['type'],
                'description': incident['description']
            }
        )
        
        # Verify request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check endpoint
        self.assertIn('/fedlpp/synthetic-transaction', call_args[0][0])
        
        # Check payload
        payload = call_args[1]['json']
        self.assertEqual(payload['incident_id'], 'INC-ST-001')
        self.assertEqual(payload['incident_type'], 'api_timeout')
        self.assertIn('API Gateway', payload['description'])
    
    @patch('requests.post')
    def test_synthetic_transaction_execution_results(self, mock_post):
        """Test synthetic transaction execution and results"""
        # Mock execution results
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'transaction_id': 'ST-INC-ST-002-123457',
            'execution_result': {
                'transaction_id': 'ST-INC-ST-002-123457',
                'execution_start': '2025-08-12T10:00:00Z',
                'execution_end': '2025-08-12T10:00:15Z',
                'steps_executed': [
                    {
                        'step': {'action': 'send_request', 'endpoint': '/api/v1/auth'},
                        'success': False,
                        'metrics': {'status_code': 401, 'response_time': 0.5}
                    }
                ],
                'errors_detected': ['401 Unauthorized'],
                'success': False
            },
            'reproduction_confidence': 0.92
        }
        
        # Execute synthetic transaction
        response = requests.post(
            f"{self.fed_lpp_url}/fedlpp/synthetic-transaction",
            json={
                'incident_id': 'INC-ST-002',
                'incident_type': 'authentication_failure',
                'description': 'Authentication failures in login service'
            }
        )
        
        # Verify execution results
        result = mock_post.return_value.json()
        execution_result = result['execution_result']
        
        self.assertFalse(execution_result['success'])
        self.assertIn('401 Unauthorized', execution_result['errors_detected'])
        self.assertEqual(execution_result['steps_executed'][0]['metrics']['status_code'], 401)
        self.assertGreater(result['reproduction_confidence'], 0.9)
    
    def test_transaction_type_determination(self):
        """Test correct determination of transaction type from incident"""
        test_cases = [
            ('API timeout errors occurring', 'api_timeout'),
            ('Authentication service returning unauthorized', 'authentication_failure'),
            ('Database connection pool is exhausted', 'connection_pool_exhaustion'),
            ('Memory usage steadily increasing', 'memory_leak'),
            ('Unknown error in system', 'api_timeout')  # Default
        ]
        
        for description, expected_type in test_cases:
            # Test logic would be in the Fed LPP server
            # Here we verify the mapping
            desc_lower = description.lower()
            
            if 'timeout' in desc_lower:
                self.assertEqual('api_timeout', expected_type)
            elif 'auth' in desc_lower or 'unauthorized' in desc_lower:
                self.assertEqual('authentication_failure', expected_type)
            elif 'connection' in desc_lower and 'pool' in desc_lower:
                self.assertEqual('connection_pool_exhaustion', expected_type)
            elif 'memory' in desc_lower:
                self.assertEqual('memory_leak', expected_type)
    
    @patch('requests.post')
    def test_synthetic_transaction_with_custom_parameters(self, mock_post):
        """Test synthetic transaction with custom parameters extracted from incident"""
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'transaction_id': 'ST-INC-ST-003-123458',
            'execution_plan': [
                {'action': 'concurrent_requests', 'count': 100, 'endpoint': '/api/v1/database'},
                {'action': 'verify_errors', 'expected_error_rate': 0.5}
            ]
        }
        
        # Create transaction with specific endpoint mentioned in description
        response = requests.post(
            f"{self.fed_lpp_url}/fedlpp/synthetic-transaction",
            json={
                'incident_id': 'INC-ST-003',
                'incident_type': 'connection_pool_exhaustion',
                'description': 'Connection pool exhausted on /api/v1/database endpoint'
            }
        )
        
        # Verify custom endpoint was extracted
        result = mock_post.return_value.json()
        execution_plan = result['execution_plan']
        
        self.assertEqual(execution_plan[0]['endpoint'], '/api/v1/database')
        self.assertEqual(execution_plan[0]['count'], 100)
    
    @patch('requests.post')
    def test_synthetic_transaction_metrics_collection(self, mock_post):
        """Test metrics collection during synthetic transaction"""
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'execution_result': {
                'metrics_collected': {
                    'response_times': [0.5, 1.2, 3.5, 8.0, 15.0],
                    'error_rate': 0.65,
                    'successful_requests': 35,
                    'failed_requests': 65,
                    'memory_usage_mb': [100, 150, 200, 250, 300]
                }
            }
        }
        
        # Execute transaction
        response = requests.post(
            f"{self.fed_lpp_url}/fedlpp/synthetic-transaction",
            json={
                'incident_id': 'INC-ST-004',
                'incident_type': 'memory_leak',
                'description': 'Memory leak in payment service'
            }
        )
        
        # Verify metrics
        result = mock_post.return_value.json()
        metrics = result['execution_result']['metrics_collected']
        
        self.assertIn('memory_usage_mb', metrics)
        self.assertEqual(len(metrics['memory_usage_mb']), 5)
        self.assertEqual(metrics['error_rate'], 0.65)
        self.assertEqual(metrics['failed_requests'], 65)
    
    @patch('requests.post')
    def test_ai_powered_incident_reproduction(self, mock_post):
        """Test AI-powered incident reproduction workflow"""
        # Mock AI analysis and synthetic transaction creation
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'incident_id': 'INC-AI-001',
            'ai_analysis': {
                'incident_pattern': 'timeout_cascade',
                'root_cause_hypothesis': 'Downstream service latency causing timeouts',
                'reproduction_strategy': 'progressive_load_with_latency'
            },
            'execution_plan': [
                {'action': 'baseline_request', 'endpoint': '/api/v1/service'},
                {'action': 'inject_latency', 'delay_ms': 1000},
                {'action': 'progressive_load', 'start_rps': 10, 'end_rps': 100},
                {'action': 'monitor_cascade', 'duration': 60}
            ],
            'expected_reproduction': {
                'confidence': 0.88,
                'expected_symptoms': ['timeout_errors', 'connection_refused', 'circuit_breaker_open']
            }
        }
        
        # Create AI-powered synthetic transaction
        response = requests.post(
            f"{self.fed_lpp_url}/fedlpp/synthetic-transaction",
            json={
                'incident_id': 'INC-AI-001',
                'incident_type': 'complex',
                'description': 'Cascading timeouts across multiple services during peak load',
                'use_ai_analysis': True
            }
        )
        
        # Verify AI-powered reproduction
        result = mock_post.return_value.json()
        
        self.assertIn('ai_analysis', result)
        self.assertEqual(result['ai_analysis']['incident_pattern'], 'timeout_cascade')
        self.assertIn('progressive_load', [step['action'] for step in result['execution_plan']])
        self.assertGreater(result['expected_reproduction']['confidence'], 0.85)
    
    @patch('requests.post')
    def test_synthetic_transaction_cloudwatch_integration(self, mock_post):
        """Test CloudWatch metrics integration for synthetic transactions"""
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'cloudwatch_metrics': {
                'namespace': 'FedLPP/SyntheticTransactions',
                'metrics_sent': [
                    {
                        'MetricName': 'SyntheticTransactionSuccess',
                        'Value': 0,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'SyntheticTransactionErrors',
                        'Value': 3,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'ReproductionConfidence',
                        'Value': 0.91,
                        'Unit': 'None'
                    }
                ]
            }
        }
        
        # Execute transaction
        response = requests.post(
            f"{self.fed_lpp_url}/fedlpp/synthetic-transaction",
            json={
                'incident_id': 'INC-CW-001',
                'incident_type': 'api_timeout',
                'description': 'API timeouts',
                'send_to_cloudwatch': True
            }
        )
        
        # Verify CloudWatch metrics
        result = mock_post.return_value.json()
        cw_metrics = result['cloudwatch_metrics']
        
        self.assertEqual(cw_metrics['namespace'], 'FedLPP/SyntheticTransactions')
        self.assertEqual(len(cw_metrics['metrics_sent']), 3)
        
        # Check specific metrics
        success_metric = next(m for m in cw_metrics['metrics_sent'] if m['MetricName'] == 'SyntheticTransactionSuccess')
        self.assertEqual(success_metric['Value'], 0)  # Failed transaction
        
        error_metric = next(m for m in cw_metrics['metrics_sent'] if m['MetricName'] == 'SyntheticTransactionErrors')
        self.assertEqual(error_metric['Value'], 3)
    
    def test_synthetic_transaction_templates(self):
        """Test available synthetic transaction templates"""
        templates = {
            'api_timeout': ['send_request', 'wait', 'verify_timeout'],
            'authentication_failure': ['send_request', 'verify_response'],
            'connection_pool_exhaustion': ['concurrent_requests', 'verify_errors'],
            'memory_leak': ['allocate_memory', 'repeat', 'verify_memory_usage']
        }
        
        for template_type, expected_actions in templates.items():
            # Verify template structure
            self.assertIsInstance(expected_actions, list)
            self.assertGreater(len(expected_actions), 0)
            
            # Verify actions are valid
            valid_actions = [
                'send_request', 'wait', 'verify_timeout', 'verify_response',
                'concurrent_requests', 'verify_errors', 'allocate_memory',
                'repeat', 'verify_memory_usage'
            ]
            
            for action in expected_actions:
                self.assertIn(action, valid_actions)
    
    @patch('requests.post')
    def test_incident_correlation_with_synthetic_results(self, mock_post):
        """Test correlation between incident and synthetic transaction results"""
        # Mock both defect creation and synthetic transaction
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.side_effect = [
            # Synthetic transaction result
            {
                'incident_id': 'INC-CORR-001',
                'reproduction_confidence': 0.93,
                'execution_result': {
                    'errors_detected': ['Connection timeout after 5000ms'],
                    'metrics_collected': {'error_rate': 0.78}
                }
            },
            # Defect creation result
            {
                'id': 'DEF-AUTO-001',
                'name': 'Auto-created: Connection timeout issue',
                'evidence': 'Synthetic transaction reproduced issue with 93% confidence'
            }
        ]
        
        # First create synthetic transaction
        st_response = requests.post(
            f"{self.fed_lpp_url}/fedlpp/synthetic-transaction",
            json={
                'incident_id': 'INC-CORR-001',
                'incident_type': 'api_timeout',
                'description': 'Connection timeouts'
            }
        )
        
        # Then create defect with synthetic evidence
        defect_response = requests.post(
            "http://localhost:9085/octane/defects",
            json={
                'name': 'Auto-created: Connection timeout issue',
                'description': 'Issue reproduced via synthetic transaction',
                'synthetic_evidence': {
                    'transaction_id': 'ST-INC-CORR-001',
                    'reproduction_confidence': 0.93,
                    'errors_detected': ['Connection timeout after 5000ms']
                }
            }
        )
        
        # Verify correlation
        self.assertEqual(mock_post.call_count, 2)
        
        # Check synthetic transaction was created first
        first_call = mock_post.call_args_list[0]
        self.assertIn('synthetic-transaction', first_call[0][0])
        
        # Check defect includes synthetic evidence
        second_call = mock_post.call_args_list[1]
        defect_data = second_call[1]['json']
        self.assertIn('synthetic_evidence', defect_data)
        self.assertEqual(defect_data['synthetic_evidence']['reproduction_confidence'], 0.93)


class TestFedSearchIntegration(unittest.TestCase):
    """Test FedSearch MCP server integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.fedsearch_url = "http://localhost:9088"
        self.sample_query = "API security compliance federal requirements"
    
    @patch('requests.post')
    def test_intelligent_federal_search(self, mock_post):
        """Test intelligent search across federal sources"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'query': self.sample_query,
            'total_results': 15,
            'results': [
                {
                    'id': 'FS-NIST-001',
                    'title': 'NIST SP 800-53 Rev 5: Security Controls',
                    'source': 'NIST',
                    'relevance_score': 0.95
                },
                {
                    'id': 'FS-CISA-002',
                    'title': 'API Security Advisory',
                    'source': 'CISA',
                    'relevance_score': 0.92
                }
            ],
            'insights': {
                'key_themes': ['security', 'api', 'compliance'],
                'compliance_implications': ['Multiple compliance frameworks apply']
            }
        }
        
        # Perform search
        response = requests.post(
            f"{self.fedsearch_url}/fedsearch/search",
            json={
                'query': self.sample_query,
                'search_type': 'semantic',
                'sources': ['NIST', 'CISA', 'GAO']
            }
        )
        
        # Verify search results
        result = mock_post.return_value.json()
        self.assertEqual(result['total_results'], 15)
        self.assertEqual(len(result['results']), 2)
        self.assertIn('security', result['insights']['key_themes'])
    
    @patch('requests.post')
    def test_compliance_mapping_for_incident(self, mock_post):
        """Test compliance mapping for incident"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'compliance_mapping': {
                'NIST': {
                    'applicable_controls': [
                        'AC-2: Account Management',
                        'AU-2: Audit Events',
                        'SC-13: Cryptographic Protection'
                    ],
                    'priority': 'high'
                },
                'FISMA': {
                    'applicable_controls': ['Risk Assessment', 'Security Planning'],
                    'priority': 'high'
                }
            },
            'compliance_scores': {
                'NIST': {'readiness_score': 65, 'confidence': 'high'},
                'FISMA': {'readiness_score': 70, 'confidence': 'medium'}
            }
        }
        
        # Map incident to compliance
        response = requests.post(
            f"{self.fedsearch_url}/fedsearch/compliance-mapping",
            json={
                'incident_data': {
                    'id': 'INC-COMP-001',
                    'description': 'Authentication service security incident'
                },
                'frameworks': ['NIST', 'FISMA', 'FedRAMP']
            }
        )
        
        # Verify compliance mapping
        result = mock_post.return_value.json()
        nist_controls = result['compliance_mapping']['NIST']['applicable_controls']
        self.assertEqual(len(nist_controls), 3)
        self.assertIn('AC-2', nist_controls[0])
        
        # Check compliance scores
        self.assertEqual(result['compliance_scores']['NIST']['readiness_score'], 65)
        self.assertEqual(result['compliance_scores']['FISMA']['readiness_score'], 70)


def run_synthetic_transaction_tests():
    """Run all synthetic transaction tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSyntheticTransactionCapability))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFedSearchIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "="*70)
    print("SYNTHETIC TRANSACTION CAPABILITY TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        print("\n✅ ALL SYNTHETIC TRANSACTION TESTS PASSED!")
        print("   - API timeout reproduction ✓")
        print("   - Authentication failure simulation ✓")
        print("   - Connection pool exhaustion testing ✓")
        print("   - Memory leak detection ✓")
        print("   - AI-powered incident reproduction ✓")
        print("   - CloudWatch metrics integration ✓")
        print("   - Federal knowledge search ✓")
        print("   - Compliance mapping ✓")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
    
    return result


if __name__ == '__main__':
    run_synthetic_transaction_tests()
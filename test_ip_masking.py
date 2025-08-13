#!/usr/bin/env python3
"""
Comprehensive test suite for IP address masking functionality
Tests IP masking across Lambda functions and Streamlit UI
"""

import json
import unittest
import sys
import os
import boto3
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the IP masker
from utils.ip_masker import IPMasker, mask_logs_for_llm

# Import Lambda functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/lambdas/supervisor'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/lambdas/cloudwatch_logs_agent'))


class TestIPMasker(unittest.TestCase):
    """Test the IP masking utility."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.masker = IPMasker(mask_type="partial")
        
    def test_ipv4_masking_partial(self):
        """Test partial IPv4 masking."""
        test_cases = [
            ("192.168.1.100", "192.168.XXX.XXX"),
            ("10.0.0.5", "10.0.XXX.XXX"),
            ("172.16.254.1", "172.16.XXX.XXX"),
            ("8.8.8.8", "8.8.XXX.XXX")
        ]
        
        for ip, expected in test_cases:
            masked = self.masker.mask_ip(ip)
            self.assertEqual(masked, expected, f"Failed to mask {ip}")
            
    def test_ipv4_masking_full(self):
        """Test full IPv4 masking."""
        masker = IPMasker(mask_type="full")
        test_ip = "192.168.1.100"
        masked = masker.mask_ip(test_ip)
        self.assertEqual(masked, "XXX.XXX.XXX.XXX")
        
    def test_ipv6_masking(self):
        """Test IPv6 masking."""
        test_ip = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        masked = self.masker.mask_ip(test_ip)
        self.assertTrue(masked.startswith("2001:0db8:85a3:0000:"))
        self.assertTrue("XXXX" in masked)
        
    def test_text_masking(self):
        """Test masking IPs in text."""
        test_text = "Error connecting to database at 192.168.1.100:5432 from client 10.0.0.5"
        masked_text, ip_map = self.masker.mask_text(test_text)
        
        self.assertIn("192.168.XXX.XXX", masked_text)
        self.assertIn("10.0.XXX.XXX", masked_text)
        self.assertEqual(len(ip_map), 2)
        self.assertEqual(ip_map["192.168.1.100"], "192.168.XXX.XXX")
        self.assertEqual(ip_map["10.0.0.5"], "10.0.XXX.XXX")
        
    def test_aws_log_patterns(self):
        """Test masking common AWS log patterns."""
        test_logs = [
            "srcaddr=10.0.1.100 dstaddr=10.0.2.200 action=ACCEPT",
            "ELB 192.168.1.50:443 -> 10.0.1.10:8080",
            "client_ip: 203.0.113.0 request to server",
            "source ip: 198.51.100.0 unauthorized access",
            "remote_addr: 172.16.0.50 connection refused"
        ]
        
        for log in test_logs:
            masked_log, ip_map = self.masker.mask_text(log)
            # Check that IPs were found and masked
            self.assertTrue(len(ip_map) > 0, f"No IPs found in: {log}")
            self.assertIn("XXX", masked_log)
            
    def test_json_masking(self):
        """Test masking IPs in JSON data."""
        test_json = {
            "message": "Connection from 192.168.1.100",
            "client_ip": "10.0.0.5",
            "nested": {
                "server_ip": "172.16.0.1",
                "logs": ["Error at 192.168.2.50", "Success from 10.0.1.1"]
            }
        }
        
        masked_json = self.masker.mask_json(test_json)
        
        self.assertIn("192.168.XXX.XXX", masked_json["message"])
        self.assertEqual(masked_json["client_ip"], "10.0.XXX.XXX")
        self.assertEqual(masked_json["nested"]["server_ip"], "172.16.XXX.XXX")
        self.assertIn("192.168.XXX.XXX", masked_json["nested"]["logs"][0])
        
    def test_log_entries_masking(self):
        """Test masking CloudWatch log entries."""
        log_entries = [
            {
                "message": "2024-01-15 10:30:00 ERROR Connection timeout to 192.168.1.100:3306",
                "timestamp": 1705315800000
            },
            {
                "message": '{"level":"ERROR","client":"10.0.0.5","msg":"Auth failed"}',
                "timestamp": 1705315801000
            }
        ]
        
        masked_entries = self.masker.mask_log_entries(log_entries)
        
        self.assertEqual(len(masked_entries), 2)
        self.assertIn("192.168.XXX.XXX", masked_entries[0]["message"])
        self.assertIn("10.0.XXX.XXX", masked_entries[1]["message"])
        
    def test_masking_consistency(self):
        """Test that same IP always gets same mask."""
        ip = "192.168.1.100"
        mask1 = self.masker.mask_ip(ip)
        mask2 = self.masker.mask_ip(ip)
        self.assertEqual(mask1, mask2)
        
    def test_masking_stats(self):
        """Test masking statistics."""
        self.masker.mask_text("IPs: 192.168.1.1, 192.168.1.2, 192.168.1.1")
        stats = self.masker.get_masking_stats()
        
        self.assertEqual(stats["total_ips_masked"], 3)
        self.assertEqual(stats["unique_ips"], 2)  # Only 2 unique IPs
        self.assertEqual(stats["mask_type"], "partial")
        
    def test_non_ip_text(self):
        """Test that non-IP text is not modified."""
        test_text = "This is a normal log message without any IPs"
        masked_text, ip_map = self.masker.mask_text(test_text)
        
        self.assertEqual(test_text, masked_text)
        self.assertEqual(len(ip_map), 0)


class TestSupervisorLambdaIntegration(unittest.TestCase):
    """Test IP masking integration in supervisor Lambda."""
    
    @patch('boto3.client')
    def setUp(self, mock_boto_client):
        """Set up test fixtures."""
        # Mock AWS clients
        self.mock_logs_client = MagicMock()
        self.mock_cloudwatch = MagicMock()
        self.mock_bedrock = MagicMock()
        self.mock_lambda = MagicMock()
        self.mock_ssm = MagicMock()
        
        def get_client(service):
            if service == 'logs':
                return self.mock_logs_client
            elif service == 'cloudwatch':
                return self.mock_cloudwatch
            elif service == 'bedrock-runtime':
                return self.mock_bedrock
            elif service == 'lambda':
                return self.mock_lambda
            elif service == 'ssm':
                return self.mock_ssm
                
        mock_boto_client.side_effect = get_client
        
        # Import after mocking
        from lambda_function import lambda_handler, get_demo_logs
        self.lambda_handler = lambda_handler
        self.get_demo_logs = get_demo_logs
        
    def test_get_demo_logs_with_masking(self):
        """Test that get_demo_logs masks IP addresses."""
        # Mock log data with IPs
        self.mock_logs_client.describe_log_streams.return_value = {
            'logStreams': [{'logStreamName': 'test-stream'}]
        }
        
        self.mock_logs_client.filter_log_events.return_value = {
            'events': [
                {
                    'message': json.dumps({
                        'level': 'ERROR',
                        'message': 'Connection failed to 192.168.1.100:5432'
                    })
                },
                {
                    'message': json.dumps({
                        'level': 'WARN',
                        'message': 'Slow response from server at 10.0.0.5'
                    })
                }
            ]
        }
        
        # Get logs with masking enabled
        log_data = self.get_demo_logs(mask_ips=True)
        
        # Check that IPs were masked
        self.assertTrue(log_data['ip_masking_applied'])
        self.assertGreater(log_data['masked_ip_count'], 0)
        
        # Check masked messages
        for event in log_data['recent_events']:
            if 'message' in event:
                self.assertNotIn('192.168.1.100', event['message'])
                self.assertNotIn('10.0.0.5', event['message'])
                
    def test_get_demo_logs_without_masking(self):
        """Test that get_demo_logs can return unmasked logs."""
        # Mock log data
        self.mock_logs_client.describe_log_streams.return_value = {
            'logStreams': [{'logStreamName': 'test-stream'}]
        }
        
        self.mock_logs_client.filter_log_events.return_value = {
            'events': [
                {
                    'message': json.dumps({
                        'level': 'ERROR',
                        'message': 'Connection failed to 192.168.1.100:5432'
                    })
                }
            ]
        }
        
        # Get logs without masking
        log_data = self.get_demo_logs(mask_ips=False)
        
        # Check that IPs were NOT masked
        self.assertFalse(log_data['ip_masking_applied'])
        self.assertEqual(log_data['masked_ip_count'], 0)
        
        # Check original messages preserved
        for event in log_data['recent_events']:
            if event.get('message') == 'Connection failed to 192.168.1.100:5432':
                self.assertIn('192.168.1.100', event['message'])
                
    def test_lambda_handler_masking_parameter(self):
        """Test Lambda handler respects mask_ips parameter."""
        # Mock required services
        self.mock_cloudwatch.get_metric_statistics.return_value = {'Datapoints': []}
        self.mock_logs_client.describe_log_streams.return_value = {'logStreams': []}
        self.mock_lambda.invoke.return_value = {
            'Payload': MagicMock(read=lambda: json.dumps({'statusCode': 200}).encode())
        }
        
        # Test with masking enabled (default)
        event = {
            'incident_description': 'Test incident',
            'mask_ips': True
        }
        
        response = self.lambda_handler(event, None)
        response_body = json.loads(response['body'])
        
        self.assertEqual(response['statusCode'], 200)
        self.assertTrue(response_body['metadata']['security']['ip_masking_enabled'])


class TestCloudWatchLogsAgentIntegration(unittest.TestCase):
    """Test IP masking in CloudWatch logs agent."""
    
    @patch('boto3.client')
    def setUp(self, mock_boto_client):
        """Set up test fixtures."""
        # Mock AWS clients
        self.mock_logs = MagicMock()
        self.mock_cloudwatch = MagicMock()
        self.mock_bedrock = MagicMock()
        
        def get_client(service):
            if service == 'logs':
                return self.mock_logs
            elif service == 'cloudwatch':
                return self.mock_cloudwatch
            elif service == 'bedrock-runtime':
                return self.mock_bedrock
                
        mock_boto_client.side_effect = get_client
        
        # Import after mocking
        from lambda_function import lambda_handler, analyze_with_bedrock
        self.lambda_handler = lambda_handler
        self.analyze_with_bedrock = analyze_with_bedrock
        
    def test_analyze_with_bedrock_masking(self):
        """Test that logs are masked before sending to Bedrock."""
        # Mock Bedrock response
        self.mock_bedrock.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': json.dumps({
                        'summary': 'Test analysis',
                        'issues': ['High error rate'],
                        'recommendations': ['Check database connections']
                    })
                }]
            }).encode())
        }
        
        # Test events with IPs
        events = [
            {'message': 'Error connecting to 192.168.1.100'},
            {'message': 'Timeout from client 10.0.0.5'}
        ]
        
        error_patterns = {'connection_error': 5}
        
        # Analyze with Bedrock
        result = self.analyze_with_bedrock(events, error_patterns)
        
        # Check that Bedrock was called
        self.mock_bedrock.invoke_model.assert_called_once()
        
        # Get the prompt sent to Bedrock
        call_args = self.mock_bedrock.invoke_model.call_args
        body = json.loads(call_args[1]['body'])
        prompt = body['messages'][0]['content']
        
        # Verify IPs were masked in the prompt
        self.assertNotIn('192.168.1.100', prompt)
        self.assertNotIn('10.0.0.5', prompt)
        self.assertIn('XXX', prompt)
        
        # Check masking stats in result
        self.assertIn('masking_stats', result)
        self.assertGreater(result['masking_stats']['total_ips_masked'], 0)


class TestEndToEndMasking(unittest.TestCase):
    """End-to-end test of IP masking across the system."""
    
    def test_complete_flow(self):
        """Test complete flow from log generation to UI display."""
        # Sample incident with logs containing IPs
        test_logs = [
            {
                'message': 'Database connection timeout at 192.168.1.100:5432',
                'level': 'ERROR',
                'timestamp': '2024-01-15T10:30:00Z'
            },
            {
                'message': 'Unauthorized access attempt from 203.0.113.50',
                'level': 'WARN',
                'timestamp': '2024-01-15T10:31:00Z'
            },
            {
                'message': 'API rate limit exceeded for client 10.0.0.25',
                'level': 'ERROR',
                'timestamp': '2024-01-15T10:32:00Z'
            }
        ]
        
        # Test masking utility
        masker = IPMasker(mask_type="partial")
        masked_logs = []
        total_masked = 0
        
        for log in test_logs:
            masked_msg, ip_map = masker.mask_text(log['message'])
            masked_log = log.copy()
            masked_log['message'] = masked_msg
            masked_logs.append(masked_log)
            total_masked += len(ip_map)
            
        # Verify all IPs were masked
        self.assertEqual(total_masked, 3)
        
        # Verify original IPs are not in masked logs
        for log in masked_logs:
            self.assertNotIn('192.168.1.100', log['message'])
            self.assertNotIn('203.0.113.50', log['message'])
            self.assertNotIn('10.0.0.25', log['message'])
            
        # Verify masked IPs are present
        self.assertIn('192.168.XXX.XXX', masked_logs[0]['message'])
        self.assertIn('203.0.XXX.XXX', masked_logs[1]['message'])
        self.assertIn('10.0.XXX.XXX', masked_logs[2]['message'])
        
    def test_security_scenarios(self):
        """Test various security-sensitive log scenarios."""
        security_logs = [
            "SSH login attempt from 192.168.1.100 for user admin",
            "Failed authentication: user=john ip=10.0.0.50 attempts=5",
            "Firewall blocked connection from 203.0.113.0 to 172.16.0.10",
            "API key exposed in request from client_ip: 198.51.100.5",
            "VPC Flow: srcaddr=10.0.1.100 dstaddr=10.0.2.200 protocol=TCP"
        ]
        
        masker = IPMasker(mask_type="partial")
        
        for log in security_logs:
            masked_log, ip_map = masker.mask_text(log)
            
            # Ensure all IPs were found and masked
            self.assertGreater(len(ip_map), 0, f"No IPs found in: {log}")
            
            # Verify no original IPs remain
            for original_ip in ip_map.keys():
                self.assertNotIn(original_ip, masked_log)
                
            # Verify masked versions are present
            for masked_ip in ip_map.values():
                self.assertIn(masked_ip, masked_log)


def run_all_tests():
    """Run all test suites."""
    print("🧪 Running IP Masking Test Suite")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestIPMasker,
        TestSupervisorLambdaIntegration,
        TestCloudWatchLogsAgentIntegration,
        TestEndToEndMasking
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
        
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"🚫 Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 All tests passed! IP masking is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
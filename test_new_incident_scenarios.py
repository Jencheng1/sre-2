#!/usr/bin/env python3
"""
Test cases for new incident scenarios:
1. RDS Database Connection Pool Exhaustion
2. Lambda Cold Start Storm During Black Friday  
3. S3 Bucket Exposure via Misconfigured CloudFront
"""

import json
import unittest
from datetime import datetime, timedelta
import boto3
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lambdas.supervisor.lambda_function import lambda_handler as supervisor_handler
from src.lambdas.knowledge_base_agent.lambda_function_serverless import lambda_handler as kb_handler


class TestNewIncidentScenarios(unittest.TestCase):
    """Test cases for the three new incident scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.maxDiff = None
        
        # Load the incident scenarios
        with open('additional_incident_scenarios.json', 'r') as f:
            self.scenarios = json.load(f)['additional_scenarios']
        
        # Load the comprehensive scenarios with SSM data
        with open('comprehensive_incident_scenarios_with_ssm.json', 'r') as f:
            self.ssm_scenarios = json.load(f)['incident_scenarios_with_real_aws_data']
    
    @patch('boto3.client')
    def test_rds_connection_pool_exhaustion(self, mock_boto_client):
        """Test RDS connection pool exhaustion scenario"""
        print("\n=== Testing RDS Connection Pool Exhaustion Scenario ===")
        
        scenario = self.scenarios[0]  # RDS scenario
        
        # Mock CloudWatch client
        mock_cw = Mock()
        mock_cw.get_metric_statistics.return_value = {
            'Datapoints': [
                {
                    'Timestamp': datetime.now() - timedelta(minutes=30),
                    'Average': 150.0,
                    'Unit': 'Count'
                }
            ]
        }
        
        # Mock CloudTrail client
        mock_ct = Mock()
        mock_ct.lookup_events.return_value = {
            'Events': [
                {
                    'EventTime': datetime.now() - timedelta(hours=1),
                    'EventName': 'ModifyDBInstance',
                    'Resources': [{'ResourceName': 'prod-mysql-primary'}],
                    'CloudTrailEvent': json.dumps({
                        'requestParameters': {
                            'vpcSecurityGroupIds': ['sg-0987654321fedcba0', 'sg-1234567890abcdef1']
                        }
                    })
                }
            ]
        }
        
        # Mock VPC Flow Logs
        mock_logs = Mock()
        mock_logs.filter_log_events.return_value = {
            'events': [
                {
                    'timestamp': int((datetime.now() - timedelta(minutes=20)).timestamp() * 1000),
                    'message': '2 123456789012 eni-rds-0123456 10.0.2.200 10.0.10.50 38456 3306 6 3 180 1722855605 1722855615 REJECT OK'
                }
            ]
        }
        
        # Mock Knowledge Base
        mock_kb = Mock()
        mock_kb.invoke.return_value = {
            'statusCode': 200,
            'body': json.dumps({
                'results': [
                    {
                        'title': 'RDS Connection Pool Best Practices',
                        'content': 'Monitor connection pool usage and set alarms at 80%',
                        'similarity': 0.95
                    }
                ]
            })
        }
        
        mock_boto_client.side_effect = lambda service, **kwargs: {
            'cloudwatch': mock_cw,
            'cloudtrail': mock_ct,
            'logs': mock_logs,
            'lambda': mock_kb
        }.get(service, Mock())
        
        # Create supervisor event
        event = {
            'incident_type': 'database',
            'incident_id': 'INC-004',
            'description': scenario['description'],
            'severity': 'critical',
            'affected_resources': ['prod-mysql-primary'],
            'metrics': {
                'database_connections': 150,
                'connection_pool_size': 150,
                'failed_connections': 450
            }
        }
        
        # Test supervisor analysis
        response = supervisor_handler(event, {})
        
        # Assertions
        self.assertEqual(response['statusCode'], 200)
        analysis = json.loads(response['body'])
        
        print(f"Root Cause: {analysis.get('root_cause', 'Not found')}")
        print(f"Severity: {analysis.get('severity', 'Not found')}")
        
        # Verify security group change was detected
        self.assertIn('security group', analysis.get('root_cause', '').lower())
        
        # Verify connection pool exhaustion was identified
        self.assertIn('connection', analysis.get('root_cause', '').lower())
        
        # Verify recommendations include fixing security groups
        recommendations = analysis.get('recommendations', [])
        self.assertTrue(any('security group' in r.lower() for r in recommendations))
        
        print("✓ RDS Connection Pool Exhaustion test passed")
    
    @patch('boto3.client')
    def test_lambda_cold_start_storm(self, mock_boto_client):
        """Test Lambda cold start storm scenario"""
        print("\n=== Testing Lambda Cold Start Storm Scenario ===")
        
        scenario = self.scenarios[1]  # Lambda scenario
        
        # Mock CloudWatch client
        mock_cw = Mock()
        mock_cw.get_metric_statistics.return_value = {
            'Datapoints': [
                {
                    'Timestamp': datetime.now() - timedelta(minutes=10),
                    'Average': 15000.0,  # 15 second duration
                    'Unit': 'Milliseconds'
                }
            ]
        }
        
        # Mock CloudWatch Logs
        mock_logs = Mock()
        mock_logs.filter_log_events.return_value = {
            'events': [
                {
                    'timestamp': int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000),
                    'message': 'REPORT RequestId: 123 Duration: 15000.00 ms Init Duration: 12543.21 ms'
                },
                {
                    'timestamp': int((datetime.now() - timedelta(minutes=4)).timestamp() * 1000),
                    'message': 'Task timed out after 15.00 seconds'
                }
            ]
        }
        
        # Mock Lambda client
        mock_lambda = Mock()
        mock_lambda.get_function_configuration.return_value = {
            'ReservedConcurrentExecutions': 100,
            'Runtime': 'python3.9',
            'MemorySize': 3008,
            'VpcConfig': {
                'SubnetIds': ['subnet-12345'],
                'SecurityGroupIds': ['sg-12345']
            }
        }
        
        mock_boto_client.side_effect = lambda service, **kwargs: {
            'cloudwatch': mock_cw,
            'logs': mock_logs,
            'lambda': mock_lambda
        }.get(service, Mock())
        
        # Create supervisor event
        event = {
            'incident_type': 'performance',
            'incident_id': 'INC-005',
            'description': scenario['description'],
            'severity': 'critical',
            'affected_resources': ['checkout-processor'],
            'metrics': {
                'error_rate': 35,
                'timeout_rate': 28,
                'average_duration': 14500,
                'invocation_rate': 1000
            }
        }
        
        # Test supervisor analysis
        response = supervisor_handler(event, {})
        
        # Assertions
        self.assertEqual(response['statusCode'], 200)
        analysis = json.loads(response['body'])
        
        print(f"Root Cause: {analysis.get('root_cause', 'Not found')}")
        print(f"Business Impact: {analysis.get('business_impact', {})}")
        
        # Verify cold start issue was detected
        self.assertIn('cold start', analysis.get('root_cause', '').lower())
        
        # Verify VPC configuration issue was identified
        root_cause = analysis.get('root_cause', '').lower()
        self.assertTrue('vpc' in root_cause or 'concurrency' in root_cause)
        
        # Verify recommendations include provisioned concurrency
        recommendations = analysis.get('recommendations', [])
        self.assertTrue(any('concurrency' in r.lower() for r in recommendations))
        
        print("✓ Lambda Cold Start Storm test passed")
    
    @patch('boto3.client')
    def test_s3_bucket_exposure(self, mock_boto_client):
        """Test S3 bucket exposure scenario"""
        print("\n=== Testing S3 Bucket Exposure Scenario ===")
        
        scenario = self.scenarios[2]  # S3 scenario
        
        # Mock CloudTrail client
        mock_ct = Mock()
        mock_ct.lookup_events.return_value = {
            'Events': [
                {
                    'EventTime': datetime.now() - timedelta(minutes=45),
                    'EventName': 'UpdateDistribution',
                    'Resources': [{'ResourceName': 'E1234567890ABC'}],
                    'CloudTrailEvent': json.dumps({
                        'requestParameters': {
                            'distributionConfig': {
                                'origins': {
                                    'items': [{
                                        's3OriginConfig': {
                                            'originAccessIdentity': ''
                                        }
                                    }]
                                }
                            }
                        }
                    })
                },
                {
                    'EventTime': datetime.now() - timedelta(minutes=40),
                    'EventName': 'PutBucketPolicy',
                    'Resources': [{'ResourceName': 'private-docs-bucket'}],
                    'CloudTrailEvent': json.dumps({
                        'requestParameters': {
                            'bucketPolicy': {
                                'Statement': [{
                                    'Principal': '*',
                                    'Action': 's3:GetObject'
                                }]
                            }
                        }
                    })
                }
            ]
        }
        
        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.get_bucket_policy.return_value = {
            'Policy': json.dumps({
                'Statement': [{
                    'Effect': 'Allow',
                    'Principal': '*',
                    'Action': 's3:GetObject',
                    'Resource': 'arn:aws:s3:::private-docs-bucket/*'
                }]
            })
        }
        
        # Mock Trusted Advisor
        mock_support = Mock()
        mock_support.describe_trusted_advisor_check_result.return_value = {
            'result': {
                'status': 'error',
                'flaggedResources': [
                    {
                        'resourceId': 'private-docs-bucket',
                        'metadata': [
                            'private-docs-bucket',
                            'Bucket allows public read access',
                            'Policy allows s3:GetObject to principal *'
                        ]
                    }
                ]
            }
        }
        
        mock_boto_client.side_effect = lambda service, **kwargs: {
            'cloudtrail': mock_ct,
            's3': mock_s3,
            'support': mock_support
        }.get(service, Mock())
        
        # Create supervisor event
        event = {
            'incident_type': 'security',
            'incident_id': 'INC-006',
            'description': scenario['description'],
            'severity': 'critical',
            'affected_resources': ['private-docs-bucket', 'E1234567890ABC'],
            'security_findings': {
                'exposed_objects': 47,
                'unauthorized_access_attempts': 15,
                'data_classification': 'confidential'
            }
        }
        
        # Test supervisor analysis
        response = supervisor_handler(event, {})
        
        # Assertions
        self.assertEqual(response['statusCode'], 200)
        analysis = json.loads(response['body'])
        
        print(f"Root Cause: {analysis.get('root_cause', 'Not found')}")
        print(f"Compliance Impact: {analysis.get('compliance_impact', [])}")
        
        # Verify CloudFront OAI removal was detected
        self.assertIn('origin access identity', analysis.get('root_cause', '').lower())
        
        # Verify public access issue was identified
        self.assertIn('public', analysis.get('root_cause', '').lower())
        
        # Verify recommendations include immediate remediation
        recommendations = analysis.get('recommendations', [])
        self.assertTrue(any('immediately' in r.lower() for r in recommendations))
        self.assertTrue(any('block public access' in r.lower() for r in recommendations))
        
        print("✓ S3 Bucket Exposure test passed")
    
    def test_correlation_with_ssm_data(self):
        """Test correlation with AWS Systems Manager data"""
        print("\n=== Testing Correlation with SSM Change Calendar and OpsItems ===")
        
        # Test that each scenario has proper SSM correlation
        for ssm_scenario in self.ssm_scenarios:
            print(f"\nTesting scenario: {ssm_scenario['name']}")
            
            # Verify Change Calendar data
            self.assertIn('aws_systems_manager_change_calendar', ssm_scenario)
            change_requests = ssm_scenario['aws_systems_manager_change_calendar']['changeRequests']
            self.assertTrue(len(change_requests) > 0)
            
            # Verify each change request has required fields
            for cr in change_requests:
                self.assertIn('changeRequestId', cr)
                self.assertIn('status', cr)
                self.assertEqual(cr['status'], 'APPROVED')
                self.assertIn('changeDetails', cr)
            
            # Verify OpsItems data
            self.assertIn('aws_systems_manager_opsitems', ssm_scenario)
            opsitem = ssm_scenario['aws_systems_manager_opsitems']
            self.assertIn('opsItemId', opsitem)
            self.assertIn('severity', opsitem)
            self.assertIn('operationalData', opsitem)
            
            # Verify correlation analysis
            self.assertIn('correlation_and_root_cause', ssm_scenario)
            correlation = ssm_scenario['correlation_and_root_cause']
            self.assertIn('correlated_events', correlation)
            
            # Verify timeline correlation
            events = correlation['correlated_events']
            change_event = next((e for e in events if e['source'] == 'Change Calendar'), None)
            self.assertIsNotNone(change_event)
            self.assertEqual(change_event['relevance'], 'HIGH')
            
            print(f"✓ SSM correlation verified for {ssm_scenario['name']}")
    
    @patch('requests.post')
    @patch('requests.get')
    def test_mcp_integration(self, mock_get, mock_post):
        """Test MCP server integration"""
        print("\n=== Testing MCP Server Integration ===")
        
        # Mock MCP responses
        mock_post.return_value.json.return_value = {
            'results': [
                {
                    'timestamp': '2025-08-05T04:00:00',
                    'host': 'prod-app-01',
                    'avg_latency': 250.5,
                    'packet_loss': 5.2
                }
            ]
        }
        
        mock_get.return_value.json.return_value = {
            'incidents': [
                {
                    'number': 'INC0012345',
                    'short_description': 'Database connectivity issue',
                    'sys_created_on': '2025-08-05T03:45:00'
                }
            ]
        }
        
        # Test each MCP endpoint
        mcp_endpoints = {
            'splunk': 'http://localhost:9080/splunk/search',
            'dynatrace': 'http://localhost:9081/dynatrace/metrics',
            'servicenow': 'http://localhost:9082/servicenow/incidents',
            'confluence': 'http://localhost:9083/confluence/search',
            'gitlab': 'http://localhost:9084/gitlab/search'
        }
        
        for service, endpoint in mcp_endpoints.items():
            print(f"Testing {service} MCP server...")
            
            if service == 'splunk':
                mock_post.assert_called()
            else:
                mock_get.assert_called()
            
            print(f"✓ {service} MCP integration verified")
    
    def test_comprehensive_scenario_validation(self):
        """Validate all comprehensive scenario data"""
        print("\n=== Validating Comprehensive Scenario Data ===")
        
        required_log_types = [
            'cloudtrail_events',
            'vpc_flow_logs', 
            'trusted_advisor_checks',
            'personal_health_dashboard_events'
        ]
        
        for scenario in self.ssm_scenarios:
            print(f"\nValidating: {scenario['name']}")
            
            # Check all required log types exist
            for log_type in required_log_types:
                self.assertIn(log_type, scenario, f"Missing {log_type} in {scenario['id']}")
            
            # Validate CloudTrail events
            ct_events = scenario['cloudtrail_events']
            self.assertTrue(len(ct_events) > 0)
            for event_group in ct_events:
                records = event_group.get('Records', [])
                for record in records:
                    self.assertIn('eventName', record)
                    self.assertIn('eventSource', record)
                    self.assertIn('eventTime', record)
            
            # Validate VPC Flow Logs
            flow_logs = scenario['vpc_flow_logs']
            for log in flow_logs:
                self.assertIn('action', log)
                self.assertIn('srcaddr', log)
                self.assertIn('dstaddr', log)
                self.assertIn('protocol', log)
            
            # Validate Personal Health Dashboard
            phd = scenario['personal_health_dashboard_events']
            self.assertIn('events', phd)
            for event in phd['events']:
                self.assertIn('arn', event)
                self.assertIn('service', event)
                self.assertIn('eventTypeCode', event)
            
            print(f"✓ All data validated for {scenario['name']}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
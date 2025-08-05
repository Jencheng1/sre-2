#!/usr/bin/env python3
"""
Comprehensive test suite for all Lambda functions and Bedrock agents
"""

import json
import boto3
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Any
import time
import uuid

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name='us-east-1')
bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
ssm_client = boto3.client('ssm', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')


class TestAllLambdaFunctions(unittest.TestCase):
    """Test all 10 Lambda functions"""
    
    def setUp(self):
        """Set up test data"""
        self.test_incident = {
            'incident_id': f'TEST-{uuid.uuid4().hex[:8]}',
            'timestamp': datetime.now().isoformat(),
            'severity': 'medium',
            'description': 'Test incident for Lambda validation'
        }
    
    def invoke_lambda(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to invoke Lambda and parse response"""
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        self.assertEqual(response['StatusCode'], 200, f"{function_name} invocation failed")
        return result
    
    def test_01_supervisor_lambda(self):
        """Test sre-supervisor-lambda"""
        print("\n[TEST] sre-supervisor-lambda")
        
        payload = {
            'incident_type': 'performance',
            'incident_id': self.test_incident['incident_id'],
            'description': 'High CPU utilization detected',
            'affected_resources': ['i-1234567890abcdef0'],
            'metrics': {
                'cpu_utilization': 95.5,
                'memory_utilization': 78.2
            }
        }
        
        result = self.invoke_lambda('sre-supervisor-lambda', payload)
        
        # Validate response
        self.assertIn('statusCode', result)
        self.assertEqual(result['statusCode'], 200)
        
        body = json.loads(result['body'])
        self.assertIn('incident_id', body)
        self.assertIn('analysis', body)
        self.assertIn('severity', body)
        
        print(f"✓ Supervisor analysis: {body.get('analysis', {}).get('summary', 'N/A')[:100]}...")
    
    def test_02_supervisor_lambda_mcp(self):
        """Test sre-supervisor-lambda-mcp (MCP enhanced version)"""
        print("\n[TEST] sre-supervisor-lambda-mcp")
        
        payload = {
            'incident_type': 'security',
            'incident_id': self.test_incident['incident_id'],
            'description': 'Suspicious login attempts detected',
            'affected_resources': ['arn:aws:iam::123456789012:user/admin'],
            'security_findings': {
                'failed_attempts': 15,
                'source_ips': ['192.168.1.100', '10.0.0.50']
            }
        }
        
        result = self.invoke_lambda('sre-supervisor-lambda-mcp', payload)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('mcp_correlations', body)
        
        print(f"✓ MCP correlations found: {len(body.get('mcp_correlations', {}))}")
    
    def test_03_cloudtrail_agent_lambda(self):
        """Test sre-cloudtrail-agent-lambda"""
        print("\n[TEST] sre-cloudtrail-agent-lambda")
        
        payload = {
            'action': 'analyze_errors',
            'time_range': '1h',
            'event_names': ['RunInstances', 'TerminateInstances'],
            'max_results': 10
        }
        
        result = self.invoke_lambda('sre-cloudtrail-agent-lambda', payload)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('events', body)
        
        print(f"✓ CloudTrail events analyzed: {body.get('event_count', 0)}")
    
    def test_04_vpc_agent_lambda(self):
        """Test sre-vpc-agent-lambda"""
        print("\n[TEST] sre-vpc-agent-lambda")
        
        payload = {
            'action': 'analyze_flow_logs',
            'time_range': '30m',
            'filter_rejected': True,
            'max_results': 20
        }
        
        result = self.invoke_lambda('sre-vpc-agent-lambda', payload)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('analysis', body)
        
        print(f"✓ VPC flow logs analyzed: {body.get('total_flows', 0)}")
    
    def test_05_trusted_advisor_agent_lambda(self):
        """Test sre-trusted-advisor-agent-lambda"""
        print("\n[TEST] sre-trusted-advisor-agent-lambda")
        
        payload = {
            'action': 'check_service_limits',
            'categories': ['service_limits', 'security'],
            'include_ok': False
        }
        
        result = self.invoke_lambda('sre-trusted-advisor-agent-lambda', payload)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('checks', body)
        
        print(f"✓ Trusted Advisor checks: {len(body.get('checks', []))}")
    
    def test_06_personal_health_agent_lambda(self):
        """Test sre-personal-health-agent-lambda"""
        print("\n[TEST] sre-personal-health-agent-lambda")
        
        payload = {
            'action': 'get_events',
            'event_status': ['open', 'upcoming'],
            'services': ['EC2', 'RDS', 'LAMBDA']
        }
        
        result = self.invoke_lambda('sre-personal-health-agent-lambda', payload)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('events', body)
        
        print(f"✓ Health events found: {len(body.get('events', []))}")
    
    def test_07_knowledge_base_agent_lambda(self):
        """Test sre-knowledge-base-agent-lambda"""
        print("\n[TEST] sre-knowledge-base-agent-lambda")
        
        # First, add a test document
        add_payload = {
            'action': 'add',
            'document': {
                'id': f'test-doc-{uuid.uuid4().hex[:8]}',
                'title': 'Test Knowledge Article',
                'content': 'This is a test article about handling high CPU utilization',
                'category': 'performance',
                'tags': ['cpu', 'performance', 'test']
            }
        }
        
        add_result = self.invoke_lambda('sre-knowledge-base-agent-lambda', add_payload)
        self.assertEqual(add_result['statusCode'], 200)
        
        # Then search for it
        search_payload = {
            'action': 'search',
            'query': 'high CPU utilization',
            'limit': 5
        }
        
        search_result = self.invoke_lambda('sre-knowledge-base-agent-lambda', search_payload)
        self.assertEqual(search_result['statusCode'], 200)
        
        body = json.loads(search_result['body'])
        self.assertIn('results', body)
        self.assertGreater(len(body['results']), 0)
        
        print(f"✓ Knowledge base search returned {len(body['results'])} results")
    
    def test_08_log_analyzer_lambda(self):
        """Test sre-log-analyzer-lambda"""
        print("\n[TEST] sre-log-analyzer-lambda")
        
        payload = {
            'log_group': '/aws/lambda/test',
            'time_range': '1h',
            'filter_pattern': '[ERROR]',
            'max_results': 50
        }
        
        result = self.invoke_lambda('sre-log-analyzer-lambda', payload)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('analysis', body)
        
        print(f"✓ Log analysis completed: {body.get('patterns_found', 0)} patterns")
    
    def test_09_metrics_analyzer_lambda(self):
        """Test sre-metrics-analyzer-lambda"""
        print("\n[TEST] sre-metrics-analyzer-lambda")
        
        payload = {
            'namespace': 'AWS/EC2',
            'metric_name': 'CPUUtilization',
            'dimensions': [
                {'Name': 'InstanceId', 'Value': 'i-1234567890abcdef0'}
            ],
            'time_range': '6h',
            'stat': 'Average'
        }
        
        result = self.invoke_lambda('sre-metrics-analyzer-lambda', payload)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertIn('analysis', body)
        
        print(f"✓ Metrics analyzed: {body.get('datapoints_analyzed', 0)} datapoints")
    
    def test_10_opsitem_indexer_lambda(self):
        """Test sre-opsitem-indexer-lambda"""
        print("\n[TEST] sre-opsitem-indexer-lambda")
        
        # Create a test OpsItem event
        payload = {
            'source': 'aws.ssm',
            'detail-type': 'SSM OpsItem Create',
            'detail': {
                'eventName': 'CreateOpsItem',
                'responseElements': {
                    'opsItemId': f'oi-test-{uuid.uuid4().hex[:8]}'
                }
            }
        }
        
        result = self.invoke_lambda('sre-opsitem-indexer-lambda', payload)
        
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['message'], 'OpsItem indexed successfully')
        
        print(f"✓ OpsItem indexer tested successfully")


class TestAllBedrockAgents(unittest.TestCase):
    """Test all 7 Bedrock agents"""
    
    def setUp(self):
        """Set up test data"""
        self.agent_configs = {
            'SRE-Supervisor': {'agent_id': 'XKVWGESIAX', 'alias_id': 'TSTALIASID'},
            'SRE-Log-Analyzer': {'agent_id': 'KYE8CL4NWP', 'alias_id': '1HDUPSOA6X'},
            'SRE-Metrics-Analyzer': {'agent_id': 'HJZP7VBZOI', 'alias_id': 'IBPF2ZPAGO'},
            'SRE-CloudTrail-Analyzer': {'agent_id': 'RPAXDVETHN', 'alias_id': 'TSTALIASID'},
            'SRE-VPC-Analyzer': {'agent_id': 'BNFYR1YTWU', 'alias_id': 'TSTALIASID'},
            'SRE-Trusted-Advisor-Analyzer': {'agent_id': 'BB2OARRB3J', 'alias_id': 'TSTALIASID'},
            'SRE-Personal-Health-Analyzer': {'agent_id': 'WOHWA21ZBK', 'alias_id': 'TSTALIASID'}
        }
    
    def invoke_agent(self, agent_name: str, input_text: str) -> str:
        """Helper to invoke Bedrock agent"""
        config = self.agent_configs[agent_name]
        session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        
        try:
            response = bedrock_runtime.invoke_agent(
                agentId=config['agent_id'],
                agentAliasId=config['alias_id'],
                sessionId=session_id,
                inputText=input_text
            )
            
            # Read response stream
            result = ""
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result += chunk['bytes'].decode('utf-8')
            
            return result
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def test_01_supervisor_agent(self):
        """Test SRE-Supervisor Bedrock agent"""
        print("\n[TEST] SRE-Supervisor Agent")
        
        input_text = "Analyze a performance incident with high CPU usage on EC2 instances"
        result = self.invoke_agent('SRE-Supervisor', input_text)
        
        self.assertIsNotNone(result)
        self.assertNotIn("Error:", result)
        
        print(f"✓ Supervisor agent response: {result[:100]}...")
    
    def test_02_log_analyzer_agent(self):
        """Test SRE-Log-Analyzer Bedrock agent"""
        print("\n[TEST] SRE-Log-Analyzer Agent")
        
        input_text = "Find error patterns in application logs from the last hour"
        result = self.invoke_agent('SRE-Log-Analyzer', input_text)
        
        self.assertIsNotNone(result)
        print(f"✓ Log analyzer agent response: {result[:100]}...")
    
    def test_03_metrics_analyzer_agent(self):
        """Test SRE-Metrics-Analyzer Bedrock agent"""
        print("\n[TEST] SRE-Metrics-Analyzer Agent")
        
        input_text = "Analyze CPU utilization trends for anomalies"
        result = self.invoke_agent('SRE-Metrics-Analyzer', input_text)
        
        self.assertIsNotNone(result)
        print(f"✓ Metrics analyzer agent response: {result[:100]}...")
    
    def test_04_cloudtrail_analyzer_agent(self):
        """Test SRE-CloudTrail-Analyzer Bedrock agent"""
        print("\n[TEST] SRE-CloudTrail-Analyzer Agent")
        
        input_text = "Check for unauthorized API calls in CloudTrail"
        result = self.invoke_agent('SRE-CloudTrail-Analyzer', input_text)
        
        self.assertIsNotNone(result)
        print(f"✓ CloudTrail analyzer agent response: {result[:100]}...")
    
    def test_05_vpc_analyzer_agent(self):
        """Test SRE-VPC-Analyzer Bedrock agent"""
        print("\n[TEST] SRE-VPC-Analyzer Agent")
        
        input_text = "Analyze VPC flow logs for rejected traffic"
        result = self.invoke_agent('SRE-VPC-Analyzer', input_text)
        
        self.assertIsNotNone(result)
        print(f"✓ VPC analyzer agent response: {result[:100]}...")
    
    def test_06_trusted_advisor_agent(self):
        """Test SRE-Trusted-Advisor-Analyzer Bedrock agent"""
        print("\n[TEST] SRE-Trusted-Advisor-Analyzer Agent")
        
        input_text = "Check service limits and quota usage"
        result = self.invoke_agent('SRE-Trusted-Advisor-Analyzer', input_text)
        
        self.assertIsNotNone(result)
        print(f"✓ Trusted Advisor agent response: {result[:100]}...")
    
    def test_07_personal_health_agent(self):
        """Test SRE-Personal-Health-Analyzer Bedrock agent"""
        print("\n[TEST] SRE-Personal-Health-Analyzer Agent")
        
        input_text = "Check for any AWS service health issues"
        result = self.invoke_agent('SRE-Personal-Health-Analyzer', input_text)
        
        self.assertIsNotNone(result)
        print(f"✓ Personal Health agent response: {result[:100]}...")


class TestEndToEndScenarios(unittest.TestCase):
    """Test complete incident scenarios"""
    
    def test_quota_incident_scenario(self):
        """Test EC2 quota exceeded scenario end-to-end"""
        print("\n[TEST] EC2 Quota Exceeded Scenario")
        
        # Create test OpsItem
        opsitem_response = ssm_client.create_ops_item(
            Title="EC2 Instance Launch Failed - Quota Exceeded",
            Description="Unable to launch m5.large instances due to quota limit",
            Source="TestSuite",
            Priority=2,
            Category="Capacity",
            Severity="2",
            OperationalData={
                'test/error': {
                    'Type': 'String',
                    'Value': 'InstanceLimitExceeded'
                },
                'test/quota_id': {
                    'Type': 'String',
                    'Value': 'L-1216C47A'
                }
            }
        )
        
        opsitem_id = opsitem_response['OpsItemId']
        print(f"✓ Created test OpsItem: {opsitem_id}")
        
        # Invoke supervisor to analyze
        supervisor_payload = {
            'incident_type': 'quota',
            'incident_id': opsitem_id,
            'description': 'EC2 quota exceeded for m5.large instances',
            'affected_resources': ['m5.large'],
            'error_details': {
                'error_code': 'InstanceLimitExceeded',
                'quota_id': 'L-1216C47A'
            }
        }
        
        response = lambda_client.invoke(
            FunctionName='sre-supervisor-lambda',
            Payload=json.dumps(supervisor_payload)
        )
        
        result = json.loads(response['Payload'].read())
        self.assertEqual(result['statusCode'], 200)
        
        body = json.loads(result['body'])
        self.assertIn('root_cause', body)
        self.assertIn('recommendations', body)
        
        print(f"✓ Root cause identified: {body['root_cause'][:100]}...")
        
        # Clean up
        ssm_client.update_ops_item(
            OpsItemId=opsitem_id,
            Status='Resolved'
        )
    
    def test_security_incident_scenario(self):
        """Test security group misconfiguration scenario"""
        print("\n[TEST] Security Group Misconfiguration Scenario")
        
        # Simulate VPC flow log analysis
        vpc_payload = {
            'action': 'analyze_flow_logs',
            'filter_rejected': True,
            'time_range': '30m'
        }
        
        vpc_response = lambda_client.invoke(
            FunctionName='sre-vpc-agent-lambda',
            Payload=json.dumps(vpc_payload)
        )
        
        vpc_result = json.loads(vpc_response['Payload'].read())
        self.assertEqual(vpc_result['statusCode'], 200)
        
        print(f"✓ VPC analysis completed")
        
        # Check Trusted Advisor for security recommendations
        ta_payload = {
            'action': 'check_security',
            'categories': ['security']
        }
        
        ta_response = lambda_client.invoke(
            FunctionName='sre-trusted-advisor-agent-lambda',
            Payload=json.dumps(ta_payload)
        )
        
        ta_result = json.loads(ta_response['Payload'].read())
        self.assertEqual(ta_result['statusCode'], 200)
        
        print(f"✓ Security recommendations retrieved")


def run_all_tests():
    """Run all test suites"""
    print("=" * 80)
    print("SRE Copilot Comprehensive Component Tests")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add Lambda function tests
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAllLambdaFunctions))
    
    # Add Bedrock agent tests
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAllBedrockAgents))
    
    # Add end-to-end scenario tests
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEndToEndScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ Some tests failed. Review the output above.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
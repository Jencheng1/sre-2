#!/usr/bin/env python3
"""
SRE Copilot Infrastructure End-to-End Test
Tests all components of the SRE system including:
- Lambda function invocations
- Bedrock agent interactions
- Knowledge base queries
- Root cause analysis workflow
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

class SREInfrastructureTester:
    def __init__(self):
        self.region = 'us-east-1'
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        self.logs_client = boto3.client('logs', region_name=self.region)
        
        # Test results
        self.test_results = {
            'lambda_tests': {},
            'agent_tests': {},
            'integration_tests': {},
            'timestamp': datetime.now().isoformat()
        }
    
    def print_header(self, text: str):
        print(f"\n{'='*80}")
        print(f"{text:^80}")
        print(f"{'='*80}\n")
    
    def test_lambda_function(self, function_name: str, payload: Dict) -> Dict:
        """Test individual Lambda function"""
        try:
            print(f"Testing Lambda: {function_name}")
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            status_code = response['StatusCode']
            
            # Read response payload
            response_payload = json.loads(response['Payload'].read())
            
            if status_code == 200 and 'FunctionError' not in response:
                print(f"✓ {function_name} - SUCCESS")
                return {
                    'success': True,
                    'status_code': status_code,
                    'response': response_payload
                }
            else:
                print(f"✗ {function_name} - FAILED")
                return {
                    'success': False,
                    'status_code': status_code,
                    'error': response.get('FunctionError', 'Unknown error'),
                    'response': response_payload
                }
                
        except Exception as e:
            print(f"✗ {function_name} - ERROR: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_all_lambda_functions(self):
        """Test all Lambda functions"""
        self.print_header("Testing Lambda Functions")
        
        # Define test payloads for each function
        lambda_tests = [
            {
                'name': 'sre-supervisor-lambda',
                'payload': {
                    'action': 'test',
                    'message': 'Infrastructure validation test'
                }
            },
            {
                'name': 'sre-cloudtrail-agent-lambda',
                'payload': {
                    'action': 'analyze',
                    'query': 'recent API calls',
                    'timeRange': {
                        'start': (datetime.now() - timedelta(hours=1)).isoformat(),
                        'end': datetime.now().isoformat()
                    }
                }
            },
            {
                'name': 'sre-vpc-agent-lambda',
                'payload': {
                    'action': 'analyze_vpc',
                    'vpc_id': 'vpc-default'
                }
            },
            {
                'name': 'sre-cloudwatch-logs-agent-lambda',
                'payload': {
                    'action': 'analyze_logs',
                    'log_group': '/aws/lambda/sre-supervisor-lambda',
                    'timeRange': {
                        'start': (datetime.now() - timedelta(hours=1)).isoformat(),
                        'end': datetime.now().isoformat()
                    }
                }
            },
            {
                'name': 'sre-log-analyzer-lambda',
                'payload': {
                    'log_group': '/aws/lambda/sre-supervisor-lambda',
                    'pattern': 'ERROR',
                    'hours': 1
                }
            },
            {
                'name': 'sre-metrics-analyzer-lambda',
                'payload': {
                    'namespace': 'AWS/Lambda',
                    'metric_name': 'Invocations',
                    'hours': 1
                }
            },
            {
                'name': 'sre-knowledge-base-agent-lambda',
                'payload': {
                    'action': 'search',
                    'query': 'high CPU usage',
                    'limit': 5
                }
            }
        ]
        
        for test in lambda_tests:
            result = self.test_lambda_function(test['name'], test['payload'])
            self.test_results['lambda_tests'][test['name']] = result
            time.sleep(1)  # Avoid throttling
    
    def test_bedrock_agent(self, agent_name: str, agent_id: str, query: str) -> Dict:
        """Test Bedrock agent interaction"""
        try:
            print(f"Testing Bedrock Agent: {agent_name}")
            
            # Invoke agent
            response = self.bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId='TSTALIASID',  # Use test alias
                sessionId=f'test-session-{int(time.time())}',
                inputText=query
            )
            
            # Collect response chunks
            completion = ""
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
            
            if completion:
                print(f"✓ {agent_name} - SUCCESS")
                return {
                    'success': True,
                    'response': completion[:200] + '...' if len(completion) > 200 else completion
                }
            else:
                print(f"✗ {agent_name} - No response")
                return {
                    'success': False,
                    'error': 'No response from agent'
                }
                
        except Exception as e:
            print(f"✗ {agent_name} - ERROR: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_all_bedrock_agents(self):
        """Test all Bedrock agents"""
        self.print_header("Testing Bedrock Agents")
        
        # Get list of agents
        try:
            agents_response = self.bedrock_agent.list_agents()
            agents = agents_response.get('agentSummaries', [])
            
            # Filter SRE agents
            sre_agents = [agent for agent in agents if agent['agentName'].startswith('SRE-')]
            
            test_queries = {
                'SRE-Supervisor': 'What is the current system status?',
                'SRE-CloudTrail-Analyzer': 'Show me recent API activity',
                'SRE-Personal-Health-Analyzer': 'Are there any AWS service issues?',
                'SRE-Trusted-Advisor-Analyzer': 'What are the current recommendations?',
                'SRE-Metrics-Analyzer': 'Show recent CloudWatch metrics',
                'SRE-Log-Analyzer': 'Find recent errors in logs'
            }
            
            for agent in sre_agents:
                agent_name = agent['agentName']
                agent_id = agent['agentId']
                
                if agent['agentStatus'] == 'PREPARED':
                    query = test_queries.get(agent_name, 'Test query')
                    result = self.test_bedrock_agent(agent_name, agent_id, query)
                    self.test_results['agent_tests'][agent_name] = result
                else:
                    print(f"⚠ {agent_name} - Not PREPARED (Status: {agent['agentStatus']})")
                    self.test_results['agent_tests'][agent_name] = {
                        'success': False,
                        'error': f"Agent not prepared: {agent['agentStatus']}"
                    }
                
                time.sleep(2)  # Avoid throttling
                
        except Exception as e:
            print(f"Error testing Bedrock agents: {str(e)}")
            self.test_results['agent_tests']['error'] = str(e)
    
    def test_integration_workflow(self):
        """Test end-to-end integration workflow"""
        self.print_header("Testing Integration Workflow")
        
        try:
            # 1. Create a test OpsItem
            print("1. Creating test OpsItem...")
            ops_item_response = self.ssm_client.create_ops_item(
                Title="Test Infrastructure Validation",
                Description="Automated test for SRE infrastructure validation",
                Source="test-script",
                Severity="3",
                Category="Test",
                Tags=[
                    {'Key': 'Environment', 'Value': 'test'},
                    {'Key': 'CreatedBy', 'Value': 'infrastructure-validator'}
                ]
            )
            ops_item_id = ops_item_response['OpsItemId']
            print(f"   Created OpsItem: {ops_item_id}")
            
            # 2. Test supervisor Lambda with incident
            print("\n2. Testing supervisor analysis...")
            supervisor_result = self.test_lambda_function(
                'sre-supervisor-lambda',
                {
                    'action': 'analyze',
                    'incident_description': 'Test incident: High CPU usage on production servers',
                    'ops_item_id': ops_item_id
                }
            )
            
            # 3. Test knowledge base search
            print("\n3. Testing knowledge base search...")
            kb_result = self.test_lambda_function(
                'sre-knowledge-base-agent-lambda',
                {
                    'action': 'search',
                    'query': 'high CPU usage production',
                    'category': 'incident'
                }
            )
            
            # 4. Test CloudWatch logs analysis
            print("\n4. Testing CloudWatch logs analysis...")
            logs_result = self.test_lambda_function(
                'sre-cloudwatch-logs-agent-lambda',
                {
                    'action': 'analyze',
                    'log_groups': ['/aws/lambda/sre-supervisor-lambda'],
                    'filter_pattern': 'ERROR',
                    'time_range': {
                        'start': (datetime.now() - timedelta(hours=1)).isoformat(),
                        'end': datetime.now().isoformat()
                    }
                }
            )
            
            # Store integration test results
            self.test_results['integration_tests'] = {
                'ops_item_creation': {'success': True, 'ops_item_id': ops_item_id},
                'supervisor_analysis': supervisor_result,
                'knowledge_base_search': kb_result,
                'logs_analysis': logs_result
            }
            
            print("\n✓ Integration workflow completed")
            
        except Exception as e:
            print(f"\n✗ Integration workflow failed: {str(e)}")
            self.test_results['integration_tests'] = {
                'success': False,
                'error': str(e)
            }
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        self.print_header("Test Results Summary")
        
        # Lambda tests summary
        lambda_success = sum(1 for r in self.test_results['lambda_tests'].values() if r.get('success', False))
        lambda_total = len(self.test_results['lambda_tests'])
        print(f"Lambda Functions: {lambda_success}/{lambda_total} passed")
        
        # Bedrock agents summary
        agent_success = sum(1 for r in self.test_results['agent_tests'].values() if r.get('success', False))
        agent_total = len(self.test_results['agent_tests'])
        print(f"Bedrock Agents: {agent_success}/{agent_total} passed")
        
        # Integration tests summary
        integration_success = all(
            r.get('success', False) 
            for r in self.test_results['integration_tests'].values() 
            if isinstance(r, dict)
        )
        print(f"Integration Tests: {'PASSED' if integration_success else 'FAILED'}")
        
        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        # Overall status
        overall_success = (
            lambda_success == lambda_total and
            agent_success > 0 and
            integration_success
        )
        
        return overall_success
    
    def run_all_tests(self):
        """Run all infrastructure tests"""
        print("SRE Copilot Infrastructure Test Suite")
        print(f"Region: {self.region}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run test suites
        self.test_all_lambda_functions()
        self.test_all_bedrock_agents()
        self.test_integration_workflow()
        
        # Generate report
        success = self.generate_test_report()
        
        print("\n" + "="*80)
        if success:
            print("✓ All infrastructure tests PASSED")
        else:
            print("✗ Some infrastructure tests FAILED - Review the report for details")
        print("="*80)
        
        return success


def main():
    tester = SREInfrastructureTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
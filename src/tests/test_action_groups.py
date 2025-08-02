#!/usr/bin/env python3
import json
import boto3
import pytest
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-agent-runtime')
lambda_client = boto3.client('lambda')

class TestActionGroups:
    @pytest.fixture(scope="class")
    def config(self):
        """Load the SRE Copilot configuration file."""
        with open('sre_copilot_config.json', 'r') as f:
            return json.load(f)
    
    @pytest.fixture(scope="class")
    def test_params(self):
        """Set up test parameters."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        return {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'max_results': 10
        }
    
    def test_cloudtrail_action_group(self, config, test_params):
        """Test the CloudTrail agent action group."""
        if 'cloudtrail_agent' not in config:
            pytest.skip("CloudTrail agent not configured")
        
        agent_id = config['cloudtrail_agent']['id']
        
        # Test get_api_errors action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_api_errors',
                'max_results': test_params['max_results'],
                'start_time': test_params['start_time'],
                'end_time': test_params['end_time']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
        
        # Test get_security_events action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_security_events',
                'max_results': test_params['max_results'],
                'start_time': test_params['start_time'],
                'end_time': test_params['end_time']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
        
        # Test get_compliance_events action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_compliance_events',
                'max_results': test_params['max_results'],
                'start_time': test_params['start_time'],
                'end_time': test_params['end_time']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
    
    def test_vpc_action_group(self, config, test_params):
        """Test the VPC agent action group."""
        if 'vpc_agent' not in config:
            pytest.skip("VPC agent not configured")
        
        agent_id = config['vpc_agent']['id']
        
        # Test analyze_flow_logs action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'analyze_flow_logs',
                'max_results': test_params['max_results'],
                'start_time': test_params['start_time'],
                'end_time': test_params['end_time']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
        
        # Test get_rejected_traffic action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_rejected_traffic',
                'max_results': test_params['max_results'],
                'start_time': test_params['start_time'],
                'end_time': test_params['end_time']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
        
        # Test get_security_group_changes action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_security_group_changes',
                'max_results': test_params['max_results'],
                'start_time': test_params['start_time'],
                'end_time': test_params['end_time']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
    
    def test_trusted_advisor_action_group(self, config, test_params):
        """Test the Trusted Advisor agent action group."""
        if 'trusted_advisor_agent' not in config:
            pytest.skip("Trusted Advisor agent not configured")
        
        agent_id = config['trusted_advisor_agent']['id']
        
        # Test get_service_quotas action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_service_quotas',
                'max_results': test_params['max_results']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
        
        # Test get_security_checks action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_security_checks',
                'max_results': test_params['max_results']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
        
        # Test get_cost_optimization action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_cost_optimization',
                'max_results': test_params['max_results']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
    
    def test_personal_health_action_group(self, config, test_params):
        """Test the Personal Health agent action group."""
        if 'personal_health_agent' not in config:
            pytest.skip("Personal Health agent not configured")
        
        agent_id = config['personal_health_agent']['id']
        
        # Test get_maintenance_events action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_maintenance_events',
                'max_results': test_params['max_results'],
                'start_time': test_params['start_time'],
                'end_time': test_params['end_time']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
        
        # Test get_service_issues action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_service_issues',
                'max_results': test_params['max_results'],
                'start_time': test_params['start_time'],
                'end_time': test_params['end_time']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body
        
        # Test get_account_notifications action
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',
            sessionId='test-session',
            inputText=json.dumps({
                'action': 'get_account_notifications',
                'max_results': test_params['max_results'],
                'start_time': test_params['start_time'],
                'end_time': test_params['end_time']
            })
        )
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'results' in body
        assert 'analysis' in body 
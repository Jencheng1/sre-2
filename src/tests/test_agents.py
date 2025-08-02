import boto3
import json
import logging
import pytest
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestSRECopilotAgents:
    def setup_method(self):
        """Set up test environment."""
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        self.lambda_client = boto3.client('lambda')
        
        # Load agent IDs from config
        with open('sre_copilot_config.json', 'r') as f:
            self.config = json.load(f)
            
        # Set up test parameters
        self.end_time = datetime.utcnow()
        self.start_time = self.end_time - timedelta(hours=24)
        self.max_results = 10

    def test_cloudtrail_agent(self):
        """Test CloudTrail agent functionality."""
        logger.info("Testing CloudTrail agent...")
        
        # Test API errors endpoint
        response = self.lambda_client.invoke(
            FunctionName='cloudtrail-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_api_errors',
                'max_results': self.max_results,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'api_errors' in result['body']
        
        # Test security events endpoint
        response = self.lambda_client.invoke(
            FunctionName='cloudtrail-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_security_events',
                'max_results': self.max_results,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'security_events' in result['body']
        
        # Test compliance events endpoint
        response = self.lambda_client.invoke(
            FunctionName='cloudtrail-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_compliance_events',
                'max_results': self.max_results,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'compliance_events' in result['body']

    def test_vpc_agent(self):
        """Test VPC agent functionality."""
        logger.info("Testing VPC agent...")
        
        # Test flow logs analysis endpoint
        response = self.lambda_client.invoke(
            FunctionName='vpc-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'analyze_flow_logs',
                'log_group': '/aws/vpc/flow-logs',
                'time_range': '24h',
                'max_results': self.max_results
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'flow_logs' in result['body']
        
        # Test rejected traffic endpoint
        response = self.lambda_client.invoke(
            FunctionName='vpc-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_rejected_traffic',
                'log_group': '/aws/vpc/flow-logs',
                'time_range': '24h',
                'max_results': self.max_results
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'rejected_traffic' in result['body']
        
        # Test security group changes endpoint
        response = self.lambda_client.invoke(
            FunctionName='vpc-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_security_group_changes',
                'max_results': self.max_results
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'security_group_issues' in result['body']

    def test_trusted_advisor_agent(self):
        """Test Trusted Advisor agent functionality."""
        logger.info("Testing Trusted Advisor agent...")
        
        # Test service quotas endpoint
        response = self.lambda_client.invoke(
            FunctionName='trusted-advisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_service_quotas',
                'max_results': self.max_results
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'service_quotas' in result['body']
        
        # Test security checks endpoint
        response = self.lambda_client.invoke(
            FunctionName='trusted-advisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_security_checks',
                'max_results': self.max_results
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'security_checks' in result['body']
        
        # Test cost optimization endpoint
        response = self.lambda_client.invoke(
            FunctionName='trusted-advisor-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_cost_optimization',
                'max_results': self.max_results
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'cost_optimization' in result['body']

    def test_personal_health_agent(self):
        """Test Personal Health agent functionality."""
        logger.info("Testing Personal Health agent...")
        
        # Test maintenance events endpoint
        response = self.lambda_client.invoke(
            FunctionName='personal-health-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_maintenance_events',
                'max_results': self.max_results,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'maintenance_events' in result['body']
        
        # Test service issues endpoint
        response = self.lambda_client.invoke(
            FunctionName='personal-health-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_service_issues',
                'max_results': self.max_results,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'service_issues' in result['body']
        
        # Test account notifications endpoint
        response = self.lambda_client.invoke(
            FunctionName='personal-health-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_account_notifications',
                'max_results': self.max_results,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            })
        )
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'account_notifications' in result['body']

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 
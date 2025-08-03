#!/usr/bin/env python3
"""
Update Lambda environment variables with alternate MCP ports
"""

import boto3
import json

# Load alternate ports
with open('mcp_ports.json', 'r') as f:
    MCP_PORTS = json.load(f)

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

# Update environment variables
env_vars = {
    'MCP_ENABLED': 'true',
    'KB_ENABLED': 'true',
    'SPLUNK_ENDPOINT': f'http://localhost:{MCP_PORTS["splunk"]}/splunk',
    'DYNATRACE_ENDPOINT': f'http://localhost:{MCP_PORTS["dynatrace"]}/dynatrace',
    'SERVICENOW_ENDPOINT': f'http://localhost:{MCP_PORTS["servicenow"]}/servicenow',
    'CONFLUENCE_ENDPOINT': f'http://localhost:{MCP_PORTS["confluence"]}/confluence',
    'GITLAB_ENDPOINT': f'http://localhost:{MCP_PORTS["gitlab"]}/gitlab'
}

try:
    # Get current configuration
    response = lambda_client.get_function_configuration(
        FunctionName='sre-supervisor-lambda-mcp'
    )
    
    # Update environment variables
    current_env = response.get('Environment', {}).get('Variables', {})
    current_env.update(env_vars)
    
    # Update Lambda function
    lambda_client.update_function_configuration(
        FunctionName='sre-supervisor-lambda-mcp',
        Environment={'Variables': current_env}
    )
    
    print("✓ Updated Lambda environment variables with new MCP ports:")
    for key, value in env_vars.items():
        print(f"  {key}: {value}")
    
except Exception as e:
    print(f"✗ Failed to update Lambda configuration: {e}")

# Also update SSM parameters for configuration
ssm_client = boto3.client('ssm', region_name='us-east-1')

# Update MCP server configurations in SSM
mcp_configs = {
    'splunk': {
        'endpoint': f'http://localhost:{MCP_PORTS["splunk"]}/splunk',
        'enabled': True,
        'test_mode': True
    },
    'dynatrace': {
        'endpoint': f'http://localhost:{MCP_PORTS["dynatrace"]}/dynatrace',
        'enabled': True,
        'test_mode': True
    },
    'servicenow': {
        'endpoint': f'http://localhost:{MCP_PORTS["servicenow"]}/servicenow',
        'enabled': True,
        'test_mode': True
    },
    'confluence': {
        'endpoint': f'http://localhost:{MCP_PORTS["confluence"]}/confluence',
        'enabled': True,
        'test_mode': True
    },
    'gitlab': {
        'endpoint': f'http://localhost:{MCP_PORTS["gitlab"]}/gitlab',
        'enabled': True,
        'test_mode': True
    }
}

for service, config in mcp_configs.items():
    try:
        ssm_client.put_parameter(
            Name=f'/sre-copilot/mcp/{service}/config',
            Value=json.dumps(config),
            Type='String',
            Overwrite=True
        )
        print(f"✓ Updated SSM config for {service}")
    except Exception as e:
        print(f"✗ Failed to update SSM config for {service}: {e}")
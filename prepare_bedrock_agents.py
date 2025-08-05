#!/usr/bin/env python3
"""
Prepare Bedrock agents and create missing action groups
"""

import boto3
import json
import time
from typing import Dict, List

# Initialize clients
bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
iam = boto3.client('iam')

# Agent IDs that need preparation
agents_to_prepare = {
    'SRE-VPC-Analyzer': {
        'agent_id': 'BNFYR1YTWU',
        'lambda_function': 'sre-vpc-agent-lambda',
        'action_group_name': 'vpc-analysis-actions',
        'description': 'Analyzes VPC Flow Logs for network issues'
    },
    'SRE-Trusted-Advisor-Analyzer': {
        'agent_id': 'BB2OARRB3J',
        'lambda_function': 'sre-trusted-advisor-agent-lambda',
        'action_group_name': 'trusted-advisor-actions',
        'description': 'Analyzes Trusted Advisor recommendations'
    },
    'SRE-Personal-Health-Analyzer': {
        'agent_id': 'WOHWA21ZBK',
        'lambda_function': 'sre-personal-health-agent-lambda',
        'action_group_name': 'personal-health-actions',
        'description': 'Analyzes Personal Health Dashboard events'
    }
}

def create_action_group(agent_id: str, agent_name: str, action_group_name: str, 
                       lambda_function: str, description: str):
    """Create an action group for a Bedrock agent"""
    try:
        # Get Lambda function ARN
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        lambda_info = lambda_client.get_function(FunctionName=lambda_function)
        lambda_arn = lambda_info['Configuration']['FunctionArn']
        
        print(f"Creating action group '{action_group_name}' for {agent_name}...")
        
        # Create action group
        response = bedrock_agent.create_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupName=action_group_name,
            description=description,
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            apiSchema={
                'payload': json.dumps({
                    "openapi": "3.0.0",
                    "info": {
                        "title": f"{agent_name} API",
                        "version": "1.0.0",
                        "description": description
                    },
                    "paths": {
                        "/analyze": {
                            "post": {
                                "summary": "Analyze data",
                                "description": f"Analyze data for {agent_name}",
                                "operationId": "analyze",
                                "requestBody": {
                                    "required": True,
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "action": {
                                                        "type": "string",
                                                        "description": "The action to perform"
                                                    },
                                                    "parameters": {
                                                        "type": "object",
                                                        "description": "Parameters for the action"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                "responses": {
                                    "200": {
                                        "description": "Successful response",
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "object"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                })
            }
        )
        
        print(f"✓ Created action group: {response['agentActionGroup']['actionGroupId']}")
        
        # Add Lambda permission for Bedrock to invoke
        try:
            lambda_client.add_permission(
                FunctionName=lambda_function,
                StatementId=f'AllowBedrockInvoke-{agent_id}',
                Action='lambda:InvokeFunction',
                Principal='bedrock.amazonaws.com',
                SourceArn=f"arn:aws:bedrock:us-east-1:*:agent/{agent_id}"
            )
            print(f"✓ Added Lambda permission for {lambda_function}")
        except lambda_client.exceptions.ResourceConflictException:
            print(f"ℹ Lambda permission already exists for {lambda_function}")
        
        return response['agentActionGroup']['actionGroupId']
        
    except Exception as e:
        print(f"✗ Error creating action group: {str(e)}")
        return None

def prepare_agent(agent_id: str, agent_name: str):
    """Prepare a Bedrock agent"""
    try:
        print(f"\nPreparing agent {agent_name} ({agent_id})...")
        
        # Get current agent status
        agent_info = bedrock_agent.get_agent(agentId=agent_id)
        current_status = agent_info['agent']['agentStatus']
        
        print(f"Current status: {current_status}")
        
        if current_status == 'PREPARED':
            print(f"✓ Agent already prepared")
            return True
        
        # Prepare the agent
        response = bedrock_agent.prepare_agent(agentId=agent_id)
        print(f"Preparation initiated...")
        
        # Wait for preparation to complete
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(5)
            agent_info = bedrock_agent.get_agent(agentId=agent_id)
            status = agent_info['agent']['agentStatus']
            
            if status == 'PREPARED':
                print(f"✓ Agent prepared successfully")
                return True
            elif status == 'FAILED':
                print(f"✗ Agent preparation failed")
                return False
            else:
                print(f"  Status: {status} (attempt {attempt + 1}/{max_attempts})")
        
        print(f"✗ Timeout waiting for agent preparation")
        return False
        
    except Exception as e:
        print(f"✗ Error preparing agent: {str(e)}")
        return False

def create_agent_alias(agent_id: str, agent_name: str):
    """Create an alias for the agent"""
    try:
        print(f"Creating alias for {agent_name}...")
        
        # Check if alias already exists
        aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)
        
        if aliases['agentAliasSummaries']:
            print(f"✓ Alias already exists: {aliases['agentAliasSummaries'][0]['agentAliasId']}")
            return aliases['agentAliasSummaries'][0]['agentAliasId']
        
        # Create new alias
        response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName='latest',
            description=f'Latest version of {agent_name}'
        )
        
        alias_id = response['agentAlias']['agentAliasId']
        print(f"✓ Created alias: {alias_id}")
        return alias_id
        
    except Exception as e:
        print(f"✗ Error creating alias: {str(e)}")
        return None

def main():
    """Main function to prepare all agents"""
    print("Preparing Bedrock Agents and Creating Action Groups")
    print("=" * 60)
    
    success_count = 0
    total_count = len(agents_to_prepare)
    
    for agent_name, agent_config in agents_to_prepare.items():
        print(f"\n{agent_name}")
        print("-" * 40)
        
        agent_id = agent_config['agent_id']
        
        # Create action group if missing
        action_group_id = create_action_group(
            agent_id=agent_id,
            agent_name=agent_name,
            action_group_name=agent_config['action_group_name'],
            lambda_function=agent_config['lambda_function'],
            description=agent_config['description']
        )
        
        # Prepare the agent
        if prepare_agent(agent_id, agent_name):
            # Create alias
            alias_id = create_agent_alias(agent_id, agent_name)
            if alias_id:
                success_count += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: {success_count}/{total_count} agents prepared successfully")
    
    if success_count == total_count:
        print("✓ All agents are now prepared and ready!")
    else:
        print("⚠ Some agents failed to prepare. Check the errors above.")

if __name__ == '__main__':
    main()
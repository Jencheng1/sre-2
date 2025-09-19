#!/usr/bin/env python3
"""
Configure Bedrock Agents and Action Groups
This script ensures all Bedrock agents are properly configured with their action groups
"""

import boto3
import json
import time
from typing import Dict, List
from botocore.exceptions import ClientError

class BedrockAgentConfigurator:
    def __init__(self):
        self.region = 'us-east-1'
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        
        # Define agent configurations
        self.agent_configs = [
            {
                'name': 'SRE-Supervisor',
                'description': 'Main supervisor agent that orchestrates root cause analysis',
                'lambda_function': 'sre-supervisor-lambda',
                'action_group_name': 'supervisor-actions',
                'action_group_description': 'Actions for orchestrating RCA analysis',
                'instructions': '''You are an SRE supervisor agent that orchestrates root cause analysis for incidents. 
                Your role is to coordinate with other specialized agents to analyze various AWS services and provide 
                comprehensive incident analysis.'''
            },
            {
                'name': 'SRE-CloudTrail-Analyzer',
                'description': 'Analyzes CloudTrail events for security and API activity',
                'lambda_function': 'sre-cloudtrail-agent-lambda',
                'action_group_name': 'cloudtrail-analysis-actions',
                'action_group_description': 'Actions for analyzing CloudTrail events',
                'instructions': '''You are a CloudTrail analysis agent. Analyze AWS CloudTrail logs to identify:
                - Unusual API calls or access patterns
                - Security events and unauthorized access attempts
                - Configuration changes that might impact services
                - User activity patterns'''
            },
            {
                'name': 'SRE-VPC-Analyzer',
                'description': 'Analyzes VPC configurations and network issues',
                'lambda_function': 'sre-vpc-agent-lambda',
                'action_group_name': 'vpc-analysis-actions',
                'action_group_description': 'Actions for analyzing VPC configurations',
                'instructions': '''You are a VPC analysis agent. Analyze VPC configurations to identify:
                - Security group misconfigurations
                - Network ACL issues
                - Route table problems
                - VPC peering and connectivity issues'''
            },
            {
                'name': 'SRE-VPC-Flow-Logs-Analyzer',
                'description': 'Analyzes VPC Flow Logs for network traffic patterns',
                'lambda_function': 'sre-vpc-flow-logs-agent-lambda',
                'action_group_name': 'vpc-flow-logs-actions',
                'action_group_description': 'Actions for analyzing VPC Flow Logs',
                'instructions': '''You are a VPC Flow Logs analysis agent. Analyze network traffic to identify:
                - Unusual traffic patterns or spikes
                - Blocked connections
                - Network performance issues
                - Security threats or DDoS attempts'''
            },
            {
                'name': 'SRE-Trusted-Advisor-Analyzer',
                'description': 'Analyzes Trusted Advisor recommendations',
                'lambda_function': 'sre-trusted-advisor-agent-lambda',
                'action_group_name': 'trusted-advisor-actions',
                'action_group_description': 'Actions for analyzing Trusted Advisor checks',
                'instructions': '''You are a Trusted Advisor analysis agent. Analyze recommendations for:
                - Cost optimization opportunities
                - Performance improvements
                - Security best practices
                - Fault tolerance enhancements
                - Service limit warnings'''
            },
            {
                'name': 'SRE-Personal-Health-Analyzer',
                'description': 'Analyzes AWS Personal Health Dashboard events',
                'lambda_function': 'sre-personal-health-agent-lambda',
                'action_group_name': 'personal-health-actions',
                'action_group_description': 'Actions for analyzing AWS Health events',
                'instructions': '''You are a Personal Health Dashboard analysis agent. Monitor and analyze:
                - AWS service health events
                - Scheduled maintenance
                - Service degradations
                - Regional issues affecting resources'''
            },
            {
                'name': 'SRE-CloudWatch-Logs-Analyzer',
                'description': 'Analyzes CloudWatch logs for application issues',
                'lambda_function': 'sre-cloudwatch-logs-agent-lambda',
                'action_group_name': 'cloudwatch-logs-actions',
                'action_group_description': 'Actions for analyzing CloudWatch logs',
                'instructions': '''You are a CloudWatch Logs analysis agent. Analyze application logs to identify:
                - Error patterns and exceptions
                - Performance bottlenecks
                - Resource utilization issues
                - Application-specific problems'''
            }
        ]
    
    def get_or_create_agent(self, agent_config: Dict) -> str:
        """Get existing agent or create new one"""
        try:
            # List existing agents
            response = self.bedrock_agent.list_agents()
            agents = response.get('agents', [])
            
            # Check if agent already exists
            for agent in agents:
                if agent['name'] == agent_config['name']:
                    print(f"Agent '{agent_config['name']}' already exists with ID: {agent['agentId']}")
                    return agent['agentId']
            
            # Create new agent
            print(f"Creating new agent: {agent_config['name']}")
            
            # Get Lambda function ARN
            lambda_response = self.lambda_client.get_function(
                FunctionName=agent_config['lambda_function']
            )
            lambda_arn = lambda_response['Configuration']['FunctionArn']
            
            # Create IAM role for agent (you might need to adjust this based on your setup)
            role_arn = self.get_or_create_agent_role(agent_config['name'])
            
            # Create agent
            create_response = self.bedrock_agent.create_agent(
                agentName=agent_config['name'],
                description=agent_config['description'],
                instruction=agent_config['instructions'],
                foundationModel='anthropic.claude-v2',
                agentResourceRoleArn=role_arn
            )
            
            agent_id = create_response['agent']['agentId']
            print(f"Created agent '{agent_config['name']}' with ID: {agent_id}")
            
            return agent_id
            
        except Exception as e:
            print(f"Error creating agent '{agent_config['name']}': {str(e)}")
            raise
    
    def get_or_create_agent_role(self, agent_name: str) -> str:
        """Get or create IAM role for Bedrock agent"""
        iam = boto3.client('iam')
        role_name = f"AmazonBedrockExecutionRoleForAgents_{agent_name.replace('-', '')}"
        
        try:
            # Check if role exists
            response = iam.get_role(RoleName=role_name)
            return response['Role']['Arn']
        except ClientError:
            # Create role
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "bedrock.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            response = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Execution role for Bedrock agent {agent_name}"
            )
            
            # Attach necessary policies
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
            )
            
            return response['Role']['Arn']
    
    def create_or_update_action_group(self, agent_id: str, agent_config: Dict):
        """Create or update action group for agent"""
        try:
            # Get Lambda ARN
            lambda_response = self.lambda_client.get_function(
                FunctionName=agent_config['lambda_function']
            )
            lambda_arn = lambda_response['Configuration']['FunctionArn']
            
            # List existing action groups
            try:
                response = self.bedrock_agent.list_agent_action_groups(
                    agentId=agent_id
                )
                action_groups = response.get('actionGroups', [])
                
                # Check if action group exists
                for ag in action_groups:
                    if ag['name'] == agent_config['action_group_name']:
                        print(f"Action group '{agent_config['action_group_name']}' already exists")
                        return
            except:
                pass
            
            # Define action group schema
            api_schema = {
                "openapi": "3.0.0",
                "info": {
                    "title": f"{agent_config['name']} API",
                    "version": "1.0.0",
                    "description": agent_config['action_group_description']
                },
                "paths": {
                    "/analyze": {
                        "post": {
                            "summary": "Analyze data",
                            "description": f"Analyze data for {agent_config['name']}",
                            "operationId": "analyze",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "query": {
                                                    "type": "string",
                                                    "description": "Analysis query"
                                                },
                                                "timeRange": {
                                                    "type": "object",
                                                    "properties": {
                                                        "start": {"type": "string"},
                                                        "end": {"type": "string"}
                                                    }
                                                },
                                                "filters": {
                                                    "type": "object",
                                                    "additionalProperties": True
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Analysis results",
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
            }
            
            # Create action group
            print(f"Creating action group '{agent_config['action_group_name']}' for agent {agent_id}")
            
            response = self.bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                actionGroupName=agent_config['action_group_name'],
                actionGroupExecutor={
                    'lambda': lambda_arn
                },
                apiSchema={
                    'payload': json.dumps(api_schema)
                },
                description=agent_config['action_group_description']
            )
            
            print(f"Created action group: {agent_config['action_group_name']}")
            
            # Add Lambda permission for Bedrock to invoke
            try:
                self.lambda_client.add_permission(
                    FunctionName=agent_config['lambda_function'],
                    StatementId=f'AllowBedrockInvoke_{agent_id}_{agent_config["action_group_name"]}',
                    Action='lambda:InvokeFunction',
                    Principal='bedrock.amazonaws.com',
                    SourceArn=f'arn:aws:bedrock:{self.region}:*:agent/{agent_id}'
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceConflictException':
                    raise
            
        except Exception as e:
            print(f"Error creating action group: {str(e)}")
            raise
    
    def prepare_agent(self, agent_id: str, agent_name: str):
        """Prepare agent for use"""
        try:
            print(f"Preparing agent {agent_name} (ID: {agent_id})...")
            
            response = self.bedrock_agent.prepare_agent(
                agentId=agent_id
            )
            
            # Wait for preparation to complete
            max_attempts = 30
            for i in range(max_attempts):
                agent_response = self.bedrock_agent.get_agent(agentId=agent_id)
                status = agent_response['agent']['agentStatus']
                
                if status == 'PREPARED':
                    print(f"Agent {agent_name} is now PREPARED")
                    return True
                elif status == 'FAILED':
                    print(f"Agent {agent_name} preparation FAILED")
                    return False
                else:
                    print(f"Agent {agent_name} status: {status}... waiting...")
                    time.sleep(10)
            
            print(f"Timeout waiting for agent {agent_name} to be prepared")
            return False
            
        except Exception as e:
            print(f"Error preparing agent: {str(e)}")
            return False
    
    def configure_all_agents(self):
        """Configure all Bedrock agents"""
        print("Configuring Bedrock Agents and Action Groups")
        print("=" * 80)
        
        results = []
        
        for agent_config in self.agent_configs:
            print(f"\nProcessing agent: {agent_config['name']}")
            print("-" * 40)
            
            try:
                # Get or create agent
                agent_id = self.get_or_create_agent(agent_config)
                
                # Create or update action group
                self.create_or_update_action_group(agent_id, agent_config)
                
                # Prepare agent
                success = self.prepare_agent(agent_id, agent_config['name'])
                
                results.append({
                    'name': agent_config['name'],
                    'id': agent_id,
                    'status': 'SUCCESS' if success else 'FAILED'
                })
                
            except Exception as e:
                print(f"Error configuring agent {agent_config['name']}: {str(e)}")
                results.append({
                    'name': agent_config['name'],
                    'id': None,
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        # Print summary
        print("\n" + "=" * 80)
        print("Configuration Summary")
        print("=" * 80)
        
        for result in results:
            status_icon = "✓" if result['status'] == 'SUCCESS' else "✗"
            print(f"{status_icon} {result['name']}: {result['status']}")
            if result.get('id'):
                print(f"  Agent ID: {result['id']}")
            if result.get('error'):
                print(f"  Error: {result['error']}")
        
        # Save results
        with open('bedrock_agents_config_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: bedrock_agents_config_results.json")


def main():
    configurator = BedrockAgentConfigurator()
    configurator.configure_all_agents()


if __name__ == "__main__":
    main()
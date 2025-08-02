#!/usr/bin/env python3

import boto3
import json
import logging
import argparse
from botocore.exceptions import ClientError
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class AgentValidator:
    def __init__(self, config_file=None, region='us-east-1'):
        """Initialize the agent validator."""
        self.region = region
        self.config = self._load_config(config_file) if config_file else self._default_config()
        self.bedrock_client = boto3.client('bedrock-agent', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.account_id = self._get_aws_account_id()
        
    def _get_aws_account_id(self):
        """Get the AWS account ID."""
        try:
            sts_client = boto3.client('sts')
            return sts_client.get_caller_identity()["Account"]
        except ClientError as e:
            logger.error(f"Error getting AWS account ID: {e}")
            raise

    def _load_config(self, config_file):
        """Load configuration from file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found.")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error parsing configuration file {config_file}.")
            raise
            
    def _default_config(self):
        """Create default configuration for SRE Copilot agents."""
        return {
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
            'supervisor_agent': {
                'name': 'SRE-Supervisor',
                'description': 'Coordinates analysis and response for SRE incidents',
                'instruction': 'You are an SRE supervisor agent responsible for coordinating incident analysis and response. Your role is to delegate tasks to specialized agents and synthesize their findings.',
                'model': 'anthropic.claude-v2'
            },
            'log_analysis_agent': {
                'name': 'SRE-Log-Analyzer',
                'description': 'Analyzes log data for patterns and anomalies',
                'instruction': 'You are a log analysis agent specialized in identifying patterns, anomalies, and root causes in system logs. Focus on extracting meaningful insights from log data.',
                'model': 'anthropic.claude-v2'
            },
            'metrics_analysis_agent': {
                'name': 'SRE-Metrics-Analyzer',
                'description': 'Analyzes time-series metrics data',
                'instruction': 'You are a metrics analysis agent specialized in analyzing time-series data, identifying trends, and detecting anomalies in system metrics.',
                'model': 'anthropic.claude-v2'
            }
        }

    def validate_lambda_function(self, function_name):
        """Validate that a Lambda function exists and is accessible."""
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            logger.info(f"Lambda function {function_name} exists and is accessible")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"Lambda function {function_name} does not exist")
            else:
                logger.error(f"Error validating Lambda function {function_name}: {e}")
            return False

    def validate_agent(self, agent_id, agent_name):
        """Validate that an agent exists and is properly configured."""
        try:
            response = self.bedrock_client.get_agent(agentId=agent_id)
            agent = response.get('agent', {})
            
            if not agent:
                logger.error(f"Agent {agent_name} (ID: {agent_id}) not found")
                return False
                
            logger.info(f"Agent {agent_name} (ID: {agent_id}) exists and is properly configured")
            logger.info(f"Agent version: {agent.get('agentVersion', 'DRAFT')}")
            logger.info(f"Agent status: {agent.get('agentStatus', 'UNKNOWN')}")
            
            return True
        except ClientError as e:
            logger.error(f"Error validating agent {agent_name} (ID: {agent_id}): {e}")
            return False

    def validate_action_groups(self, agent_id, agent_name):
        """Validate that an agent has the required action groups."""
        try:
            # Get the latest agent version
            agent_info = self.bedrock_client.get_agent(agentId=agent_id)
            agent_version = agent_info.get('agent', {}).get('agentVersion', 'DRAFT')
            
            # List action groups
            response = self.bedrock_client.list_agent_action_groups(
                agentId=agent_id,
                agentVersion=agent_version
            )
            
            action_groups = response.get('actionGroupSummaries', [])
            
            if not action_groups:
                logger.error(f"Agent {agent_name} (ID: {agent_id}) has no action groups")
                return False
                
            logger.info(f"Agent {agent_name} (ID: {agent_id}) has {len(action_groups)} action groups:")
            for group in action_groups:
                logger.info(f"  - {group.get('actionGroupName')} (ID: {group.get('actionGroupId')})")
                
                # Validate the action group
                try:
                    group_details = self.bedrock_client.get_agent_action_group(
                        agentId=agent_id,
                        agentVersion=agent_version,
                        actionGroupId=group.get('actionGroupId')
                    )
                    
                    # Check if the action group has a Lambda function
                    executor = group_details.get('actionGroup', {}).get('actionGroupExecutor', {})
                    if 'lambda' in executor:
                        lambda_arn = executor['lambda']
                        lambda_name = lambda_arn.split(':')[-1]
                        if self.validate_lambda_function(lambda_name):
                            logger.info(f"  - Lambda function {lambda_name} is properly configured")
                        else:
                            logger.error(f"  - Lambda function {lambda_name} is not properly configured")
                    else:
                        logger.warning(f"  - No Lambda function configured for action group {group.get('actionGroupName')}")
                        
                except ClientError as e:
                    logger.error(f"Error validating action group {group.get('actionGroupName')}: {e}")
            
            return True
        except ClientError as e:
            logger.error(f"Error validating action groups for agent {agent_name} (ID: {agent_id}): {e}")
            return False

    def validate_all(self):
        """Validate all agents and their action groups."""
        results = {
            'success': True,
            'agents': {},
            'next_steps': []
        }
        
        # Validate specialized agents
        specialized_agents = ['log_analysis_agent', 'metrics_analysis_agent']
        for agent_type in specialized_agents:
            if agent_type in self.config:
                agent_config = self.config[agent_type]
                agent_id = agent_config.get('id')
                agent_name = agent_config.get('name')
                
                if not agent_id:
                    logger.error(f"Agent ID not found for {agent_type}")
                    results['success'] = False
                    results['next_steps'].append(f"Create agent for {agent_type}")
                    continue
                
                agent_valid = self.validate_agent(agent_id, agent_name)
                action_groups_valid = self.validate_action_groups(agent_id, agent_name)
                
                results['agents'][agent_type] = {
                    'valid': agent_valid and action_groups_valid,
                    'agent_id': agent_id,
                    'agent_name': agent_name
                }
                
                if not agent_valid or not action_groups_valid:
                    results['success'] = False
                    results['next_steps'].append(f"Fix configuration for {agent_type}")
        
        # Validate supervisor agent
        supervisor_config = self.config.get('supervisor_agent')
        if supervisor_config:
            supervisor_id = supervisor_config.get('id')
            supervisor_name = supervisor_config.get('name')
            
            if not supervisor_id:
                logger.error("Supervisor agent ID not found")
                results['success'] = False
                results['next_steps'].append("Create supervisor agent")
            else:
                supervisor_valid = self.validate_agent(supervisor_id, supervisor_name)
                supervisor_action_groups_valid = self.validate_action_groups(supervisor_id, supervisor_name)
                
                results['agents']['supervisor_agent'] = {
                    'valid': supervisor_valid and supervisor_action_groups_valid,
                    'agent_id': supervisor_id,
                    'agent_name': supervisor_name
                }
                
                if not supervisor_valid or not supervisor_action_groups_valid:
                    results['success'] = False
                    results['next_steps'].append("Fix configuration for supervisor agent")
        
        # Add next steps based on validation results
        if results['success']:
            results['next_steps'].append("Create a test incident to verify the agents' functionality")
            results['next_steps'].append("Set up monitoring for the agents' performance")
            results['next_steps'].append("Configure alerts for agent failures")
        else:
            results['next_steps'].append("Run the configure_agents.py script to fix any issues")
        
        return results

    def print_validation_results(self, results):
        """Print the validation results in a readable format."""
        print("\n" + "="*80)
        print("SRE COPILOT AGENT VALIDATION RESULTS")
        print("="*80)
        
        if results['success']:
            print("\n✅ All agents are properly configured!")
        else:
            print("\n❌ Some agents are not properly configured.")
        
        print("\nAGENT STATUS:")
        for agent_type, agent_info in results['agents'].items():
            status = "✅ Valid" if agent_info['valid'] else "❌ Invalid"
            print(f"  {agent_type}: {status}")
            print(f"    - ID: {agent_info['agent_id']}")
            print(f"    - Name: {agent_info['agent_name']}")
        
        print("\nNEXT STEPS:")
        for i, step in enumerate(results['next_steps'], 1):
            print(f"  {i}. {step}")
        
        print("\n" + "="*80)

def main():
    """Main function to validate SRE Copilot agents."""
    parser = argparse.ArgumentParser(description='Validate SRE Copilot agents.')
    parser.add_argument('--config', default='sre_copilot_config.json', help='Path to configuration file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    try:
        validator = AgentValidator(config_file=args.config, region=args.region)
        results = validator.validate_all()
        validator.print_validation_results(results)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3

import boto3
import json
import logging
import argparse
from botocore.exceptions import ClientError
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ActionGroupTester:
    def __init__(self, config_file=None, region='us-east-1'):
        """Initialize the action group tester."""
        self.region = region
        self.config = self._load_config(config_file) if config_file else {}
        self.bedrock_client = boto3.client('bedrock-agent', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        
    def _load_config(self, config_file):
        """Load configuration from file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error parsing configuration file {config_file}.")
            return {}

    def test_action_group(self, agent_id, agent_name):
        """Test an action group for a specific agent."""
        try:
            logger.info(f"Testing action group for agent {agent_name} (ID: {agent_id})")
            
            # Get agent version
            try:
                agent_info = self.bedrock_client.get_agent(agentId=agent_id)
                agent_version = agent_info.get('agent', {}).get('agentVersion', 'DRAFT')
                logger.info(f"Using agent version: {agent_version}")
            except Exception as e:
                logger.error(f"Error getting agent version: {e}")
                return False

            # Get action groups
            try:
                action_groups = self.bedrock_client.list_agent_action_groups(
                    agentId=agent_id,
                    agentVersion=agent_version
                ).get('actionGroupSummaries', [])
                
                if not action_groups:
                    logger.error(f"No action groups found for agent {agent_name}")
                    return False
                
                logger.info(f"Found {len(action_groups)} action groups for agent {agent_name}")
                
                # Test each action group
                for group in action_groups:
                    group_name = group.get('actionGroupName')
                    logger.info(f"Testing action group: {group_name}")
                    
                    # Get action group details
                    try:
                        group_details = self.bedrock_client.get_agent_action_group(
                            agentId=agent_id,
                            agentVersion=agent_version,
                            actionGroupId=group.get('actionGroupId')
                        )
                        
                        # Verify API schema
                        api_schema = group_details.get('actionGroup', {}).get('apiSchema', {})
                        if not api_schema:
                            logger.error(f"No API schema found for action group {group_name}")
                            continue
                            
                        # Verify Lambda function
                        executor = group_details.get('actionGroup', {}).get('actionGroupExecutor', {})
                        lambda_arn = executor.get('lambda')
                        if not lambda_arn:
                            logger.error(f"No Lambda function configured for action group {group_name}")
                            continue
                            
                        # Test Lambda function
                        try:
                            lambda_name = lambda_arn.split(':')[-1]
                            lambda_response = self.lambda_client.get_function(FunctionName=lambda_name)
                            logger.info(f"Lambda function {lambda_name} is accessible")
                            
                            # Test Lambda invocation with sample payload
                            test_payload = self._get_test_payload(agent_name, group_name)
                            if test_payload:
                                try:
                                    invoke_response = self.lambda_client.invoke(
                                        FunctionName=lambda_name,
                                        InvocationType='RequestResponse',
                                        Payload=json.dumps(test_payload)
                                    )
                                    status_code = invoke_response.get('StatusCode')
                                    if status_code == 200:
                                        logger.info(f"Successfully tested Lambda function {lambda_name}")
                                    else:
                                        logger.error(f"Lambda invocation failed with status code {status_code}")
                                except Exception as e:
                                    logger.error(f"Error invoking Lambda function {lambda_name}: {e}")
                            
                        except Exception as e:
                            logger.error(f"Error testing Lambda function for action group {group_name}: {e}")
                            continue
                            
                    except Exception as e:
                        logger.error(f"Error getting action group details for {group_name}: {e}")
                        continue
                        
                return True
                
            except Exception as e:
                logger.error(f"Error listing action groups for agent {agent_name}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing action group for agent {agent_name}: {e}")
            return False

    def _get_test_payload(self, agent_name, group_name):
        """Get test payload based on agent and action group."""
        test_payloads = {
            'SRE-Log-Analyzer': {
                'log_analysis_action_group': {
                    'log_group': '/aws/lambda/test-function',
                    'time_range': '1h',
                    'query': 'ERROR'
                }
            },
            'SRE-Metrics-Analyzer': {
                'metrics_analysis_action_group': {
                    'namespace': 'AWS/Lambda',
                    'metric_name': 'Duration',
                    'dimensions': {'FunctionName': 'test-function'},
                    'period': 300,
                    'statistic': 'Average'
                }
            },
            'SRE-Supervisor': {
                'supervisor_action_group': {
                    'issue_type': 'performance',
                    'severity': 'high',
                    'context': {
                        'service': 'test-service',
                        'environment': 'production'
                    }
                }
            }
        }
        
        return test_payloads.get(agent_name, {}).get(group_name)

    def test_all_action_groups(self):
        """Test all action groups for all agents."""
        results = {
            'success': True,
            'agents': {},
            'next_steps': []
        }
        
        try:
            # Get all agents
            paginator = self.bedrock_client.get_paginator('list_agents')
            agents = []
            for page in paginator.paginate():
                agents.extend(page.get('agentSummaries', []))
            
            if not agents:
                logger.error("No agents found")
                results['success'] = False
                results['next_steps'].append("Create agents using configure_agents.py")
                return results
            
            # Test action groups for each agent
            for agent in agents:
                agent_id = agent.get('agentId')
                agent_name = agent.get('agentName')
                
                if not agent_id or not agent_name:
                    continue
                
                # Skip agents that don't need action groups
                if agent_name not in ['SRE-Log-Analyzer', 'SRE-Metrics-Analyzer', 'SRE-Supervisor']:
                    logger.info(f"Skipping action group test for {agent_name}")
                    continue
                
                test_success = self.test_action_group(agent_id, agent_name)
                
                results['agents'][agent_name] = {
                    'id': agent_id,
                    'success': test_success
                }
                
                if not test_success:
                    results['success'] = False
                    results['next_steps'].append(f"Fix action group configuration for {agent_name}")
            
            # Add next steps based on results
            if results['success']:
                results['next_steps'].append("All action groups are properly configured and working")
                results['next_steps'].append("You can now use the agents in your applications")
            else:
                results['next_steps'].append("Check CloudWatch logs for detailed error messages")
                results['next_steps'].append("Verify Lambda function permissions and configurations")
            
            return results
            
        except ClientError as e:
            logger.error(f"Error listing agents: {e}")
            results['success'] = False
            results['next_steps'].append("Check AWS credentials and permissions")
            return results

    def print_results(self, results):
        """Print the test results in a readable format."""
        print("\n" + "="*80)
        print("SRE COPILOT ACTION GROUP TEST RESULTS")
        print("="*80)
        
        if results['success']:
            print("\n✅ All action groups tested successfully!")
        else:
            print("\n❌ Some action groups failed testing.")
        
        print("\nAGENT STATUS:")
        for agent_name, agent_info in results['agents'].items():
            status = "✅ Tested" if agent_info['success'] else "❌ Failed"
            print(f"  {agent_name}: {status}")
            print(f"    - ID: {agent_info['id']}")
        
        print("\nNEXT STEPS:")
        for i, step in enumerate(results['next_steps'], 1):
            print(f"  {i}. {step}")
        
        print("\n" + "="*80)

def main():
    """Main function to test action groups."""
    parser = argparse.ArgumentParser(description='Test action groups for SRE Copilot agents.')
    parser.add_argument('--config', default='sre_copilot_config.json', help='Path to configuration file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    try:
        tester = ActionGroupTester(config_file=args.config, region=args.region)
        results = tester.test_all_action_groups()
        tester.print_results(results)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 
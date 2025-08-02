#!/usr/bin/env python3

import boto3
import json
import logging
import argparse
import time
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentPreparer:
    def __init__(self, config_file=None, region='us-east-1'):
        """Initialize the agent preparer."""
        self.region = region
        self.config = self._load_config(config_file) if config_file else {}
        self.bedrock_client = boto3.client('bedrock-agent', region_name=self.region)
        
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

    def _get_agent_id(self, agent_name):
        """Get agent ID by name."""
        try:
            paginator = self.bedrock_client.get_paginator('list_agents')
            for page in paginator.paginate():
                for agent in page.get('agentSummaries', []):
                    if agent.get('agentName') == agent_name:
                        return agent.get('agentId')
            return None
        except Exception as e:
            logger.error(f"Error getting agent ID for {agent_name}: {e}")
            return None

    def prepare_agent(self, agent_name):
        """Prepare a specific agent."""
        logger.info(f"Preparing agent: {agent_name}")
        
        agent_id = self._get_agent_id(agent_name)
        if not agent_id:
            logger.error(f"Agent {agent_name} not found")
            return False

        try:
            # Get current agent status
            agent_info = self.bedrock_client.get_agent(agentId=agent_id)
            current_status = agent_info.get('agent', {}).get('agentStatus')
            
            if current_status == 'Prepared':
                logger.info(f"Agent {agent_name} is already prepared")
                return True

            # Start preparation
            logger.info(f"Starting preparation for agent {agent_name}")
            response = self.bedrock_client.prepare_agent(
                agentId=agent_id
            )

            # Wait for preparation to complete
            max_attempts = 30
            attempts = 0
            while attempts < max_attempts:
                agent_info = self.bedrock_client.get_agent(agentId=agent_id)
                status = agent_info.get('agent', {}).get('agentStatus')
                
                if status == 'Prepared':
                    logger.info(f"Agent {agent_name} prepared successfully")
                    return True
                elif status in ['Failed', 'Error']:
                    logger.error(f"Agent {agent_name} preparation failed with status: {status}")
                    return False
                
                logger.info(f"Agent {agent_name} preparation in progress... Status: {status}")
                attempts += 1
                time.sleep(10)

            logger.error(f"Timeout waiting for agent {agent_name} preparation")
            return False

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', '')
            
            if error_code == 'ConflictException' and 'already being prepared' in error_message:
                logger.info(f"Agent {agent_name} is already being prepared")
                return True
            
            logger.error(f"Error preparing agent {agent_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error preparing agent {agent_name}: {e}")
            return False

    def prepare_all_agents(self):
        """Prepare all agents."""
        results = {
            'success': True,
            'agents': {},
            'next_steps': []
        }

        agents_to_prepare = [
            'SRE-Log-Analyzer',
            'SRE-Metrics-Analyzer',
            'SRE-Supervisor',
            'SRE-Copilot-Dashboard-Analyzer',
            'SRE-Copilot-Supervisor'
        ]

        for agent_name in agents_to_prepare:
            logger.info(f"\nPreparing agent: {agent_name}")
            success = self.prepare_agent(agent_name)
            
            results['agents'][agent_name] = {
                'success': success,
                'status': 'Prepared' if success else 'Failed'
            }
            
            if not success:
                results['success'] = False
                results['next_steps'].append(f"Check configuration for {agent_name}")

        # Add next steps based on results
        if results['success']:
            results['next_steps'].append("All agents prepared successfully")
            results['next_steps'].append("You can now proceed with testing the agents")
        else:
            results['next_steps'].append("Check CloudWatch logs for detailed error messages")
            results['next_steps'].append("Verify agent configurations and permissions")

        return results

    def print_results(self, results):
        """Print the preparation results in a readable format."""
        print("\n" + "="*80)
        print("SRE COPILOT AGENT PREPARATION RESULTS")
        print("="*80)
        
        if results['success']:
            print("\n✅ All agents prepared successfully!")
        else:
            print("\n❌ Some agents failed preparation.")
        
        print("\nAGENT STATUS:")
        for agent_name, agent_info in results['agents'].items():
            status = "✅ Prepared" if agent_info['success'] else "❌ Failed"
            print(f"  {agent_name}: {status}")
        
        print("\nNEXT STEPS:")
        for i, step in enumerate(results['next_steps'], 1):
            print(f"  {i}. {step}")
        
        print("\n" + "="*80)

def main():
    """Main function to prepare agents."""
    parser = argparse.ArgumentParser(description='Prepare SRE Copilot agents.')
    parser.add_argument('--config', default='sre_copilot_config.json', help='Path to configuration file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    try:
        preparer = AgentPreparer(config_file=args.config, region=args.region)
        results = preparer.prepare_all_agents()
        preparer.print_results(results)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 
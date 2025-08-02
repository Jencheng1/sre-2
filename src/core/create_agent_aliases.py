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

class AgentAliasManager:
    def __init__(self, region='us-east-1'):
        """Initialize the agent alias manager."""
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent-runtime', region_name=self.region)
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=self.region)
        
    def _get_agent_id(self, agent_name):
        """Get agent ID by name."""
        try:
            paginator = self.bedrock_agent_client.get_paginator('list_agents')
            for page in paginator.paginate():
                for agent in page.get('agentSummaries', []):
                    if agent.get('agentName') == agent_name:
                        return agent.get('agentId')
            return None
        except Exception as e:
            logger.error(f"Error getting agent ID for {agent_name}: {e}")
            return None

    def _get_latest_version_id(self, agent_id):
        """Get the latest version ID for an agent."""
        try:
            response = self.bedrock_agent_client.list_agent_versions(agentId=agent_id)
            versions = response.get('agentVersionSummaries', [])
            if versions:
                # Sort versions by creation time and get the latest
                latest_version = sorted(versions, key=lambda x: x.get('creationDateTime', ''), reverse=True)[0]
                return latest_version.get('agentVersion')
            return None
        except Exception as e:
            logger.error(f"Error getting latest version ID: {e}")
            return None

    def _create_and_prepare_version(self, agent_id):
        """Create and prepare a version for the agent."""
        try:
            # Create a new version
            response = self.bedrock_agent_client.create_agent_version(
                agentId=agent_id
            )
            version_id = response["agentVersion"]["version"]
            logger.info(f"Created new version: {version_id}")
            
            # Wait for version to be prepared
            while True:
                desc = self.bedrock_agent_client.get_agent_version(
                    agentId=agent_id,
                    agentVersion=version_id
                )
                status = desc["agentVersion"]["status"]
                
                if status == "PREPARED":
                    logger.info(f"Version {version_id} is prepared")
                    break
                elif status == "FAILED":
                    logger.error(f"Version preparation failed: {desc}")
                    return None
                    
                time.sleep(5)  # Wait 5 seconds between checks
            
            return version_id
            
        except Exception as e:
            logger.error(f"Error creating/preparing version: {e}")
            return None

    def create_alias(self, agent_name):
        """Create an alias for an agent."""
        logger.info(f"Creating alias for agent: {agent_name}")
        
        agent_id = self._get_agent_id(agent_name)
        if not agent_id:
            logger.error(f"Agent {agent_name} not found")
            return False

        try:
            # Check if agent is prepared
            agent_info = self.bedrock_agent_client.get_agent(agentId=agent_id)
            agent_status = agent_info.get('agent', {}).get('agentStatus')
            
            if agent_status != 'PREPARED':
                logger.error(f"Agent {agent_name} is not in PREPARED status (current status: {agent_status})")
                return False

            # Create and prepare a new version
            version_id = self._create_and_prepare_version(agent_id)
            if not version_id:
                logger.error(f"Failed to create and prepare version for agent {agent_name}")
                return False

            # Check existing aliases
            try:
                aliases = self.bedrock_agent_client.list_agent_aliases(
                    agentId=agent_id
                ).get('agentAliasSummaries', [])
                
                # Check if LATEST alias exists
                for alias in aliases:
                    if alias.get('agentAliasName') == 'LATEST':
                        logger.info(f"LATEST alias already exists for agent {agent_name}")
                        return True
                
            except ClientError as e:
                logger.error(f"Error checking aliases for agent {agent_name}: {e}")
                return False

            # Create LATEST alias
            try:
                response = self.bedrock_agent_client.create_agent_alias(
                    agentId=agent_id,
                    agentAliasName='LATEST',
                    agentVersion=version_id,
                    description=f"Latest version alias for {agent_name}"
                )
                
                logger.info(f"Successfully created LATEST alias for agent {agent_name}")
                return True
                
            except ClientError as e:
                if 'ConflictException' in str(e) and 'already exists' in str(e):
                    logger.info(f"LATEST alias already exists for agent {agent_name}")
                    return True
                logger.error(f"Error creating alias for agent {agent_name}: {e}")
                return False

        except Exception as e:
            logger.error(f"Unexpected error creating alias for agent {agent_name}: {e}")
            return False

    def create_all_aliases(self):
        """Create aliases for all agents."""
        results = {
            'success': True,
            'agents': {},
            'next_steps': []
        }

        agents_to_configure = [
            'SRE-Log-Analyzer',
            'SRE-Metrics-Analyzer',
            'SRE-Supervisor',
            'SRE-Copilot-Dashboard-Analyzer',
            'SRE-Copilot-Supervisor'
        ]

        for agent_name in agents_to_configure:
            logger.info(f"\nCreating alias for agent: {agent_name}")
            success = self.create_alias(agent_name)
            
            results['agents'][agent_name] = {
                'success': success,
                'status': 'Created' if success else 'Failed'
            }
            
            if not success:
                results['success'] = False
                results['next_steps'].append(f"Check alias creation for {agent_name}")

        # Add next steps based on results
        if results['success']:
            results['next_steps'].append("All agent aliases created successfully")
            results['next_steps'].append("You can now proceed with testing the agents")
        else:
            results['next_steps'].append("Check CloudWatch logs for detailed error messages")
            results['next_steps'].append("Verify agent configurations and permissions")

        return results

    def print_results(self, results):
        """Print the alias creation results in a readable format."""
        print("\n" + "="*80)
        print("SRE COPILOT AGENT ALIAS CREATION RESULTS")
        print("="*80)
        
        if results['success']:
            print("\n✅ All agent aliases created successfully!")
        else:
            print("\n❌ Some agent aliases failed creation.")
        
        print("\nAGENT STATUS:")
        for agent_name, agent_info in results['agents'].items():
            status = "✅ Created" if agent_info['success'] else "❌ Failed"
            print(f"  {agent_name}: {status}")
        
        print("\nNEXT STEPS:")
        for i, step in enumerate(results['next_steps'], 1):
            print(f"  {i}. {step}")
        
        print("\n" + "="*80)

def main():
    """Main function to create agent aliases."""
    parser = argparse.ArgumentParser(description='Create aliases for SRE Copilot agents.')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    try:
        manager = AgentAliasManager(region=args.region)
        results = manager.create_all_aliases()
        manager.print_results(results)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
import boto3
import os
import logging
import json
import time
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_and_test_agents():
    """Create and test new SRE agents."""
    try:
        load_dotenv()
        region = os.getenv('AWS_REGION', 'us-east-1')
        account_id = boto3.client('sts').get_caller_identity()['Account']

        # Initialize Bedrock Agent client
        bedrock_agent = boto3.client('bedrock-agent')

        # Define the new agents
        new_agents = [
            {
                'name': 'SRE-CloudTrail-Analyzer',
                'description': 'Analyzes CloudTrail logs for API errors, security events, and compliance issues',
                'instruction': 'You are a CloudTrail analysis agent specialized in monitoring and analyzing AWS API activity, security events, and compliance.',
                'config_key': 'cloudtrail_agent'
            },
            {
                'name': 'SRE-VPC-Analyzer',
                'description': 'Analyzes VPC flow logs for network connectivity issues and security concerns',
                'instruction': 'You are a VPC analysis agent specialized in monitoring network traffic, analyzing connectivity issues, and identifying security concerns.',
                'config_key': 'vpc_agent'
            },
            {
                'name': 'SRE-Trusted-Advisor-Analyzer',
                'description': 'Monitors AWS Trusted Advisor for service quotas, security checks, and cost optimization',
                'instruction': 'You are a Trusted Advisor analysis agent specialized in monitoring service quotas, security recommendations, and cost optimization opportunities.',
                'config_key': 'trusted_advisor_agent'
            },
            {
                'name': 'SRE-Personal-Health-Analyzer',
                'description': 'Monitors AWS Personal Health for maintenance events, service issues, and account notifications',
                'instruction': 'You are a Personal Health analysis agent specialized in monitoring AWS service health, maintenance events, and account-specific notifications.',
                'config_key': 'personal_health_agent'
            }
        ]

        # Dictionary to store created agent IDs
        created_agents = {}

        # Create or get existing agents
        for agent in new_agents:
            try:
                logger.info("Creating agent {}...".format(agent['name']))
                response = bedrock_agent.create_agent(
                    agentName=agent['name'],
                    description=agent['description'],
                    instruction=agent['instruction'],
                    foundationModel='anthropic.claude-v2',
                    idleSessionTTLInSeconds=3600,
                    agentResourceRoleArn="arn:aws:iam::{}:role/SREKnowledgeBaseRole".format(account_id)
                )
                agent_id = response['agent']['agentId']
                logger.info("Created agent {} with ID: {}".format(agent['name'], agent_id))
                created_agents[agent['config_key']] = agent_id
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConflictException':
                    logger.info("Agent {} already exists, retrieving ID...".format(agent['name']))
                    # Get existing agent ID
                    agents = bedrock_agent.list_agents()
                    agent_id = next(a['agentId'] for a in agents['agentSummaries'] if a['agentName'] == agent['name'])
                    created_agents[agent['config_key']] = agent_id
                    logger.info("Retrieved existing agent ID: {}".format(agent_id))
                else:
                    raise

            # Wait for agent to be ready
            logger.info("Waiting for agent {} to be ready...".format(agent['name']))
            while True:
                status = bedrock_agent.get_agent(
                    agentId=agent_id
                )['agent']['agentStatus']
                if status == 'Ready':
                    break
                logger.info("Agent status: {}, waiting...".format(status))
                time.sleep(10)

        # Update config file with agent IDs
        config_path = 'sre_copilot_config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Add or update agent IDs in config
        config_updates = {}
        for agent in new_agents:
            config_updates[agent['config_key']] = {
                'id': created_agents[agent['config_key']],
                'name': agent['name'],
                'description': agent['description'],
                'instruction': agent['instruction'],
                'model': 'anthropic.claude-v2'
            }

        config.update(config_updates)

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        logger.info("Updated config file with agent IDs")
        logger.info("\n✅ All agents created and tested successfully!")

        return created_agents

    except Exception as e:
        logger.error("Error creating and testing agents: {}".format(e))
        raise

if __name__ == "__main__":
    create_and_test_agents() 
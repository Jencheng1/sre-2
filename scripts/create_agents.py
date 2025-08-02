#!/usr/bin/env python3

import boto3
import os
import logging
import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_agents():
    """Create Bedrock agents for SRE tasks."""
    try:
        load_dotenv()
        region = os.getenv('AWS_REGION', 'us-east-1')
        collection_id = os.getenv('OPENSEARCH_COLLECTION_ID')
        account_id = boto3.client('sts').get_caller_identity()['Account']

        # Initialize Bedrock Agent client
        bedrock_agent = boto3.client('bedrock-agent')

        # Create the knowledge base
        try:
            logger.info("Creating knowledge base...")
            kb_response = bedrock_agent.create_knowledge_base(
                name="SRE-Incidents-KB",
                description="Knowledge base for SRE incident data and analysis",
                roleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole",
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': f"arn:aws:aoss:{region}:{account_id}:collection/{collection_id}",
                        'vectorIndexName': 'sre-incidents-index',
                        'fieldMapping': {
                            'vectorField': 'embedding',
                            'textField': 'text',
                            'metadataField': 'metadata'
                        }
                    }
                }
            )
            kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
            logger.info(f"Knowledge base created with ID: {kb_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info("Knowledge base already exists, retrieving ID...")
                kb_list = bedrock_agent.list_knowledge_bases()
                kb_id = next(kb['knowledgeBaseId'] for kb in kb_list['knowledgeBaseSummaries'] if kb['name'] == "SRE-Incidents-KB")
            else:
                raise

        # Create the supervisor agent
        try:
            logger.info("Creating supervisor agent...")
            supervisor_response = bedrock_agent.create_agent(
                agentName="SRE-Supervisor",
                description="Coordinates analysis and response for SRE incidents",
                instruction="You are an SRE supervisor agent responsible for coordinating incident analysis and response. Your role is to delegate tasks to specialized agents and synthesize their findings.",
                foundationModel="anthropic.claude-v2",
                idleSessionTTLInSeconds=3600,
                roleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole",
                agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole"
            )
            supervisor_id = supervisor_response['agent']['agentId']
            logger.info(f"Supervisor agent created with ID: {supervisor_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info("Supervisor agent already exists")
            else:
                raise

        # Create the log analysis agent
        try:
            logger.info("Creating log analysis agent...")
            log_agent_response = bedrock_agent.create_agent(
                agentName="SRE-Log-Analyzer",
                description="Analyzes log data for patterns and anomalies",
                instruction="You are a log analysis agent specialized in identifying patterns, anomalies, and root causes in system logs. Focus on extracting meaningful insights from log data.",
                foundationModel="anthropic.claude-v2",
                idleSessionTTLInSeconds=3600,
                roleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole",
                agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole"
            )
            log_agent_id = log_agent_response['agent']['agentId']
            logger.info(f"Log analysis agent created with ID: {log_agent_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info("Log analysis agent already exists")
            else:
                raise

        # Create the metrics analysis agent
        try:
            logger.info("Creating metrics analysis agent...")
            metrics_agent_response = bedrock_agent.create_agent(
                agentName="SRE-Metrics-Analyzer",
                description="Analyzes time-series metrics data",
                instruction="You are a metrics analysis agent specialized in analyzing time-series data, identifying trends, and detecting anomalies in system metrics.",
                foundationModel="anthropic.claude-v2",
                idleSessionTTLInSeconds=3600,
                roleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole",
                agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole"
            )
            metrics_agent_id = metrics_agent_response['agent']['agentId']
            logger.info(f"Metrics analysis agent created with ID: {metrics_agent_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info("Metrics analysis agent already exists")
            else:
                raise

        # Update .env file with agent IDs
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        with open(env_path, 'r') as f:
            env_contents = f.read()

        # Add or update agent IDs in .env
        env_updates = {
            'BEDROCK_KB_ID': kb_id,
            'BEDROCK_SUPERVISOR_AGENT_ID': supervisor_id,
            'BEDROCK_LOG_AGENT_ID': log_agent_id,
            'BEDROCK_METRICS_AGENT_ID': metrics_agent_id
        }

        for key, value in env_updates.items():
            if f'{key}=' in env_contents:
                env_contents = env_contents.replace(
                    f'{key}=',
                    f'{key}={value}'
                )
            else:
                env_contents += f'\n{key}={value}'

        with open(env_path, 'w') as f:
            f.write(env_contents)

        logger.info("Updated .env file with agent IDs")
        logger.info("\n✅ All agents created successfully!")

    except Exception as e:
        logger.error(f"Error creating agents: {e}")
        raise

if __name__ == "__main__":
    create_agents() 
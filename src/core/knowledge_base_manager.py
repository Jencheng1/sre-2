#!/usr/bin/env python3

import boto3
import json
import logging
import argparse
from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SREKnowledgeBaseManager:
    def __init__(self, config_file='sre_copilot_config.json', region='us-east-1'):
        """Initialize the SRE Knowledge Base Manager."""
        self.region = region
        self.config = self._load_config(config_file)
        self.bedrock_client = boto3.client('bedrock-agent', region_name=self.region)
        self.bedrock_runtime_client = boto3.client('bedrock-runtime', region_name=self.region)
        self.opensearch_client = self._initialize_opensearch_client()
        
    def _load_config(self, config_file):
        """Load the SRE Copilot configuration."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found.")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error parsing configuration file {config_file}.")
            raise
            
    def _initialize_opensearch_client(self):
        """Initialize the OpenSearch client."""
        try:
            # Get AWS credentials
            session = boto3.Session()
            credentials = session.get_credentials()
            
            # Create AWS4Auth for OpenSearch
            auth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                self.region,
                'aoss',
                session_token=credentials.token
            )
            
            # Get OpenSearch endpoint from collection ID
            aoss_client = boto3.client('opensearchserverless', region_name=self.region)
            collection_id = self.config['knowledge_base']['data_source_config']['collectionId']
            
            response = aoss_client.batch_get_collection(
                names=[collection_id]
            )
            
            if not response['collectionDetails']:
                logger.error(f"Collection {collection_id} not found.")
                raise ValueError(f"Collection {collection_id} not found.")
                
            endpoint = response['collectionDetails'][0]['collectionEndpoint']
            
            # Initialize OpenSearch client
            opensearch_client = OpenSearch(
                hosts=[{'host': endpoint.replace('https://', ''), 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )
            
            return opensearch_client
            
        except ClientError as e:
            logger.error(f"Error initializing OpenSearch client: {e}")
            raise
            
    def add_incident(self, incident_id, description, root_cause, resolution, services):
        """Add an incident to the knowledge base."""
        try:
            logger.info(f"Adding incident {incident_id} to knowledge base...")
            
            # Create incident document
            incident_doc = {
                'incident_id': incident_id,
                'description': description,
                'root_cause': root_cause,
                'resolution': resolution,
                'services_affected': services.split(',') if isinstance(services, str) else services
            }
            
            # Generate embedding for the incident description
            embedding = self._generate_embedding(description)
            incident_doc['embedding'] = embedding
            
            # Index the document in OpenSearch
            index_name = self.config['knowledge_base']['data_source_config']['vectorIndexName']
            
            response = self.opensearch_client.index(
                index=index_name,
                body=incident_doc,
                id=incident_id,
                refresh=True
            )
            
            logger.info(f"Incident {incident_id} added to knowledge base. Response: {response['result']}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding incident to knowledge base: {e}")
            raise
            
    def _generate_embedding(self, text):
        """Generate embedding for text using Amazon Titan Embeddings."""
        try:
            response = self.bedrock_runtime_client.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'inputText': text
                })
            )
            
            response_body = json.loads(response['body'].read())
            embedding = response_body['embedding']
            
            return embedding
            
        except ClientError as e:
            logger.error(f"Error generating embedding: {e}")
            raise
            
    def update_incident(self, incident_id, field, value):
        """Update a field in an existing incident."""
        try:
            logger.info(f"Updating incident {incident_id}, field {field}...")
            
            # Get the existing document
            index_name = self.config['knowledge_base']['data_source_config']['vectorIndexName']
            
            try:
                response = self.opensearch_client.get(
                    index=index_name,
                    id=incident_id
                )
                
                existing_doc = response['_source']
                
            except Exception as e:
                logger.error(f"Incident {incident_id} not found: {e}")
                return False
                
            # Update the field
            if field in existing_doc:
                existing_doc[field] = value
                
                # If description is updated, regenerate the embedding
                if field == 'description':
                    embedding = self._generate_embedding(value)
                    existing_doc['embedding'] = embedding
                
                # Update the document
                response = self.opensearch_client.index(
                    index=index_name,
                    body=existing_doc,
                    id=incident_id,
                    refresh=True
                )
                
                logger.info(f"Incident {incident_id} updated. Response: {response['result']}")
                return True
                
            else:
                logger.error(f"Field {field} not found in incident {incident_id}.")
                return False
                
        except Exception as e:
            logger.error(f"Error updating incident: {e}")
            raise
            
    def query_incidents(self, query_text, limit=5):
        """Query incidents by semantic similarity."""
        try:
            logger.info(f"Querying incidents with: '{query_text}'")
            
            # Generate embedding for the query
            embedding = self._generate_embedding(query_text)
            
            # Perform vector search
            index_name = self.config['knowledge_base']['data_source_config']['vectorIndexName']
            
            query = {
                "size": limit,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": embedding,
                            "k": limit
                        }
                    }
                }
            }
            
            response = self.opensearch_client.search(
                index=index_name,
                body=query
            )
            
            # Process and return results
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    'incident_id': hit['_source']['incident_id'],
                    'description': hit['_source']['description'],
                    'root_cause': hit['_source']['root_cause'],
                    'resolution': hit['_source']['resolution'],
                    'services_affected': hit['_source']['services_affected'],
                    'score': hit['_score']
                })
                
            logger.info(f"Found {len(results)} similar incidents.")
            return results
            
        except Exception as e:
            logger.error(f"Error querying incidents: {e}")
            raise
            
    def backup_knowledge_base(self, output_file):
        """Backup all incidents in the knowledge base to a file."""
        try:
            logger.info(f"Backing up knowledge base to {output_file}...")
            
            # Get all documents
            index_name = self.config['knowledge_base']['data_source_config']['vectorIndexName']
            
            query = {
                "size": 10000,  # Adjust as needed
                "query": {
                    "match_all": {}
                }
            }
            
            response = self.opensearch_client.search(
                index=index_name,
                body=query
            )
            
            # Extract documents
            documents = []
            for hit in response['hits']['hits']:
                documents.append(hit['_source'])
                
            # Write to file
            with open(output_file, 'w') as f:
                json.dump(documents, f, indent=2)
                
            logger.info(f"Backed up {len(documents)} incidents to {output_file}.")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up knowledge base: {e}")
            raise
            
    def restore_knowledge_base(self, input_file):
        """Restore incidents from a backup file to the knowledge base."""
        try:
            logger.info(f"Restoring knowledge base from {input_file}...")
            
            # Read documents from file
            with open(input_file, 'r') as f:
                documents = json.load(f)
                
            # Index each document
            index_name = self.config['knowledge_base']['data_source_config']['vectorIndexName']
            
            for doc in documents:
                incident_id = doc['incident_id']
                
                response = self.opensearch_client.index(
                    index=index_name,
                    body=doc,
                    id=incident_id,
                    refresh=True
                )
                
                logger.info(f"Restored incident {incident_id}. Response: {response['result']}")
                
            logger.info(f"Restored {len(documents)} incidents to knowledge base.")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring knowledge base: {e}")
            raise

class KnowledgeBaseManager:
    def __init__(self, region='us-east-1'):
        """Initialize the Knowledge Base manager."""
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent', region_name=self.region)
        self.account_id = self._get_aws_account_id()
        
    def _get_aws_account_id(self):
        """Get the AWS account ID."""
        try:
            sts_client = boto3.client('sts')
            return sts_client.get_caller_identity()["Account"]
        except ClientError as e:
            logger.error(f"Error getting AWS account ID: {e}")
            raise

    def create_knowledge_base(self, config):
        """Create a knowledge base for storing historical incident data."""
        try:
            # Get the account ID and region
            region = self.region
            kb_name = config['name']
            logger.info(f"Checking for existing knowledge base: {kb_name}")
            
            # Check if knowledge base already exists
            paginator = self.bedrock_client.get_paginator('list_knowledge_bases')
            for page in paginator.paginate():
                for kb in page.get('knowledgeBases', []):
                    if kb['name'] == kb_name:
                        logger.info(f"Knowledge base {kb_name} already exists with ID: {kb['knowledgeBaseId']}")
                        return kb['knowledgeBaseId']
            
            logger.info(f"No existing knowledge base found. Creating new knowledge base: {kb_name}")
            
            # If we get here, the knowledge base doesn't exist, so create it
            # Ensure we have a valid collection ID
            if 'data_source_config' not in config:
                raise ValueError("Missing data_source_config in knowledge base configuration")
                
            data_source_config = config['data_source_config']
            if 'collectionId' not in data_source_config:
                raise ValueError("Missing collectionId in data_source_config")
                
            collection_id = data_source_config['collectionId']
            
            # Use a dedicated role for knowledge base
            kb_role_name = "BedrockKnowledgeBaseRole"
            
            # Create IAM client
            iam_client = boto3.client('iam')
            
            # Define trust and permission policies
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
            
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "aoss:*"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:*"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            # Create or update the role
            try:
                logger.info(f"Creating IAM role: {kb_role_name}")
                role_response = iam_client.create_role(
                    RoleName=kb_role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="Role for Bedrock Knowledge Base to access OpenSearch"
                )
                
                logger.info("Attaching policy to role")
                iam_client.put_role_policy(
                    RoleName=kb_role_name,
                    PolicyName="BedrockKnowledgeBasePolicy",
                    PolicyDocument=json.dumps(policy_document)
                )
                
            except iam_client.exceptions.EntityAlreadyExistsException:
                logger.info(f"Role {kb_role_name} already exists")
                logger.info("Updating existing role with new trust policy and permissions")
                iam_client.update_assume_role_policy(
                    RoleName=kb_role_name,
                    PolicyDocument=json.dumps(trust_policy)
                )
                iam_client.put_role_policy(
                    RoleName=kb_role_name,
                    PolicyName="BedrockKnowledgeBasePolicy",
                    PolicyDocument=json.dumps(policy_document)
                )
            
            # Wait for role to propagate
            logger.info("Waiting for role to propagate...")
            time.sleep(30)  # Increased wait time for better propagation
            
            role_arn = f"arn:aws:iam::{self.account_id}:role/{kb_role_name}"
            
            # Create OpenSearch client to verify access
            aoss = boto3.client('opensearchserverless')
            try:
                logger.info("Verifying OpenSearch collection access...")
                aoss.batch_get_collection(
                    ids=[collection_id]
                )
            except Exception as e:
                logger.warning(f"OpenSearch collection access check failed: {e}")
            
            response = self.bedrock_client.create_knowledge_base(
                name=kb_name,
                description=config['description'],
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f"arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v1"
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': f"arn:aws:aoss:{region}:{self.account_id}:collection/{collection_id}",
                        'vectorIndexName': data_source_config['vectorIndexName'],
                        'fieldMapping': data_source_config['fieldMapping']
                    }
                }
            )
            
            logger.info(f"Knowledge base created successfully: {response['knowledgeBase']['knowledgeBaseId']}")
            return response['knowledgeBase']['knowledgeBaseId']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                # If we somehow missed it in the initial check, try one more time to get the ID
                logger.info("Knowledge base already exists, retrieving ID...")
                paginator = self.bedrock_client.get_paginator('list_knowledge_bases')
                for page in paginator.paginate():
                    for kb in page.get('knowledgeBases', []):
                        if kb['name'] == kb_name:
                            logger.info(f"Found existing knowledge base ID: {kb['knowledgeBaseId']}")
                            return kb['knowledgeBaseId']
                raise ValueError(f"Could not find ID for existing knowledge base: {kb_name}")
            raise
        except Exception as e:
            logger.error(f"Error creating knowledge base: {e}")
            raise

def main():
    """Main function to manage the SRE knowledge base."""
    parser = argparse.ArgumentParser(description='Manage SRE knowledge base.')
    parser.add_argument('--config', default='sre_copilot_config.json', help='Path to the configuration file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add incident command
    add_parser = subparsers.add_parser('add', help='Add an incident to the knowledge base')
    add_parser.add_argument('--incident-id', required=True, help='Incident ID')
    add_parser.add_argument('--description', required=True, help='Incident description')
    add_parser.add_argument('--root-cause', required=True, help='Root cause of the incident')
    add_parser.add_argument('--resolution', required=True, help='Resolution steps')
    add_parser.add_argument('--services', required=True, help='Affected services (comma-separated)')
    
    # Update incident command
    update_parser = subparsers.add_parser('update', help='Update an incident in the knowledge base')
    update_parser.add_argument('--incident-id', required=True, help='Incident ID')
    update_parser.add_argument('--field', required=True, choices=['description', 'root_cause', 'resolution', 'services_affected'], help='Field to update')
    update_parser.add_argument('--value', required=True, help='New value for the field')
    
    # Query incidents command
    query_parser = subparsers.add_parser('query', help='Query incidents by semantic similarity')
    query_parser.add_argument('--query', required=True, help='Query text')
    query_parser.add_argument('--limit', type=int, default=5, help='Maximum number of results')
    
    # Backup knowledge base command
    backup_parser = subparsers.add_parser('backup', help='Backup knowledge base to a file')
    backup_parser.add_argument('--output', required=True, help='Output file path')
    
    # Restore knowledge base command
    restore_parser = subparsers.add_parser('restore', help='Restore knowledge base from a file')
    restore_parser.add_argument('--input', required=True, help='Input file path')
    
    args = parser.parse_args()
    
    try:
        kb_manager = SREKnowledgeBaseManager(config_file=args.config, region=args.region)
        
        if args.command == 'add':
            kb_manager.add_incident(
                args.incident_id,
                args.description,
                args.root_cause,
                args.resolution,
                args.services
            )
            
        elif args.command == 'update':
            kb_manager.update_incident(
                args.incident_id,
                args.field,
                args.value
            )
            
        elif args.command == 'query':
            results = kb_manager.query_incidents(
                args.query,
                args.limit
            )
            
            # Print results
            print(json.dumps(results, indent=2))
            
        elif args.command == 'backup':
            kb_manager.backup_knowledge_base(args.output)
            
        elif args.command == 'restore':
            kb_manager.restore_knowledge_base(args.input)
            
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()

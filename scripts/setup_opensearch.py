#!/usr/bin/env python3

import boto3
import os
import time
import logging
import json
import requests
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_policy(policy, policy_type):
    """Validate the policy format before creating it."""
    try:
        # Check if policy is a valid JSON
        if isinstance(policy, str):
            policy = json.loads(policy)
        
        # Check if policy is a list
        if not isinstance(policy, list):
            logger.error(f"{policy_type} policy must be a list")
            return False
        
        # Check if policy has at least one rule
        if len(policy) == 0:
            logger.error(f"{policy_type} policy must have at least one rule")
            return False
        
        # Check each rule
        for rule in policy:
            if 'Resource' not in rule:
                logger.error(f"{policy_type} policy rule must have a 'Resource' field")
                return False
            
            if 'ResourceType' not in rule:
                logger.error(f"{policy_type} policy rule must have a 'ResourceType' field")
                return False
            
            if rule['ResourceType'] != 'collection':
                logger.error(f"{policy_type} policy rule 'ResourceType' must be 'collection'")
                return False
        
        logger.info(f"{policy_type} policy format is valid")
        return True
    
    except json.JSONDecodeError:
        logger.error(f"{policy_type} policy is not a valid JSON")
        return False
    except Exception as e:
        logger.error(f"Error validating {policy_type} policy: {str(e)}")
        return False

def setup_opensearch():
    """Set up OpenSearch Serverless vector index for existing collection."""
    try:
        load_dotenv()
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Create AWS credentials
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            'aoss',
            session_token=credentials.token
        )

        # Use existing collection
        collection_name = 'sre-incidents'
        collection_id = 'stxbcop00bopzuvkh3ig'
        logger.info(f"Using existing collection: {collection_name} (ID: {collection_id})")

        # OpenSearch endpoint from the screenshot
        host = f'https://{collection_id}.us-east-1.aoss.amazonaws.com'
        
        # Initialize the OpenSearch client
        opensearch_client = OpenSearch(
            hosts=[{'host': host.replace('https://', ''), 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )

        # Create vector search index
        index_name = f"{collection_name}-index"
        logger.info(f"Creating vector search index: {index_name}")
        
        try:
            index_body = {
                'settings': {
                    'index': {
                        'knn': True,
                    }
                },
                'mappings': {
                    'properties': {
                        'embedding': {
                            'type': 'knn_vector',
                            'dimension': 1536,
                            'method': {
                                'name': 'hnsw',
                                'space_type': 'cosinesimil',
                                'engine': 'nmslib'
                            }
                        },
                        'text': {'type': 'text'},
                        'metadata': {'type': 'object'}
                    }
                }
            }
            
            response = opensearch_client.indices.create(
                index=index_name,
                body=index_body
            )
            
            logger.info(f"Vector search index created: {response}")
            
            # Update .env file with collection ID
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            with open(env_path, 'r') as f:
                env_contents = f.read()
            
            if 'OPENSEARCH_COLLECTION_ID=' in env_contents:
                env_contents = env_contents.replace(
                    'OPENSEARCH_COLLECTION_ID=',
                    f'OPENSEARCH_COLLECTION_ID={collection_id}'
                )
            else:
                env_contents += f'\nOPENSEARCH_COLLECTION_ID={collection_id}'
            
            with open(env_path, 'w') as f:
                f.write(env_contents)
            
            logger.info("Updated .env file with collection ID")
            
            return collection_id
            
        except Exception as e:
            if 'resource_already_exists_exception' in str(e):
                logger.info(f"Index {index_name} already exists")
                return collection_id
            else:
                raise

    except Exception as e:
        logger.error(f"Error setting up OpenSearch vector index: {e}")
        raise

if __name__ == "__main__":
    setup_opensearch()

#!/usr/bin/env python3

import boto3
import os
import logging
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_setup():
    """Validate if all prerequisites are ready for creating agents."""
    try:
        load_dotenv()
        region = os.getenv('AWS_REGION', 'us-east-1')
        collection_id = os.getenv('OPENSEARCH_COLLECTION_ID')
        
        validation_results = {
            'aws_credentials': False,
            'iam_role': False,
            'opensearch_collection': False,
            'opensearch_index': False,
            'bedrock_access': False
        }

        # Check AWS credentials
        try:
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            validation_results['aws_credentials'] = True
            logger.info("✅ AWS credentials are valid")
        except Exception as e:
            logger.error(f"❌ AWS credentials check failed: {e}")
            return False

        # Check IAM role
        try:
            iam = boto3.client('iam')
            role_name = "SREKnowledgeBaseRole"
            iam.get_role(RoleName=role_name)
            validation_results['iam_role'] = True
            logger.info(f"✅ IAM role '{role_name}' exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                logger.error(f"❌ IAM role '{role_name}' not found")
            else:
                logger.error(f"❌ Error checking IAM role: {e}")
            return False

        # Check OpenSearch collection
        try:
            if not collection_id:
                logger.error("❌ OPENSEARCH_COLLECTION_ID not found in .env file")
                return False

            aoss = boto3.client('opensearchserverless')
            collection = aoss.batch_get_collection(names=['sre-incidents'])
            if collection['collectionDetails'][0]['status'] == 'ACTIVE':
                validation_results['opensearch_collection'] = True
                logger.info("✅ OpenSearch collection is active")
            else:
                logger.error("❌ OpenSearch collection is not active")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking OpenSearch collection: {e}")
            return False

        # Check OpenSearch index
        try:
            # Create AWS auth
            credentials = boto3.Session().get_credentials()
            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                region,
                'aoss',
                session_token=credentials.token
            )

            # Initialize OpenSearch client
            host = f'https://{collection_id}.{region}.aoss.amazonaws.com'
            opensearch_client = OpenSearch(
                hosts=[{'host': host.replace('https://', ''), 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )

            index_name = 'sre-incidents-index'
            index_exists = opensearch_client.indices.exists(index_name)
            if index_exists:
                validation_results['opensearch_index'] = True
                logger.info(f"✅ OpenSearch index '{index_name}' exists")
            else:
                logger.error(f"❌ OpenSearch index '{index_name}' not found")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking OpenSearch index: {e}")
            return False

        # Check Bedrock access
        try:
            bedrock = boto3.client('bedrock-runtime')
            # List available models to verify access
            bedrock.list_foundation_models()
            validation_results['bedrock_access'] = True
            logger.info("✅ Bedrock access is configured")
        except Exception as e:
            logger.error(f"❌ Error checking Bedrock access: {e}")
            return False

        # Final validation
        all_valid = all(validation_results.values())
        if all_valid:
            logger.info("\n✅ All prerequisites are ready for creating agents!")
        else:
            failed_checks = [k for k, v in validation_results.items() if not v]
            logger.error(f"\n❌ Some checks failed: {', '.join(failed_checks)}")

        return all_valid

    except Exception as e:
        logger.error(f"Error during validation: {e}")
        return False

if __name__ == "__main__":
    validate_setup() 
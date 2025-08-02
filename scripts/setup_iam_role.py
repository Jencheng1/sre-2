#!/usr/bin/env python3

import boto3
import json
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_iam_role():
    """Set up IAM role with necessary permissions."""
    try:
        iam = boto3.client('iam')
        role_name = "SREKnowledgeBaseRole"

        # Create the role
        try:
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": [
                                "bedrock.amazonaws.com",
                                "aoss.amazonaws.com"
                            ]
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }

            logger.info(f"Creating IAM role: {role_name}")
            role = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for SRE Copilot knowledge base and agents"
            )
            logger.info(f"Role {role_name} created successfully")

        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.info(f"Role {role_name} already exists")
                role = iam.get_role(RoleName=role_name)
            else:
                raise

        # Create OpenSearch policy
        opensearch_policy_name = "SREOpenSearchPolicy"
        opensearch_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "aoss:CreateCollection",
                        "aoss:DeleteCollection",
                        "aoss:UpdateCollection",
                        "aoss:BatchGetCollection",
                        "aoss:CreateSecurityPolicy",
                        "aoss:CreateAccessPolicy",
                        "aoss:ListCollections",
                        "aoss:APIAccessAll"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "aoss:*"
                    ],
                    "Resource": [
                        "arn:aws:aoss:*:*:collection/*"
                    ]
                }
            ]
        }

        try:
            logger.info(f"Creating IAM policy: {opensearch_policy_name}")
            policy = iam.create_policy(
                PolicyName=opensearch_policy_name,
                PolicyDocument=json.dumps(opensearch_policy)
            )
            policy_arn = policy['Policy']['Arn']
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.info(f"Policy {opensearch_policy_name} already exists")
                account_id = boto3.client('sts').get_caller_identity()['Account']
                policy_arn = f"arn:aws:iam::{account_id}:policy/{opensearch_policy_name}"
            else:
                raise

        # Create Bedrock policy
        bedrock_policy_name = "SREBedrockPolicy"
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:*",
                        "bedrock-agent:*",
                        "bedrock-runtime:*"
                    ],
                    "Resource": "*"
                }
            ]
        }

        try:
            logger.info(f"Creating IAM policy: {bedrock_policy_name}")
            policy = iam.create_policy(
                PolicyName=bedrock_policy_name,
                PolicyDocument=json.dumps(bedrock_policy)
            )
            bedrock_policy_arn = policy['Policy']['Arn']
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.info(f"Policy {bedrock_policy_name} already exists")
                account_id = boto3.client('sts').get_caller_identity()['Account']
                bedrock_policy_arn = f"arn:aws:iam::{account_id}:policy/{bedrock_policy_name}"
            else:
                raise

        # Attach policies to role
        try:
            logger.info("Attaching policies to role...")
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=bedrock_policy_arn
            )
            logger.info("Policies attached successfully")
        except ClientError as e:
            if e.response['Error']['Code'] != 'EntityAlreadyExists':
                raise

        logger.info("\n✅ IAM role and policies set up successfully!")
        return role['Role']['Arn']

    except Exception as e:
        logger.error(f"Error setting up IAM role: {e}")
        raise

if __name__ == "__main__":
    setup_iam_role() 
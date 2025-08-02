#!/usr/bin/env python3
import json
import boto3
import logging
import os
from datetime import datetime
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AWS clients
bedrock_client = boto3.client('bedrock-agent')
lambda_client = boto3.client('lambda')

def load_config():
    """Load the SRE Copilot configuration file."""
    try:
        with open('sre_copilot_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise

def get_lambda_function_arn(function_name):
    """Get the ARN of a Lambda function by name."""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        logger.error(f"Error getting Lambda function ARN: {e}")
        return None

def create_action_group(agent_id, agent_type, lambda_function_name):
    """Create an action group for an agent."""
    try:
        # Get the Lambda function ARN
        lambda_function_arn = get_lambda_function_arn(lambda_function_name)
        if not lambda_function_arn:
            logger.error(f"Could not find Lambda function ARN for {lambda_function_name}")
            return False

        # Get the latest agent version
        try:
            versions_response = bedrock_client.list_agent_versions(
                agentId=agent_id,
                maxResults=1
            )
            if not versions_response['agentVersionSummaries']:
                logger.error(f"No versions found for agent {agent_id}")
                return False
            
            agent_version = versions_response['agentVersionSummaries'][0]['agentVersion']
            logger.info(f"Using agent version {agent_version} for agent {agent_id}")
        except Exception as e:
            logger.error(f"Error getting agent version: {e}")
            return False

        # Define action groups based on agent type
        action_groups = {
            'cloudtrail_agent': {
                'name': 'CloudTrailAnalysis',
                'description': 'Analyzes CloudTrail logs for API errors, security events, and compliance issues',
                'api_schema': {
                    'payload': {
                        'openapi': '3.0.0',
                        'info': {
                            'title': 'CloudTrail Analysis API',
                            'version': '1.0.0'
                        },
                        'paths': {
                            '/analyze-cloudtrail': {
                                'post': {
                                    'summary': 'Analyze CloudTrail logs',
                                    'requestBody': {
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'action': {
                                                            'type': 'string',
                                                            'enum': ['get_api_errors', 'get_security_events', 'get_compliance_events']
                                                        },
                                                        'max_results': {
                                                            'type': 'integer',
                                                            'default': 100
                                                        },
                                                        'start_time': {
                                                            'type': 'string',
                                                            'format': 'date-time'
                                                        },
                                                        'end_time': {
                                                            'type': 'string',
                                                            'format': 'date-time'
                                                        }
                                                    },
                                                    'required': ['action']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Successful analysis',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'statusCode': {
                                                                'type': 'integer'
                                                            },
                                                            'body': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'results': {
                                                                        'type': 'array',
                                                                        'items': {
                                                                            'type': 'object'
                                                                        }
                                                                    },
                                                                    'analysis': {
                                                                        'type': 'object'
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'vpc_agent': {
                'name': 'VPCAnalysis',
                'description': 'Analyzes VPC flow logs for network connectivity issues and security concerns',
                'api_schema': {
                    'payload': {
                        'openapi': '3.0.0',
                        'info': {
                            'title': 'VPC Analysis API',
                            'version': '1.0.0'
                        },
                        'paths': {
                            '/analyze-vpc': {
                                'post': {
                                    'summary': 'Analyze VPC flow logs',
                                    'requestBody': {
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'action': {
                                                            'type': 'string',
                                                            'enum': ['analyze_flow_logs', 'get_rejected_traffic', 'get_security_group_changes']
                                                        },
                                                        'max_results': {
                                                            'type': 'integer',
                                                            'default': 100
                                                        },
                                                        'start_time': {
                                                            'type': 'string',
                                                            'format': 'date-time'
                                                        },
                                                        'end_time': {
                                                            'type': 'string',
                                                            'format': 'date-time'
                                                        }
                                                    },
                                                    'required': ['action']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Successful analysis',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'statusCode': {
                                                                'type': 'integer'
                                                            },
                                                            'body': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'results': {
                                                                        'type': 'array',
                                                                        'items': {
                                                                            'type': 'object'
                                                                        }
                                                                    },
                                                                    'analysis': {
                                                                        'type': 'object'
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'trusted_advisor_agent': {
                'name': 'TrustedAdvisorAnalysis',
                'description': 'Monitors AWS Trusted Advisor for service quotas, security checks, and cost optimization',
                'api_schema': {
                    'payload': {
                        'openapi': '3.0.0',
                        'info': {
                            'title': 'Trusted Advisor Analysis API',
                            'version': '1.0.0'
                        },
                        'paths': {
                            '/analyze-trusted-advisor': {
                                'post': {
                                    'summary': 'Analyze Trusted Advisor checks',
                                    'requestBody': {
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'action': {
                                                            'type': 'string',
                                                            'enum': ['get_service_quotas', 'get_security_checks', 'get_cost_optimization']
                                                        },
                                                        'check_id': {
                                                            'type': 'string'
                                                        },
                                                        'max_results': {
                                                            'type': 'integer',
                                                            'default': 100
                                                        }
                                                    },
                                                    'required': ['action']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Successful analysis',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'statusCode': {
                                                                'type': 'integer'
                                                            },
                                                            'body': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'results': {
                                                                        'type': 'array',
                                                                        'items': {
                                                                            'type': 'object'
                                                                        }
                                                                    },
                                                                    'analysis': {
                                                                        'type': 'object'
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'personal_health_agent': {
                'name': 'PersonalHealthAnalysis',
                'description': 'Monitors AWS Personal Health for maintenance events, service issues, and account notifications',
                'api_schema': {
                    'payload': {
                        'openapi': '3.0.0',
                        'info': {
                            'title': 'Personal Health Analysis API',
                            'version': '1.0.0'
                        },
                        'paths': {
                            '/analyze-personal-health': {
                                'post': {
                                    'summary': 'Analyze Personal Health events',
                                    'requestBody': {
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'action': {
                                                            'type': 'string',
                                                            'enum': ['get_maintenance_events', 'get_service_issues', 'get_account_notifications']
                                                        },
                                                        'max_results': {
                                                            'type': 'integer',
                                                            'default': 100
                                                        },
                                                        'start_time': {
                                                            'type': 'string',
                                                            'format': 'date-time'
                                                        },
                                                        'end_time': {
                                                            'type': 'string',
                                                            'format': 'date-time'
                                                        }
                                                    },
                                                    'required': ['action']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Successful analysis',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'statusCode': {
                                                                'type': 'integer'
                                                            },
                                                            'body': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'results': {
                                                                        'type': 'array',
                                                                        'items': {
                                                                            'type': 'object'
                                                                        }
                                                                    },
                                                                    'analysis': {
                                                                        'type': 'object'
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Create action group using the correct method
        try:
            response = bedrock_client.create_agent_action_group(
                agentId=agent_id,
                agentVersion=agent_version,
                actionGroupName=action_groups[agent_type]['name'],
                description=action_groups[agent_type]['description'],
                apiSchema=action_groups[agent_type]['api_schema'],
                actionGroupExecutor={
                    'lambda': lambda_function_arn
                }
            )
            logger.info(f"Created action group {action_groups[agent_type]['name']} for agent {agent_id}")
            return True
        except bedrock_client.exceptions.ConflictException:
            logger.info(f"Action group {action_groups[agent_type]['name']} already exists for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating action group for agent {agent_id}: {e}")
            return False

    except Exception as e:
        logger.error(f"Error in create_action_group for agent {agent_id}: {e}")
        return False

def create_action_groups():
    """Create action groups for all SRE agents."""
    try:
        load_dotenv()
        region = os.getenv('AWS_REGION', 'us-east-1')
        account_id = boto3.client('sts').get_caller_identity()['Account']

        # Initialize Bedrock Agent client
        bedrock_agent = boto3.client('bedrock-agent')

        # Create CloudTrail agent action group
        try:
            logger.info("Creating CloudTrail agent action group...")
            cloudtrail_response = bedrock_agent.create_agent(
                agentName="SRE-CloudTrail-Analyzer",
                description="Analyzes CloudTrail logs for API errors, security events, and compliance issues",
                instruction="You are a CloudTrail analysis agent specialized in monitoring and analyzing AWS API activity, security events, and compliance.",
                foundationModel="anthropic.claude-v2",
                idleSessionTTLInSeconds=3600,
                roleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole",
                agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole"
            )
            cloudtrail_id = cloudtrail_response['agent']['agentId']
            logger.info(f"CloudTrail agent created with ID: {cloudtrail_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info("CloudTrail agent already exists")
                # Get existing agent ID
                agents = bedrock_agent.list_agents()
                cloudtrail_id = next(a['agentId'] for a in agents['agentSummaries'] if a['agentName'] == "SRE-CloudTrail-Analyzer")
            else:
                raise

        # Create VPC agent action group
        try:
            logger.info("Creating VPC agent action group...")
            vpc_response = bedrock_agent.create_agent(
                agentName="SRE-VPC-Analyzer",
                description="Analyzes VPC flow logs for network connectivity issues and security concerns",
                instruction="You are a VPC analysis agent specialized in monitoring network traffic, analyzing connectivity issues, and identifying security concerns.",
                foundationModel="anthropic.claude-v2",
                idleSessionTTLInSeconds=3600,
                roleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole",
                agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole"
            )
            vpc_id = vpc_response['agent']['agentId']
            logger.info(f"VPC agent created with ID: {vpc_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info("VPC agent already exists")
                # Get existing agent ID
                agents = bedrock_agent.list_agents()
                vpc_id = next(a['agentId'] for a in agents['agentSummaries'] if a['agentName'] == "SRE-VPC-Analyzer")
            else:
                raise

        # Create Trusted Advisor agent action group
        try:
            logger.info("Creating Trusted Advisor agent action group...")
            trusted_advisor_response = bedrock_agent.create_agent(
                agentName="SRE-Trusted-Advisor-Analyzer",
                description="Monitors AWS Trusted Advisor for service quotas, security checks, and cost optimization",
                instruction="You are a Trusted Advisor analysis agent specialized in monitoring service quotas, security recommendations, and cost optimization opportunities.",
                foundationModel="anthropic.claude-v2",
                idleSessionTTLInSeconds=3600,
                roleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole",
                agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole"
            )
            trusted_advisor_id = trusted_advisor_response['agent']['agentId']
            logger.info(f"Trusted Advisor agent created with ID: {trusted_advisor_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info("Trusted Advisor agent already exists")
                # Get existing agent ID
                agents = bedrock_agent.list_agents()
                trusted_advisor_id = next(a['agentId'] for a in agents['agentSummaries'] if a['agentName'] == "SRE-Trusted-Advisor-Analyzer")
            else:
                raise

        # Create Personal Health agent action group
        try:
            logger.info("Creating Personal Health agent action group...")
            personal_health_response = bedrock_agent.create_agent(
                agentName="SRE-Personal-Health-Analyzer",
                description="Monitors AWS Personal Health for maintenance events, service issues, and account notifications",
                instruction="You are a Personal Health analysis agent specialized in monitoring AWS service health, maintenance events, and account-specific notifications.",
                foundationModel="anthropic.claude-v2",
                idleSessionTTLInSeconds=3600,
                roleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole",
                agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/SREKnowledgeBaseRole"
            )
            personal_health_id = personal_health_response['agent']['agentId']
            logger.info(f"Personal Health agent created with ID: {personal_health_id}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info("Personal Health agent already exists")
                # Get existing agent ID
                agents = bedrock_agent.list_agents()
                personal_health_id = next(a['agentId'] for a in agents['agentSummaries'] if a['agentName'] == "SRE-Personal-Health-Analyzer")
            else:
                raise

        # Update config file with agent IDs
        config_path = 'sre_copilot_config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Add or update agent IDs in config
        config_updates = {
            'cloudtrail_agent': {
                'id': cloudtrail_id,
                'name': 'SRE-CloudTrail-Analyzer',
                'description': 'Analyzes CloudTrail logs for API errors, security events, and compliance issues',
                'instruction': 'You are a CloudTrail analysis agent specialized in monitoring and analyzing AWS API activity, security events, and compliance.',
                'model': 'anthropic.claude-v2'
            },
            'vpc_agent': {
                'id': vpc_id,
                'name': 'SRE-VPC-Analyzer',
                'description': 'Analyzes VPC flow logs for network connectivity issues and security concerns',
                'instruction': 'You are a VPC analysis agent specialized in monitoring network traffic, analyzing connectivity issues, and identifying security concerns.',
                'model': 'anthropic.claude-v2'
            },
            'trusted_advisor_agent': {
                'id': trusted_advisor_id,
                'name': 'SRE-Trusted-Advisor-Analyzer',
                'description': 'Monitors AWS Trusted Advisor for service quotas, security checks, and cost optimization',
                'instruction': 'You are a Trusted Advisor analysis agent specialized in monitoring service quotas, security recommendations, and cost optimization opportunities.',
                'model': 'anthropic.claude-v2'
            },
            'personal_health_agent': {
                'id': personal_health_id,
                'name': 'SRE-Personal-Health-Analyzer',
                'description': 'Monitors AWS Personal Health for maintenance events, service issues, and account notifications',
                'instruction': 'You are a Personal Health analysis agent specialized in monitoring AWS service health, maintenance events, and account-specific notifications.',
                'model': 'anthropic.claude-v2'
            }
        }

        config.update(config_updates)

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        logger.info("Updated config file with agent IDs")
        logger.info("\n✅ All action groups created successfully!")

    except Exception as e:
        logger.error(f"Error creating action groups: {e}")
        raise

if __name__ == "__main__":
    create_action_groups() 
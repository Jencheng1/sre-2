#!/usr/bin/env python3
import boto3
import os
import logging
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_lambda_function_arn(lambda_client, function_name):
    """Get the ARN of a Lambda function by name."""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        logger.error(f"Error getting Lambda function ARN: {e}")
        return None

def create_action_groups():
    """Create action groups for all SRE agents."""
    try:
        load_dotenv()
        region = os.getenv('AWS_REGION', 'us-east-1')
        account_id = boto3.client('sts').get_caller_identity()['Account']

        # Initialize AWS clients
        bedrock_agent = boto3.client('bedrock-agent')
        lambda_client = boto3.client('lambda')

        # Load config file
        with open('sre_copilot_config.json', 'r') as f:
            config = json.load(f)

        # Define the action groups
        action_groups = {
            'cloudtrail_agent': {
                'name': 'CloudTrailAnalysis',
                'description': 'Analyzes CloudTrail logs for API errors, security events, and compliance issues',
                'lambda_name': 'sre-cloudtrail-agent-lambda',
                'api_schema': {
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
            },
            'vpc_agent': {
                'name': 'VPCAnalysis',
                'description': 'Analyzes VPC flow logs for network connectivity issues and security concerns',
                'lambda_name': 'sre-vpc-agent-lambda',
                'api_schema': {
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
            },
            'trusted_advisor_agent': {
                'name': 'TrustedAdvisorAnalysis',
                'description': 'Monitors AWS Trusted Advisor for service quotas, security checks, and cost optimization',
                'lambda_name': 'sre-trusted-advisor-agent-lambda',
                'api_schema': {
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
            },
            'personal_health_agent': {
                'name': 'PersonalHealthAnalysis',
                'description': 'Monitors AWS Personal Health for maintenance events, service issues, and account notifications',
                'lambda_name': 'sre-personal-health-agent-lambda',
                'api_schema': {
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

        # Create action groups for each agent
        for agent_type, group_config in action_groups.items():
            if agent_type not in config:
                logger.warning(f"Agent type {agent_type} not found in configuration")
                continue

            agent_id = config[agent_type]['id']
            lambda_arn = get_lambda_function_arn(lambda_client, group_config['lambda_name'])
            if not lambda_arn:
                logger.error(f"Could not find Lambda function ARN for {group_config['lambda_name']}")
                continue

            try:
                logger.info(f"Creating action group for {agent_type}...")
                response = bedrock_agent.create_agent_action_group(
                    agentId=agent_id,
                    actionGroupName=group_config['name'],
                    description=group_config['description'],
                    apiSchema=group_config['api_schema'],
                    actionGroupExecutor={
                        'lambda': lambda_arn
                    }
                )
                logger.info(f"Created action group {group_config['name']} for agent {agent_id}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConflictException':
                    logger.info(f"Action group {group_config['name']} already exists for agent {agent_id}")
                else:
                    logger.error(f"Error creating action group for {agent_type}: {e}")

        logger.info("\n✅ All action groups created successfully!")

    except Exception as e:
        logger.error(f"Error creating action groups: {e}")
        raise

if __name__ == "__main__":
    create_action_groups() 
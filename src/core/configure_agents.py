#!/usr/bin/env python3

import boto3
import json
import time
import logging
import argparse
from botocore.exceptions import ClientError
import os
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class SRECopilotAgentConfigurator:
    def __init__(self, config_file=None, region='us-east-1'):
        """Initialize the SRE Copilot agent configurator."""
        self.region = region
        self.config = self._load_config(config_file) if config_file else self._default_config()
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

    def _load_config(self, config_file):
        """Load configuration from file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found.")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error parsing configuration file {config_file}.")
            raise
            
    def _default_config(self):
        """Create default configuration for SRE Copilot agents."""
        return {
            'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
            'create_agents': True,
            'supervisor_agent': {
                'name': 'SRE-Supervisor',
                'description': 'Coordinates analysis and response for SRE incidents',
                'instruction': 'You are an SRE supervisor agent responsible for coordinating incident analysis and response. Your role is to delegate tasks to specialized agents and synthesize their findings.',
                'model': 'anthropic.claude-v2'
            },
            'log_analysis_agent': {
                'name': 'SRE-Log-Analyzer',
                'description': 'Analyzes log data for patterns and anomalies',
                'instruction': 'You are a log analysis agent specialized in identifying patterns, anomalies, and root causes in system logs. Focus on extracting meaningful insights from log data.',
                'model': 'anthropic.claude-v2'
            },
            'metrics_analysis_agent': {
                'name': 'SRE-Metrics-Analyzer',
                'description': 'Analyzes time-series metrics data',
                'instruction': 'You are a metrics analysis agent specialized in analyzing time-series data, identifying trends, and detecting anomalies in system metrics.',
                'model': 'anthropic.claude-v2'
            },
            'cloudtrail_agent': {
                'name': 'SRE-CloudTrail-Analyzer',
                'description': 'Analyzes AWS CloudTrail logs for security and compliance',
                'instruction': 'You are a CloudTrail analysis agent specialized in monitoring and analyzing AWS API activity. Focus on identifying security issues, compliance violations, and unauthorized access attempts.',
                'model': 'anthropic.claude-v2'
            },
            'vpc_agent': {
                'name': 'SRE-VPC-Analyzer',
                'description': 'Analyzes VPC Flow Logs for network traffic patterns',
                'instruction': 'You are a VPC analysis agent specialized in analyzing network traffic patterns from VPC Flow Logs. Focus on identifying suspicious traffic, network bottlenecks, and security group violations.',
                'model': 'anthropic.claude-v2'
            },
            'trusted_advisor_agent': {
                'name': 'SRE-Trusted-Advisor-Analyzer',
                'description': 'Analyzes AWS Trusted Advisor recommendations',
                'instruction': 'You are a Trusted Advisor analysis agent specialized in processing AWS service quotas, security recommendations, and cost optimization opportunities. Focus on identifying critical service limits, security risks, and cost savings.',
                'model': 'anthropic.claude-v2'
            },
            'personal_health_agent': {
                'name': 'SRE-Personal-Health-Analyzer',
                'description': 'Analyzes AWS Personal Health Dashboard events',
                'instruction': 'You are a Personal Health analysis agent specialized in monitoring AWS service health events. Focus on identifying service issues, maintenance events, and account-specific notifications that may impact system reliability.',
                'model': 'anthropic.claude-v2'
            },
            'knowledge_base': {
                'name': 'sre-copilot-knowledge-base',
                'description': 'Knowledge base for storing historical incident data',
                'data_source_config': {
                    'collectionId': 'sre-copilot-collection',
                    'vectorIndexName': 'sre-copilot-index',
                    'fieldMapping': {
                        'text_field': 'description',
                        'metadata_fields': ['incident_id', 'root_cause', 'resolution', 'services_affected']
                    }
                }
            }
        }

    def create_bedrock_agent(self, agent_config):
        """Create a Bedrock agent."""
        try:
            logger.info(f"Creating agent: {agent_config['name']}")
            
            # Create the agent
            response = self.bedrock_client.create_agent(
                agentName=agent_config['name'],
                description=agent_config['description'],
                instruction=agent_config['instruction'],
                foundationModel=agent_config['model'],
                idleSessionTTLInSeconds=3600,
                agentResourceRoleArn=f"arn:aws:iam::{self.account_id}:role/service-role/AmazonBedrockExecutionRoleForAgents_{self.account_id}"
            )
            
            # Extract the agent ID from the response
            if 'agent' in response and 'agentId' in response['agent']:
                agent_id = response['agent']['agentId']
                logger.info(f"Agent created with ID: {agent_id}")
                return agent_id
            else:
                raise ValueError(f"Could not find agent ID in response for agent {agent_config['name']}")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                # Agent already exists, try to get its ID
                logger.info(f"Agent {agent_config['name']} already exists, retrieving its ID...")
                
                # List all agents to find the one with matching name
                try:
                    paginator = self.bedrock_client.get_paginator('list_agents')
                    for page in paginator.paginate():
                        for agent in page.get('agentSummaries', []):
                            if agent['agentName'] == agent_config['name']:
                                agent_id = agent['agentId']
                                logger.info(f"Found existing agent ID: {agent_id}")
                                return agent_id
                    
                    # If we couldn't find the agent by listing, try to extract from error message
                    error_message = e.response['Error']['Message']
                    if 'id:' in error_message:
                        # Extract just the ID part using regex
                        match = re.search(r'id:\s*([0-9a-zA-Z]{10})', error_message)
                        if match:
                            agent_id = match.group(1)
                            logger.info(f"Found existing agent ID from error message: {agent_id}")
                            return agent_id
                    
                    raise ValueError(f"Could not find agent ID for agent {agent_config['name']}")
                except Exception as list_error:
                    logger.error(f"Error listing agents: {list_error}")
                    raise
            else:
                logger.error(f"Error creating agent {agent_config['name']}: {e}")
                raise
        except Exception as e:
            logger.error(f"Error creating agent {agent_config['name']}: {e}")
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

    def validate_lambda_function(self, function_name):
        """Validate that a Lambda function exists and is accessible."""
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            lambda_client.get_function(FunctionName=function_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"Lambda function {function_name} does not exist")
            else:
                logger.error(f"Error validating Lambda function {function_name}: {e}")
            return False

    def create_agent_action_group(self, agent_id, agent_type):
        """Create an action group for the agent."""
        try:
            # Get the latest agent version
            agent = self.bedrock_client.get_agent(agentId=agent_id)
            agent_version = agent['agentVersion']

            # Define action groups based on agent type
            action_groups = {
                'log_analysis_agent': {
                    'name': 'LogAnalysisActionGroup',
                    'description': 'Action group for analyzing log data',
                    'apiSchema': {
                        'openapi': '3.0.0',
                        'info': {'title': 'Log Analysis API', 'version': '1.0.0'},
                        'paths': {
                            '/analyze-logs': {
                                'post': {
                                    'summary': 'Analyze log data',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'log_data': {'type': 'array', 'items': {'type': 'string'}},
                                                        'time_range': {'type': 'string'},
                                                        'severity_threshold': {'type': 'string'}
                                                    },
                                                    'required': ['log_data']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'findings': {'type': 'array', 'items': {'type': 'object'}},
                                                            'summary': {'type': 'string'},
                                                            'recommendations': {'type': 'array', 'items': {'type': 'string'}}
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
                'metrics_analysis_agent': {
                    'name': 'MetricsAnalysisActionGroup',
                    'description': 'Action group for analyzing metrics data',
                    'apiSchema': {
                        'openapi': '3.0.0',
                        'info': {'title': 'Metrics Analysis API', 'version': '1.0.0'},
                        'paths': {
                            '/analyze-metrics': {
                                'post': {
                                    'summary': 'Analyze metrics data',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'metrics_data': {'type': 'array', 'items': {'type': 'object'}},
                                                        'time_range': {'type': 'string'},
                                                        'threshold': {'type': 'number'}
                                                    },
                                                    'required': ['metrics_data']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'anomalies': {'type': 'array', 'items': {'type': 'object'}},
                                                            'trends': {'type': 'array', 'items': {'type': 'object'}},
                                                            'summary': {'type': 'object'}
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
                'cloudtrail_agent': {
                    'name': 'CloudTrailActionGroup',
                    'description': 'Action group for analyzing CloudTrail logs',
                    'apiSchema': {
                        'openapi': '3.0.0',
                        'info': {'title': 'CloudTrail Analysis API', 'version': '1.0.0'},
                        'paths': {
                            '/get-api-errors': {
                                'post': {
                                    'summary': 'Get API errors from CloudTrail',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'max_results': {'type': 'integer'},
                                                        'start_time': {'type': 'string'},
                                                        'end_time': {'type': 'string'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'API error analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'api_errors': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            '/get-security-events': {
                                'post': {
                                    'summary': 'Get security events from CloudTrail',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'max_results': {'type': 'integer'},
                                                        'start_time': {'type': 'string'},
                                                        'end_time': {'type': 'string'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Security event analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'security_events': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            '/get-compliance-events': {
                                'post': {
                                    'summary': 'Get compliance events from CloudTrail',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'max_results': {'type': 'integer'},
                                                        'start_time': {'type': 'string'},
                                                        'end_time': {'type': 'string'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Compliance event analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'compliance_events': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
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
                    'name': 'VPCActionGroup',
                    'description': 'Action group for analyzing VPC flow logs',
                    'apiSchema': {
                        'openapi': '3.0.0',
                        'info': {'title': 'VPC Analysis API', 'version': '1.0.0'},
                        'paths': {
                            '/analyze-flow-logs': {
                                'post': {
                                    'summary': 'Analyze VPC flow logs',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'log_group': {'type': 'string'},
                                                        'time_range': {'type': 'string'},
                                                        'max_results': {'type': 'integer'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Flow log analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'flow_logs': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'},
                                                            'issues': {'type': 'array', 'items': {'type': 'object'}}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            '/get-rejected-traffic': {
                                'post': {
                                    'summary': 'Get rejected traffic from VPC flow logs',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'log_group': {'type': 'string'},
                                                        'time_range': {'type': 'string'},
                                                        'max_results': {'type': 'integer'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Rejected traffic analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'rejected_traffic': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            '/get-security-group-changes': {
                                'post': {
                                    'summary': 'Get security group changes',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {}
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Security group change analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'security_group_issues': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            '/get-network-acl-changes': {
                                'post': {
                                    'summary': 'Get network ACL changes',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {}
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Network ACL change analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'network_acl_issues': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
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
                    'name': 'TrustedAdvisorActionGroup',
                    'description': 'Action group for analyzing Trusted Advisor checks',
                    'apiSchema': {
                        'openapi': '3.0.0',
                        'info': {'title': 'Trusted Advisor Analysis API', 'version': '1.0.0'},
                        'paths': {
                            '/get-service-quotas': {
                                'post': {
                                    'summary': 'Get service quota checks',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'check_id': {'type': 'string'},
                                                        'max_results': {'type': 'integer'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Service quota check results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'service_quotas': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            '/get-security-checks': {
                                'post': {
                                    'summary': 'Get security checks',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'check_id': {'type': 'string'},
                                                        'max_results': {'type': 'integer'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Security check results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'security_checks': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            '/get-cost-optimization': {
                                'post': {
                                    'summary': 'Get cost optimization checks',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'check_id': {'type': 'string'},
                                                        'max_results': {'type': 'integer'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Cost optimization check results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'cost_optimization': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
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
                    'name': 'PersonalHealthActionGroup',
                    'description': 'Action group for analyzing AWS Personal Health events',
                    'apiSchema': {
                        'openapi': '3.0.0',
                        'info': {'title': 'Personal Health Analysis API', 'version': '1.0.0'},
                        'paths': {
                            '/get-maintenance-events': {
                                'post': {
                                    'summary': 'Get maintenance events',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'max_results': {'type': 'integer'},
                                                        'start_time': {'type': 'string'},
                                                        'end_time': {'type': 'string'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Maintenance event analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'maintenance_events': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            '/get-service-issues': {
                                'post': {
                                    'summary': 'Get service issues',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'max_results': {'type': 'integer'},
                                                        'start_time': {'type': 'string'},
                                                        'end_time': {'type': 'string'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Service issue analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'service_issues': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            '/get-account-notifications': {
                                'post': {
                                    'summary': 'Get account notifications',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'max_results': {'type': 'integer'},
                                                        'start_time': {'type': 'string'},
                                                        'end_time': {'type': 'string'}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Account notification analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'account_notifications': {'type': 'array', 'items': {'type': 'object'}},
                                                            'analysis': {'type': 'object'}
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
                'supervisor_agent': {
                    'name': 'SupervisorActionGroup',
                    'description': 'Action group for coordinating incident response',
                    'apiSchema': {
                        'openapi': '3.0.0',
                        'info': {'title': 'Supervisor API', 'version': '1.0.0'},
                        'paths': {
                            '/coordinate-response': {
                                'post': {
                                    'summary': 'Coordinate incident response',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'incident_data': {'type': 'object'},
                                                        'analysis_results': {'type': 'array', 'items': {'type': 'object'}}
                                                    },
                                                    'required': ['incident_data']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Response plan',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'incident_priority': {'type': 'string'},
                                                            'findings': {'type': 'array', 'items': {'type': 'object'}},
                                                            'action_items': {'type': 'array', 'items': {'type': 'object'}},
                                                            'recommendations': {'type': 'array', 'items': {'type': 'string'}}
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

            if agent_type not in action_groups:
                logging.warning(f"No action group defined for agent type: {agent_type}")
                return None

            action_group_config = action_groups[agent_type]

            # Check if action group already exists
            try:
                existing_action_groups = self.bedrock_client.list_agent_action_groups(
                    agentId=agent_id,
                    agentVersion=agent_version
                )['agentActionGroups']

                for group in existing_action_groups:
                    if group['actionGroupName'] == action_group_config['name']:
                        logging.info(f"Action group {action_group_config['name']} already exists with ID: {group['actionGroupId']}")
                        return group['actionGroupId']

            except self.bedrock_client.exceptions.ResourceNotFoundException:
                pass

            # Create new action group
            lambda_arn = self._get_lambda_function_arn(agent_type)
            response = self.bedrock_client.create_agent_action_group(
                agentId=agent_id,
                agentVersion=agent_version,
                actionGroupName=action_group_config['name'],
                actionGroupDescription=action_group_config['description'],
                apiSchema=json.dumps(action_group_config['apiSchema']),
                actionGroupExecutor={
                    'lambda': {
                        'lambdaArn': lambda_arn
                    }
                }
            )

            logging.info(f"Created action group {action_group_config['name']} with ID: {response['agentActionGroup']['actionGroupId']}")
            return response['agentActionGroup']['actionGroupId']

        except self.bedrock_client.exceptions.ConflictException as e:
            logging.warning(f"Action group already exists: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error creating action group: {str(e)}")
            raise

    def create_agent_version(self, agent_id, agent_type):
        """Create a new version for the agent."""
        try:
            # Get the latest agent version
            agent = self.bedrock_client.get_agent(agentId=agent_id)
            current_version = agent['agentVersion']

            # Create action group for the agent
            action_group_id = self.create_agent_action_group(agent_id, agent_type)
            if not action_group_id:
                logging.error(f"Failed to create action group for agent {agent_type}")
                return None

            # Prepare the version configuration
            version_config = {
                'log_analysis_agent': {
                    'name': 'LogAnalysisVersion',
                    'description': 'Version for analyzing log data',
                    'instructions': 'Analyze log data to identify patterns, anomalies, and potential issues.'
                },
                'metrics_analysis_agent': {
                    'name': 'MetricsAnalysisVersion',
                    'description': 'Version for analyzing metrics data',
                    'instructions': 'Analyze metrics data to identify trends, anomalies, and performance issues.'
                },
                'cloudtrail_agent': {
                    'name': 'CloudTrailVersion',
                    'description': 'Version for analyzing CloudTrail logs',
                    'instructions': '''Monitor and analyze CloudTrail logs to identify:
1. API errors and unauthorized access attempts
2. Security-related events and potential breaches
3. Compliance violations and policy changes
4. Service usage patterns and anomalies
Focus on providing actionable insights and recommendations for security and compliance.'''
                },
                'vpc_agent': {
                    'name': 'VPCVersion',
                    'description': 'Version for analyzing VPC flow logs',
                    'instructions': '''Monitor and analyze VPC flow logs to identify:
1. Network traffic patterns and anomalies
2. Security group and NACL violations
3. Rejected traffic and potential attacks
4. Network performance issues
Focus on providing actionable insights for network security and optimization.'''
                },
                'trusted_advisor_agent': {
                    'name': 'TrustedAdvisorVersion',
                    'description': 'Version for analyzing Trusted Advisor checks',
                    'instructions': '''Monitor and analyze Trusted Advisor checks for:
1. Service quotas and limits
2. Security best practices
3. Cost optimization opportunities
4. Performance recommendations
Focus on providing actionable insights for improving security, performance, and cost efficiency.'''
                },
                'personal_health_agent': {
                    'name': 'PersonalHealthVersion',
                    'description': 'Version for analyzing AWS Personal Health events',
                    'instructions': '''Monitor and analyze AWS Personal Health events for:
1. Scheduled maintenance events
2. Service issues and disruptions
3. Account notifications and alerts
4. Security and compliance updates
Focus on providing actionable insights for maintaining service availability and security.'''
                },
                'supervisor_agent': {
                    'name': 'SupervisorVersion',
                    'description': 'Version for coordinating incident response',
                    'instructions': 'Coordinate incident response by analyzing findings from specialized agents and providing actionable recommendations.'
                }
            }

            if agent_type not in version_config:
                logging.warning(f"No version configuration defined for agent type: {agent_type}")
                return None

            config = version_config[agent_type]

            # Create new agent version
            response = self.bedrock_client.create_agent_version(
                agentId=agent_id,
                agentName=config['name'],
                agentVersion=str(int(current_version) + 1) if current_version.isdigit() else '1',
                instruction=config['instructions'],
                description=config['description'],
                actionGroupIds=[action_group_id]
            )

            logging.info(f"Created agent version {response['agentVersion']['agentVersion']} for {agent_type}")
            return response['agentVersion']['agentVersion']

        except self.bedrock_client.exceptions.ConflictException as e:
            logging.warning(f"Agent version already exists: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error creating agent version: {str(e)}")
            raise

    def configure_agents(self):
        """Configure all SRE Copilot agents."""
        try:
            # Create specialized agents first
            log_analysis_agent = self.create_bedrock_agent(self.config['log_analysis_agent'])
            logger.info(f"Created log analysis agent: {log_analysis_agent}")

            metrics_analysis_agent = self.create_bedrock_agent(self.config['metrics_analysis_agent'])
            logger.info(f"Created metrics analysis agent: {metrics_analysis_agent}")

            # Create new specialized agents
            cloudtrail_agent = self.create_bedrock_agent(self.config['cloudtrail_agent'])
            logger.info(f"Created CloudTrail agent: {cloudtrail_agent}")

            vpc_agent = self.create_bedrock_agent(self.config['vpc_agent'])
            logger.info(f"Created VPC agent: {vpc_agent}")

            trusted_advisor_agent = self.create_bedrock_agent(self.config['trusted_advisor_agent'])
            logger.info(f"Created Trusted Advisor agent: {trusted_advisor_agent}")

            personal_health_agent = self.create_bedrock_agent(self.config['personal_health_agent'])
            logger.info(f"Created Personal Health agent: {personal_health_agent}")

            # Create supervisor agent last
            supervisor_agent = self.create_bedrock_agent(self.config['supervisor_agent'])
            logger.info(f"Created supervisor agent: {supervisor_agent}")

            # Create action groups for all agents
            logger.info("Creating action groups for all agents...")
            
            # Create action group for log analysis agent
            log_analysis_action_group = self.create_agent_action_group(log_analysis_agent, 'log_analysis_agent')
            logger.info(f"Created action group for log analysis agent: {log_analysis_action_group}")
            
            # Create action group for metrics analysis agent
            metrics_analysis_action_group = self.create_agent_action_group(metrics_analysis_agent, 'metrics_analysis_agent')
            logger.info(f"Created action group for metrics analysis agent: {metrics_analysis_action_group}")
            
            # Create action group for CloudTrail agent
            cloudtrail_action_group = self.create_agent_action_group(cloudtrail_agent, 'cloudtrail_agent')
            logger.info(f"Created action group for CloudTrail agent: {cloudtrail_action_group}")
            
            # Create action group for VPC agent
            vpc_action_group = self.create_agent_action_group(vpc_agent, 'vpc_agent')
            logger.info(f"Created action group for VPC agent: {vpc_action_group}")
            
            # Create action group for Trusted Advisor agent
            trusted_advisor_action_group = self.create_agent_action_group(trusted_advisor_agent, 'trusted_advisor_agent')
            logger.info(f"Created action group for Trusted Advisor agent: {trusted_advisor_action_group}")
            
            # Create action group for Personal Health agent
            personal_health_action_group = self.create_agent_action_group(personal_health_agent, 'personal_health_agent')
            logger.info(f"Created action group for Personal Health agent: {personal_health_action_group}")
            
            # Create action group for supervisor agent
            supervisor_action_group = self.create_agent_action_group(supervisor_agent, 'supervisor_agent')
            logger.info(f"Created action group for supervisor agent: {supervisor_action_group}")

            # Save agent IDs to config file
            config = self.config.copy()
            config['log_analysis_agent']['id'] = log_analysis_agent
            config['metrics_analysis_agent']['id'] = metrics_analysis_agent
            config['cloudtrail_agent']['id'] = cloudtrail_agent
            config['vpc_agent']['id'] = vpc_agent
            config['trusted_advisor_agent']['id'] = trusted_advisor_agent
            config['personal_health_agent']['id'] = personal_health_agent
            config['supervisor_agent']['id'] = supervisor_agent

            with open('sre_copilot_config.json', 'w') as f:
                json.dump(config, f, indent=4)

            logger.info("Successfully configured all SRE Copilot agents")
            return True

        except Exception as e:
            logger.error(f"Error configuring agents: {str(e)}")
            return False

def main():
    """Main function to configure SRE Copilot agents."""
    parser = argparse.ArgumentParser(description='Configure SRE Copilot agents.')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    try:
        configurator = SRECopilotAgentConfigurator(config_file=args.config, region=args.region)
        configurator.configure_agents()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()

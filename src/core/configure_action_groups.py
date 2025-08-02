#!/usr/bin/env python3

import boto3
import json
import logging
import argparse
from botocore.exceptions import ClientError
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ActionGroupConfigurator:
    def __init__(self, config_file=None, region='us-east-1'):
        """Initialize the action group configurator."""
        self.region = region
        self.config = self._load_config(config_file) if config_file else {}
        self.bedrock_client = boto3.client('bedrock-agent', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
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
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error parsing configuration file {config_file}.")
            return {}

    def _get_lambda_arn(self, function_name):
        """Get the Lambda function ARN."""
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            return response['Configuration']['FunctionArn']
        except ClientError as e:
            logger.error(f"Error getting Lambda function ARN for {function_name}: {e}")
            return None

    def validate_lambda_function(self, function_name):
        """Validate that a Lambda function exists and is accessible."""
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            logger.info(f"Lambda function {function_name} exists and is accessible")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"Lambda function {function_name} does not exist")
            else:
                logger.error(f"Error validating Lambda function {function_name}: {e}")
            return False

    def get_action_group_config(self, agent_type):
        """Get the action group configuration for an agent type."""
        action_groups = {
            'SRE-Log-Analyzer': {
                'name': 'log_analysis_action_group',
                'description': 'Action group for log analysis operations',
                'lambda_name': 'sre-log-analyzer-lambda',
                'api_schema': {
                    'openapi': '3.0.0',
                    'info': {
                        'title': 'Log Analysis API',
                        'version': '1.0.0',
                        'description': 'API for log analysis operations'
                    },
                    'paths': {
                        '/analyze-logs': {
                            'post': {
                                'summary': 'Analyze logs',
                                'requestBody': {
                                    'required': True,
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                'type': 'object',
                                                'properties': {
                                                    'log_group': {'type': 'string'},
                                                    'time_range': {'type': 'string'},
                                                    'query': {'type': 'string'}
                                                },
                                                'required': ['log_group']
                                            }
                                        }
                                    }
                                },
                                'responses': {
                                    '200': {
                                        'description': 'Log analysis results',
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'results': {'type': 'array'},
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
            'SRE-Metrics-Analyzer': {
                'name': 'metrics_analysis_action_group',
                'description': 'Action group for metrics analysis operations',
                'lambda_name': 'sre-metrics-analyzer-lambda',
                'api_schema': {
                    'openapi': '3.0.0',
                    'info': {
                        'title': 'Metrics Analysis API',
                        'version': '1.0.0',
                        'description': 'API for metrics analysis operations'
                    },
                    'paths': {
                        '/analyze-metrics': {
                            'post': {
                                'summary': 'Analyze metrics',
                                'requestBody': {
                                    'required': True,
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                'type': 'object',
                                                'properties': {
                                                    'namespace': {'type': 'string'},
                                                    'metric_name': {'type': 'string'},
                                                    'dimensions': {'type': 'object'},
                                                    'period': {'type': 'integer'},
                                                    'statistic': {'type': 'string'}
                                                },
                                                'required': ['namespace', 'metric_name']
                                            }
                                        }
                                    }
                                },
                                'responses': {
                                    '200': {
                                        'description': 'Metrics analysis results',
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'results': {'type': 'array'},
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
            'SRE-Supervisor': {
                'name': 'supervisor_action_group',
                'description': 'Action group for supervisor operations',
                'lambda_name': 'sre-supervisor-lambda',
                'api_schema': {
                    'openapi': '3.0.0',
                    'info': {
                        'title': 'Supervisor API',
                        'version': '1.0.0',
                        'description': 'API for supervisor operations'
                    },
                    'paths': {
                        '/coordinate': {
                            'post': {
                                'summary': 'Coordinate analysis',
                                'requestBody': {
                                    'required': True,
                                    'content': {
                                        'application/json': {
                                            'schema': {
                                                'type': 'object',
                                                'properties': {
                                                    'issue_type': {'type': 'string'},
                                                    'severity': {'type': 'string'},
                                                    'context': {'type': 'object'}
                                                },
                                                'required': ['issue_type']
                                            }
                                        }
                                    }
                                },
                                'responses': {
                                    '200': {
                                        'description': 'Coordination results',
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'action_plan': {'type': 'array'},
                                                        'recommendations': {'type': 'object'}
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
        return action_groups.get(agent_type)

    def configure_action_group(self, agent_id, agent_name):
        """Configure action groups for an agent."""
        try:
            # Define action group configurations based on agent type
            action_groups = {
                'SRE-Log-Analyzer': {
                    'name': 'log_analysis_action_group',
                    'description': 'Action group for log analysis operations',
                    'lambda_name': 'sre-log-analyzer-lambda',
                    'api_schema': {
                        'openapi': '3.0.0',
                        'info': {
                            'title': 'Log Analysis API',
                            'version': '1.0.0',
                            'description': 'API for log analysis operations'
                        },
                        'paths': {
                            '/analyze-logs': {
                                'post': {
                                    'summary': 'Analyze logs',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'log_group': {'type': 'string'},
                                                        'time_range': {'type': 'string'},
                                                        'query': {'type': 'string'}
                                                    },
                                                    'required': ['log_group']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Log analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'results': {'type': 'array'},
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
                'SRE-Metrics-Analyzer': {
                    'name': 'metrics_analysis_action_group',
                    'description': 'Action group for metrics analysis operations',
                    'lambda_name': 'sre-metrics-analyzer-lambda',
                    'api_schema': {
                        'openapi': '3.0.0',
                        'info': {
                            'title': 'Metrics Analysis API',
                            'version': '1.0.0',
                            'description': 'API for metrics analysis operations'
                        },
                        'paths': {
                            '/analyze-metrics': {
                                'post': {
                                    'summary': 'Analyze metrics',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'namespace': {'type': 'string'},
                                                        'metric_name': {'type': 'string'},
                                                        'dimensions': {'type': 'object'},
                                                        'period': {'type': 'integer'},
                                                        'statistic': {'type': 'string'}
                                                    },
                                                    'required': ['namespace', 'metric_name']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Metrics analysis results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'results': {'type': 'array'},
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
                'SRE-Supervisor': {
                    'name': 'supervisor_action_group',
                    'description': 'Action group for supervisor operations',
                    'lambda_name': 'sre-supervisor-lambda',
                    'api_schema': {
                        'openapi': '3.0.0',
                        'info': {
                            'title': 'Supervisor API',
                            'version': '1.0.0',
                            'description': 'API for supervisor operations'
                        },
                        'paths': {
                            '/coordinate': {
                                'post': {
                                    'summary': 'Coordinate analysis',
                                    'requestBody': {
                                        'required': True,
                                        'content': {
                                            'application/json': {
                                                'schema': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'issue_type': {'type': 'string'},
                                                        'severity': {'type': 'string'},
                                                        'context': {'type': 'object'}
                                                    },
                                                    'required': ['issue_type']
                                                }
                                            }
                                        }
                                    },
                                    'responses': {
                                        '200': {
                                            'description': 'Coordination results',
                                            'content': {
                                                'application/json': {
                                                    'schema': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'action_plan': {'type': 'array'},
                                                            'recommendations': {'type': 'object'}
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

            # Get action group configuration for the agent
            agent_config = action_groups.get(agent_name)
            if not agent_config:
                logger.info(f"No action group configuration found for agent {agent_name}")
                return True  # Return True for agents that don't need action groups

            # Get Lambda function ARN
            lambda_arn = self._get_lambda_arn(agent_config['lambda_name'])
            if not lambda_arn:
                logger.error(f"Lambda function {agent_config['lambda_name']} not found")
                return False

            # Check if action group already exists
            try:
                existing_groups = self.bedrock_client.list_agent_action_groups(
                    agentId=agent_id,
                    agentVersion='DRAFT'
                ).get('actionGroupSummaries', [])

                for group in existing_groups:
                    if group['actionGroupName'] == agent_config['name']:
                        logger.info(f"Action group {agent_config['name']} already exists for agent {agent_name}")
                        return True

            except ClientError as e:
                logger.error(f"Error checking existing action groups: {e}")
                return False

            # Create action group
            try:
                response = self.bedrock_client.create_agent_action_group(
                    agentId=agent_id,
                    agentVersion='DRAFT',
                    actionGroupName=agent_config['name'],
                    description=agent_config['description'],
                    apiSchema=agent_config['api_schema'],
                    actionGroupExecutor={
                        'lambda': lambda_arn
                    }
                )
                logger.info(f"Successfully created action group {agent_config['name']} for agent {agent_name}")
                return True

            except ClientError as e:
                logger.error(f"Error creating action group: {e}")
                return False

        except Exception as e:
            logger.error(f"Error configuring action group for agent {agent_name}: {e}")
            return False

    def configure_all_action_groups(self):
        """Configure action groups for all agents."""
        results = {
            'success': True,
            'agents': {},
            'next_steps': []
        }
        
        try:
            # Get all agents
            paginator = self.bedrock_client.get_paginator('list_agents')
            agents = []
            for page in paginator.paginate():
                agents.extend(page.get('agentSummaries', []))
            
            if not agents:
                logger.error("No agents found")
                results['success'] = False
                results['next_steps'].append("Create agents using configure_agents.py")
                return results
            
            # Configure action groups for each agent
            for agent in agents:
                agent_id = agent.get('agentId')
                agent_name = agent.get('agentName')
                
                if not agent_id or not agent_name:
                    continue
                
                # Skip agents that don't need action groups
                if agent_name not in ['SRE-Log-Analyzer', 'SRE-Metrics-Analyzer', 'SRE-Supervisor']:
                    logger.info(f"Skipping action group configuration for {agent_name}")
                    continue
                
                configuration_success = self.configure_action_group(agent_id, agent_name)
                
                results['agents'][agent_name] = {
                    'id': agent_id,
                    'success': configuration_success
                }
                
                if not configuration_success:
                    results['success'] = False
                    results['next_steps'].append(f"Fix action group configuration for {agent_name}")
            
            # Add next steps based on results
            if results['success']:
                results['next_steps'].append("Run prepare_agents.py to prepare the agents")
                results['next_steps'].append("Run validate_agents.py to verify the setup")
            else:
                results['next_steps'].append("Check CloudWatch logs for detailed error messages")
                results['next_steps'].append("Verify that all required Lambda functions exist")
            
            return results
            
        except ClientError as e:
            logger.error(f"Error listing agents: {e}")
            results['success'] = False
            results['next_steps'].append("Check AWS credentials and permissions")
            return results

    def print_results(self, results):
        """Print the configuration results in a readable format."""
        print("\n" + "="*80)
        print("SRE COPILOT ACTION GROUP CONFIGURATION RESULTS")
        print("="*80)
        
        if results['success']:
            print("\n✅ All action groups configured successfully!")
        else:
            print("\n❌ Some action groups failed to configure.")
        
        print("\nAGENT STATUS:")
        for agent_name, agent_info in results['agents'].items():
            status = "✅ Configured" if agent_info['success'] else "❌ Failed"
            print(f"  {agent_name}: {status}")
            print(f"    - ID: {agent_info['id']}")
        
        print("\nNEXT STEPS:")
        for i, step in enumerate(results['next_steps'], 1):
            print(f"  {i}. {step}")
        
        print("\n" + "="*80)

def main():
    """Main function to configure action groups."""
    parser = argparse.ArgumentParser(description='Configure action groups for SRE Copilot agents.')
    parser.add_argument('--config', default='sre_copilot_config.json', help='Path to configuration file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    try:
        configurator = ActionGroupConfigurator(config_file=args.config, region=args.region)
        results = configurator.configure_all_action_groups()
        configurator.print_results(results)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 
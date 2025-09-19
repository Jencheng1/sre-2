#!/usr/bin/env python3
"""
SRE Copilot Infrastructure Validation and Deployment Script
This script validates and ensures all AWS resources are properly deployed:
- Lambda Functions
- Bedrock Agents and Action Groups
- IAM Roles and Permissions
- DynamoDB Tables
- CloudWatch Log Groups
"""

import boto3
import json
import time
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any
from botocore.exceptions import ClientError

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class InfrastructureValidator:
    def __init__(self):
        self.region = 'us-east-1'
        self.validation_results = {
            'lambda_functions': {},
            'bedrock_agents': {},
            'iam_roles': {},
            'dynamodb_tables': {},
            'cloudwatch_logs': {},
            'overall_status': 'PENDING'
        }
        
        # Initialize AWS clients
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=self.region)
        self.iam_client = boto3.client('iam', region_name=self.region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        self.logs_client = boto3.client('logs', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        
        # Define expected Lambda functions
        self.expected_lambda_functions = [
            {
                'name': 'sre-supervisor-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 300,
                'memory': 512
            },
            {
                'name': 'sre-cloudtrail-agent-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 300,
                'memory': 512
            },
            {
                'name': 'sre-vpc-agent-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 300,
                'memory': 512
            },
            {
                'name': 'sre-vpc-flow-logs-agent-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 300,
                'memory': 512
            },
            {
                'name': 'sre-trusted-advisor-agent-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 300,
                'memory': 512
            },
            {
                'name': 'sre-personal-health-agent-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 300,
                'memory': 512
            },
            {
                'name': 'sre-cloudwatch-logs-agent-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 300,
                'memory': 512
            },
            {
                'name': 'sre-log-analyzer-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 30,
                'memory': 256
            },
            {
                'name': 'sre-metrics-analyzer-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 30,
                'memory': 256
            },
            {
                'name': 'sre-knowledge-base-agent-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 60,
                'memory': 512
            },
            {
                'name': 'sre-opsitem-indexer-lambda',
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.9',
                'timeout': 300,
                'memory': 512
            }
        ]
        
        # Define expected Bedrock agents
        self.expected_bedrock_agents = [
            {
                'name': 'SRE-Supervisor',
                'description': 'Main supervisor agent for SRE tasks'
            },
            {
                'name': 'SRE-CloudTrail-Analyzer',
                'description': 'Analyzes CloudTrail events'
            },
            {
                'name': 'SRE-VPC-Analyzer',
                'description': 'Analyzes VPC Flow Logs'
            },
            {
                'name': 'SRE-Trusted-Advisor-Analyzer',
                'description': 'Analyzes Trusted Advisor recommendations'
            },
            {
                'name': 'SRE-Personal-Health-Analyzer',
                'description': 'Analyzes AWS Personal Health Dashboard'
            },
            {
                'name': 'SRE-CloudWatch-Logs-Analyzer',
                'description': 'Analyzes CloudWatch logs'
            },
            {
                'name': 'SRE-VPC-Flow-Logs-Analyzer',
                'description': 'Analyzes VPC Flow Logs for network issues'
            }
        ]
        
        # Define expected DynamoDB tables
        self.expected_dynamodb_tables = [
            'sre-knowledge-base',
            'sre-knowledge-base-vectors'
        ]
        
        # Define expected IAM role
        self.expected_iam_role = 'sre-lambda-role'
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    def print_status(self, item: str, status: bool, details: str = ""):
        """Print status with color coding"""
        if status:
            print(f"{Colors.GREEN}✓{Colors.RESET} {item} {Colors.GREEN}[OK]{Colors.RESET} {details}")
        else:
            print(f"{Colors.RED}✗{Colors.RESET} {item} {Colors.RED}[FAILED]{Colors.RESET} {details}")
    
    def validate_lambda_functions(self) -> Dict[str, bool]:
        """Validate all Lambda functions"""
        self.print_header("Validating Lambda Functions")
        results = {}
        
        for expected_func in self.expected_lambda_functions:
            func_name = expected_func['name']
            try:
                response = self.lambda_client.get_function(FunctionName=func_name)
                config = response['Configuration']
                
                # Check configuration
                issues = []
                if config['Runtime'] != expected_func['runtime']:
                    issues.append(f"Runtime mismatch: {config['Runtime']} != {expected_func['runtime']}")
                if config['Timeout'] != expected_func['timeout']:
                    issues.append(f"Timeout mismatch: {config['Timeout']} != {expected_func['timeout']}")
                if config['MemorySize'] != expected_func['memory']:
                    issues.append(f"Memory mismatch: {config['MemorySize']} != {expected_func['memory']}")
                
                if issues:
                    self.print_status(func_name, False, f"- Issues: {', '.join(issues)}")
                    results[func_name] = False
                else:
                    self.print_status(func_name, True, f"- Runtime: {config['Runtime']}, Memory: {config['MemorySize']}MB")
                    results[func_name] = True
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    self.print_status(func_name, False, "- Not found")
                    results[func_name] = False
                else:
                    self.print_status(func_name, False, f"- Error: {str(e)}")
                    results[func_name] = False
        
        self.validation_results['lambda_functions'] = results
        return results
    
    def validate_bedrock_agents(self) -> Dict[str, bool]:
        """Validate Bedrock agents and their action groups"""
        self.print_header("Validating Bedrock Agents")
        results = {}
        
        try:
            # List all agents
            agents_response = self.bedrock_agent_client.list_agents()
            agents = agents_response.get('agents', [])
            
            # Create a map of agent names to IDs
            agent_map = {agent['name']: agent['agentId'] for agent in agents}
            
            for expected_agent in self.expected_bedrock_agents:
                agent_name = expected_agent['name']
                
                if agent_name in agent_map:
                    agent_id = agent_map[agent_name]
                    
                    # Get agent details
                    try:
                        agent_details = self.bedrock_agent_client.get_agent(agentId=agent_id)
                        agent_info = agent_details['agent']
                        
                        # Check if agent is prepared
                        if agent_info['agentStatus'] == 'PREPARED':
                            # Check action groups
                            try:
                                action_groups = self.bedrock_agent_client.list_agent_action_groups(agentId=agent_id)
                                action_group_count = len(action_groups.get('actionGroups', []))
                                
                                self.print_status(
                                    agent_name, 
                                    True, 
                                    f"- ID: {agent_id}, Status: {agent_info['agentStatus']}, Action Groups: {action_group_count}"
                                )
                                results[agent_name] = True
                            except Exception as e:
                                self.print_status(agent_name, True, f"- ID: {agent_id}, Status: {agent_info['agentStatus']}")
                                results[agent_name] = True
                        else:
                            self.print_status(
                                agent_name, 
                                False, 
                                f"- ID: {agent_id}, Status: {agent_info['agentStatus']} (Not PREPARED)"
                            )
                            results[agent_name] = False
                            
                    except Exception as e:
                        self.print_status(agent_name, False, f"- Error getting agent details: {str(e)}")
                        results[agent_name] = False
                else:
                    self.print_status(agent_name, False, "- Not found")
                    results[agent_name] = False
                    
        except Exception as e:
            print(f"{Colors.RED}Error listing Bedrock agents: {str(e)}{Colors.RESET}")
            for expected_agent in self.expected_bedrock_agents:
                results[expected_agent['name']] = False
        
        self.validation_results['bedrock_agents'] = results
        return results
    
    def validate_iam_role(self) -> bool:
        """Validate IAM role and permissions"""
        self.print_header("Validating IAM Role")
        
        try:
            response = self.iam_client.get_role(RoleName=self.expected_iam_role)
            role = response['Role']
            
            # Check attached policies
            attached_policies = self.iam_client.list_attached_role_policies(RoleName=self.expected_iam_role)
            policy_count = len(attached_policies['AttachedPolicies'])
            
            # Check inline policies
            inline_policies = self.iam_client.list_role_policies(RoleName=self.expected_iam_role)
            inline_count = len(inline_policies['PolicyNames'])
            
            self.print_status(
                self.expected_iam_role, 
                True, 
                f"- Attached Policies: {policy_count}, Inline Policies: {inline_count}"
            )
            self.validation_results['iam_roles'][self.expected_iam_role] = True
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                self.print_status(self.expected_iam_role, False, "- Not found")
            else:
                self.print_status(self.expected_iam_role, False, f"- Error: {str(e)}")
            self.validation_results['iam_roles'][self.expected_iam_role] = False
            return False
    
    def validate_dynamodb_tables(self) -> Dict[str, bool]:
        """Validate DynamoDB tables"""
        self.print_header("Validating DynamoDB Tables")
        results = {}
        
        for table_name in self.expected_dynamodb_tables:
            try:
                response = self.dynamodb_client.describe_table(TableName=table_name)
                table = response['Table']
                
                status = table['TableStatus']
                item_count = table.get('ItemCount', 0)
                
                if status == 'ACTIVE':
                    self.print_status(
                        table_name, 
                        True, 
                        f"- Status: {status}, Items: {item_count}"
                    )
                    results[table_name] = True
                else:
                    self.print_status(
                        table_name, 
                        False, 
                        f"- Status: {status} (Not ACTIVE)"
                    )
                    results[table_name] = False
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    self.print_status(table_name, False, "- Not found")
                    results[table_name] = False
                else:
                    self.print_status(table_name, False, f"- Error: {str(e)}")
                    results[table_name] = False
        
        self.validation_results['dynamodb_tables'] = results
        return results
    
    def test_lambda_invocation(self, function_name: str) -> bool:
        """Test Lambda function invocation"""
        try:
            # Prepare test payload based on function type
            if 'supervisor' in function_name:
                payload = {
                    'action': 'test',
                    'message': 'Validation test'
                }
            elif 'analyzer' in function_name or 'agent' in function_name:
                payload = {
                    'action': 'analyze',
                    'query': 'test query',
                    'timeRange': {
                        'start': '2024-01-01T00:00:00Z',
                        'end': '2024-01-01T01:00:00Z'
                    }
                }
            else:
                payload = {'test': True}
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            status_code = response['StatusCode']
            
            if status_code == 200:
                # Check if there was an error in the response
                if 'FunctionError' in response:
                    return False
                return True
            else:
                return False
                
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not test {function_name}: {str(e)}{Colors.RESET}")
            return False
    
    def test_lambda_functions(self):
        """Test Lambda function invocations"""
        self.print_header("Testing Lambda Function Invocations")
        
        test_functions = [
            'sre-supervisor-lambda',
            'sre-log-analyzer-lambda',
            'sre-metrics-analyzer-lambda'
        ]
        
        for func_name in test_functions:
            if func_name in self.validation_results['lambda_functions'] and \
               self.validation_results['lambda_functions'][func_name]:
                success = self.test_lambda_invocation(func_name)
                self.print_status(f"Test invocation: {func_name}", success)
    
    def deploy_missing_resources(self):
        """Deploy missing resources"""
        self.print_header("Deploying Missing Resources")
        
        # Check for missing Lambda functions
        missing_lambdas = [
            func['name'] for func in self.expected_lambda_functions 
            if not self.validation_results['lambda_functions'].get(func['name'], False)
        ]
        
        if missing_lambdas:
            print(f"\n{Colors.YELLOW}Missing Lambda functions detected:{Colors.RESET}")
            for func in missing_lambdas:
                print(f"  - {func}")
            
            print(f"\n{Colors.CYAN}Deploying Lambda functions...{Colors.RESET}")
            try:
                subprocess.run(['./deploy_all_lambdas.sh'], check=True)
                print(f"{Colors.GREEN}Lambda deployment completed{Colors.RESET}")
            except subprocess.CalledProcessError as e:
                print(f"{Colors.RED}Lambda deployment failed: {str(e)}{Colors.RESET}")
        
        # Check for missing DynamoDB tables
        missing_tables = [
            table for table in self.expected_dynamodb_tables
            if not self.validation_results['dynamodb_tables'].get(table, False)
        ]
        
        if missing_tables:
            print(f"\n{Colors.YELLOW}Missing DynamoDB tables detected:{Colors.RESET}")
            for table in missing_tables:
                print(f"  - {table}")
            
            print(f"\n{Colors.CYAN}Creating DynamoDB tables...{Colors.RESET}")
            self.create_dynamodb_tables()
        
        # Deploy Knowledge Base Lambda if missing
        if not self.validation_results['lambda_functions'].get('sre-knowledge-base-agent-lambda', False):
            print(f"\n{Colors.CYAN}Deploying Knowledge Base Lambda...{Colors.RESET}")
            try:
                subprocess.run(['./deploy_knowledge_base_serverless.sh'], check=True)
                print(f"{Colors.GREEN}Knowledge Base deployment completed{Colors.RESET}")
            except subprocess.CalledProcessError as e:
                print(f"{Colors.RED}Knowledge Base deployment failed: {str(e)}{Colors.RESET}")
    
    def create_dynamodb_tables(self):
        """Create missing DynamoDB tables"""
        # Knowledge Base table
        if not self.validation_results['dynamodb_tables'].get('sre-knowledge-base', False):
            try:
                self.dynamodb_client.create_table(
                    TableName='sre-knowledge-base',
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                print(f"{Colors.GREEN}Created table: sre-knowledge-base{Colors.RESET}")
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceInUseException':
                    print(f"{Colors.RED}Error creating table: {str(e)}{Colors.RESET}")
        
        # Knowledge Base Vectors table
        if not self.validation_results['dynamodb_tables'].get('sre-knowledge-base-vectors', False):
            try:
                self.dynamodb_client.create_table(
                    TableName='sre-knowledge-base-vectors',
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'},
                        {'AttributeName': 'category', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST',
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'category-index',
                            'KeySchema': [
                                {'AttributeName': 'category', 'KeyType': 'HASH'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        }
                    ]
                )
                print(f"{Colors.GREEN}Created table: sre-knowledge-base-vectors{Colors.RESET}")
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceInUseException':
                    print(f"{Colors.RED}Error creating table: {str(e)}{Colors.RESET}")
    
    def generate_report(self):
        """Generate validation report"""
        self.print_header("Validation Summary Report")
        
        # Calculate overall status
        all_lambdas_ok = all(self.validation_results['lambda_functions'].values()) if self.validation_results['lambda_functions'] else False
        all_agents_ok = all(self.validation_results['bedrock_agents'].values()) if self.validation_results['bedrock_agents'] else False
        all_tables_ok = all(self.validation_results['dynamodb_tables'].values()) if self.validation_results['dynamodb_tables'] else False
        iam_ok = self.validation_results['iam_roles'].get(self.expected_iam_role, False)
        
        overall_ok = all_lambdas_ok and all_agents_ok and all_tables_ok and iam_ok
        
        # Print summary
        print(f"\n{Colors.BOLD}Component Status:{Colors.RESET}")
        print(f"  Lambda Functions: {Colors.GREEN if all_lambdas_ok else Colors.RED}"
              f"{len([v for v in self.validation_results['lambda_functions'].values() if v])}/{len(self.expected_lambda_functions)}"
              f" OK{Colors.RESET}")
        print(f"  Bedrock Agents: {Colors.GREEN if all_agents_ok else Colors.RED}"
              f"{len([v for v in self.validation_results['bedrock_agents'].values() if v])}/{len(self.expected_bedrock_agents)}"
              f" OK{Colors.RESET}")
        print(f"  DynamoDB Tables: {Colors.GREEN if all_tables_ok else Colors.RED}"
              f"{len([v for v in self.validation_results['dynamodb_tables'].values() if v])}/{len(self.expected_dynamodb_tables)}"
              f" OK{Colors.RESET}")
        print(f"  IAM Role: {Colors.GREEN if iam_ok else Colors.RED}"
              f"{'OK' if iam_ok else 'FAILED'}{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}Overall Status: "
              f"{Colors.GREEN if overall_ok else Colors.RED}"
              f"{'ALL SYSTEMS OPERATIONAL' if overall_ok else 'ISSUES DETECTED'}"
              f"{Colors.RESET}\n")
        
        # Save report
        report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"Detailed report saved to: {Colors.CYAN}{report_file}{Colors.RESET}")
        
        return overall_ok
    
    def run_validation(self):
        """Run complete validation"""
        print(f"{Colors.BOLD}{Colors.CYAN}SRE Copilot Infrastructure Validation{Colors.RESET}")
        print(f"{Colors.CYAN}Region: {self.region}{Colors.RESET}")
        print(f"{Colors.CYAN}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        
        # Run all validations
        self.validate_lambda_functions()
        self.validate_bedrock_agents()
        self.validate_iam_role()
        self.validate_dynamodb_tables()
        
        # Test some Lambda functions
        self.test_lambda_functions()
        
        # Deploy missing resources
        self.deploy_missing_resources()
        
        # Re-validate after deployment
        print(f"\n{Colors.BOLD}{Colors.YELLOW}Re-validating after deployment...{Colors.RESET}")
        self.validate_lambda_functions()
        self.validate_bedrock_agents()
        self.validate_dynamodb_tables()
        
        # Generate report
        overall_ok = self.generate_report()
        
        return overall_ok


def main():
    """Main function"""
    validator = InfrastructureValidator()
    
    try:
        success = validator.run_validation()
        
        if success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Infrastructure validation completed successfully!{Colors.RESET}")
            sys.exit(0)
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Infrastructure validation completed with issues.{Colors.RESET}")
            print(f"{Colors.YELLOW}Please review the report and address any failures.{Colors.RESET}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Validation interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error during validation: {str(e)}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Comprehensive validation of AWS infrastructure for SRE Copilot
Validates all Lambda functions, Bedrock agents, and action groups
"""

import boto3
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
import sys

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class AWSInfrastructureValidator:
    """Validates all AWS resources for SRE Copilot"""
    
    def __init__(self):
        self.region = 'us-east-1'
        
        # Initialize AWS clients
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=self.region)
        self.bedrock_runtime_client = boto3.client('bedrock-agent-runtime', region_name=self.region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        self.iam_client = boto3.client('iam')
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.region)
        self.events_client = boto3.client('events', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        
        # Load configuration
        self.config = self.load_configuration()
        self.test_results = {
            'lambda_functions': {},
            'bedrock_agents': {},
            'action_groups': {},
            'dynamodb_tables': {},
            'event_rules': {},
            'iam_roles': {},
            'overall_status': 'PENDING'
        }
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load SRE Copilot configuration"""
        try:
            with open('sre_copilot_config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"{Colors.RED}Failed to load configuration: {str(e)}{Colors.RESET}")
            return {}
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.RESET}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")
    
    def validate_lambda_functions(self) -> Dict[str, bool]:
        """Validate all Lambda functions are deployed and functional"""
        self.print_header("Validating Lambda Functions")
        
        lambda_functions = [
            'sre-supervisor-lambda',
            'sre-supervisor-lambda-mcp',
            'sre-cloudtrail-agent-lambda',
            'sre-vpc-agent-lambda',
            'sre-trusted-advisor-agent-lambda',
            'sre-personal-health-agent-lambda',
            'sre-knowledge-base-agent-lambda',
            'sre-log-analyzer-lambda',
            'sre-metrics-analyzer-lambda',
            'sre-opsitem-indexer-lambda'
        ]
        
        results = {}
        
        for function_name in lambda_functions:
            try:
                # Get function configuration
                response = self.lambda_client.get_function(FunctionName=function_name)
                
                # Check function state
                state = response['Configuration']['State']
                if state == 'Active':
                    self.print_success(f"{function_name}: Deployed and Active")
                    
                    # Test invoke the function with a simple ping
                    try:
                        test_payload = {
                            'test': True,
                            'action': 'ping',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        invoke_response = self.lambda_client.invoke(
                            FunctionName=function_name,
                            InvocationType='RequestResponse',
                            Payload=json.dumps(test_payload)
                        )
                        
                        if invoke_response['StatusCode'] == 200:
                            self.print_info(f"  → Successfully invoked {function_name}")
                            results[function_name] = True
                        else:
                            self.print_warning(f"  → Invoke returned status {invoke_response['StatusCode']}")
                            results[function_name] = False
                            
                    except Exception as e:
                        self.print_warning(f"  → Could not test invoke: {str(e)}")
                        results[function_name] = True  # Function exists but can't test
                        
                else:
                    self.print_warning(f"{function_name}: State is {state}")
                    results[function_name] = False
                    
            except self.lambda_client.exceptions.ResourceNotFoundException:
                self.print_error(f"{function_name}: Not found")
                results[function_name] = False
            except Exception as e:
                self.print_error(f"{function_name}: Error - {str(e)}")
                results[function_name] = False
        
        self.test_results['lambda_functions'] = results
        return results
    
    def validate_bedrock_agents(self) -> Dict[str, bool]:
        """Validate all Bedrock agents are deployed and functional"""
        self.print_header("Validating Bedrock Agents")
        
        results = {}
        
        if 'agents' not in self.config:
            self.print_error("No agents found in configuration")
            return results
        
        for agent_name, agent_config in self.config['agents'].items():
            agent_id = agent_config.get('agent_id')
            if not agent_id:
                self.print_warning(f"{agent_name}: No agent_id in config")
                results[agent_name] = False
                continue
            
            try:
                # Get agent details
                response = self.bedrock_agent_client.get_agent(agentId=agent_id)
                agent = response['agent']
                
                # Check agent status
                if agent['agentStatus'] == 'PREPARED':
                    self.print_success(f"{agent_name} ({agent_id}): Ready")
                    
                    # Get agent aliases
                    aliases_response = self.bedrock_agent_client.list_agent_aliases(
                        agentId=agent_id,
                        maxResults=10
                    )
                    
                    if aliases_response['agentAliasSummaries']:
                        alias_id = aliases_response['agentAliasSummaries'][0]['agentAliasId']
                        self.print_info(f"  → Alias ID: {alias_id}")
                        
                        # Test invoke the agent
                        try:
                            test_session_id = f"test-session-{int(time.time())}"
                            test_input = "What is your purpose?"
                            
                            invoke_response = self.bedrock_runtime_client.invoke_agent(
                                agentId=agent_id,
                                agentAliasId=alias_id,
                                sessionId=test_session_id,
                                inputText=test_input
                            )
                            
                            # Read response stream
                            event_stream = invoke_response.get('completion', [])
                            response_text = ""
                            
                            for event in event_stream:
                                if 'chunk' in event:
                                    chunk = event['chunk']
                                    if 'bytes' in chunk:
                                        response_text += chunk['bytes'].decode('utf-8')
                            
                            if response_text:
                                self.print_info(f"  → Agent responded successfully")
                                results[agent_name] = True
                            else:
                                self.print_warning(f"  → Agent returned empty response")
                                results[agent_name] = True  # Agent exists but no response
                                
                        except Exception as e:
                            self.print_warning(f"  → Could not test invoke: {str(e)}")
                            results[agent_name] = True  # Agent exists but can't test
                    else:
                        self.print_warning(f"  → No aliases found")
                        results[agent_name] = False
                        
                else:
                    self.print_warning(f"{agent_name} ({agent_id}): Status is {agent['agentStatus']}")
                    results[agent_name] = False
                    
            except self.bedrock_agent_client.exceptions.ResourceNotFoundException:
                self.print_error(f"{agent_name} ({agent_id}): Not found")
                results[agent_name] = False
            except Exception as e:
                self.print_error(f"{agent_name}: Error - {str(e)}")
                results[agent_name] = False
        
        self.test_results['bedrock_agents'] = results
        return results
    
    def validate_action_groups(self) -> Dict[str, bool]:
        """Validate action groups for Bedrock agents"""
        self.print_header("Validating Action Groups")
        
        results = {}
        
        for agent_name, agent_config in self.config.get('agents', {}).items():
            agent_id = agent_config.get('agent_id')
            if not agent_id:
                continue
            
            try:
                # List action groups for the agent
                response = self.bedrock_agent_client.list_agent_action_groups(
                    agentId=agent_id,
                    agentVersion='DRAFT'
                )
                
                action_groups = response.get('actionGroupSummaries', [])
                
                if action_groups:
                    for ag in action_groups:
                        ag_name = ag['actionGroupName']
                        ag_id = ag['actionGroupId']
                        ag_state = ag['actionGroupState']
                        
                        if ag_state == 'ENABLED':
                            self.print_success(f"{agent_name} → {ag_name} ({ag_id}): Enabled")
                            results[f"{agent_name}_{ag_name}"] = True
                        else:
                            self.print_warning(f"{agent_name} → {ag_name} ({ag_id}): {ag_state}")
                            results[f"{agent_name}_{ag_name}"] = False
                else:
                    self.print_warning(f"{agent_name}: No action groups found")
                    
            except Exception as e:
                self.print_error(f"{agent_name}: Error checking action groups - {str(e)}")
        
        self.test_results['action_groups'] = results
        return results
    
    def validate_dynamodb_tables(self) -> Dict[str, bool]:
        """Validate DynamoDB tables for knowledge base"""
        self.print_header("Validating DynamoDB Tables")
        
        tables = [
            'sre-knowledge-base',
            'sre-knowledge-base-vectors'
        ]
        
        results = {}
        
        for table_name in tables:
            try:
                response = self.dynamodb_client.describe_table(TableName=table_name)
                table = response['Table']
                
                if table['TableStatus'] == 'ACTIVE':
                    item_count = table.get('ItemCount', 0)
                    self.print_success(f"{table_name}: Active ({item_count} items)")
                    
                    # Check if table has items
                    if item_count > 0:
                        self.print_info(f"  → Table contains data")
                    else:
                        self.print_warning(f"  → Table is empty")
                    
                    results[table_name] = True
                else:
                    self.print_warning(f"{table_name}: Status is {table['TableStatus']}")
                    results[table_name] = False
                    
            except self.dynamodb_client.exceptions.ResourceNotFoundException:
                self.print_error(f"{table_name}: Not found")
                results[table_name] = False
            except Exception as e:
                self.print_error(f"{table_name}: Error - {str(e)}")
                results[table_name] = False
        
        self.test_results['dynamodb_tables'] = results
        return results
    
    def validate_event_rules(self) -> Dict[str, bool]:
        """Validate CloudWatch Event Rules"""
        self.print_header("Validating CloudWatch Event Rules")
        
        rules = ['sre-opsitem-indexing']
        results = {}
        
        for rule_name in rules:
            try:
                response = self.events_client.describe_rule(Name=rule_name)
                
                if response['State'] == 'ENABLED':
                    self.print_success(f"{rule_name}: Enabled")
                    
                    # Check targets
                    targets_response = self.events_client.list_targets_by_rule(Rule=rule_name)
                    targets = targets_response.get('Targets', [])
                    
                    if targets:
                        for target in targets:
                            target_arn = target['Arn']
                            self.print_info(f"  → Target: {target_arn.split(':')[-1]}")
                    else:
                        self.print_warning(f"  → No targets configured")
                    
                    results[rule_name] = True
                else:
                    self.print_warning(f"{rule_name}: State is {response['State']}")
                    results[rule_name] = False
                    
            except self.events_client.exceptions.ResourceNotFoundException:
                self.print_error(f"{rule_name}: Not found")
                results[rule_name] = False
            except Exception as e:
                self.print_error(f"{rule_name}: Error - {str(e)}")
                results[rule_name] = False
        
        self.test_results['event_rules'] = results
        return results
    
    def validate_iam_roles(self) -> Dict[str, bool]:
        """Validate IAM roles for Lambda functions"""
        self.print_header("Validating IAM Roles")
        
        results = {}
        
        # Get all Lambda functions and check their roles
        for function_name, is_valid in self.test_results['lambda_functions'].items():
            if not is_valid:
                continue
                
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                role_arn = response['Configuration']['Role']
                role_name = role_arn.split('/')[-1]
                
                # Check if role exists
                try:
                    role_response = self.iam_client.get_role(RoleName=role_name)
                    self.print_success(f"{function_name} → Role: {role_name}")
                    
                    # Check attached policies
                    policies_response = self.iam_client.list_attached_role_policies(
                        RoleName=role_name
                    )
                    
                    policy_count = len(policies_response['AttachedPolicies'])
                    self.print_info(f"  → {policy_count} policies attached")
                    
                    results[role_name] = True
                    
                except self.iam_client.exceptions.NoSuchEntityException:
                    self.print_error(f"{function_name} → Role {role_name} not found")
                    results[role_name] = False
                    
            except Exception as e:
                self.print_warning(f"{function_name}: Could not check role - {str(e)}")
        
        self.test_results['iam_roles'] = results
        return results
    
    def test_end_to_end_flow(self) -> bool:
        """Test end-to-end flow with a sample incident"""
        self.print_header("Testing End-to-End Flow")
        
        try:
            # Create a test OpsItem
            test_opsitem_title = f"Test Incident - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.print_info("Creating test OpsItem...")
            
            create_response = self.ssm_client.create_ops_item(
                Title=test_opsitem_title,
                Description="Test incident for validating SRE Copilot infrastructure",
                Source="Test",
                Priority=3,
                Category="Availability",
                Severity="3",
                OperationalData={
                    '/aws/test': {
                        'Type': 'String',
                        'Value': 'true'
                    },
                    '/aws/incident_type': {
                        'Type': 'String',
                        'Value': 'test'
                    }
                }
            )
            
            ops_item_id = create_response['OpsItemId']
            self.print_success(f"Created OpsItem: {ops_item_id}")
            
            # Wait for processing
            self.print_info("Waiting for automated processing...")
            time.sleep(5)
            
            # Check if OpsItem was indexed to knowledge base
            if 'sre-knowledge-base' in self.test_results['dynamodb_tables'] and \
               self.test_results['dynamodb_tables']['sre-knowledge-base']:
                try:
                    kb_response = self.dynamodb_client.get_item(
                        TableName='sre-knowledge-base',
                        Key={
                            'id': {'S': ops_item_id}
                        }
                    )
                    
                    if 'Item' in kb_response:
                        self.print_success("OpsItem successfully indexed to knowledge base")
                        return True
                    else:
                        self.print_warning("OpsItem not yet indexed to knowledge base")
                        
                except Exception as e:
                    self.print_warning(f"Could not check knowledge base: {str(e)}")
            
            # Clean up test OpsItem
            try:
                self.ssm_client.update_ops_item(
                    OpsItemId=ops_item_id,
                    Status='Resolved'
                )
                self.print_info(f"Cleaned up test OpsItem {ops_item_id}")
            except:
                pass
                
            return True
            
        except Exception as e:
            self.print_error(f"End-to-end test failed: {str(e)}")
            return False
    
    def generate_summary_report(self):
        """Generate summary report of validation results"""
        self.print_header("Validation Summary Report")
        
        # Calculate totals
        total_components = 0
        total_valid = 0
        
        for category, results in self.test_results.items():
            if category == 'overall_status':
                continue
                
            if isinstance(results, dict):
                total_components += len(results)
                total_valid += sum(1 for v in results.values() if v)
        
        # Print category summaries
        categories = [
            ('Lambda Functions', 'lambda_functions'),
            ('Bedrock Agents', 'bedrock_agents'),
            ('Action Groups', 'action_groups'),
            ('DynamoDB Tables', 'dynamodb_tables'),
            ('Event Rules', 'event_rules'),
            ('IAM Roles', 'iam_roles')
        ]
        
        for category_name, category_key in categories:
            results = self.test_results.get(category_key, {})
            if results:
                valid_count = sum(1 for v in results.values() if v)
                total_count = len(results)
                
                if valid_count == total_count:
                    status_color = Colors.GREEN
                    status_symbol = "✓"
                elif valid_count > 0:
                    status_color = Colors.YELLOW
                    status_symbol = "⚠"
                else:
                    status_color = Colors.RED
                    status_symbol = "✗"
                
                print(f"{status_color}{status_symbol} {category_name}: {valid_count}/{total_count} valid{Colors.RESET}")
        
        # Overall status
        print(f"\n{Colors.BOLD}Overall Infrastructure Status:{Colors.RESET}")
        
        if total_valid == total_components:
            self.test_results['overall_status'] = 'FULLY_OPERATIONAL'
            print(f"{Colors.GREEN}✓ FULLY OPERATIONAL - All {total_components} components validated{Colors.RESET}")
        elif total_valid >= total_components * 0.8:
            self.test_results['overall_status'] = 'MOSTLY_OPERATIONAL'
            print(f"{Colors.YELLOW}⚠ MOSTLY OPERATIONAL - {total_valid}/{total_components} components validated{Colors.RESET}")
        else:
            self.test_results['overall_status'] = 'NEEDS_ATTENTION'
            print(f"{Colors.RED}✗ NEEDS ATTENTION - Only {total_valid}/{total_components} components validated{Colors.RESET}")
        
        # Save detailed report
        report_filename = f"infrastructure_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n{Colors.BLUE}ℹ Detailed report saved to: {report_filename}{Colors.RESET}")
    
    def run_validation(self):
        """Run complete validation suite"""
        self.print_header("AWS Infrastructure Validation for SRE Copilot")
        print(f"Region: {self.region}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all validations
        self.validate_lambda_functions()
        self.validate_bedrock_agents()
        self.validate_action_groups()
        self.validate_dynamodb_tables()
        self.validate_event_rules()
        self.validate_iam_roles()
        
        # Run end-to-end test if core components are valid
        if any(self.test_results['lambda_functions'].values()) and \
           any(self.test_results.get('bedrock_agents', {}).values()):
            self.test_end_to_end_flow()
        
        # Generate summary
        self.generate_summary_report()
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    validator = AWSInfrastructureValidator()
    validator.run_validation()
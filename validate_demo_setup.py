#!/usr/bin/env python3
"""
Validate that all demo components are properly set up and working.
"""

import boto3
import json
import sys
from datetime import datetime

class DemoValidator:
    """Validate demo setup and components."""
    
    def __init__(self):
        self.region = 'us-east-1'
        self.all_checks_passed = True
        self.results = []
        
    def check_lambda_functions(self):
        """Check that all required Lambda functions exist."""
        print("\n🔍 Checking Lambda Functions...")
        
        lambda_client = boto3.client('lambda', region_name=self.region)
        
        required_functions = [
            'sre-supervisor-lambda',
            'sre-cloudwatch-logs-agent-lambda',
            'sre-cloudtrail-agent-lambda',
            'sre-vpc-flow-logs-agent-lambda',
            'sre-personal-health-agent-lambda',
            'sre-trusted-advisor-agent-lambda',
            'sre-log-analyzer-lambda',
            'sre-metrics-analyzer-lambda'
        ]
        
        for func_name in required_functions:
            try:
                response = lambda_client.get_function(FunctionName=func_name)
                self.results.append((f"Lambda: {func_name}", True, "Deployed"))
            except lambda_client.exceptions.ResourceNotFoundException:
                self.results.append((f"Lambda: {func_name}", False, "Not found"))
                self.all_checks_passed = False
            except Exception as e:
                self.results.append((f"Lambda: {func_name}", False, str(e)))
                self.all_checks_passed = False
                
    def check_iam_permissions(self):
        """Check basic IAM permissions."""
        print("\n🔍 Checking IAM Permissions...")
        
        # Test various service permissions
        services_to_check = [
            ('logs', 'describe_log_groups'),
            ('cloudwatch', 'list_metrics'),
            ('ec2', 'describe_security_groups'),
            ('ssm', 'describe_ops_items'),
            ('cloudtrail', 'lookup_events')
        ]
        
        for service_name, operation in services_to_check:
            try:
                client = boto3.client(service_name, region_name=self.region)
                
                if service_name == 'logs':
                    client.describe_log_groups(limit=1)
                elif service_name == 'cloudwatch':
                    client.list_metrics(Limit=1)
                elif service_name == 'ec2':
                    client.describe_security_groups(MaxResults=5)
                elif service_name == 'ssm':
                    client.describe_ops_items(MaxResults=1)
                elif service_name == 'cloudtrail':
                    client.lookup_events(MaxResults=1)
                    
                self.results.append((f"IAM: {service_name} access", True, "Authorized"))
            except Exception as e:
                if 'AccessDenied' in str(e):
                    self.results.append((f"IAM: {service_name} access", False, "Access denied"))
                    self.all_checks_passed = False
                else:
                    self.results.append((f"IAM: {service_name} access", True, "Authorized"))
                    
    def check_bedrock_agents(self):
        """Check Bedrock agent configuration."""
        print("\n🔍 Checking Bedrock Agents...")
        
        try:
            with open('sre_copilot_config.json', 'r') as f:
                config = json.load(f)
                
            agents = [
                'supervisor_agent',
                'log_analysis_agent',
                'metrics_analysis_agent',
                'cloudtrail_agent',
                'vpc_agent',
                'trusted_advisor_agent',
                'personal_health_agent'
            ]
            
            for agent in agents:
                if agent in config and 'id' in config[agent]:
                    agent_id = config[agent]['id']
                    if agent_id:
                        self.results.append((f"Bedrock: {agent}", True, f"ID: {agent_id}"))
                    else:
                        self.results.append((f"Bedrock: {agent}", False, "No ID"))
                        self.all_checks_passed = False
                else:
                    self.results.append((f"Bedrock: {agent}", False, "Not configured"))
                    self.all_checks_passed = False
                    
        except FileNotFoundError:
            self.results.append(("Bedrock: Config file", False, "sre_copilot_config.json not found"))
            self.all_checks_passed = False
        except Exception as e:
            self.results.append(("Bedrock: Config file", False, str(e)))
            self.all_checks_passed = False
            
    def check_demo_scripts(self):
        """Check that demo scripts exist and are executable."""
        print("\n🔍 Checking Demo Scripts...")
        
        import os
        
        scripts = [
            'incident_generator_demo.py',
            'test_root_cause_analysis.py'
        ]
        
        for script in scripts:
            if os.path.exists(script):
                if os.access(script, os.X_OK):
                    self.results.append((f"Script: {script}", True, "Executable"))
                else:
                    self.results.append((f"Script: {script}", True, "Exists (not executable)"))
            else:
                self.results.append((f"Script: {script}", False, "Not found"))
                self.all_checks_passed = False
                
    def test_supervisor_lambda(self):
        """Test supervisor Lambda with a health check."""
        print("\n🔍 Testing Supervisor Lambda...")
        
        lambda_client = boto3.client('lambda', region_name=self.region)
        
        try:
            response = lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({'action': 'health_check'})
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') in [200, 201]:
                self.results.append(("Supervisor: Health check", True, "Operational"))
            else:
                self.results.append(("Supervisor: Health check", False, f"Status: {result.get('statusCode')}"))
                self.all_checks_passed = False
                
        except Exception as e:
            self.results.append(("Supervisor: Health check", False, str(e)))
            self.all_checks_passed = False
            
    def display_results(self):
        """Display validation results."""
        print("\n" + "="*80)
        print("📊 VALIDATION RESULTS")
        print("="*80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        # Group results by category
        categories = {}
        for check, passed, message in self.results:
            category = check.split(':')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append((check, passed, message))
            
        # Display by category
        for category, checks in categories.items():
            print(f"\n{category} Checks:")
            print("-" * 60)
            for check, passed, message in checks:
                status = "✅" if passed else "❌"
                print(f"{status} {check:<40} {message}")
                
        # Overall result
        print("\n" + "="*80)
        if self.all_checks_passed:
            print("✅ ALL CHECKS PASSED - Demo is ready to run!")
            print("\nNext steps:")
            print("1. Run: python3 incident_generator_demo.py")
            print("2. Run: python3 test_root_cause_analysis.py")
        else:
            print("❌ SOME CHECKS FAILED - Please address the issues above")
            print("\nTroubleshooting:")
            print("- Ensure all Lambda functions are deployed")
            print("- Check IAM permissions for your AWS user/role")
            print("- Verify sre_copilot_config.json exists with agent IDs")
        print("="*80 + "\n")
        
    def run_validation(self):
        """Run all validation checks."""
        print("\n" + "="*80)
        print("🚀 SRE COPILOT DEMO VALIDATION")
        print("="*80)
        
        self.check_lambda_functions()
        self.check_iam_permissions()
        self.check_bedrock_agents()
        self.check_demo_scripts()
        self.test_supervisor_lambda()
        
        self.display_results()
        
        return self.all_checks_passed


def main():
    """Main validation execution."""
    validator = DemoValidator()
    
    try:
        success = validator.run_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
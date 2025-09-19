#!/usr/bin/env python3
"""
Validate all functionality is working for the demo.
"""

import json
import boto3
import time
import requests
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name='us-east-1')
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

class DemoValidator:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.issues = []
        
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.CYAN}{text.center(60)}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
        
    def test(self, name, condition, error_msg=""):
        if condition:
            print(f"{Fore.GREEN}✓ {name}{Style.RESET_ALL}")
            self.passed += 1
        else:
            print(f"{Fore.RED}✗ {name}{Style.RESET_ALL}")
            if error_msg:
                print(f"  {Fore.YELLOW}Issue: {error_msg}{Style.RESET_ALL}")
            self.failed += 1
            self.issues.append(f"{name}: {error_msg}")
            
    def validate_ai_analysis(self):
        """Validate AI-powered root cause analysis."""
        print(f"\n{Fore.BLUE}1. Testing AI-Powered Root Cause Analysis{Style.RESET_ALL}")
        
        try:
            payload = {
                'action': 'analyze',
                'incident_description': 'Database connection pool exhausted causing application errors',
                'service': 'demo-app',
                'environment': 'production'
            }
            
            response = lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result['statusCode'] == 200:
                body = json.loads(result['body'])
                analysis = body.get('root_cause_analysis', '')
                
                # Check for AI-generated content
                ai_indicators = [
                    'root cause analysis',
                    'impact assessment',
                    'mitigation steps',
                    'recommendations'
                ]
                
                indicators_found = sum(1 for ind in ai_indicators if ind.lower() in analysis.lower())
                
                self.test("AI Analysis Generated", 
                         indicators_found >= 3 and len(analysis) > 500,
                         f"Only {indicators_found}/4 AI sections found")
                
                # Check that it's not using fallback
                self.test("Not Using Fallback Analysis",
                         "Under investigation" not in analysis,
                         "AI may be falling back to rule-based analysis")
            else:
                self.test("AI Analysis Generated", False, f"Lambda error: {result['statusCode']}")
                
        except Exception as e:
            self.test("AI Analysis Generated", False, str(e))
            
    def validate_knowledge_base(self):
        """Validate Knowledge Base functionality."""
        print(f"\n{Fore.BLUE}2. Testing Knowledge Base{Style.RESET_ALL}")
        
        try:
            # Check tables exist
            kb_table = dynamodb.Table('sre-knowledge-base')
            kb_vectors_table = dynamodb.Table('sre-knowledge-base-vectors')
            
            self.test("KB Tables Exist",
                     kb_table.table_status == 'ACTIVE' and kb_vectors_table.table_status == 'ACTIVE',
                     "Tables not active")
            
            # Test adding an item
            test_item = {
                'action': 'add_item',
                'item': {
                    'id': f'demo-test-{int(time.time())}',
                    'type': 'test',
                    'title': 'Demo Validation Test',
                    'description': 'Testing KB for demo'
                }
            }
            
            response = lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_item)
            )
            
            result = json.loads(response['Payload'].read())
            self.test("KB Add Item", result['statusCode'] == 200, "Failed to add item")
            
            # Test search
            search_payload = {
                'action': 'semantic_search',
                'query': 'demo validation test',
                'limit': 5
            }
            
            response = lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(search_payload)
            )
            
            result = json.loads(response['Payload'].read())
            self.test("KB Search", result['statusCode'] == 200, "Search failed")
            
        except Exception as e:
            self.test("Knowledge Base", False, str(e))
            
    def validate_metrics(self):
        """Validate CloudWatch metrics."""
        print(f"\n{Fore.BLUE}3. Testing CloudWatch Metrics{Style.RESET_ALL}")
        
        try:
            # Put test metric
            cloudwatch.put_metric_data(
                Namespace='SREDemo/Application',
                MetricData=[{
                    'MetricName': 'DemoValidation',
                    'Value': 1.0,
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Environment', 'Value': 'demo'},
                        {'Name': 'Service', 'Value': 'sre-demo-app'}
                    ]
                }]
            )
            
            self.test("Metrics Published", True)
            
            # Check if demo metrics exist
            response = cloudwatch.list_metrics(
                Namespace='SREDemo/Application',
                Dimensions=[
                    {'Name': 'Environment', 'Value': 'demo'}
                ]
            )
            
            metrics_count = len(response.get('Metrics', []))
            self.test("Demo Metrics Available", 
                     metrics_count > 0,
                     f"Found {metrics_count} metrics")
                     
        except Exception as e:
            self.test("CloudWatch Metrics", False, str(e))
            
    def validate_lambdas(self):
        """Validate all Lambda functions."""
        print(f"\n{Fore.BLUE}4. Testing Lambda Functions{Style.RESET_ALL}")
        
        required_lambdas = [
            'sre-supervisor-lambda',
            'sre-knowledge-base-agent-lambda',
            'sre-cloudtrail-agent-lambda',
            'sre-vpc-agent-lambda',
            'sre-cloudwatch-logs-agent-lambda',
            'sre-trusted-advisor-agent-lambda',
            'sre-personal-health-agent-lambda'
        ]
        
        try:
            response = lambda_client.list_functions()
            deployed_lambdas = [f['FunctionName'] for f in response.get('Functions', [])]
            
            for lambda_name in required_lambdas:
                self.test(f"Lambda: {lambda_name}", 
                         lambda_name in deployed_lambdas,
                         "Not deployed")
                         
        except Exception as e:
            self.test("Lambda Functions", False, str(e))
            
    def validate_streamlit(self):
        """Validate Streamlit dashboard."""
        print(f"\n{Fore.BLUE}5. Testing Streamlit Dashboard{Style.RESET_ALL}")
        
        try:
            response = requests.get('http://localhost:8501', timeout=5)
            self.test("Streamlit Running", 
                     response.status_code == 200,
                     f"Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.test("Streamlit Running", False, "Not accessible on port 8501")
        except Exception as e:
            self.test("Streamlit Running", False, str(e))
            
    def validate_incident_generation(self):
        """Validate incident generation and analysis flow."""
        print(f"\n{Fore.BLUE}6. Testing End-to-End Incident Flow{Style.RESET_ALL}")
        
        try:
            # Generate test incident
            test_incident = {
                'action': 'analyze',
                'incident_description': 'High memory usage detected on production servers, approaching 95% utilization',
                'service': 'validation-test',
                'environment': 'production',
                'enable_kb': True
            }
            
            response = lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(test_incident)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result['statusCode'] == 200:
                body = json.loads(result['body'])
                
                # Check all components
                self.test("Incident Type Detection",
                         body.get('incident_type') == 'performance',
                         f"Detected: {body.get('incident_type')}")
                
                self.test("Root Cause Analysis",
                         len(body.get('root_cause_analysis', '')) > 100,
                         "Analysis too short")
                
                self.test("Metrics Collection",
                         body.get('metrics_summary', {}) != {},
                         "No metrics collected")
                
                self.test("KB Integration",
                         'knowledge_base_insights' in body,
                         "KB insights missing")
            else:
                self.test("Incident Flow", False, f"Status: {result['statusCode']}")
                
        except Exception as e:
            self.test("Incident Flow", False, str(e))
            
    def generate_report(self):
        """Generate final validation report."""
        self.print_header("DEMO VALIDATION REPORT")
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"{Fore.CYAN}Total Checks: {total}")
        print(f"{Fore.GREEN}Passed: {self.passed}")
        print(f"{Fore.RED}Failed: {self.failed}")
        print(f"{Fore.YELLOW}Pass Rate: {pass_rate:.1f}%{Style.RESET_ALL}\n")
        
        if pass_rate >= 90:
            print(f"{Fore.GREEN}✓ SYSTEM READY FOR DEMO{Style.RESET_ALL}")
        elif pass_rate >= 70:
            print(f"{Fore.YELLOW}⚠ SYSTEM MOSTLY READY - Fix remaining issues{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ SYSTEM NOT READY - Critical issues found{Style.RESET_ALL}")
            
        if self.issues:
            print(f"\n{Fore.RED}Issues to Fix:{Style.RESET_ALL}")
            for issue in self.issues:
                print(f"  - {issue}")
                
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'passed': self.passed,
            'failed': self.failed,
            'pass_rate': pass_rate,
            'issues': self.issues,
            'demo_ready': pass_rate >= 90
        }
        
        with open('demo_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n{Fore.CYAN}Report saved to: demo_validation_report.json{Style.RESET_ALL}")
        
def main():
    validator = DemoValidator()
    
    validator.print_header("SRE COPILOT DEMO VALIDATION")
    
    print(f"{Fore.YELLOW}Running comprehensive validation for demo readiness...{Style.RESET_ALL}")
    
    # Run all validations
    validator.validate_ai_analysis()
    validator.validate_knowledge_base()
    validator.validate_metrics()
    validator.validate_lambdas()
    validator.validate_streamlit()
    validator.validate_incident_generation()
    
    # Generate report
    validator.generate_report()
    
if __name__ == "__main__":
    main()
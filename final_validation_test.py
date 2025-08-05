#!/usr/bin/env python3
"""
Final validation test - simplified to verify all components are operational
"""

import json
import boto3
import requests
from datetime import datetime
from typing import Dict, List

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class FinalValidator:
    def __init__(self):
        self.region = 'us-east-1'
        self.results = {
            'lambda_functions': [],
            'bedrock_agents': [],
            'mcp_servers': [],
            'infrastructure': [],
            'test_scenarios': []
        }
    
    def print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    def test_lambda_functions(self):
        """Test all Lambda functions are deployed"""
        self.print_header("Lambda Functions Status")
        
        lambda_client = boto3.client('lambda', region_name=self.region)
        
        functions = [
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
        
        success_count = 0
        for func in functions:
            try:
                response = lambda_client.get_function(FunctionName=func)
                if response['Configuration']['State'] == 'Active':
                    print(f"{Colors.GREEN}✓ {func}: Active{Colors.RESET}")
                    success_count += 1
                    self.results['lambda_functions'].append({'name': func, 'status': 'Active'})
                else:
                    print(f"{Colors.YELLOW}⚠ {func}: {response['Configuration']['State']}{Colors.RESET}")
                    self.results['lambda_functions'].append({'name': func, 'status': response['Configuration']['State']})
            except Exception as e:
                print(f"{Colors.RED}✗ {func}: Not found{Colors.RESET}")
                self.results['lambda_functions'].append({'name': func, 'status': 'Not found'})
        
        print(f"\nLambda Functions: {success_count}/10 operational")
        return success_count == 10
    
    def test_bedrock_agents(self):
        """Test all Bedrock agents are prepared"""
        self.print_header("Bedrock Agents Status")
        
        bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
        
        agents = {
            'SRE-Supervisor': 'XKVWGESIAX',
            'SRE-Log-Analyzer': 'KYE8CL4NWP',
            'SRE-Metrics-Analyzer': 'HJZP7VBZOI',
            'SRE-CloudTrail-Analyzer': 'RPAXDVETHN',
            'SRE-VPC-Analyzer': 'BNFYR1YTWU',
            'SRE-Trusted-Advisor-Analyzer': 'BB2OARRB3J',
            'SRE-Personal-Health-Analyzer': 'WOHWA21ZBK'
        }
        
        success_count = 0
        for name, agent_id in agents.items():
            try:
                response = bedrock_agent.get_agent(agentId=agent_id)
                status = response['agent']['agentStatus']
                if status == 'PREPARED':
                    print(f"{Colors.GREEN}✓ {name}: Prepared{Colors.RESET}")
                    success_count += 1
                    self.results['bedrock_agents'].append({'name': name, 'status': 'Prepared'})
                else:
                    print(f"{Colors.YELLOW}⚠ {name}: {status}{Colors.RESET}")
                    self.results['bedrock_agents'].append({'name': name, 'status': status})
            except Exception as e:
                print(f"{Colors.RED}✗ {name}: Error - {str(e)[:50]}{Colors.RESET}")
                self.results['bedrock_agents'].append({'name': name, 'status': 'Error'})
        
        print(f"\nBedrock Agents: {success_count}/7 prepared")
        return success_count == 7
    
    def test_mcp_servers(self):
        """Test MCP servers are running"""
        self.print_header("MCP Servers Status")
        
        servers = {
            'Splunk': 'http://localhost:9080/splunk/search',
            'Dynatrace': 'http://localhost:9081/dynatrace/metrics',
            'ServiceNow': 'http://localhost:9082/servicenow/incidents',
            'Confluence': 'http://localhost:9083/confluence/search',
            'GitLab': 'http://localhost:9084/gitlab/search'
        }
        
        success_count = 0
        for name, url in servers.items():
            try:
                if name == 'Splunk':
                    response = requests.post(url, json={'query': 'test'}, timeout=2)
                else:
                    response = requests.get(url, timeout=2)
                
                if response.status_code == 200:
                    print(f"{Colors.GREEN}✓ {name}: Running{Colors.RESET}")
                    success_count += 1
                    self.results['mcp_servers'].append({'name': name, 'status': 'Running'})
                else:
                    print(f"{Colors.YELLOW}⚠ {name}: Status {response.status_code}{Colors.RESET}")
                    self.results['mcp_servers'].append({'name': name, 'status': f'Status {response.status_code}'})
            except Exception as e:
                print(f"{Colors.RED}✗ {name}: Not accessible{Colors.RESET}")
                self.results['mcp_servers'].append({'name': name, 'status': 'Not accessible'})
        
        print(f"\nMCP Servers: {success_count}/5 running")
        return success_count == 5
    
    def test_infrastructure(self):
        """Test supporting infrastructure"""
        self.print_header("Infrastructure Components")
        
        # Test DynamoDB tables
        dynamodb = boto3.client('dynamodb', region_name=self.region)
        tables = ['sre-knowledge-base', 'sre-knowledge-base-vectors']
        
        table_count = 0
        for table in tables:
            try:
                response = dynamodb.describe_table(TableName=table)
                if response['Table']['TableStatus'] == 'ACTIVE':
                    print(f"{Colors.GREEN}✓ DynamoDB {table}: Active{Colors.RESET}")
                    table_count += 1
                    self.results['infrastructure'].append({'component': f'DynamoDB {table}', 'status': 'Active'})
            except:
                print(f"{Colors.RED}✗ DynamoDB {table}: Not found{Colors.RESET}")
                self.results['infrastructure'].append({'component': f'DynamoDB {table}', 'status': 'Not found'})
        
        # Test Streamlit
        try:
            response = requests.get('http://localhost:8501', timeout=2)
            if response.status_code == 200:
                print(f"{Colors.GREEN}✓ Streamlit Dashboard: Running{Colors.RESET}")
                self.results['infrastructure'].append({'component': 'Streamlit', 'status': 'Running'})
            else:
                print(f"{Colors.YELLOW}⚠ Streamlit Dashboard: Status {response.status_code}{Colors.RESET}")
                self.results['infrastructure'].append({'component': 'Streamlit', 'status': f'Status {response.status_code}'})
        except:
            print(f"{Colors.RED}✗ Streamlit Dashboard: Not accessible{Colors.RESET}")
            self.results['infrastructure'].append({'component': 'Streamlit', 'status': 'Not accessible'})
        
        return table_count == 2
    
    def test_scenarios(self):
        """Test incident scenarios are loaded"""
        self.print_header("Test Scenarios")
        
        scenario_files = [
            'incident_test_cases.json',
            'additional_incident_scenarios.json',
            'comprehensive_incident_scenarios_with_ssm.json'
        ]
        
        total_scenarios = 0
        for file in scenario_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    count = len(data.get('test_cases', [])) + \
                           len(data.get('additional_scenarios', [])) + \
                           len(data.get('incident_scenarios_with_real_aws_data', []))
                    print(f"{Colors.GREEN}✓ {file}: {count} scenarios{Colors.RESET}")
                    total_scenarios += count
                    self.results['test_scenarios'].append({'file': file, 'count': count})
            except Exception as e:
                print(f"{Colors.RED}✗ {file}: Error loading{Colors.RESET}")
                self.results['test_scenarios'].append({'file': file, 'count': 0})
        
        print(f"\nTotal Test Scenarios: {total_scenarios}")
        return total_scenarios > 0
    
    def generate_summary(self):
        """Generate final summary"""
        self.print_header("Final Validation Summary")
        
        # Calculate totals
        lambda_active = sum(1 for f in self.results['lambda_functions'] if f['status'] == 'Active')
        agents_prepared = sum(1 for a in self.results['bedrock_agents'] if a['status'] == 'Prepared')
        mcp_running = sum(1 for m in self.results['mcp_servers'] if m['status'] == 'Running')
        infra_active = sum(1 for i in self.results['infrastructure'] if 'Active' in i['status'] or 'Running' in i['status'])
        scenarios_total = sum(s['count'] for s in self.results['test_scenarios'])
        
        # Print summary
        print(f"{Colors.BOLD}Component Status:{Colors.RESET}")
        print(f"  Lambda Functions:    {lambda_active}/10 ({lambda_active*10}%)")
        print(f"  Bedrock Agents:      {agents_prepared}/7 ({int(agents_prepared/7*100)}%)")
        print(f"  MCP Servers:         {mcp_running}/5 ({mcp_running*20}%)")
        print(f"  Infrastructure:      {infra_active}/3 ({int(infra_active/3*100)}%)")
        print(f"  Test Scenarios:      {scenarios_total} loaded")
        
        # Calculate overall percentage
        total_components = 10 + 7 + 5 + 3
        total_operational = lambda_active + agents_prepared + mcp_running + infra_active
        overall_percentage = int(total_operational / total_components * 100)
        
        print(f"\n{Colors.BOLD}Overall System Status: {overall_percentage}% Operational{Colors.RESET}")
        
        if overall_percentage == 100:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SYSTEM FULLY OPERATIONAL!{Colors.RESET}")
            print(f"{Colors.GREEN}All components are deployed and ready for use.{Colors.RESET}")
        elif overall_percentage >= 90:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SYSTEM OPERATIONAL!{Colors.RESET}")
            print(f"{Colors.GREEN}The system is ready for use with minor components pending.{Colors.RESET}")
        elif overall_percentage >= 80:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  SYSTEM MOSTLY OPERATIONAL{Colors.RESET}")
            print(f"{Colors.YELLOW}Most components are ready but some key features may be limited.{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ SYSTEM NEEDS ATTENTION{Colors.RESET}")
            print(f"{Colors.RED}Several components need to be fixed before the system is fully functional.{Colors.RESET}")
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_percentage': overall_percentage,
            'summary': {
                'lambda_functions': f"{lambda_active}/10",
                'bedrock_agents': f"{agents_prepared}/7",
                'mcp_servers': f"{mcp_running}/5",
                'infrastructure': f"{infra_active}/3",
                'test_scenarios': scenarios_total
            },
            'details': self.results
        }
        
        with open('final_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Colors.BLUE}ℹ Detailed report saved to: final_validation_report.json{Colors.RESET}")
        
        return overall_percentage >= 90
    
    def run(self):
        """Run all validation tests"""
        print(f"{Colors.BOLD}SRE Copilot Final System Validation{Colors.RESET}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        self.test_lambda_functions()
        self.test_bedrock_agents()
        self.test_mcp_servers()
        self.test_infrastructure()
        self.test_scenarios()
        
        # Generate summary
        success = self.generate_summary()
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success


if __name__ == '__main__':
    validator = FinalValidator()
    success = validator.run()
    exit(0 if success else 1)
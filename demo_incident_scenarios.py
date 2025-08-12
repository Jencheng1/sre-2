#!/usr/bin/env python3
"""
Interactive demo script to test the three incident scenarios
"""

import json
import boto3
import time
from datetime import datetime
from typing import Dict, Any

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name='us-east-1')

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.RESET}\n")


def print_scenario(name: str, description: str):
    """Print scenario details"""
    print(f"{Colors.BOLD}{Colors.BLUE}Scenario:{Colors.RESET} {name}")
    print(f"{Colors.BOLD}{Colors.BLUE}Description:{Colors.RESET} {description}")
    print()


def invoke_supervisor(payload: Dict[str, Any], use_mcp: bool = False) -> Dict[str, Any]:
    """Invoke supervisor Lambda and return analysis"""
    function_name = 'sre-supervisor-lambda-mcp' if use_mcp else 'sre-supervisor-lambda'
    
    print(f"{Colors.YELLOW}Invoking {function_name}...{Colors.RESET}")
    
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return json.loads(result['body'])
    else:
        return {'error': 'Analysis failed', 'details': result}


def display_analysis(analysis: Dict[str, Any]):
    """Display analysis results"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}Analysis Results:{Colors.RESET}")
    
    # Root Cause
    if 'root_cause' in analysis:
        print(f"\n{Colors.BOLD}Root Cause:{Colors.RESET}")
        print(f"  {analysis['root_cause']}")
    
    # Severity
    if 'severity' in analysis:
        severity_color = Colors.RED if analysis['severity'] == 'critical' else Colors.YELLOW
        print(f"\n{Colors.BOLD}Severity:{Colors.RESET} {severity_color}{analysis['severity']}{Colors.RESET}")
    
    # Recommendations
    if 'recommendations' in analysis:
        print(f"\n{Colors.BOLD}Recommendations:{Colors.RESET}")
        for i, rec in enumerate(analysis['recommendations'][:3], 1):
            print(f"  {i}. {rec}")
    
    # MCP Correlations (if available)
    if 'mcp_correlations' in analysis:
        print(f"\n{Colors.BOLD}External Service Correlations:{Colors.RESET}")
        for service, data in analysis['mcp_correlations'].items():
            if isinstance(data, dict) and data:
                print(f"  • {service.capitalize()}: Found relevant data")


def test_ec2_quota_scenario():
    """Test EC2 Service Quota Exceeded scenario"""
    print_header("EC2 Service Quota Exceeded")
    print_scenario(
        "EC2 Quota Limit Reached",
        "Auto-scaling attempts to launch 25 m5.large instances but quota is 20"
    )
    
    # Simulate incident data
    payload = {
        'incident_type': 'quota',
        'incident_id': f'DEMO-QUOTA-{int(time.time())}',
        'description': 'EC2 RunInstances failed with InstanceLimitExceeded during Black Friday scaling',
        'severity': 'high',
        'affected_resources': ['m5.large', 'us-west-2'],
        'error_details': {
            'error_code': 'Client.InstanceLimitExceeded',
            'error_message': 'You have requested more instances (25) than your current instance limit of 20',
            'quota_id': 'L-1216C47A',
            'current_limit': 20,
            'requested': 25,
            'instance_type': 'm5.large'
        },
        'timeline': [
            {'time': 'T-30min', 'event': 'Black Friday sale starts'},
            {'time': 'T-15min', 'event': 'Traffic increases 5x'},
            {'time': 'T-5min', 'event': 'Auto-scaling triggered'},
            {'time': 'T-0min', 'event': 'Instance launch failures begin'}
        ]
    }
    
    # Test without MCP
    print(f"{Colors.BOLD}Testing without MCP integration:{Colors.RESET}")
    analysis = invoke_supervisor(payload, use_mcp=False)
    display_analysis(analysis)
    
    # Test with MCP
    print(f"\n{Colors.BOLD}Testing with MCP integration:{Colors.RESET}")
    analysis_mcp = invoke_supervisor(payload, use_mcp=True)
    display_analysis(analysis_mcp)
    
    # Show expected vs actual
    print(f"\n{Colors.BOLD}Expected Root Cause:{Colors.RESET}")
    print("  EC2 service quota (20 instances) insufficient for requested deployment of 25 m5.large instances")
    
    input(f"\n{Colors.YELLOW}Press Enter to continue to next scenario...{Colors.RESET}")


def test_security_group_scenario():
    """Test Network Security Group Misconfiguration scenario"""
    print_header("Network Security Group Misconfiguration")
    print_scenario(
        "Security Group Rules Blocking Traffic",
        "Compliance update removes critical ingress rules causing connectivity loss"
    )
    
    payload = {
        'incident_type': 'network',
        'incident_id': f'DEMO-NET-{int(time.time())}',
        'description': 'Multiple EC2 instances unreachable after security group compliance update',
        'severity': 'critical',
        'affected_resources': [
            'sg-0123456789abcdef0',
            'i-1111111111111111',
            'i-2222222222222222'
        ],
        'network_details': {
            'reject_count': 450,
            'affected_ports': [443, 3306],
            'blocked_subnets': ['10.0.1.0/24', '10.0.2.0/24'],
            'security_group_changes': [{
                'time': 'T-15min',
                'action': 'RevokeSecurityGroupIngress',
                'removed_rule': '10.0.0.0/8 on port 443'
            }]
        },
        'business_impact': {
            'affected_services': ['API Gateway', 'Backend Services'],
            'users_affected': 5000,
            'revenue_impact': 'High'
        }
    }
    
    # Test without MCP
    print(f"{Colors.BOLD}Testing without MCP integration:{Colors.RESET}")
    analysis = invoke_supervisor(payload, use_mcp=False)
    display_analysis(analysis)
    
    # Test with MCP
    print(f"\n{Colors.BOLD}Testing with MCP integration:{Colors.RESET}")
    analysis_mcp = invoke_supervisor(payload, use_mcp=True)
    display_analysis(analysis_mcp)
    
    # Show VPC Flow Log correlation
    print(f"\n{Colors.BOLD}VPC Flow Log Analysis:{Colors.RESET}")
    print("  • 450 REJECT actions detected")
    print("  • Source: 10.0.1.0/24, 10.0.2.0/24")
    print("  • Destination: 10.0.3.0/24 (Backend subnet)")
    print("  • Blocked Port: 443 (HTTPS)")
    
    input(f"\n{Colors.YELLOW}Press Enter to continue to next scenario...{Colors.RESET}")


def test_api_throttling_scenario():
    """Test API Throttling incident scenario"""
    print_header("API Throttling During Peak Load")
    print_scenario(
        "EC2 RunInstances API Throttling",
        "Auto-scaling making too many API calls without retry logic"
    )
    
    payload = {
        'incident_type': 'api_throttling',
        'incident_id': f'DEMO-THROTTLE-{int(time.time())}',
        'description': 'EC2 RunInstances API calls being throttled during flash sale event',
        'severity': 'high',
        'affected_resources': ['RunInstances', 'app-asg', 'us-west-2'],
        'throttling_details': {
            'api_operation': 'RunInstances',
            'current_rate': 150,
            'rate_limit': 100,
            'error_rate': 33,
            'failed_requests': 50,
            'time_window': '1 minute'
        },
        'contributing_factors': [
            'No exponential backoff implemented',
            'Batch size too large (10 instances per call)',
            'Multiple parallel deployment processes'
        ]
    }
    
    # Test without MCP
    print(f"{Colors.BOLD}Testing without MCP integration:{Colors.RESET}")
    analysis = invoke_supervisor(payload, use_mcp=False)
    display_analysis(analysis)
    
    # Test with MCP
    print(f"\n{Colors.BOLD}Testing with MCP integration:{Colors.RESET}")
    analysis_mcp = invoke_supervisor(payload, use_mcp=True)
    display_analysis(analysis_mcp)
    
    # Show API metrics
    print(f"\n{Colors.BOLD}API Usage Metrics:{Colors.RESET}")
    print("  • Current Rate: 150 calls/minute")
    print("  • Rate Limit: 100 calls/minute")
    print("  • Error Rate: 33%")
    print("  • Recommendation: Implement retry with exponential backoff")
    
    input(f"\n{Colors.YELLOW}Press Enter to finish demo...{Colors.RESET}")


def run_all_scenarios():
    """Run all three scenarios"""
    print_header("SRE Copilot Incident Scenario Demo")
    print(f"This demo will test three incident scenarios:")
    print(f"1. EC2 Service Quota Exceeded")
    print(f"2. Network Security Group Misconfiguration")
    print(f"3. API Throttling During Peak Load")
    
    input(f"\n{Colors.YELLOW}Press Enter to start...{Colors.RESET}")
    
    # Run each scenario
    test_ec2_quota_scenario()
    test_security_group_scenario()
    test_api_throttling_scenario()
    
    # Summary
    print_header("Demo Complete")
    print(f"{Colors.GREEN}✓ All three scenarios have been demonstrated{Colors.RESET}")
    print(f"\nYou can now:")
    print(f"1. View the incidents in the Streamlit dashboard")
    print(f"2. Check the Knowledge Base for indexed incidents")
    print(f"3. Review CloudWatch Logs for detailed analysis")
    print(f"\nStreamlit Dashboard: http://localhost:8501")


def quick_test_single_scenario():
    """Quick test menu for single scenario"""
    print_header("Quick Scenario Test")
    
    print("Select a scenario to test:")
    print("1. EC2 Service Quota Exceeded")
    print("2. Network Security Group Misconfiguration")
    print("3. API Throttling")
    print("4. Run all scenarios")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == '1':
        test_ec2_quota_scenario()
    elif choice == '2':
        test_security_group_scenario()
    elif choice == '3':
        test_api_throttling_scenario()
    elif choice == '4':
        run_all_scenarios()
    else:
        print(f"{Colors.RED}Invalid choice{Colors.RESET}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_test_single_scenario()
    else:
        run_all_scenarios()
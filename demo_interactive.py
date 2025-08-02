#!/usr/bin/env python3
"""
Interactive demo for testing SRE Copilot agents with real AWS APIs.
"""

import boto3
import json
import os
from datetime import datetime

def print_menu():
    """Print interactive menu."""
    print("\n" + "="*60)
    print("🎯 SRE COPILOT INTERACTIVE DEMO")
    print("="*60)
    print("\nSelect an option to test REAL AWS APIs:")
    print("\n1. Test Personal Health Agent")
    print("2. Test CloudWatch Logs Agent")
    print("3. Test Supervisor Agent (Orchestration)")
    print("4. Run All Working Tests")
    print("5. Exit")
    print("\n" + "="*60)

def test_personal_health():
    """Interactive test for Personal Health agent."""
    print("\n🏥 PERSONAL HEALTH AGENT TEST")
    print("-"*60)
    print("\nSelect action:")
    print("1. Get Maintenance Events")
    print("2. Get Service Issues")
    print("3. Get Account Notifications")
    print("4. Test All Actions")
    
    choice = input("\nEnter choice (1-4): ")
    
    lambda_client = boto3.client('lambda')
    
    actions = {
        '1': ('get_maintenance_events', 'Maintenance Events'),
        '2': ('get_service_issues', 'Service Issues'),
        '3': ('get_account_notifications', 'Account Notifications')
    }
    
    if choice == '4':
        # Test all actions
        for action, desc in actions.values():
            print(f"\n📌 Testing {desc}...")
            invoke_agent('sre-personal-health-agent-lambda', action, {'max_results': 10})
    elif choice in actions:
        action, desc = actions[choice]
        print(f"\n📌 Testing {desc}...")
        invoke_agent('sre-personal-health-agent-lambda', action, {'max_results': 10})
    else:
        print("Invalid choice")

def test_cloudwatch_logs():
    """Interactive test for CloudWatch Logs agent."""
    print("\n📊 CLOUDWATCH LOGS AGENT TEST")
    print("-"*60)
    print("\nSelect action:")
    print("1. List Log Groups")
    print("2. Search Logs")
    print("3. Analyze Log Group")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == '1':
        print("\n📌 Listing Real Log Groups...")
        invoke_agent('sre-cloudwatch-logs-agent-lambda', 'get_log_groups', {'max_results': 10})
    
    elif choice == '2':
        log_group = input("\nEnter log group name (e.g., /aws/lambda/sre-supervisor-lambda): ")
        pattern = input("Enter search pattern (e.g., ERROR, INFO): ")
        print(f"\n📌 Searching for '{pattern}' in {log_group}...")
        invoke_agent('sre-cloudwatch-logs-agent-lambda', 'search_logs', {
            'log_group_name': log_group,
            'pattern': pattern,
            'hours': 1
        })
    
    elif choice == '3':
        log_group = input("\nEnter log group name to analyze: ")
        print(f"\n📌 Analyzing {log_group}...")
        invoke_agent('sre-cloudwatch-logs-agent-lambda', 'analyze_log_group', {
            'log_group_name': log_group,
            'hours': 1
        })
    else:
        print("Invalid choice")

def test_supervisor():
    """Interactive test for Supervisor agent."""
    print("\n🎯 SUPERVISOR AGENT TEST")
    print("-"*60)
    print("\nEnter incident description or select preset:")
    print("1. High CPU usage on production servers")
    print("2. API response time degradation")
    print("3. Database connection issues")
    print("4. Custom incident description")
    
    choice = input("\nEnter choice (1-4): ")
    
    descriptions = {
        '1': 'High CPU usage detected on production servers, averaging 95% for the last hour',
        '2': 'API response times have increased from 200ms to 2000ms affecting all endpoints',
        '3': 'Database connection pool exhausted, applications failing to connect'
    }
    
    if choice in descriptions:
        description = descriptions[choice]
    elif choice == '4':
        description = input("\nEnter incident description: ")
    else:
        print("Invalid choice")
        return
    
    print(f"\n📌 Analyzing: {description}")
    print("Supervisor will orchestrate all agents...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        response = lambda_client.invoke(
            FunctionName='sre-supervisor-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps({
                    'action': 'analyze',
                    'description': description
                })
            })
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            
            print("\n✅ SUPERVISOR ANALYSIS COMPLETE")
            print("-"*40)
            
            if 'monitoring_data' in body:
                md = body['monitoring_data']
                print("\n📊 Real Data Collected:")
                
                for key, value in md.items():
                    if isinstance(value, dict):
                        if 'log_groups' in value:
                            print(f"   • {key}: {len(value.get('log_groups', []))} log groups")
                        elif 'maintenance_events' in value:
                            print(f"   • {key}: {len(value.get('maintenance_events', []))} events")
                        else:
                            print(f"   • {key}: Data collected")
            
            if 'analysis' in body:
                print("\n🤖 AI Analysis:")
                print(f"   {body['analysis'][:300]}...")
            
            print("\n✅ All data from REAL AWS APIs!")
        else:
            print(f"❌ Error: {result.get('body')}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def invoke_agent(function_name, action, params=None):
    """Invoke an agent and display results."""
    lambda_client = boto3.client('lambda')
    
    payload = {'action': action}
    if params:
        payload.update(params)
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            
            print("\n✅ SUCCESS - Real AWS API Response")
            print("-"*40)
            
            # Display relevant data
            for key, value in body.items():
                if isinstance(value, list):
                    print(f"   • {key}: {len(value)} items")
                    if value and len(value) > 0:
                        print(f"     Sample: {value[0]}")
                elif key == 'analysis' and value:
                    print(f"   • AI Analysis: Completed")
                elif key != 'analysis':
                    print(f"   • {key}: {type(value).__name__}")
            
            print("\n✅ This is REAL data from AWS APIs!")
            
        else:
            print(f"\n❌ Error: {result.get('body')}")
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")

def run_all_tests():
    """Run all working tests."""
    print("\n🔄 RUNNING ALL WORKING TESTS")
    print("="*60)
    
    # Test Personal Health
    print("\n1️⃣ Personal Health Agent")
    for action in ['get_maintenance_events', 'get_service_issues', 'get_account_notifications']:
        print(f"\n   Testing {action}...")
        invoke_agent('sre-personal-health-agent-lambda', action, {'max_results': 5})
    
    # Test CloudWatch Logs
    print("\n\n2️⃣ CloudWatch Logs Agent")
    print("\n   Testing get_log_groups...")
    invoke_agent('sre-cloudwatch-logs-agent-lambda', 'get_log_groups', {'max_results': 5})
    
    # Test Supervisor
    print("\n\n3️⃣ Supervisor Agent")
    print("\n   Testing orchestration...")
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName='sre-supervisor-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'body': json.dumps({
                'action': 'analyze',
                'description': 'System health check'
            })
        })
    )
    
    result = json.loads(response['Payload'].read())
    if result.get('statusCode') == 200:
        print("\n✅ Supervisor orchestration successful!")
    else:
        print("\n❌ Supervisor error")
    
    print("\n✅ All tests completed!")

def main():
    """Main interactive loop."""
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    print("\n" + "="*80)
    print("🚀 SRE COPILOT - REAL AWS API INTERACTIVE DEMO")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis demo lets you interactively test agents with REAL AWS APIs.")
    print("All data comes from your actual AWS account - NO mocks!")
    
    while True:
        print_menu()
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            test_personal_health()
        elif choice == '2':
            test_cloudwatch_logs()
        elif choice == '3':
            test_supervisor()
        elif choice == '4':
            run_all_tests()
        elif choice == '5':
            print("\n👋 Exiting demo. Thank you!")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
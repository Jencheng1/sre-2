#!/usr/bin/env python3
"""
Streamlit Workflow Test - Tests actual working components
"""

import requests
import json
import boto3
import time
from datetime import datetime

def test_workflow():
    """Test the complete incident analysis workflow"""
    print("🧪 Testing SRE Copilot Workflow")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Streamlit is running
    print("\n1️⃣ Testing Streamlit Dashboard...")
    tests_total += 1
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit dashboard is running on port 8501")
            tests_passed += 1
        else:
            print("❌ Streamlit returned status:", response.status_code)
    except Exception as e:
        print("❌ Cannot connect to Streamlit:", str(e))
    
    # Test 2: MCP Services
    print("\n2️⃣ Testing MCP Services...")
    with open('mcp_ports.json', 'r') as f:
        mcp_ports = json.load(f)
    
    critical_services = ['splunk', 'alm_octane', 'jira', 'servicenow']
    working_services = []
    
    for service in critical_services:
        tests_total += 1
        port = mcp_ports.get(service)
        try:
            if service == 'splunk':
                resp = requests.post(f"http://localhost:{port}/splunk/search",
                                   json={"query": "test", "time_range": "-1h"}, timeout=2)
            elif service == 'alm_octane':
                resp = requests.get(f"http://localhost:{port}/octane/defects", timeout=2)
            elif service == 'jira':
                resp = requests.get(f"http://localhost:{port}/jira/issues", timeout=2)
            elif service == 'servicenow':
                resp = requests.get(f"http://localhost:{port}/servicenow/incidents", timeout=2)
            
            if resp.status_code in [200, 201]:
                print(f"✅ {service.upper()} MCP server is working on port {port}")
                working_services.append(service)
                tests_passed += 1
            else:
                print(f"❌ {service.upper()} returned status {resp.status_code}")
        except Exception as e:
            print(f"❌ {service.upper()} connection failed: {str(e)[:50]}")
    
    # Test 3: Lambda Functions
    print("\n3️⃣ Testing AWS Lambda Functions...")
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    critical_lambdas = ['sre-supervisor-lambda', 'sre-knowledge-base-agent']
    working_lambdas = []
    
    for lambda_name in critical_lambdas:
        tests_total += 1
        try:
            response = lambda_client.get_function(FunctionName=lambda_name)
            if response['Configuration']['State'] == 'Active':
                print(f"✅ {lambda_name} is active and ready")
                working_lambdas.append(lambda_name)
                tests_passed += 1
            else:
                print(f"❌ {lambda_name} is in state: {response['Configuration']['State']}")
        except Exception as e:
            print(f"❌ {lambda_name} not found or error: {str(e)[:50]}")
    
    # Test 4: Incident Scenarios
    print("\n4️⃣ Testing Incident Scenarios...")
    tests_total += 1
    try:
        import incident_scenarios
        # Call the module's main function to get scenarios
        scenarios = incident_scenarios.IncidentScenarios()
        scenario_list = scenarios.get_all_scenarios()
        
        if len(scenario_list) >= 8:
            print(f"✅ Found {len(scenario_list)} incident scenarios")
            tests_passed += 1
        else:
            print(f"❌ Only found {len(scenario_list)} scenarios (expected 8+)")
    except Exception as e:
        print(f"❌ Error loading scenarios: {str(e)}")
    
    # Test 5: Knowledge Base
    print("\n5️⃣ Testing Knowledge Base...")
    tests_total += 1
    try:
        # Test if DynamoDB table exists
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('sre-knowledge-base')
        response = table.scan(Limit=1)
        print(f"✅ Knowledge base table exists with {response['Count']} test items")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Knowledge base error: {str(e)[:50]}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 WORKFLOW TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total*100):.1f}%")
    
    if tests_passed >= 4:
        print("\n✅ Core components are working! You can:")
        print("1. Access dashboard at http://localhost:8501")
        print("2. Create and analyze incidents")
        print("3. Use MCP integrations for enhanced analysis")
        print(f"4. Working MCP services: {', '.join(working_services)}")
        print(f"5. Active Lambda functions: {', '.join(working_lambdas)}")
    else:
        print("\n⚠️  Some core components are not working properly")
        print("Please check the logs and ensure all services are started")
    
    return tests_passed >= 4

if __name__ == "__main__":
    success = test_workflow()
    exit(0 if success else 1)
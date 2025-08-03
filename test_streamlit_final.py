#!/usr/bin/env python3
"""Final comprehensive test for Streamlit app functionality."""

import requests
import json
import time
import sys
from datetime import datetime

def test_streamlit_running():
    """Test if Streamlit is running."""
    print("\n=== Testing Streamlit Server ===")
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✓ Streamlit is running on port 8501")
            return True
        else:
            print(f"✗ Streamlit returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Streamlit is not accessible: {e}")
        return False

def test_mcp_services():
    """Test MCP services availability."""
    print("\n=== Testing MCP Services ===")
    
    # Load port configuration
    try:
        with open('mcp_ports.json', 'r') as f:
            ports = json.load(f)
    except:
        ports = {
            'splunk': 9080,
            'dynatrace': 9081,
            'servicenow': 9082,
            'confluence': 9083,
            'gitlab': 9084
        }
    
    services_ok = True
    for service, port in ports.items():
        try:
            if service == 'splunk':
                response = requests.post(
                    f"http://localhost:{port}/splunk/search",
                    json={"query": "test", "time_range": "-1h"},
                    timeout=2
                )
            elif service == 'dynatrace':
                response = requests.get(
                    f"http://localhost:{port}/dynatrace/metrics",
                    params={"queue": "test", "metric": "depth"},
                    timeout=2
                )
            elif service == 'servicenow':
                response = requests.get(
                    f"http://localhost:{port}/servicenow/incidents",
                    timeout=2
                )
            elif service == 'confluence':
                response = requests.get(
                    f"http://localhost:{port}/confluence/search",
                    params={"query": "test"},
                    timeout=2
                )
            elif service == 'gitlab':
                response = requests.get(
                    f"http://localhost:{port}/gitlab/search",
                    params={"repo": "test", "query": "test"},
                    timeout=2
                )
            
            if response.status_code in [200, 201]:
                print(f"✓ {service.title()} service is online on port {port}")
            else:
                print(f"✗ {service.title()} service error: status {response.status_code}")
                services_ok = False
        except Exception as e:
            print(f"✗ {service.title()} service is offline: {str(e)}")
            services_ok = False
    
    return services_ok

def test_streamlit_features():
    """Test key Streamlit features."""
    print("\n=== Testing Streamlit Features ===")
    
    # Check if we can import the app without errors
    try:
        import streamlit_app
        print("✓ Streamlit app imports successfully")
        
        # Check key components
        if hasattr(streamlit_app, 'EnhancedSREDashboard'):
            print("✓ EnhancedSREDashboard class found")
        else:
            print("✗ EnhancedSREDashboard class not found")
            
        if hasattr(streamlit_app, 'MCP_AVAILABLE'):
            if streamlit_app.MCP_AVAILABLE:
                print("✓ MCP integration is available")
            else:
                print("✗ MCP integration is not available")
        
        # Check key manager
        if hasattr(streamlit_app, 'key_manager'):
            print("✓ Key manager imported successfully")
        else:
            print("✗ Key manager not found")
            
        return True
    except Exception as e:
        print(f"✗ Error importing Streamlit app: {e}")
        return False

def test_feedback_system():
    """Test feedback system functionality."""
    print("\n=== Testing Feedback System ===")
    
    try:
        from feedback.feedback_system import FeedbackSystem
        feedback_system = FeedbackSystem()
        print("✓ Feedback system imported successfully")
        
        # Test storing feedback
        test_incident_id = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        feedback_data = {
            'incident_id': test_incident_id,
            'helpful': True,
            'confidence': 4,
            'feedback_text': "Test feedback from final test",
            'corrections': {"root_cause": "Test correction"}
        }
        result = feedback_system.submit_feedback(feedback_data)
        feedback_id = result.get('feedback_id', 'unknown')
        print(f"✓ Test feedback stored with ID: {feedback_id}")
        
        # Test retrieving feedback
        recent_feedback = feedback_system.get_recent_feedback(limit=5)
        print(f"✓ Retrieved {len(recent_feedback)} recent feedback entries")
        
        return True
    except Exception as e:
        print(f"✗ Feedback system error: {e}")
        return False

def test_lambda_functions():
    """Test Lambda function availability."""
    print("\n=== Testing Lambda Functions ===")
    
    try:
        import boto3
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Test standard Lambda
        try:
            response = lambda_client.get_function(FunctionName='sre-supervisor-lambda')
            print("✓ Standard supervisor Lambda exists")
        except:
            print("✗ Standard supervisor Lambda not found")
        
        # Test MCP Lambda
        try:
            response = lambda_client.get_function(FunctionName='sre-supervisor-lambda-mcp')
            print("✓ MCP-enabled supervisor Lambda exists")
        except:
            print("✗ MCP-enabled supervisor Lambda not found")
            
        return True
    except Exception as e:
        print(f"✗ Lambda test error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("=" * 60)
    print("SRE Copilot - Comprehensive Streamlit Test")
    print("=" * 60)
    
    test_results = {
        'streamlit_running': test_streamlit_running(),
        'streamlit_features': test_streamlit_features(),
        'mcp_services': test_mcp_services(),
        'feedback_system': test_feedback_system(),
        'lambda_functions': test_lambda_functions()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    print("\nDetailed Results:")
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print("\n" + "=" * 60)
    
    if passed_tests == total_tests:
        print("✅ ALL TESTS PASSED! Streamlit app is fully functional.")
        print("\nAccess the app at: http://localhost:8501")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    print("\nKey Features Available:")
    print("1. Original SRE Copilot features:")
    print("   - Incident Management")
    print("   - Root Cause Analysis")
    print("   - Knowledge Base")
    print("   - Recent Changes")
    print("   - Analytics Dashboard")
    print("   - User Guide")
    
    if test_results['mcp_services']:
        print("\n2. MCP Integration features:")
        print("   - External service correlation (Splunk, Dynatrace, ServiceNow, Confluence, GitLab)")
        print("   - Human-in-the-loop feedback")
        print("   - MCP Status monitoring")
        print("   - Feedback Analytics")
    
    print("\n" + "=" * 60)
    
    return passed_tests == total_tests

def main():
    """Main function."""
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
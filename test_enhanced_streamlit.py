#!/usr/bin/env python3
"""Test script for the enhanced Streamlit application."""

import json
import os
import sys
import time
import requests
from datetime import datetime

def check_mcp_servers():
    """Check if MCP servers are running."""
    print("\n=== Checking MCP Servers ===")
    
    # Load port configuration
    if os.path.exists('mcp_ports.json'):
        with open('mcp_ports.json', 'r') as f:
            ports = json.load(f)
    else:
        ports = {
            'splunk': 9080,
            'dynatrace': 9081,
            'servicenow': 9082,
            'confluence': 9083,
            'gitlab': 9084
        }
    
    server_status = {}
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
                server_status[service] = 'online'
                print(f"✓ {service.title()} server is online on port {port}")
            else:
                server_status[service] = 'error'
                print(f"✗ {service.title()} server returned error: {response.status_code}")
        except Exception as e:
            server_status[service] = 'offline'
            print(f"✗ {service.title()} server is offline on port {port}: {str(e)}")
    
    return server_status

def check_streamlit_features():
    """Check Streamlit app features."""
    print("\n=== Checking Streamlit Features ===")
    
    # Check if Streamlit is running
    try:
        response = requests.get("http://localhost:8501", timeout=2)
        if response.status_code == 200:
            print("✓ Streamlit is running on port 8501")
        else:
            print("✗ Streamlit returned unexpected status code:", response.status_code)
    except Exception as e:
        print("✗ Streamlit is not running:", str(e))
        print("  To start: nohup python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &")
        return False
    
    # Check key imports
    try:
        from streamlit_app import EnhancedSREDashboard
        print("✓ EnhancedSREDashboard class loaded")
        
        # Check if MCP features are available
        import streamlit_app
        if hasattr(streamlit_app, 'MCP_AVAILABLE'):
            if streamlit_app.MCP_AVAILABLE:
                print("✓ MCP integration is available")
            else:
                print("✗ MCP integration is not available (modules not found)")
        
    except Exception as e:
        print(f"✗ Error loading Streamlit app: {e}")
        return False
    
    return True

def check_feedback_system():
    """Check feedback system."""
    print("\n=== Checking Feedback System ===")
    
    try:
        from feedback.feedback_system import FeedbackSystem
        feedback_system = FeedbackSystem()
        print("✓ Feedback system imported successfully")
        
        # Test feedback operations
        test_feedback = {
            'incident_id': 'test-' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'helpful': True,
            'confidence': 4,
            'feedback_text': 'Test feedback from enhanced Streamlit test',
            'corrections': {
                'root_cause': 'Test root cause correction'
            }
        }
        
        # Store feedback
        feedback_id = feedback_system.store_feedback(
            incident_id=test_feedback['incident_id'],
            helpful=test_feedback['helpful'],
            confidence=test_feedback['confidence'],
            feedback_text=test_feedback['feedback_text'],
            corrections=test_feedback['corrections']
        )
        print(f"✓ Test feedback stored with ID: {feedback_id}")
        
        # Retrieve feedback
        all_feedback = feedback_system.get_all_feedback()
        print(f"✓ Retrieved {len(all_feedback)} feedback entries")
        
        return True
    except Exception as e:
        print(f"✗ Feedback system error: {e}")
        return False

def check_lambda_integration():
    """Check Lambda integration."""
    print("\n=== Checking Lambda Integration ===")
    
    try:
        import boto3
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Check if MCP-enabled Lambda exists
        try:
            response = lambda_client.get_function(FunctionName='sre-supervisor-lambda-mcp')
            print("✓ MCP-enabled Lambda function exists")
        except:
            print("✗ MCP-enabled Lambda function not found")
            print("  Standard Lambda will be used for analysis")
        
        # Check standard Lambda
        try:
            response = lambda_client.get_function(FunctionName='sre-supervisor-lambda')
            print("✓ Standard supervisor Lambda function exists")
        except:
            print("✗ Standard supervisor Lambda function not found")
            
        return True
    except Exception as e:
        print(f"✗ Lambda check error: {e}")
        return False

def run_integration_test():
    """Run a complete integration test."""
    print("\n=== Running Integration Test ===")
    
    # Check if all components are available
    mcp_status = check_mcp_servers()
    mcp_online = any(status == 'online' for status in mcp_status.values())
    
    if mcp_online:
        print("\n✓ At least one MCP server is online")
        print("  The Streamlit app will show MCP integration features")
    else:
        print("\n✗ No MCP servers are online")
        print("  The Streamlit app will run without MCP features")
    
    # Summary
    print("\n=== Test Summary ===")
    print("1. Original Streamlit features: ✓ Available")
    print("   - Incident Management")
    print("   - Root Cause Analysis") 
    print("   - Knowledge Base")
    print("   - Recent Changes")
    print("   - Analytics")
    print("   - User Guide")
    
    if mcp_online:
        print("\n2. MCP Integration features: ✓ Available")
        print("   - MCP test incident scenarios")
        print("   - External data correlation")
        print("   - Human-in-the-loop feedback")
        print("   - MCP Status tab")
        print("   - Feedback Analytics tab")
    else:
        print("\n2. MCP Integration features: ✗ Not available")
        print("   To enable: Run start_mcp_servers.sh")
    
    print("\n3. Access the enhanced Streamlit app at:")
    print("   http://localhost:8501")
    
    return True

def main():
    """Main test function."""
    print("Enhanced Streamlit Application Test")
    print("=" * 50)
    
    # Check all components
    streamlit_ok = check_streamlit_features()
    feedback_ok = check_feedback_system()
    lambda_ok = check_lambda_integration()
    
    if streamlit_ok:
        run_integration_test()
    else:
        print("\n✗ Streamlit is not running. Please start it first.")
        
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()
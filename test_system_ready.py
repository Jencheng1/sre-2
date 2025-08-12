#!/usr/bin/env python3
"""
Quick system readiness test for defect management integration
"""

import requests
import json
import os

def test_system_readiness():
    """Test all components are ready"""
    print("🧪 Testing Defect Management System Readiness")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Streamlit Dashboard
    total_tests += 1
    try:
        response = requests.get("http://localhost:8501/_stcore/health", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit Dashboard: Running")
            tests_passed += 1
        else:
            print(f"❌ Streamlit Dashboard: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Streamlit Dashboard: {e}")
    
    # Test 2: ALM Octane MCP Server
    total_tests += 1
    try:
        response = requests.get("http://localhost:9085/octane/defects", timeout=5)
        if response.status_code == 200:
            defects = response.json()
            print(f"✅ ALM Octane Server: {len(defects)} defects available")
            tests_passed += 1
        else:
            print(f"❌ ALM Octane Server: Status {response.status_code}")
    except Exception as e:
        print(f"❌ ALM Octane Server: {e}")
    
    # Test 3: Jira MCP Server  
    total_tests += 1
    try:
        response = requests.get("http://localhost:9086/jira/issues", timeout=5)
        if response.status_code == 200:
            issues = response.json()
            print(f"✅ Jira Server: {len(issues)} issues available")
            tests_passed += 1
        else:
            print(f"❌ Jira Server: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Jira Server: {e}")
    
    # Test 4: Defect Creation
    total_tests += 1
    try:
        test_defect = {
            "name": "System Readiness Test Defect",
            "description": "Testing defect creation for system readiness",
            "severity": "Low",
            "component": "Test System"
        }
        
        response = requests.post("http://localhost:9085/octane/defects", 
                               json=test_defect, timeout=5)
        if response.status_code == 201:
            print("✅ Defect Creation: Working")
            tests_passed += 1
        else:
            print(f"❌ Defect Creation: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Defect Creation: {e}")
    
    # Test 5: Analytics Endpoints
    total_tests += 1
    try:
        response = requests.get("http://localhost:9085/octane/analytics/quality-metrics", timeout=5)
        if response.status_code == 200:
            print("✅ Analytics Endpoints: Working")
            tests_passed += 1
        else:
            print(f"❌ Analytics Endpoints: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Analytics Endpoints: {e}")
    
    print("=" * 50)
    print(f"📊 System Readiness: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All systems operational! Ready for defect management testing.")
        print("🌐 Access dashboard: http://localhost:8501")
        return True
    else:
        print(f"⚠️  {total_tests - tests_passed} components need attention")
        return False

if __name__ == "__main__":
    # Set AWS region
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['AWS_REGION'] = 'us-east-1'
    
    success = test_system_readiness()
    exit(0 if success else 1)
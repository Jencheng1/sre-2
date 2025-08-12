#!/usr/bin/env python3
"""
Test that the enhanced streamlit has all the expected tabs including defect management
"""

import requests
import time

def test_streamlit_tabs():
    """Test that streamlit is running with expected functionality"""
    print("🧪 Testing Enhanced Streamlit Dashboard Tabs")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Streamlit is running
    total_tests += 1
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit Dashboard: Running")
            tests_passed += 1
        else:
            print(f"❌ Streamlit Dashboard: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Streamlit Dashboard: {e}")
    
    # Test 2: MCP servers for defect management
    total_tests += 1
    try:
        alm_response = requests.get("http://localhost:9085/octane/defects", timeout=5)
        jira_response = requests.get("http://localhost:9086/jira/issues", timeout=5)
        
        if alm_response.status_code == 200 and jira_response.status_code == 200:
            print("✅ Defect Management Servers: Both ALM Octane and Jira operational")
            tests_passed += 1
        else:
            print(f"❌ Defect Management Servers: ALM Octane={alm_response.status_code}, Jira={jira_response.status_code}")
    except Exception as e:
        print(f"❌ Defect Management Servers: {e}")
    
    # Test 3: Check if streamlit has been enhanced (file modification check)
    total_tests += 1
    try:
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
            if 'render_defect_management' in content and 'render_defect_correlation' in content:
                print("✅ Streamlit Enhancement: Defect management methods added")
                tests_passed += 1
            else:
                print("❌ Streamlit Enhancement: Defect management methods not found")
    except Exception as e:
        print(f"❌ Streamlit Enhancement: {e}")
    
    # Test 4: Check tab navigation structure
    total_tests += 1
    try:
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
            if 'Defect Management' in content and 'Defect Correlation' in content and 'Correlation Scenarios' in content:
                print("✅ Tab Navigation: All 3 new defect management tabs found")
                tests_passed += 1
            else:
                print("❌ Tab Navigation: Missing defect management tabs")
    except Exception as e:
        print(f"❌ Tab Navigation: {e}")
    
    print("=" * 50)
    print(f"📊 Enhanced Streamlit Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Enhanced Streamlit with defect management is fully operational.")
        print("🌐 Access dashboard: http://localhost:8501")
        print("🐛 New tabs available: Defect Management, Defect Correlation, Correlation Scenarios")
        return True
    else:
        print(f"⚠️ {total_tests - tests_passed} tests failed")
        return False

if __name__ == "__main__":
    test_streamlit_tabs()
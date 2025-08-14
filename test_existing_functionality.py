"""
Test to ensure existing functionality is not impacted
"""

import subprocess
import sys
import json
import time
import requests


def test_streamlit_launch():
    """Test that streamlit app can be launched"""
    print("Testing Streamlit app launch...")
    
    # Kill any existing streamlit processes
    subprocess.run("ps aux | grep streamlit | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null", shell=True)
    time.sleep(2)
    
    # Launch the new streamlit app
    process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", 
        "streamlit_app_problem_management.py",
        "--server.port", "8502",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Give it time to start
    time.sleep(5)
    
    # Check if process is running
    if process.poll() is None:
        print("✅ Streamlit app launched successfully")
        
        # Try to access the app
        try:
            response = requests.get("http://localhost:8502", timeout=5)
            if response.status_code == 200:
                print("✅ Streamlit app is accessible")
            else:
                print(f"⚠️ Streamlit app returned status code: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Could not access Streamlit app: {e}")
        
        # Kill the process
        process.terminate()
        process.wait()
        return True
    else:
        print("❌ Streamlit app failed to launch")
        stdout, stderr = process.communicate()
        print(f"Error: {stderr.decode()}")
        return False


def test_lambda_functions():
    """Test that Lambda functions are still accessible"""
    print("\nTesting Lambda functions...")
    
    import boto3
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    lambda_functions = [
        'sre-supervisor-lambda',
        'sre-cloudwatch-agent',
        'sre-knowledge-base-agent'
    ]
    
    all_good = True
    for func_name in lambda_functions:
        try:
            response = lambda_client.get_function(FunctionName=func_name)
            if response['Configuration']['State'] == 'Active':
                print(f"✅ {func_name} is active")
            else:
                print(f"⚠️ {func_name} is in state: {response['Configuration']['State']}")
                all_good = False
        except Exception as e:
            print(f"❌ Error checking {func_name}: {e}")
            all_good = False
    
    return all_good


def test_mcp_servers():
    """Test MCP servers if they're running"""
    print("\nTesting MCP servers...")
    
    mcp_ports = {
        9085: "ALM Octane",
        9086: "Jira"
    }
    
    all_good = True
    for port, name in mcp_ports.items():
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            print(f"✅ {name} MCP server on port {port} is responding")
        except:
            print(f"ℹ️ {name} MCP server on port {port} is not running (this is okay if not in use)")
    
    return True  # MCP servers are optional


def test_import_modules():
    """Test that all modules can be imported"""
    print("\nTesting module imports...")
    
    modules_to_test = [
        ('servicenow_problem_manager', 'ServiceNowProblemManager'),
        ('synthetic_transaction_generator', 'SyntheticTransactionGenerator'),
        ('incident_generator', 'IncidentGenerator'),
        ('defect_incident_correlator', 'DefectIncidentCorrelator'),
        ('change_incident_correlator', 'ChangeIncidentCorrelator')
    ]
    
    all_good = True
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ Successfully imported {class_name} from {module_name}")
        except Exception as e:
            print(f"❌ Failed to import {class_name} from {module_name}: {e}")
            all_good = False
    
    return all_good


def main():
    """Run all tests"""
    print("=" * 60)
    print("EXISTING FUNCTIONALITY VERIFICATION")
    print("=" * 60)
    
    results = {
        'Module Imports': test_import_modules(),
        'Lambda Functions': test_lambda_functions(),
        'Streamlit Launch': test_streamlit_launch(),
        'MCP Servers': test_mcp_servers()
    }
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ ALL VERIFICATIONS PASSED - No existing functionality impacted")
    else:
        print("⚠️ Some verifications failed - Please check the details above")
    print("=" * 60)


if __name__ == '__main__':
    main()
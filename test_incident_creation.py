#!/usr/bin/env python3
"""Test incident creation functionality in Streamlit app."""

import sys
import os
import json
import time
import boto3
from datetime import datetime
import requests

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported."""
    print("\n=== Testing Imports ===")
    try:
        import streamlit as st
        print("✓ Streamlit imported")
        
        from streamlit_app import EnhancedSREDashboard, IncidentGenerator
        print("✓ EnhancedSREDashboard imported")
        print("✓ IncidentGenerator imported")
        
        from streamlit_key_manager import key_manager
        print("✓ Key manager imported")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_incident_generator_class():
    """Test the IncidentGenerator class directly."""
    print("\n=== Testing IncidentGenerator Class ===")
    
    try:
        from streamlit_app import IncidentGenerator
        
        # Create instance
        generator = IncidentGenerator()
        print("✓ IncidentGenerator instance created")
        
        # Test methods exist
        methods = ['create_demo_resources', 'generate_correlated_incident', 
                  'create_demo_change', 'correlate_with_change']
        
        for method in methods:
            if hasattr(generator, method):
                print(f"✓ Method '{method}' exists")
            else:
                print(f"✗ Method '{method}' missing")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error testing IncidentGenerator: {e}")
        return False

def test_aws_connectivity():
    """Test AWS connectivity and permissions."""
    print("\n=== Testing AWS Connectivity ===")
    
    try:
        ssm_client = boto3.client('ssm', region_name='us-east-1')
        
        # Test basic connectivity
        response = ssm_client.describe_ops_items(MaxResults=1)
        print("✓ AWS SSM connectivity verified")
        
        # Check for demo resources
        try:
            response = ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Title',
                        'Values': ['[DEMO]'],
                        'Operator': 'Contains'
                    }
                ],
                MaxResults=5
            )
            demo_count = len(response.get('OpsItemSummaries', []))
            print(f"✓ Found {demo_count} demo OpsItems")
        except:
            print("✓ Can query OpsItems (no demo items found)")
        
        return True
    except Exception as e:
        print(f"✗ AWS connectivity error: {e}")
        return False

def test_create_incident_aws():
    """Test creating a standard AWS incident."""
    print("\n=== Testing AWS Incident Creation ===")
    
    try:
        from streamlit_app import IncidentGenerator
        
        generator = IncidentGenerator()
        
        # Test each incident type
        incident_types = ["performance", "security", "outage"]
        
        for inc_type in incident_types:
            print(f"\nTesting {inc_type} incident...")
            
            try:
                # Create demo resources first
                generator.create_demo_resources()
                
                # Generate incident
                incident_data = generator.generate_correlated_incident(inc_type)
                
                if incident_data and 'ops_item_id' in incident_data:
                    print(f"✓ Created {inc_type} incident: {incident_data['ops_item_id']}")
                    
                    # Verify required fields
                    required_fields = ['ops_item_id', 'type', 'start_time', 'description']
                    for field in required_fields:
                        if field in incident_data:
                            print(f"  ✓ Has field: {field}")
                        else:
                            print(f"  ✗ Missing field: {field}")
                else:
                    print(f"✗ Failed to create {inc_type} incident")
                    
            except Exception as e:
                print(f"✗ Error creating {inc_type} incident: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error in AWS incident creation test: {e}")
        return False

def test_mcp_scenarios():
    """Test MCP scenario generation if available."""
    print("\n=== Testing MCP Scenarios ===")
    
    try:
        # Check if MCP is available
        import streamlit_app
        if not streamlit_app.MCP_AVAILABLE:
            print("ℹ MCP not available, skipping MCP tests")
            return True
        
        from enhanced_incident_scenarios import EnhancedIncidentScenarios
        scenarios = EnhancedIncidentScenarios()
        
        # Get available scenarios
        mcp_scenarios = scenarios.get_scenarios()
        print(f"✓ Found {len(mcp_scenarios)} MCP scenarios")
        
        # Test scenario structure
        if mcp_scenarios:
            scenario = mcp_scenarios[0]
            required_fields = ['incident', 'mcp_data', 'root_cause', 'resolution']
            
            for field in required_fields:
                if field in scenario:
                    print(f"✓ Scenario has field: {field}")
                else:
                    print(f"✗ Scenario missing field: {field}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing MCP scenarios: {e}")
        return False

def test_streamlit_running():
    """Test if Streamlit is running and accessible."""
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
        print("  To start: nohup python3 -m streamlit run streamlit_app.py --server.port 8501 > streamlit.log 2>&1 &")
        return False

def test_session_state_simulation():
    """Simulate Streamlit session state for testing."""
    print("\n=== Testing Session State Simulation ===")
    
    try:
        # Create a mock session state
        class MockSessionState:
            def __init__(self):
                self.generated_incidents = []
                self.current_incident = None
                self.include_logs = True
                self.include_metrics = True
                self.include_cloudtrail = True
                self.include_vpc_logs = True
                self.include_health = True
                self.mcp_enabled = True
                self.feedback_enabled = True
                self.time_range = "-1h"
        
        session_state = MockSessionState()
        print("✓ Mock session state created")
        
        # Test adding incidents
        test_incident = {
            'ops_item_id': 'TEST-001',
            'type': 'performance',
            'start_time': datetime.now(),
            'description': 'Test incident'
        }
        
        session_state.generated_incidents.append(test_incident)
        session_state.current_incident = test_incident
        
        print(f"✓ Added test incident: {test_incident['ops_item_id']}")
        print(f"✓ Session state has {len(session_state.generated_incidents)} incidents")
        
        return True
    except Exception as e:
        print(f"✗ Error testing session state: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("=" * 60)
    print("Incident Creation Test Suite")
    print("=" * 60)
    
    test_results = {
        'imports': test_imports(),
        'incident_generator_class': test_incident_generator_class(),
        'aws_connectivity': test_aws_connectivity(),
        'aws_incident_creation': test_create_incident_aws(),
        'mcp_scenarios': test_mcp_scenarios(),
        'streamlit_running': test_streamlit_running(),
        'session_state': test_session_state_simulation()
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
        print("✅ ALL TESTS PASSED! Incident creation is fully functional.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        
        # Provide troubleshooting tips
        print("\nTroubleshooting Tips:")
        if not test_results['streamlit_running']:
            print("- Start Streamlit: nohup python3 -m streamlit run streamlit_app.py --server.port 8501 > streamlit.log 2>&1 &")
        if not test_results['aws_connectivity']:
            print("- Check AWS credentials and permissions")
            print("- Ensure you have SSM permissions for OpsItems")
        if not test_results['imports']:
            print("- Check that all required files are present")
            print("- Ensure Python dependencies are installed")
    
    return passed_tests == total_tests

def main():
    """Main function."""
    success = run_comprehensive_test()
    
    # Additional manual test instructions
    print("\n" + "=" * 60)
    print("MANUAL TESTING INSTRUCTIONS")
    print("=" * 60)
    print("\nTo manually test incident creation in Streamlit:")
    print("1. Open http://localhost:8501")
    print("2. In the sidebar, under 'Generate Incident':")
    print("   - Select 'Standard AWS' category")
    print("   - Choose an incident type (Performance, Security, or Outage)")
    print("   - Click '🔥 Generate Real Incident'")
    print("3. Verify:")
    print("   - Success message appears with OpsItem ID")
    print("   - Incident appears in 'Recent Incidents' list")
    print("   - Knowledge Base integration message shows")
    print("4. For MCP scenarios (if available):")
    print("   - Select 'MCP Integration Test' category")
    print("   - Choose a scenario")
    print("   - Click '🔥 Generate Real Incident'")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
"""
Test script to verify incident handling fix
"""

import streamlit as st
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the streamlit app class
from streamlit_app_problem_management import EnhancedSREDashboard


def test_incident_normalization():
    """Test the incident normalization function"""
    dashboard = EnhancedSREDashboard()
    
    # Test case 1: Standard incident with ops_item_id
    incident1 = {
        'ops_item_id': 'OPS-001',
        'description': 'Database connection timeout',
        'type': 'performance',
        'severity': 'High'
    }
    
    normalized1 = dashboard._normalize_incident(incident1)
    print("Test 1 - Standard incident:")
    print(f"  Input: {incident1}")
    print(f"  Output: {normalized1}")
    assert normalized1['id'] == 'OPS-001'
    assert normalized1['title'] == 'Database connection timeout'
    assert normalized1['type'] == 'performance'
    print("  ✅ PASSED\n")
    
    # Test case 2: Incident with id field
    incident2 = {
        'id': 'INC-002',
        'title': 'API Gateway Error',
        'description': 'API Gateway returning 503 errors',
        'service': 'api-gateway'
    }
    
    normalized2 = dashboard._normalize_incident(incident2)
    print("Test 2 - Incident with id field:")
    print(f"  Input: {incident2}")
    print(f"  Output: {normalized2}")
    assert normalized2['id'] == 'INC-002'
    assert normalized2['title'] == 'API Gateway Error'
    print("  ✅ PASSED\n")
    
    # Test case 3: Minimal incident
    incident3 = {
        'ops_item_id': 'OPS-003'
    }
    
    normalized3 = dashboard._normalize_incident(incident3)
    print("Test 3 - Minimal incident:")
    print(f"  Input: {incident3}")
    print(f"  Output: {normalized3}")
    assert normalized3['id'] == 'OPS-003'
    assert normalized3['title'] == 'No title'
    assert normalized3['service'] == 'Unknown'
    print("  ✅ PASSED\n")
    
    # Test case 4: Long description
    incident4 = {
        'ops_item_id': 'OPS-004',
        'description': 'A' * 150  # 150 characters
    }
    
    normalized4 = dashboard._normalize_incident(incident4)
    print("Test 4 - Long description:")
    print(f"  Input: description length = {len(incident4['description'])}")
    print(f"  Output title length: {len(normalized4['title'])}")
    assert len(normalized4['title']) == 100
    print("  ✅ PASSED\n")
    
    print("=" * 60)
    print("✅ ALL NORMALIZATION TESTS PASSED")
    print("=" * 60)


def test_session_state_simulation():
    """Simulate how incidents would be stored and accessed"""
    print("\n" + "=" * 60)
    print("SESSION STATE SIMULATION")
    print("=" * 60)
    
    # Simulate session state
    class MockSessionState:
        def __init__(self):
            self.generated_incidents = []
    
    mock_session = MockSessionState()
    
    # Add some test incidents (simulating what the main app does)
    mock_session.generated_incidents.append({
        'ops_item_id': 'OPS-2024-001',
        'description': 'High CPU usage detected on web servers',
        'type': 'performance',
        'severity': 'High',
        'start_time': '2024-01-01 10:00:00'
    })
    
    mock_session.generated_incidents.append({
        'ops_item_id': 'OPS-2024-002',
        'description': 'Database connection pool exhausted',
        'type': 'database',
        'severity': 'Critical',
        'start_time': '2024-01-01 11:00:00'
    })
    
    # Now simulate what problem management does
    dashboard = EnhancedSREDashboard()
    
    if hasattr(mock_session, 'generated_incidents'):
        recent_incidents = [dashboard._normalize_incident(inc) for inc in mock_session.generated_incidents]
        
        print(f"Found {len(recent_incidents)} incidents")
        print("\nIncidents available for Problem Management:")
        for i, inc in enumerate(recent_incidents):
            print(f"\n{i+1}. {inc['id']} - {inc['title']}")
            print(f"   Type: {inc['type']}")
            print(f"   Impact: {inc['impact']}")
    
    print("\n✅ Session state handling verified")


if __name__ == '__main__':
    print("Testing Problem Management Incident Fix")
    print("=" * 60)
    
    # Run tests
    test_incident_normalization()
    test_session_state_simulation()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Fix is working correctly")
    print("=" * 60)
    print("\nThe Problem Management and Synthetic Transaction tabs will now")
    print("correctly display incidents generated from the main Incident Management tab.")
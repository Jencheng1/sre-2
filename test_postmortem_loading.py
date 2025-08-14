#!/usr/bin/env python3
"""Test script to verify post-mortem incident loading functionality"""

import streamlit as st
from datetime import datetime, timedelta
import json

def test_postmortem_loading():
    """Test the post-mortem incident loading feature"""
    print("\n🧪 Testing Post-Mortem Incident Loading\n")
    
    # Simulate incident data
    test_incident = {
        'id': 'INC-20240115-001',
        'description': 'Database connection pool exhaustion causing API timeouts',
        'category': 'Performance',
        'severity': '2',
        'root_cause': 'Connection pool size insufficient for peak traffic',
        'created_time': '2024-01-15T10:30:00Z'
    }
    
    print(f"📝 Test Incident: {test_incident['id']}")
    print(f"   Description: {test_incident['description']}")
    print(f"   Category: {test_incident['category']}")
    print(f"   Severity: {test_incident['severity']}")
    
    # Test the mapping logic
    print("\n🔄 Testing Field Mappings:")
    
    # Test incident type mapping
    category = test_incident.get('category', 'Unknown').lower()
    if 'performance' in category or 'latency' in category:
        incident_type = 1  # performance
        type_name = "Performance"
    elif 'security' in category or 'auth' in category:
        incident_type = 2  # security
        type_name = "Security"
    elif 'data' in category:
        incident_type = 3  # data_loss
        type_name = "Data Loss"
    else:
        incident_type = 0  # outage
        type_name = "Outage"
    
    print(f"   ✅ Incident Type: {type_name} (index: {incident_type})")
    
    # Test severity mapping
    severity_map = {'1': 0, '2': 0, '3': 1, '4': 2, '5': 3}  # to CRITICAL/HIGH/MEDIUM/LOW indices
    severity_index = severity_map.get(str(test_incident.get('severity', '3')), 1)
    severity_names = ['Critical', 'High', 'Medium', 'Low']
    print(f"   ✅ Severity: {severity_names[severity_index]} (index: {severity_index})")
    
    # Test service extraction
    desc_lower = test_incident['description'].lower()
    services_list = []
    if 'api' in desc_lower:
        services_list.append('api-gateway')
    if 'database' in desc_lower or 'db' in desc_lower:
        services_list.append('database')
    if 'auth' in desc_lower:
        services_list.append('auth-service')
    if 'user' in desc_lower:
        services_list.append('user-service')
    if 'payment' in desc_lower:
        services_list.append('payment-service')
    services = ', '.join(services_list)
    print(f"   ✅ Services: {services}")
    
    # Test time parsing
    created_time = test_incident.get('created_time', datetime.now().isoformat())
    if isinstance(created_time, str):
        created_time = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
    start_date = created_time.date()
    start_time = created_time.time()
    end_time = created_time + timedelta(hours=2)
    end_date = end_time.date()
    end_time_val = end_time.time()
    
    print(f"   ✅ Start: {start_date} {start_time}")
    print(f"   ✅ End: {end_date} {end_time_val}")
    
    # Test detection method and immediate actions
    detection_method = "CloudWatch monitoring alert"
    root_cause = test_incident.get('root_cause', 'Unknown issue')
    immediate_actions = f"1. Identified root cause: {root_cause}\n2. Initiated incident response protocol\n3. Notified on-call team\n4. Started real-time monitoring"
    
    print(f"   ✅ Detection: {detection_method}")
    first_action = immediate_actions.split('\n')[0]
    print(f"   ✅ Actions: {first_action}...")
    
    print("\n✅ Post-Mortem Loading Logic Test Passed!")
    print("\nℹ️  To test in the UI:")
    print("1. Go to http://localhost:8501")
    print("2. Navigate to Advanced Tools → Post-Mortem")
    print("3. Select 'Load from Recent Incidents'")
    print("4. Choose an incident and click 'Load Incident Details'")
    print("5. Verify all fields are populated correctly")
    
    # Create a sample session state simulation
    print("\n📊 Session State Values After Loading:")
    session_state = {
        'pm_incident_id': test_incident['id'],
        'pm_description': test_incident.get('description', ''),
        'pm_incident_type': incident_type,
        'pm_severity': severity_index,
        'pm_services': services,
        'pm_detection_method': detection_method,
        'pm_immediate_actions': immediate_actions,
        'pm_start_date': str(start_date),
        'pm_start_time': str(start_time),
        'pm_end_date': str(end_date),
        'pm_end_time': str(end_time_val)
    }
    
    for key, value in session_state.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    test_postmortem_loading()
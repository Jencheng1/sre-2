#!/usr/bin/env python3
"""Test the OpsItem creation fix"""

import os
import sys
import boto3

# Set environment
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Import the dashboard class
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing OpsItem creation fix...")

# Test 1: Direct SSM client test
print("\n1. Testing direct SSM client...")
try:
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    
    # Test creating an OpsItem
    response = ssm_client.create_ops_item(
        Title="[TEST] CPU Spike Fix Validation",
        Description="Testing the ssm_client fix for CPU spike demo",
        Source="Test-Script",
        Severity="4",  # Low severity for test
        Category="Performance"
    )
    
    ops_item_id = response['OpsItemId']
    print(f"✓ OpsItem created successfully: {ops_item_id}")
    
    # Close it immediately
    ssm_client.update_ops_item(
        OpsItemId=ops_item_id,
        Status='Resolved'
    )
    print("✓ OpsItem closed")
    
except Exception as e:
    print(f"✗ Direct SSM test failed: {e}")

# Test 2: Test the dashboard class
print("\n2. Testing EnhancedSREDashboard class...")
try:
    from streamlit_app import EnhancedSREDashboard
    
    dashboard = EnhancedSREDashboard()
    
    # Verify ssm_client exists
    if hasattr(dashboard, 'ssm_client'):
        print("✓ dashboard.ssm_client exists")
    else:
        print("✗ dashboard.ssm_client missing!")
        
    # Test the fixed method
    result = dashboard._create_cpu_spike_ops_item(
        instance_id="i-test123",
        instance_name="Test-Instance",
        cpu_percent=85
    )
    
    if result:
        print(f"✓ _create_cpu_spike_ops_item succeeded: {result.get('OpsItemId', 'Unknown')}")
        
        # Clean up
        if 'OpsItemId' in result:
            dashboard.ssm_client.update_ops_item(
                OpsItemId=result['OpsItemId'],
                Status='Resolved'
            )
            print("✓ Test OpsItem cleaned up")
    else:
        print("✗ _create_cpu_spike_ops_item returned None")
        
except Exception as e:
    print(f"✗ Dashboard class test failed: {e}")

print("\n✅ Fix verification complete!")
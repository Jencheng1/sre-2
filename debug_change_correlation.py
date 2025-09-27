#!/usr/bin/env python3
"""
Debug why change records aren't being correlated
"""

import boto3
from datetime import datetime, timedelta

def check_change_records():
    """Check if change records exist and are queryable"""
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    
    print("🔍 Checking Change Records in SSM")
    print("=" * 60)
    
    # Look for changes in different ways
    filters_to_try = [
        {
            'name': 'With [CHANGE] prefix',
            'filters': [
                {
                    'Key': 'Title',
                    'Values': ['[CHANGE]'],
                    'Operator': 'Contains'
                }
            ]
        },
        {
            'name': 'With Deploy keyword',
            'filters': [
                {
                    'Key': 'Title',
                    'Values': ['Deploy', 'deployment'],
                    'Operator': 'Contains'
                }
            ]
        },
        {
            'name': 'With v2.1.0',
            'filters': [
                {
                    'Key': 'Title',
                    'Values': ['v2.1.0'],
                    'Operator': 'Contains'
                }
            ]
        },
        {
            'name': 'All recent OpsItems',
            'filters': [
                {
                    'Key': 'CreatedTime',
                    'Values': [(datetime.now() - timedelta(hours=24)).isoformat()],
                    'Operator': 'GreaterThan'
                }
            ]
        }
    ]
    
    for filter_set in filters_to_try:
        print(f"\n📋 Searching {filter_set['name']}:")
        try:
            response = ssm_client.describe_ops_items(
                OpsItemFilters=filter_set['filters'],
                MaxResults=10
            )
            
            items = response.get('OpsItemSummaries', [])
            print(f"   Found {len(items)} items")
            
            for item in items[:5]:  # Show first 5
                title = item.get('Title', '')
                created = item.get('CreatedTime', '')
                print(f"   - {item['OpsItemId']}: {title[:60]}...")
                if created:
                    print(f"     Created: {created}")
                    
        except Exception as e:
            print(f"   Error: {e}")
    
    # Test the exact query the lambda uses
    print("\n🔧 Testing Lambda Query Logic:")
    start_time = datetime.now() - timedelta(hours=24)
    
    try:
        response = ssm_client.describe_ops_items(
            OpsItemFilters=[
                {
                    'Key': 'Title',
                    'Values': ['[CHANGE]', 'Deploy', 'deployment', 'release', 'v2.1.0'],
                    'Operator': 'Contains'
                },
                {
                    'Key': 'CreatedTime',
                    'Values': [start_time.isoformat()],
                    'Operator': 'GreaterThan'
                }
            ],
            MaxResults=50
        )
        
        changes = response.get('OpsItemSummaries', [])
        print(f"   Lambda query would find: {len(changes)} changes")
        
        if changes:
            print("\n   Recent changes that should be correlated:")
            for change in changes[:3]:
                print(f"   - {change['OpsItemId']}: {change.get('Title', '')[:80]}")
                
    except Exception as e:
        print(f"   Lambda query error: {e}")

def test_lambda_locally():
    """Test the get_change_records function logic"""
    print("\n\n🧪 Testing Lambda Change Detection Logic")
    print("=" * 60)
    
    # Simulate the lambda's logic
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    incident_time = datetime.now()
    start_time = incident_time - timedelta(hours=24)
    
    # Try different filter combinations
    filter_tests = [
        {
            'name': 'Single filter with CHANGE',
            'filters': [
                {
                    'Key': 'Title',
                    'Values': ['CHANGE'],
                    'Operator': 'Contains'
                }
            ]
        },
        {
            'name': 'Time filter only',
            'filters': [
                {
                    'Key': 'CreatedTime',
                    'Values': [start_time.isoformat()],
                    'Operator': 'GreaterThan'
                }
            ]
        },
        {
            'name': 'Source filter',
            'filters': [
                {
                    'Key': 'Source',
                    'Values': ['ChangeManagement'],
                    'Operator': 'Equal'
                }
            ]
        }
    ]
    
    for test in filter_tests:
        print(f"\n🔍 {test['name']}:")
        try:
            response = ssm_client.describe_ops_items(
                OpsItemFilters=test['filters'],
                MaxResults=10
            )
            
            items = response.get('OpsItemSummaries', [])
            print(f"   Results: {len(items)} items")
            
            if items:
                for item in items[:3]:
                    print(f"   - {item['OpsItemId']}: {item.get('Title', '')[:60]}")
                    print(f"     Source: {item.get('Source', 'unknown')}")
                    
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    check_change_records()
    test_lambda_locally()
    
    print("\n\n💡 Recommendations:")
    print("1. Ensure change records have '[CHANGE]' in title")
    print("2. Check that CreatedTime filter is working correctly")
    print("3. Verify SSM permissions for Lambda role")
    print("4. Consider using Source='ChangeManagement' as primary filter")
#!/usr/bin/env python3
"""
Test OpsItem auto-indexing functionality.
"""

import boto3
import json
import time
from datetime import datetime

def create_test_opsitem():
    """Create a test OpsItem."""
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    
    try:
        # Create OpsItem
        response = ssm_client.create_ops_item(
            Title="Test KB Auto-indexing: High CPU Usage on Production Server",
            Description="""
Production web server experiencing high CPU usage causing performance degradation.

Symptoms:
- CPU utilization consistently above 90%
- Response times increased from 200ms to 2000ms
- Memory usage normal at 60%
- No unusual network traffic

Initial Investigation:
- Found multiple stuck processes
- Application logs show repeated connection timeouts
- Database queries are returning normally
""",
            Source="SRE-Test",
            Severity="2",
            OperationalData={
                "IncidentType": {"Value": "performance", "Type": "String"},
                "AffectedService": {"Value": "web-frontend", "Type": "String"},
                "Environment": {"Value": "production", "Type": "String"},
                "StartTime": {"Value": datetime.utcnow().isoformat(), "Type": "String"}
            }
        )
        
        ops_item_id = response['OpsItemId']
        print(f"✓ Created OpsItem: {ops_item_id}")
        return ops_item_id
        
    except Exception as e:
        print(f"✗ Failed to create OpsItem: {str(e)}")
        return None

def check_kb_indexing(ops_item_id, wait_time=10):
    """Check if OpsItem was indexed to KB."""
    print(f"\nWaiting {wait_time} seconds for auto-indexing...")
    time.sleep(wait_time)
    
    # Search for the OpsItem in KB
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'search_incidents',
                'query': 'High CPU Usage Production Server',
                'k': 5
            })
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            results = body.get('results', [])
            
            # Check if our OpsItem is in the results
            for doc in results:
                if f'OPS-{ops_item_id}' in doc.get('document_id', ''):
                    print(f"✓ OpsItem {ops_item_id} found in knowledge base!")
                    print(f"  Document ID: {doc['document_id']}")
                    print(f"  Title: {doc['title']}")
                    print(f"  Score: {doc.get('score', 0):.3f}")
                    return True
                    
            print(f"✗ OpsItem {ops_item_id} not found in knowledge base yet")
            
            # Show what was found
            if results:
                print("\nFound these documents instead:")
                for doc in results[:3]:
                    print(f"  - {doc['title']} ({doc['document_id']})")
        else:
            print(f"✗ Search failed: {result}")
            
    except Exception as e:
        print(f"✗ Error searching KB: {str(e)}")
        
    return False

def main():
    print("OpsItem Auto-indexing Test")
    print("=" * 60)
    
    # Create test OpsItem
    ops_item_id = create_test_opsitem()
    if not ops_item_id:
        return
    
    # Check if it gets indexed
    # Note: Auto-indexing via CloudWatch Events may take a few seconds
    indexed = check_kb_indexing(ops_item_id, wait_time=5)
    
    if not indexed:
        print("\nTrying manual indexing for comparison...")
        
        # Get the OpsItem details
        ssm_client = boto3.client('ssm', region_name='us-east-1')
        response = ssm_client.get_ops_item(OpsItemId=ops_item_id)
        ops_item = response['OpsItem']
        
        # Convert datetime objects to strings
        ops_item_serializable = {}
        for key, value in ops_item.items():
            if isinstance(value, datetime):
                ops_item_serializable[key] = value.isoformat()
            else:
                ops_item_serializable[key] = value
        
        # Manually index it
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'index_opsitem',
                'ops_item': ops_item_serializable
            })
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            print("✓ Manual indexing successful")
            
            # Check again
            if check_kb_indexing(ops_item_id, wait_time=2):
                print("\n✓ OpsItem successfully indexed and searchable!")
        else:
            print(f"✗ Manual indexing failed: {result}")
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    main()
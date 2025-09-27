#!/usr/bin/env python3
"""
Test supervisor Lambda response format
"""

import boto3
import json
from datetime import datetime, timedelta

# Initialize clients
ssm_client = boto3.client('ssm', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

# Create a test OpsItem
print("Creating test OpsItem...")
response = ssm_client.create_ops_item(
    Title="Test CPU Spike - Debug Response",
    Description="Testing supervisor Lambda response format",
    Source="Test Script",
    Severity="2"
)
ops_item_id = response['OpsItemId']
print(f"Created OpsItem: {ops_item_id}")

# Build payload
payload = {
    'action': 'analyze',
    'incident_description': "High CPU spike detected on EC2 instance. CPU utilization at 95%.",
    'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
    'end_time': datetime.utcnow().isoformat(),
    'service': 'sre-demo-app',
    'environment': 'demo',
    'additional_context': {
        'ops_item_id': ops_item_id,
        'severity': '2',
        'incident_type': 'CPU Spike'
    }
}

print("\nInvoking supervisor Lambda...")
print(f"Payload: {json.dumps(payload, indent=2)}")

# Invoke Lambda
response = lambda_client.invoke(
    FunctionName='sre-supervisor-lambda',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

# Parse response
result = json.loads(response['Payload'].read())
print("\n" + "="*60)
print("SUPERVISOR LAMBDA RESPONSE:")
print("="*60)
print(f"Status Code: {result.get('statusCode')}")
print(f"\nFull Response Structure:")
print(json.dumps(result, indent=2))

if 'body' in result:
    print("\n" + "="*60)
    print("BODY CONTENT:")
    print("="*60)
    body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
    print(json.dumps(body, indent=2))
    
    print("\n" + "="*60)
    print("AVAILABLE KEYS IN BODY:")
    print("="*60)
    for key in body.keys():
        print(f"- {key}")

# Cleanup
print("\nCleaning up...")
ssm_client.update_ops_item(OpsItemId=ops_item_id, Status='Resolved')
print("Done!")
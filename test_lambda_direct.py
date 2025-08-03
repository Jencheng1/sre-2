#!/usr/bin/env python3
"""
Test Lambda directly to check response format
"""

import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

# Simple test payload
payload = {
    "action": "analyze",
    "incident_description": "Test incident for MCP integration",
    "enable_mcp": True,
    "enable_kb": True,
    "service": "test-service",
    "environment": "test"
}

print("Testing Lambda function...")
try:
    response = lambda_client.invoke(
        FunctionName='sre-supervisor-lambda-mcp',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    print(f"Status Code: {response['StatusCode']}")
    print(f"Response Metadata: {response['ResponseMetadata']}")
    
    # Read payload
    payload_data = response['Payload'].read()
    print(f"\nRaw Payload: {payload_data[:200]}...")
    
    # Try to parse as JSON
    try:
        result = json.loads(payload_data)
        print(f"\nParsed Result Type: {type(result)}")
        print(f"Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Print full result for debugging
        print(f"\nFull Result:")
        print(json.dumps(result, indent=2)[:500] + "...")
    except json.JSONDecodeError as e:
        print(f"\nFailed to parse as JSON: {e}")
        
except Exception as e:
    print(f"Error invoking Lambda: {e}")
    import traceback
    traceback.print_exc()
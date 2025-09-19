#!/usr/bin/env python3
"""
Check actual AI output format.
"""

import json
import boto3

lambda_client = boto3.client('lambda', region_name='us-east-1')

payload = {
    'action': 'analyze',
    'incident_description': 'Application experiencing severe performance degradation with high CPU usage',
    'service': 'demo-app',
    'environment': 'production'
}

response = lambda_client.invoke(
    FunctionName='sre-supervisor-lambda',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
body = json.loads(result['body'])
analysis = body.get('root_cause_analysis', '')

print("Full Analysis Output:")
print("="*60)
print(analysis)
print("="*60)
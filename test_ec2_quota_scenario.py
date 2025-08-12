#!/usr/bin/env python3
"""
Direct test of EC2 quota scenario
"""

import json
import boto3

# Test the EC2 quota scenario
lambda_client = boto3.client('lambda', region_name='us-east-1')

# EC2 Quota Test Payload
payload = {
    'incident_type': 'quota',
    'incident_id': 'TEST-EC2-QUOTA',
    'description': 'EC2 instance launch failed - quota exceeded for m5.large',
    'severity': 'high',
    'affected_resources': ['m5.large', 'us-west-2'],
    'error_details': {
        'error_code': 'Client.InstanceLimitExceeded',
        'error_message': 'You have requested more instances (25) than your current instance limit of 20',
        'quota_id': 'L-1216C47A',
        'current_limit': 20,
        'requested': 25,
        'instance_type': 'm5.large'
    }
}

print("Testing EC2 Quota Exceeded Scenario...")
print("="*50)

# Invoke the supervisor Lambda
response = lambda_client.invoke(
    FunctionName='sre-supervisor-lambda-mcp',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

# Parse response
result = json.loads(response['Payload'].read())
if result.get('statusCode') == 200:
    analysis = json.loads(result['body'])
    
    print("\n✅ Analysis Complete!")
    print(f"\nRoot Cause: {analysis.get('root_cause', 'Not found')}")
    print(f"\nSeverity: {analysis.get('severity', 'Not determined')}")
    
    if 'recommendations' in analysis:
        print("\nRecommendations:")
        for i, rec in enumerate(analysis['recommendations'][:3], 1):
            print(f"  {i}. {rec}")
    
    if 'mcp_correlations' in analysis:
        print("\nMCP Correlations:")
        for service, data in analysis['mcp_correlations'].items():
            if data:
                print(f"  • {service}: Data found")
else:
    print("❌ Analysis failed")
    print(result)

print("\n" + "="*50)
print("To test in Streamlit UI:")
print("1. Go to http://localhost:8501")
print("2. Click '🚨 Incident Management' tab")
print("3. Look for incident generation options")
print("4. The generated incidents will appear in 'Recent Incidents'")
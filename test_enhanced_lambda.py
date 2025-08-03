#!/usr/bin/env python3
"""Test the enhanced supervisor Lambda function."""

import boto3
import json
from datetime import datetime

def test_lambda_analysis():
    """Test different incident types with enhanced Lambda."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    test_cases = [
        {
            'name': 'Performance Incident',
            'incident_description': 'Application experiencing performance degradation with slow response times',
            'expected_type': 'performance'
        },
        {
            'name': 'Security Incident', 
            'incident_description': 'Unauthorized access attempts detected, security group modified',
            'expected_type': 'security'
        },
        {
            'name': 'Outage Incident',
            'incident_description': 'Service is down and unavailable to users',
            'expected_type': 'outage'
        }
    ]
    
    for test_case in test_cases:
        print("\n" + "="*60)
        print(f"Testing: {test_case['name']}")
        print(f"Description: {test_case['incident_description']}")
        print('='*60)
        
        payload = {
            'action': 'analyze',
            'incident_description': test_case['incident_description'],
            'service': 'sre-demo-app',
            'environment': 'demo',
            'additional_context': {
                'test_run': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                
                print(f"\nIncident Type Detected: {body.get('incident_type')}")
                print(f"Expected Type: {test_case['expected_type']}")
                print(f"Match: {'YES' if body.get('incident_type') == test_case['expected_type'] else 'NO'}")
                
                print("\nAnalysis:")
                print(body.get('analysis', 'No analysis provided'))
                
                # Check monitoring data
                monitoring = body.get('monitoring_data', {})
                metrics = monitoring.get('metrics', {})
                logs = monitoring.get('logs', {})
                
                print(f"\nMonitoring Data:")
                print(f"- Metrics collected: {len(metrics)}")
                print(f"- Error count: {logs.get('error_count', 0)}")
                print(f"- Warning count: {logs.get('warning_count', 0)}")
                
            else:
                print(f"Error: Status code {result.get('statusCode')}")
                print(f"Body: {result.get('body')}")
                
        except Exception as e:
            print(f"Error invoking Lambda: {str(e)}")
            
        print("\n")

if __name__ == "__main__":
    print("Testing Enhanced Supervisor Lambda Function")
    print("=" * 60)
    test_lambda_analysis()
    print("\nTest complete!")
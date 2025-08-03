#!/usr/bin/env python3
"""Test the fixed security incident analysis."""

import boto3
import json
from datetime import datetime

def test_security_incidents():
    """Test various security incident scenarios."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    test_cases = [
        {
            'name': 'Unauthorized Access',
            'description': 'Multiple unauthorized access attempts detected from suspicious IP addresses'
        },
        {
            'name': 'Security Group Change', 
            'description': 'Security group rules were modified allowing unrestricted access'
        },
        {
            'name': 'API Failures',
            'description': 'Multiple API failures detected indicating potential security scan'
        },
        {
            'name': 'Generic Security',
            'description': 'Security incident detected with unusual activity patterns'
        }
    ]
    
    for test_case in test_cases:
        print("\n" + "="*60)
        print(f"Testing: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print("="*60)
        
        payload = {
            'action': 'analyze',
            'incident_description': test_case['description'],
            'service': 'sre-demo-app',
            'environment': 'demo'
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
                
                print(f"\nIncident Type: {body.get('incident_type')}")
                print("\nAnalysis:")
                analysis_text = body.get('analysis', '')
                
                # Extract key parts from analysis
                lines = analysis_text.split('\n')
                in_root_cause = False
                in_evidence = False
                in_recommendations = False
                
                for line in lines:
                    if '### Identified Root Cause' in line:
                        in_root_cause = True
                        in_evidence = False
                        in_recommendations = False
                    elif '### Evidence' in line:
                        in_root_cause = False
                        in_evidence = True
                        in_recommendations = False
                    elif '### Recommendations' in line or '#### Immediate Actions' in line:
                        in_root_cause = False
                        in_evidence = False
                        in_recommendations = True
                    elif '###' in line or '##' in line:
                        in_root_cause = False
                        in_evidence = False
                        in_recommendations = False
                        
                    if in_root_cause and line.strip() and '**' in line:
                        print(f"Root Cause: {line.strip()}")
                    elif in_evidence and line.strip().startswith('-'):
                        print(f"Evidence: {line.strip()}")
                    elif in_recommendations and line.strip() and not line.strip().startswith('#'):
                        print(f"Recommendation: {line.strip()}")
                        
            else:
                print(f"Error: {result}")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Testing Security Incident Analysis Improvements")
    print("=" * 60)
    test_security_incidents()
    print("\n\nTest complete!")
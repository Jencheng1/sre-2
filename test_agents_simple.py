#!/usr/bin/env python3
"""Simple test script to verify agent Lambda functions are working with real AWS APIs."""

import boto3
import json
import sys

def test_agent_lambda(function_name, action, additional_params=None):
    """Test a specific agent Lambda function."""
    print(f"\n{'='*60}")
    print(f"Testing {function_name} with action: {action}")
    print('='*60)
    
    try:
        lambda_client = boto3.client('lambda')
        
        # Prepare payload
        payload = {'action': action}
        if additional_params:
            payload.update(additional_params)
        
        # Invoke Lambda function
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Read response
        result = json.loads(response['Payload'].read())
        print(f"Status Code: {result.get('statusCode', 'N/A')}")
        
        if 'body' in result:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            print(f"Response Keys: {list(body.keys())}")
            
            # Check for errors
            if 'error' in body:
                print(f"Error: {body['error']}")
                return False
            else:
                print("✓ Success - No errors found")
                
                # Print summary of results
                for key, value in body.items():
                    if isinstance(value, list):
                        print(f"  - {key}: {len(value)} items")
                    elif isinstance(value, dict) and 'analysis' in key:
                        print(f"  - {key}: Analysis completed")
                    else:
                        print(f"  - {key}: {type(value).__name__}")
                return True
        else:
            print("Error: No body in response")
            return False
            
    except Exception as e:
        print(f"Error testing {function_name}: {str(e)}")
        return False

def main():
    """Run tests for all agent Lambda functions."""
    print("Testing SRE Agent Lambda Functions with Real AWS APIs")
    
    tests = [
        # CloudTrail Agent
        {
            'function': 'sre-cloudtrail-agent-lambda',
            'action': 'get_api_errors',
            'params': {'max_results': 10}
        },
        
        # VPC Flow Logs Agent
        {
            'function': 'sre-vpc-flow-logs-agent-lambda',
            'action': 'get_flow_log_issues',
            'params': {'timeframe_hours': 1}
        },
        
        # Trusted Advisor Agent
        {
            'function': 'sre-trusted-advisor-agent-lambda',
            'action': 'get_service_quotas',
            'params': {'max_results': 10}
        },
        
        # Personal Health Agent
        {
            'function': 'sre-personal-health-agent-lambda',
            'action': 'get_maintenance_events',
            'params': {'max_results': 10}
        }
    ]
    
    results = []
    for test in tests:
        success = test_agent_lambda(
            test['function'],
            test['action'],
            test.get('params')
        )
        results.append((test['function'], success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for function, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{function}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All agents are working with real AWS APIs!")
        return 0
    else:
        print("\n❌ Some agents failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
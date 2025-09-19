#!/usr/bin/env python3
"""
Test AI-powered root cause analysis in supervisor lambda.
"""

import json
import boto3
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

lambda_client = boto3.client('lambda', region_name='us-east-1')

def test_ai_analysis():
    """Test the AI-powered root cause analysis."""
    
    print(f"\n{Fore.CYAN}Testing AI-Powered Root Cause Analysis{Style.RESET_ALL}\n")
    
    test_incidents = [
        {
            'name': 'Performance Degradation',
            'description': 'Application experiencing severe performance degradation. Response times have increased from 200ms to 5 seconds. Users are reporting timeouts and slow page loads.',
            'expected_in_analysis': ['performance', 'response time', 'mitigation', 'recommendations']
        },
        {
            'name': 'Security Incident',
            'description': 'Multiple failed authentication attempts detected from suspicious IP addresses. Potential brute force attack on admin panel.',
            'expected_in_analysis': ['security', 'authentication', 'unauthorized', 'recommendations']
        },
        {
            'name': 'Database Outage',
            'description': 'Complete database outage. RDS instance is not responding. All queries timing out. Application cannot connect to database.',
            'expected_in_analysis': ['database', 'outage', 'connection', 'availability']
        }
    ]
    
    for test in test_incidents:
        print(f"\n{Fore.BLUE}Testing: {test['name']}{Style.RESET_ALL}")
        print(f"Description: {test['description'][:100]}...")
        
        try:
            payload = {
                'action': 'analyze',
                'incident_description': test['description'],
                'service': 'demo-app',
                'environment': 'production',
                'enable_kb': True,
                'mask_ips': True
            }
            
            response = lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse response
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                analysis = body.get('root_cause_analysis', '')
                
                # Check if AI analysis sections are present
                ai_sections = [
                    '## Root Cause Analysis',
                    '### Identified Root Cause',
                    '### Impact Assessment',
                    '### Immediate Mitigation Steps',
                    '### Long-term Recommendations'
                ]
                
                sections_found = sum(1 for section in ai_sections if section in analysis)
                
                # Check for expected keywords
                keywords_found = sum(1 for keyword in test['expected_in_analysis'] 
                                   if keyword.lower() in analysis.lower())
                
                if sections_found >= 4 and keywords_found >= 2:
                    print(f"{Fore.GREEN}✓ AI Analysis Generated Successfully{Style.RESET_ALL}")
                    print(f"  - Found {sections_found}/5 AI sections")
                    print(f"  - Found {keywords_found}/{len(test['expected_in_analysis'])} expected keywords")
                    
                    # Show preview of root cause
                    lines = analysis.split('\n')
                    for i, line in enumerate(lines):
                        if '**' in line and 'Root Cause' not in line:
                            print(f"  - Root Cause: {Fore.YELLOW}{line.strip('*').strip()}{Style.RESET_ALL}")
                            break
                else:
                    print(f"{Fore.RED}✗ AI Analysis Not Detected{Style.RESET_ALL}")
                    print(f"  - Only found {sections_found}/5 AI sections")
                    print(f"  - Analysis preview: {analysis[:200]}...")
                    
                # Show metrics summary
                metrics = body.get('metrics_summary', {})
                if metrics:
                    print(f"\n  {Fore.CYAN}Metrics Summary:{Style.RESET_ALL}")
                    for metric, values in metrics.items():
                        latest = values.get('latest_value', 0)
                        max_val = values.get('max_value', 0)
                        if latest > 0 or max_val > 0:
                            print(f"    - {metric}: Latest={latest:.1f}, Max={max_val:.1f}")
                            
            else:
                print(f"{Fore.RED}✗ Lambda returned error status: {result.get('statusCode')}{Style.RESET_ALL}")
                error_body = json.loads(result.get('body', '{}'))
                print(f"  - Error: {error_body.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"{Fore.RED}✗ Test failed with exception: {str(e)}{Style.RESET_ALL}")
            
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Test Complete - AI Root Cause Analysis{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    test_ai_analysis()
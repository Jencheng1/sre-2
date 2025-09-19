#!/usr/bin/env python3
"""
Test that incident root cause analysis is displayed correctly in Streamlit.
"""

import json
import boto3
import time
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name='us-east-1')
ssm_client = boto3.client('ssm', region_name='us-east-1')

def test_incident_display():
    """Test that root cause analysis is properly displayed."""
    
    print(f"\n{Fore.CYAN}Testing Incident Root Cause Display Fix{Style.RESET_ALL}\n")
    
    # Step 1: Create a test incident
    print(f"{Fore.BLUE}Step 1: Creating test OpsItem...{Style.RESET_ALL}")
    
    try:
        response = ssm_client.create_ops_item(
            Title='Test Incident - Database Performance Degradation',
            Description='Database queries taking 10x longer than normal. Users experiencing timeouts.',
            Source='test-display-fix',
            Severity='2',
            Tags=[
                {'Key': 'test', 'Value': 'display-fix'},
                {'Key': 'type', 'Value': 'performance'}
            ]
        )
        
        ops_item_id = response['OpsItemId']
        print(f"{Fore.GREEN}✓ Created OpsItem: {ops_item_id}{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to create OpsItem: {e}{Style.RESET_ALL}")
        return
    
    # Step 2: Analyze the incident
    print(f"\n{Fore.BLUE}Step 2: Analyzing incident...{Style.RESET_ALL}")
    
    try:
        payload = {
            'action': 'analyze',
            'incident_description': 'Database queries taking 10x longer than normal. Users experiencing timeouts.',
            'service': 'database-service',
            'environment': 'production',
            'enable_kb': True
        }
        
        response = lambda_client.invoke(
            FunctionName='sre-supervisor-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            root_cause_analysis = body.get('root_cause_analysis', '')
            
            print(f"{Fore.GREEN}✓ Analysis completed successfully{Style.RESET_ALL}")
            
            # Check if AI analysis was generated
            if len(root_cause_analysis) > 100:
                print(f"{Fore.GREEN}✓ AI analysis generated ({len(root_cause_analysis)} characters){Style.RESET_ALL}")
                
                # Show preview of root cause
                lines = root_cause_analysis.split('\n')
                for line in lines[:10]:  # Show first 10 lines
                    if 'root cause' in line.lower() and len(line) > 20:
                        print(f"\n{Fore.YELLOW}Root Cause Preview:{Style.RESET_ALL}")
                        print(f"  {line.strip()}")
                        break
            else:
                print(f"{Fore.RED}✗ Analysis too short or missing{Style.RESET_ALL}")
                
        else:
            print(f"{Fore.RED}✗ Analysis failed: {result['statusCode']}{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}✗ Analysis error: {e}{Style.RESET_ALL}")
    
    # Step 3: Instructions for manual verification
    print(f"\n{Fore.BLUE}Step 3: Manual Verification{Style.RESET_ALL}")
    print(f"\nTo verify the fix in Streamlit:")
    print(f"1. Go to http://localhost:8501")
    print(f"2. Navigate to the Incident Management tab")
    print(f"3. Look for OpsItem: {ops_item_id}")
    print(f"4. Click 'Analyze' on the incident")
    print(f"5. Verify that the root cause is displayed (not stuck at 'Analyzing...')")
    print(f"\n{Fore.YELLOW}Expected: The root cause field should show the actual analysis result{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Not: 'Analyzing...' or 'Analysis in progress...'{Style.RESET_ALL}")
    
    # Cleanup
    print(f"\n{Fore.BLUE}Cleanup: Resolving test OpsItem...{Style.RESET_ALL}")
    try:
        ssm_client.update_ops_item(
            OpsItemId=ops_item_id,
            Status='Resolved'
        )
        print(f"{Fore.GREEN}✓ Test OpsItem resolved{Style.RESET_ALL}")
    except:
        pass
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Test Complete - Check Streamlit UI for verification{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    test_incident_display()
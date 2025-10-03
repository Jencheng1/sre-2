#!/usr/bin/env python3
"""
Test the automatic AI analysis flow triggered by EventBridge.
This script creates an OpsItem and monitors the automatic analysis.
"""

import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize AWS clients
ssm = boto3.client('ssm', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
logs = boto3.client('logs', region_name='us-east-1')

def create_test_opsitem():
    """Create a test OpsItem to trigger automatic analysis."""
    print("Creating test OpsItem to trigger automatic AI analysis...")
    
    # Create OpsItem
    response = ssm.create_ops_item(
        Title="Test: High CPU Utilization Causing Performance Degradation",
        Description="""
        Production application experiencing severe performance degradation.
        Multiple users reporting slow response times and timeouts.
        CPU utilization has been consistently above 90% for the past hour.
        Memory usage is also elevated. Database connection pool exhausted.
        Error rate increased by 300% compared to baseline.
        """,
        Priority=1,
        Severity="1",
        Category="Performance",
        Source="AutomaticAnalysisTest",
        OperationalData={
            '/aws/application': {
                'Value': json.dumps({
                    'name': 'sre-demo-app',
                    'environment': 'production',
                    'version': '2.1.0'
                }),
                'Type': 'SearchableString'
            },
            '/aws/metrics': {
                'Value': json.dumps({
                    'cpu_utilization': 92.5,
                    'memory_utilization': 87.3,
                    'error_rate': 15.2,
                    'latency_p99': 2500
                }),
                'Type': 'SearchableString'
            }
        }
    )
    
    ops_item_id = response['OpsItemId']
    print(f"Created OpsItem: {ops_item_id}")
    return ops_item_id

def wait_for_analysis(ops_item_id, timeout=300):
    """Wait for automatic analysis to complete."""
    print(f"\nWaiting for automatic AI analysis to complete...")
    print("This may take 2-3 minutes as EventBridge triggers the analysis flow...")
    
    start_time = time.time()
    analysis_found = False
    
    while time.time() - start_time < timeout:
        try:
            # Get OpsItem details
            response = ssm.get_ops_item(OpsItemId=ops_item_id)
            ops_item = response['OpsItem']
            
            # Check for AI analysis in operational data
            operational_data = ops_item.get('OperationalData', {})
            
            if '/aws/ai-analysis' in operational_data:
                print("\n✅ AI Analysis completed!")
                analysis_found = True
                
                # Parse and display analysis
                ai_analysis = json.loads(operational_data['/aws/ai-analysis']['Value'])
                
                print("\n" + "="*80)
                print("AI ANALYSIS RESULTS")
                print("="*80)
                
                print(f"\nTimestamp: {ai_analysis.get('timestamp', 'N/A')}")
                print(f"\nRoot Cause: {ai_analysis.get('root_cause', 'N/A')}")
                
                print("\nRecommendations:")
                for i, rec in enumerate(ai_analysis.get('recommendations', []), 1):
                    print(f"  {i}. {rec}")
                
                print(f"\nSummary: {ai_analysis.get('summary', 'N/A')}")
                
                # Check for agent analyses
                if '/aws/agent-analyses' in operational_data:
                    agent_data = json.loads(operational_data['/aws/agent-analyses']['Value'])
                    print(f"\nAgent Analyses: {len(agent_data)} agents invoked")
                    for agent, result in agent_data.items():
                        status = "✓" if result.get('success') else "✗"
                        print(f"  {status} {agent}: {result.get('description', 'N/A')}")
                
                break
            else:
                # Show progress
                elapsed = int(time.time() - start_time)
                print(f"\rAnalysis in progress... ({elapsed}s elapsed)", end='', flush=True)
                time.sleep(5)
                
        except Exception as e:
            print(f"\nError checking OpsItem: {str(e)}")
            time.sleep(5)
    
    if not analysis_found:
        print(f"\n\n❌ Timeout waiting for analysis after {timeout} seconds")
        print("The automatic analysis may still be in progress.")
        
    return analysis_found

def check_knowledge_base(ops_item_id):
    """Check if the incident was indexed to knowledge base."""
    print("\n\nChecking Knowledge Base indexing...")
    
    try:
        # Invoke KB Lambda to search
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'search',
                'query': f'opsitem-{ops_item_id}',
                'k': 1
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            if body.get('results'):
                print("✅ OpsItem successfully indexed to Knowledge Base")
                print(f"   Document ID: {body['results'][0].get('document_id', 'N/A')}")
            else:
                print("❌ OpsItem not found in Knowledge Base yet")
        
    except Exception as e:
        print(f"Error checking Knowledge Base: {str(e)}")

def generate_test_metrics():
    """Generate test metrics in CloudWatch."""
    print("\nGenerating test metrics in CloudWatch...")
    
    namespace = 'SREDemo/Application'
    
    # Put high CPU metric
    cloudwatch.put_metric_data(
        Namespace=namespace,
        MetricData=[
            {
                'MetricName': 'CPUUtilization',
                'Value': 92.5,
                'Unit': 'Percent',
                'Dimensions': [
                    {'Name': 'ServiceName', 'Value': 'sre-demo-app'}
                ]
            },
            {
                'MetricName': 'MemoryUtilization',
                'Value': 87.3,
                'Unit': 'Percent',
                'Dimensions': [
                    {'Name': 'ServiceName', 'Value': 'sre-demo-app'}
                ]
            },
            {
                'MetricName': 'ErrorRate',
                'Value': 15.2,
                'Unit': 'Percent',
                'Dimensions': [
                    {'Name': 'ServiceName', 'Value': 'sre-demo-app'}
                ]
            }
        ]
    )
    
    print("✅ Test metrics generated")

def main():
    """Main test function."""
    print("="*80)
    print("AUTOMATIC AI ANALYSIS FLOW TEST")
    print("="*80)
    print("\nThis test will:")
    print("1. Generate test metrics in CloudWatch")
    print("2. Create an OpsItem (triggers EventBridge)")
    print("3. Monitor automatic AI analysis")
    print("4. Display results when complete")
    print("\n" + "-"*80)
    
    try:
        # Generate test data
        generate_test_metrics()
        
        # Create OpsItem
        ops_item_id = create_test_opsitem()
        
        # Wait for automatic analysis
        analysis_completed = wait_for_analysis(ops_item_id)
        
        # Check KB indexing
        check_knowledge_base(ops_item_id)
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"OpsItem ID: {ops_item_id}")
        print(f"Automatic Analysis: {'✅ Completed' if analysis_completed else '❌ Not completed'}")
        print(f"Knowledge Base: Checked")
        
        if analysis_completed:
            print("\n✨ The automatic AI analysis flow is working correctly!")
            print("   EventBridge → OpsItem Indexer → Supervisor → All Agents → AI Analysis")
        else:
            print("\n⚠️  The automatic flow may need troubleshooting.")
            print("   Check Lambda logs for errors.")
            
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
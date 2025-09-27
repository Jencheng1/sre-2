#!/usr/bin/env python3
"""
Test CPU Spike Root Cause Analysis
Tests the root cause analysis functionality for CPU spike incidents
"""

import boto3
import json
import time
from datetime import datetime, timedelta

class TestCPUSpikeRootCause:
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
        
    def create_test_ops_item(self):
        """Create a test OpsItem for CPU spike"""
        try:
            response = self.ssm_client.create_ops_item(
                Title="Test High CPU Alert - EC2 Instance",
                Description="CPU utilization spike detected on EC2 instance test-server (i-1234567890). Current CPU: 95%",
                Source="Test Script",
                Severity="2",
                OperationalData={
                    'InstanceId': {'Value': 'i-1234567890abcdef0', 'Type': 'String'},
                    'CPUPercent': {'Value': '95', 'Type': 'String'},
                    'IncidentType': {'Value': 'CPU Spike', 'Type': 'String'}
                },
                Tags=[
                    {'Key': 'Environment', 'Value': 'test'},
                    {'Key': 'Service', 'Value': 'sre-demo-app'}
                ]
            )
            return response['OpsItemId']
        except Exception as e:
            print(f"Error creating OpsItem: {e}")
            return None
            
    def run_supervisor_correlation(self, ops_item_id):
        """Run supervisor correlation analysis"""
        try:
            # Get the OpsItem details
            response = self.ssm_client.get_ops_item(OpsItemId=ops_item_id)
            ops_item = response['OpsItem']
            
            # Build the payload
            payload = {
                'action': 'analyze',
                'incident_description': f"{ops_item.get('Title', '')}. {ops_item.get('Description', '')}",
                'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'service': 'sre-demo-app',
                'environment': 'test',
                'additional_context': {
                    'ops_item_id': ops_item_id,
                    'severity': ops_item.get('Severity', '2'),
                    'incident_type': 'CPU Spike'
                }
            }
            
            print(f"Invoking supervisor Lambda with payload:")
            print(json.dumps(payload, indent=2))
            
            # Invoke the supervisor Lambda
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse the response
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error running supervisor correlation: {e}")
            return None
            
    def test_root_cause_analysis(self):
        """Test the complete root cause analysis flow"""
        print("🧪 Testing CPU Spike Root Cause Analysis")
        print("=" * 50)
        
        # Step 1: Create test OpsItem
        print("\n1️⃣ Creating test OpsItem...")
        ops_item_id = self.create_test_ops_item()
        if not ops_item_id:
            print("❌ Failed to create test OpsItem")
            return False
            
        print(f"✅ Created OpsItem: {ops_item_id}")
        
        # Step 2: Run root cause analysis
        print("\n2️⃣ Running root cause analysis...")
        result = self.run_supervisor_correlation(ops_item_id)
        
        if not result:
            print("❌ Failed to run root cause analysis")
            return False
            
        print(f"\n📊 Analysis Result:")
        print(f"Status Code: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body']) if isinstance(result.get('body'), str) else result.get('body', {})
            
            # Display root cause
            if 'root_cause' in body:
                print(f"\n🎯 Root Cause:")
                print(f"   {body['root_cause']}")
            
            # Display correlations
            if 'correlations' in body:
                print(f"\n🔗 Correlations Found:")
                for correlation in body.get('correlations', []):
                    print(f"   - {correlation.get('event_type', 'Unknown')}: {correlation.get('details', 'No details')}")
            
            # Display recommendations
            if 'recommendations' in body:
                print(f"\n💡 Recommendations:")
                for rec in body.get('recommendations', []):
                    print(f"   - {rec}")
            
            print("\n✅ Root cause analysis completed successfully!")
            return True
        else:
            print(f"❌ Analysis failed with status code: {result.get('statusCode')}")
            if 'body' in result:
                body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
                print(f"Error: {body.get('error', 'Unknown error')}")
            return False
            
    def cleanup_test_ops_item(self, ops_item_id):
        """Clean up test OpsItem"""
        try:
            self.ssm_client.update_ops_item(
                OpsItemId=ops_item_id,
                Status='Resolved'
            )
            print(f"✅ Cleaned up OpsItem: {ops_item_id}")
        except Exception as e:
            print(f"⚠️ Failed to cleanup OpsItem: {e}")
            
    def test_with_metrics(self):
        """Test root cause analysis with CloudWatch metrics"""
        print("\n🧪 Testing with CloudWatch Metrics")
        print("=" * 50)
        
        # Create test OpsItem
        ops_item_id = self.create_test_ops_item()
        if not ops_item_id:
            print("❌ Failed to create test OpsItem")
            return False
            
        try:
            # Check if we have any EC2 instances with CPU metrics
            print("\n📊 Checking for EC2 CPU metrics...")
            response = self.cloudwatch_client.list_metrics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization'
            )
            
            if response['Metrics']:
                print(f"✅ Found {len(response['Metrics'])} EC2 instances with CPU metrics")
                
                # Get a sample instance
                sample_metric = response['Metrics'][0]
                instance_id = None
                for dim in sample_metric['Dimensions']:
                    if dim['Name'] == 'InstanceId':
                        instance_id = dim['Value']
                        break
                        
                if instance_id:
                    print(f"   Using instance: {instance_id}")
                    
                    # Get recent CPU data
                    metric_response = self.cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=datetime.utcnow() - timedelta(hours=1),
                        EndTime=datetime.utcnow(),
                        Period=300,
                        Statistics=['Average', 'Maximum']
                    )
                    
                    if metric_response['Datapoints']:
                        latest = sorted(metric_response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                        print(f"   Latest CPU: {latest['Average']:.2f}% avg, {latest['Maximum']:.2f}% max")
            else:
                print("⚠️ No EC2 CPU metrics found in CloudWatch")
                
            # Run analysis
            print("\n🔍 Running root cause analysis with metrics context...")
            result = self.run_supervisor_correlation(ops_item_id)
            
            if result and result.get('statusCode') == 200:
                print("✅ Analysis with metrics completed successfully!")
                return True
            else:
                print("❌ Analysis with metrics failed")
                return False
                
        finally:
            # Cleanup
            self.cleanup_test_ops_item(ops_item_id)
            
def main():
    """Run all tests"""
    tester = TestCPUSpikeRootCause()
    
    # Test 1: Basic root cause analysis
    print("\n" + "="*70)
    print("TEST 1: Basic Root Cause Analysis")
    print("="*70)
    success1 = tester.test_root_cause_analysis()
    
    # Wait a moment between tests
    time.sleep(2)
    
    # Test 2: Analysis with CloudWatch metrics
    print("\n" + "="*70)
    print("TEST 2: Root Cause Analysis with Metrics")
    print("="*70)
    success2 = tester.test_with_metrics()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Test 1 (Basic Analysis): {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Test 2 (With Metrics): {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    overall_success = success1 and success2
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
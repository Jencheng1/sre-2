#!/usr/bin/env python3
"""
Create a change record for Java deployment to test correlation
"""

import boto3
import json
from datetime import datetime, timedelta

def create_java_deployment_change():
    """Create a change record for payment-service v2.1.0 deployment"""
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    
    print("📝 Creating Change Record for Java Deployment")
    print("=" * 60)
    
    try:
        # Create change record
        response = ssm_client.create_ops_item(
            Title="[CHANGE] Deploy payment-service v2.1.0 - Memory optimization disabled",
            Description="""Production deployment of payment-service v2.1.0
            
Changes included:
- New TransactionCache implementation for payment processing
- Removed cache eviction policy for "performance optimization"
- Increased initial heap size to 128MB
- Modified garbage collection settings
            
Risk Level: High
Rollback Plan: Revert to v2.0.3
Deployment Time: {}""".format(datetime.now().isoformat()),
            Source="ChangeManagement",
            OperationalData={
                'ChangeType': {'Value': 'Application Deployment'},
                'Service': {'Value': 'payment-service'},
                'Version': {'Value': 'v2.1.0'},
                'RiskLevel': {'Value': 'High'},
                'Environment': {'Value': 'Production'},
                'DeploymentTime': {'Value': datetime.now().isoformat()},
                'ChangeWindow': {'Value': '2 hours'},
                'Approver': {'Value': 'DevOps Team'},
                'ImplementedBy': {'Value': 'CI/CD Pipeline'}
            },
            Severity='3',
            Category='Availability'
        )
        
        change_id = response['OpsItemId']
        print(f"✅ Created change record: {change_id}")
        print(f"   Title: [CHANGE] Deploy payment-service v2.1.0")
        print(f"   Risk: High")
        print(f"   Time: {datetime.now()}")
        
        # Also create a related configuration change
        config_response = ssm_client.create_ops_item(
            Title="[CHANGE] Configuration Update - Disable cache eviction",
            Description="""Configuration change to improve transaction processing performance
            
Modified settings:
- cache.eviction.enabled = false
- cache.max.size = unlimited
- transaction.timeout = 300s
            
Expected Impact: Improved response time, higher memory usage""",
            Source="ChangeManagement",
            OperationalData={
                'ChangeType': {'Value': 'Configuration Change'},
                'Service': {'Value': 'payment-service'},
                'RelatedDeployment': {'Value': change_id},
                'ConfigFile': {'Value': 'application.properties'},
                'RiskLevel': {'Value': 'Medium'}
            },
            Severity='3',
            Category='Performance'
        )
        
        config_id = config_response['OpsItemId']
        print(f"✅ Created related config change: {config_id}")
        
        return change_id, config_id
        
    except Exception as e:
        print(f"❌ Error creating change record: {e}")
        return None, None

def push_change_metrics(change_id):
    """Push change-related metrics to CloudWatch"""
    cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
    
    print("\n📊 Pushing change metrics to CloudWatch...")
    
    try:
        # Push deployment metric
        response = cloudwatch_client.put_metric_data(
            Namespace='ChangeManagement',
            MetricData=[
                {
                    'MetricName': 'DeploymentCompleted',
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'Service', 'Value': 'payment-service'},
                        {'Name': 'Version', 'Value': 'v2.1.0'},
                        {'Name': 'ChangeId', 'Value': change_id}
                    ]
                },
                {
                    'MetricName': 'ChangeRiskScore',
                    'Value': 8,  # High risk
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': 'payment-service'},
                        {'Name': 'ChangeType', 'Value': 'Deployment'}
                    ]
                }
            ]
        )
        
        print("✅ Change metrics pushed to CloudWatch")
        
    except Exception as e:
        print(f"⚠️ Could not push metrics: {e}")

def test_correlation():
    """Test if the supervisor lambda will correlate properly"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    print("\n🧪 Testing Enhanced Correlation...")
    
    # Create a test incident
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    
    try:
        # Create CPU spike incident
        incident_response = ssm_client.create_ops_item(
            Title="High CPU Alert - Payment Service Performance Degradation",
            Description="CPU utilization spike detected on payment-service. Response times degraded. Possible memory pressure.",
            Source="CloudWatch",
            OperationalData={
                'Instance': {'Value': 'i-02bef13982a179478'},
                'Service': {'Value': 'payment-service'},
                'CPUUtilization': {'Value': '92%'},
                'MemoryUsage': {'Value': '87%'},
                'AlertTime': {'Value': datetime.now().isoformat()}
            },
            Severity='2',
            Category='Performance'
        )
        
        incident_id = incident_response['OpsItemId']
        print(f"✅ Created test incident: {incident_id}")
        
        # Invoke supervisor for analysis
        print("\n🔍 Invoking supervisor lambda for correlation...")
        
        payload = {
            'action': 'analyze',
            'incident_description': 'High CPU on payment-service with performance degradation. Memory usage elevated.',
            'start_time': (datetime.now() - timedelta(hours=1)).isoformat(),
            'end_time': datetime.now().isoformat(),
            'service': 'payment-service',
            'environment': 'production',
            'additional_context': {
                'ops_item_id': incident_id,
                'incident_type': 'CPU Spike',
                'instance_id': 'i-02bef13982a179478'
            }
        }
        
        response = lambda_client.invoke(
            FunctionName='sre-supervisor-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            analysis = body.get('root_cause_analysis', '')
            
            print("\n📋 Correlation Analysis Results:")
            print("-" * 60)
            
            # Check for key correlation indicators
            correlations_found = []
            
            if 'memory leak' in analysis.lower():
                correlations_found.append("✅ Memory leak detected")
            else:
                correlations_found.append("❌ Memory leak NOT detected")
                
            if 'v2.1.0' in analysis or 'deployment' in analysis.lower():
                correlations_found.append("✅ Deployment change correlated")
            else:
                correlations_found.append("❌ Deployment change NOT correlated")
                
            if 'transactioncache' in analysis.lower() or 'cache' in analysis.lower():
                correlations_found.append("✅ Cache issue identified")
            else:
                correlations_found.append("❌ Cache issue NOT identified")
                
            if 'garbage collection' in analysis.lower() or 'gc' in analysis.lower():
                correlations_found.append("✅ GC overhead linked to CPU")
            else:
                correlations_found.append("❌ GC overhead NOT linked")
            
            print("\nCorrelation Checks:")
            for check in correlations_found:
                print(f"   {check}")
            
            print(f"\n🔍 Analysis Preview:")
            print(analysis[:500] + "...")
            
            # Calculate success rate
            success_count = sum(1 for c in correlations_found if c.startswith("✅"))
            total_checks = len(correlations_found)
            success_rate = (success_count / total_checks) * 100
            
            print(f"\n📊 Correlation Success Rate: {success_rate:.0f}% ({success_count}/{total_checks})")
            
            if success_rate >= 75:
                print("\n🎉 EXCELLENT! Supervisor is properly correlating:")
                print("   - JVM memory leak detected")
                print("   - Change record linked")
                print("   - Root cause identified")
            else:
                print("\n⚠️ Correlation needs improvement")
                
        else:
            print(f"❌ Analysis failed: {result}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    # Create change records
    change_id, config_id = create_java_deployment_change()
    
    if change_id:
        # Push metrics
        push_change_metrics(change_id)
        
        # Wait a moment for propagation
        print("\n⏳ Waiting for changes to propagate...")
        import time
        time.sleep(5)
        
        # Test correlation
        test_correlation()
        
        print("\n✅ Change records created and correlation tested!")
        print(f"\nChange IDs:")
        print(f"   Deployment: {change_id}")
        print(f"   Configuration: {config_id}")
    else:
        print("\n❌ Failed to create change records")
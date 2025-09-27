#!/usr/bin/env python3
"""Setup CloudWatch datasource with default authentication"""

import requests
import json
import boto3
import os

# Grafana configuration
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def delete_all_cloudwatch_datasources():
    """Delete all existing CloudWatch datasources"""
    print("🗑️  Cleaning up existing CloudWatch datasources...")
    
    response = requests.get(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASS)
    )
    
    if response.status_code == 200:
        datasources = response.json()
        for ds in datasources:
            if ds['type'] == 'cloudwatch':
                print(f"   Deleting: {ds['name']}")
                requests.delete(
                    f"{GRAFANA_URL}/api/datasources/{ds['id']}",
                    auth=(GRAFANA_USER, GRAFANA_PASS)
                )

def create_cloudwatch_datasource_default():
    """Create CloudWatch datasource with default credentials"""
    print("\n📊 Creating CloudWatch datasource with default auth...")
    
    # Use default authentication which will pick up EC2 instance credentials
    datasource_config = {
        "name": "CloudWatch",
        "type": "cloudwatch",
        "access": "proxy",
        "isDefault": False,
        "jsonData": {
            "authType": "default",
            "defaultRegion": "us-east-1"
        }
    }
    
    response = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        data=json.dumps(datasource_config)
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"   ✓ Created datasource ID: {result.get('id')}")
        return result
    else:
        print(f"   ✗ Failed: {response.text}")
        return None

def test_cloudwatch_metrics():
    """Test if we can get EC2 metrics"""
    print("\n🧪 Testing CloudWatch metrics directly...")
    
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # List EC2 CPU metrics
        metrics = cloudwatch.list_metrics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[]
        )
        
        instance_count = len(set([d['Value'] for m in metrics['Metrics'] 
                                 for d in m['Dimensions'] 
                                 if d['Name'] == 'InstanceId']))
        
        print(f"   ✓ Found CPU metrics for {instance_count} EC2 instances")
        
        # Get sample data
        if metrics['Metrics']:
            instance_id = metrics['Metrics'][0]['Dimensions'][0]['Value']
            
            from datetime import datetime, timedelta
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                print(f"   ✓ Latest CPU for {instance_id}: {latest['Average']:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def create_simple_dashboard(datasource_uid):
    """Create a simple working dashboard"""
    print("\n📈 Creating simple EC2 CPU dashboard...")
    
    dashboard = {
        "dashboard": {
            "title": "EC2 CPU Monitoring - Simple",
            "uid": "ec2-cpu-simple",
            "panels": [
                {
                    "datasource": {
                        "type": "cloudwatch",
                        "uid": datasource_uid
                    },
                    "targets": [
                        {
                            "alias": "",
                            "datasource": {
                                "type": "cloudwatch",
                                "uid": datasource_uid
                            },
                            "dimensions": {},
                            "expression": "",
                            "id": "",
                            "label": "${PROP('Dim.InstanceId')}",
                            "matchExact": False,
                            "metricEditorMode": 0,
                            "metricName": "CPUUtilization",
                            "metricQueryType": 0,
                            "namespace": "AWS/EC2",
                            "period": "300",
                            "queryMode": "Metrics",
                            "refId": "A",
                            "region": "default",
                            "statistic": "Average"
                        }
                    ],
                    "title": "EC2 CPU Usage",
                    "type": "timeseries",
                    "gridPos": {
                        "h": 10,
                        "w": 24,
                        "x": 0,
                        "y": 0
                    },
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            ],
            "schemaVersion": 27,
            "version": 0,
            "refresh": "10s",
            "time": {
                "from": "now-1h",
                "to": "now"
            }
        },
        "overwrite": True
    }
    
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        data=json.dumps(dashboard)
    )
    
    if response.status_code in [200, 201]:
        print("   ✓ Dashboard created successfully")
        result = response.json()
        print(f"   URL: {GRAFANA_URL}/d/{result['uid']}/ec2-cpu-monitoring-simple")
        return True
    else:
        print(f"   ✗ Failed: {response.text}")
        return False

def check_aws_credentials():
    """Check if AWS credentials are available"""
    print("\n🔑 Checking AWS credentials...")
    
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"   ✓ AWS Account: {identity['Account']}")
        print(f"   ✓ ARN: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"   ✗ No credentials: {e}")
        return False

def main():
    print("🔧 Setting up CloudWatch with Default Authentication")
    print("=" * 60)
    
    # Check AWS access
    if not check_aws_credentials():
        print("\n❌ AWS credentials not available!")
        return
    
    # Test CloudWatch access
    if not test_cloudwatch_metrics():
        print("\n❌ Cannot access CloudWatch metrics!")
        return
    
    # Clean up
    delete_all_cloudwatch_datasources()
    
    # Create datasource
    datasource = create_cloudwatch_datasource_default()
    
    if datasource:
        # Create simple dashboard
        datasource_uid = datasource.get('datasourceUid') or datasource.get('uid') or f"datasource-{datasource.get('id')}"
        create_simple_dashboard(datasource_uid)
        
        print("\n✅ Setup complete!")
        print("\n📊 Access your dashboard at:")
        print(f"   {GRAFANA_URL}/d/ec2-cpu-simple/ec2-cpu-monitoring-simple")
        print("\n⚠️  Important:")
        print("   - Wait 30-60 seconds for data to appear")
        print("   - Make sure time range is set to 'Last 1 hour'")
        print("   - Click the refresh button if needed")
    else:
        print("\n❌ Setup failed!")

if __name__ == "__main__":
    main()
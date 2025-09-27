#!/usr/bin/env python3
"""
Simple fix for Grafana CloudWatch integration using AWS CLI credentials
"""

import os
import json
import time
import requests
import subprocess
import boto3

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def get_aws_credentials():
    """Get AWS credentials using boto3"""
    print("🔑 Getting AWS credentials...")
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials:
            creds = credentials.get_frozen_credentials()
            print("   ✅ Got AWS credentials")
            return {
                "access_key": creds.access_key,
                "secret_key": creds.secret_key,
                "token": creds.token
            }
    except Exception as e:
        print(f"   ❌ Error: {e}")
    return None

def configure_grafana_aws():
    """Configure Grafana with AWS credentials"""
    print("\n📊 Configuring Grafana CloudWatch datasource...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # First, delete all existing CloudWatch datasources
    print("   Removing existing datasources...")
    r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
    if r.status_code == 200:
        for ds in r.json():
            if ds['type'] == 'cloudwatch':
                requests.delete(f"{GRAFANA_URL}/api/datasources/{ds['id']}", auth=auth)
    
    # Get AWS credentials
    creds = get_aws_credentials()
    if not creds:
        # Try using default/EC2 instance profile
        print("   Using EC2 instance profile...")
        datasource = {
            "name": "CloudWatch",
            "type": "cloudwatch",
            "access": "proxy",
            "jsonData": {
                "authType": "ec2_iam_role",
                "defaultRegion": "us-east-1"
            }
        }
    else:
        # Use explicit credentials
        print("   Using explicit AWS credentials...")
        datasource = {
            "name": "CloudWatch",
            "type": "cloudwatch",
            "access": "proxy",
            "jsonData": {
                "authType": "keys",
                "defaultRegion": "us-east-1"
            },
            "secureJsonData": {
                "accessKey": creds["access_key"],
                "secretKey": creds["secret_key"],
                "sessionToken": creds.get("token", "")
            }
        }
    
    # Create datasource
    r = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        auth=auth,
        json=datasource
    )
    
    if r.status_code in [200, 201]:
        result = r.json()
        print(f"   ✅ Created datasource (ID: {result['id']})")
        
        # Get the full datasource info with UID
        detail_r = requests.get(f"{GRAFANA_URL}/api/datasources/{result['id']}", auth=auth)
        if detail_r.status_code == 200:
            return detail_r.json()
        else:
            return result
    else:
        print(f"   ❌ Failed: {r.text}")
        return None

def create_simple_dashboard(datasource_uid):
    """Create a simple EC2 CPU dashboard"""
    print("\n📈 Creating EC2 CPU dashboard...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # Get EC2 instances
    ec2 = boto3.client('ec2', region_name='us-east-1')
    response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])
    
    print(f"   Found {len(instances)} EC2 instances")
    
    # Create dashboard
    dashboard = {
        "dashboard": {
            "title": "EC2 CPU Usage",
            "uid": "ec2-cpu-final",
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
                            "region": "us-east-1",
                            "statistic": "Average"
                        }
                    ],
                    "title": "EC2 CPU Utilization",
                    "type": "timeseries",
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "min": 0,
                            "max": 100,
                            "color": {
                                "mode": "palette-classic"
                            }
                        }
                    },
                    "gridPos": {
                        "h": 10,
                        "w": 24,
                        "x": 0,
                        "y": 0
                    },
                    "options": {
                        "legend": {
                            "calcs": ["mean", "last"],
                            "displayMode": "table",
                            "placement": "bottom",
                            "showLegend": True
                        }
                    }
                }
            ],
            "refresh": "30s",
            "time": {
                "from": "now-1h",
                "to": "now"
            }
        },
        "overwrite": True
    }
    
    # Add individual instance panels
    y_pos = 10
    for i, instance_id in enumerate(instances):
        panel = {
            "datasource": {
                "type": "cloudwatch",
                "uid": datasource_uid
            },
            "targets": [
                {
                    "datasource": {
                        "type": "cloudwatch",
                        "uid": datasource_uid
                    },
                    "dimensions": {
                        "InstanceId": instance_id
                    },
                    "metricName": "CPUUtilization",
                    "namespace": "AWS/EC2",
                    "period": "300",
                    "region": "us-east-1",
                    "statistic": "Average",
                    "refId": "A"
                }
            ],
            "title": f"Instance: {instance_id}",
            "type": "stat",
            "fieldConfig": {
                "defaults": {
                    "unit": "percent",
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 60},
                            {"color": "red", "value": 80}
                        ]
                    }
                }
            },
            "gridPos": {
                "h": 6,
                "w": 6,
                "x": (i % 4) * 6,
                "y": y_pos + (i // 4) * 6
            }
        }
        dashboard["dashboard"]["panels"].append(panel)
    
    r = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=auth,
        json=dashboard
    )
    
    if r.status_code in [200, 201]:
        print("   ✅ Dashboard created")
        return True
    else:
        print(f"   ❌ Failed: {r.text}")
        return False

def verify_data_access():
    """Verify we can access CloudWatch data"""
    print("\n🧪 Verifying CloudWatch access...")
    
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # List metrics
        metrics = cloudwatch.list_metrics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization'
        )
        
        metric_count = len(metrics['Metrics'])
        print(f"   ✅ Found {metric_count} CPU metrics in CloudWatch")
        
        # Get sample data
        if metrics['Metrics']:
            from datetime import datetime, timedelta
            
            instance_id = metrics['Metrics'][0]['Dimensions'][0]['Value']
            
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
                print(f"   ✅ Successfully retrieved data for {instance_id}")
                latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                print(f"      Latest CPU: {latest['Average']:.2f}% at {latest['Timestamp']}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🔧 Simple Grafana CloudWatch Fix")
    print("=" * 50)
    
    # Verify CloudWatch access first
    if not verify_data_access():
        print("\n❌ Cannot access CloudWatch data!")
        return 1
    
    # Configure datasource
    datasource = configure_grafana_aws()
    if not datasource:
        print("\n❌ Failed to configure datasource!")
        return 1
    
    # Create dashboard
    if create_simple_dashboard(datasource['uid']):
        print("\n✅ Fix complete!")
        print(f"\n📊 Access your dashboard at:")
        print(f"   {GRAFANA_URL}/d/ec2-cpu-final/ec2-cpu-usage")
        print("\n⏱️  Notes:")
        print("   - Wait 30-60 seconds for data to appear")
        print("   - Dashboard refreshes every 30 seconds")
        print("   - Time range: Last 1 hour")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
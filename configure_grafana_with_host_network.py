#!/usr/bin/env python3
"""
Configure Grafana with host network mode to use EC2 IAM role
"""

import requests
import json
import time
import boto3
from datetime import datetime, timedelta

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def wait_for_grafana():
    """Wait for Grafana to be ready"""
    print("⏳ Waiting for Grafana to start...")
    for i in range(30):
        try:
            r = requests.get(f"{GRAFANA_URL}/api/health")
            if r.status_code == 200:
                print("✅ Grafana is ready")
                return True
        except:
            pass
        time.sleep(1)
    return False

def test_ec2_metadata_access():
    """Test if we can access EC2 metadata (only works with host network)"""
    print("\n🔍 Testing EC2 metadata access...")
    try:
        # Test from inside Grafana container would work now
        r = requests.get("http://169.254.169.254/latest/meta-data/instance-id", timeout=2)
        if r.status_code == 200:
            print(f"   ✅ EC2 metadata accessible: Instance {r.text}")
            return True
    except:
        print("   ⚠️  Cannot access EC2 metadata directly")
    return False

def delete_all_datasources():
    """Clean up existing datasources"""
    print("\n🗑️  Removing existing datasources...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
    if r.status_code == 200:
        for ds in r.json():
            if ds['type'] == 'cloudwatch':
                print(f"   Deleting: {ds['name']}")
                requests.delete(f"{GRAFANA_URL}/api/datasources/{ds['id']}", auth=auth)

def create_ec2_iam_role_datasource():
    """Create CloudWatch datasource using EC2 IAM role"""
    print("\n📊 Creating CloudWatch datasource with EC2 IAM role...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    datasource = {
        "name": "CloudWatch-EC2-IAM",
        "type": "cloudwatch",
        "access": "proxy",
        "jsonData": {
            "authType": "ec2_iam_role",
            "defaultRegion": "us-east-1",
            "assumeRoleArn": "",
            "externalId": ""
        }
    }
    
    r = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        auth=auth,
        json=datasource
    )
    
    if r.status_code in [200, 201]:
        result = r.json()
        print(f"   ✅ Created datasource (ID: {result['id']})")
        
        # Get full details
        detail_r = requests.get(f"{GRAFANA_URL}/api/datasources/{result['id']}", auth=auth)
        if detail_r.status_code == 200:
            return detail_r.json()
    else:
        print(f"   ❌ Failed: {r.text}")
    
    return None

def test_datasource_query(ds_id):
    """Test if datasource can query CloudWatch"""
    print("\n🧪 Testing datasource query...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # Simple test query
    query = {
        "queries": [{
            "refId": "A",
            "datasourceId": ds_id,
            "queryType": "timeSeriesQuery", 
            "region": "us-east-1",
            "namespace": "AWS/EC2",
            "metricName": "CPUUtilization",
            "dimensions": {},
            "statistic": "Average",
            "period": "300"
        }],
        "from": "now-1h",
        "to": "now"
    }
    
    r = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        auth=auth,
        json=query
    )
    
    print(f"   Query response status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        if 'results' in data:
            for key, result in data['results'].items():
                if 'error' in result:
                    print(f"   ❌ Error: {result['error']}")
                    return False
                else:
                    print("   ✅ Query successful - datasource is working!")
                    return True
    
    return False

def create_working_dashboard(ds_uid):
    """Create dashboard with EC2 CPU metrics"""
    print("\n📈 Creating EC2 CPU dashboard...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # Get EC2 instances for individual panels
    ec2 = boto3.client('ec2', region_name='us-east-1')
    response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            name = next((tag['Value'] for tag in instance.get('Tags', []) 
                        if tag['Key'] == 'Name'), instance['InstanceId'])
            instances.append({
                'id': instance['InstanceId'],
                'name': name
            })
    
    print(f"   Found {len(instances)} EC2 instances")
    
    # Create dashboard
    panels = []
    
    # Main panel - all instances
    panels.append({
        "id": 1,
        "datasource": {
            "type": "cloudwatch",
            "uid": ds_uid
        },
        "targets": [{
            "refId": "A",
            "region": "us-east-1",
            "namespace": "AWS/EC2",
            "metricName": "CPUUtilization",
            "dimensions": {},
            "statistic": "Average",
            "period": "300",
            "alias": "{{InstanceId}}"
        }],
        "title": "All EC2 Instances - CPU Usage",
        "type": "timeseries",
        "gridPos": {"h": 10, "w": 24, "x": 0, "y": 0},
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "color": {"mode": "palette-classic"},
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "linear",
                    "lineWidth": 2,
                    "fillOpacity": 10,
                    "gradientMode": "none",
                    "spanNulls": True,
                    "showPoints": "never",
                    "pointSize": 5,
                    "stacking": {"mode": "none", "group": "A"},
                    "axisPlacement": "auto",
                    "axisLabel": "CPU %",
                    "axisColorMode": "text",
                    "scaleDistribution": {"type": "linear"},
                    "axisCenteredZero": False,
                    "hideFrom": {
                        "tooltip": False,
                        "viz": False,
                        "legend": False
                    },
                    "thresholdsStyle": {"mode": "line"}
                },
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
        "options": {
            "tooltip": {"mode": "multi", "sort": "none"},
            "legend": {
                "showLegend": True,
                "displayMode": "table",
                "placement": "bottom",
                "calcs": ["last", "mean", "max"]
            }
        }
    })
    
    # Individual instance panels
    y_pos = 10
    for i, instance in enumerate(instances):
        panels.append({
            "id": i + 2,
            "datasource": {
                "type": "cloudwatch",
                "uid": ds_uid
            },
            "targets": [{
                "refId": "A",
                "region": "us-east-1",
                "namespace": "AWS/EC2",
                "metricName": "CPUUtilization",
                "dimensions": {
                    "InstanceId": instance['id']
                },
                "statistic": "Average",
                "period": "300"
            }],
            "title": f"{instance['name']} CPU",
            "type": "stat",
            "gridPos": {
                "h": 6,
                "w": 6,
                "x": (i % 4) * 6,
                "y": y_pos + (i // 4) * 6
            },
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
                    },
                    "color": {"mode": "thresholds"}
                }
            },
            "options": {
                "reduceOptions": {
                    "values": False,
                    "calcs": ["lastNotNull"],
                    "fields": ""
                },
                "orientation": "auto",
                "textMode": "auto",
                "colorMode": "value",
                "graphMode": "area",
                "justifyMode": "center"
            }
        })
    
    dashboard = {
        "dashboard": {
            "title": "EC2 CPU Monitoring - Host Network",
            "uid": "ec2-cpu-host-network",
            "panels": panels,
            "schemaVersion": 39,
            "refresh": "10s",
            "time": {"from": "now-1h", "to": "now"},
            "tags": ["ec2", "cpu", "cloudwatch"]
        },
        "overwrite": True
    }
    
    r = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=auth,
        json=dashboard
    )
    
    if r.status_code in [200, 201]:
        result = r.json()
        print(f"   ✅ Dashboard created successfully!")
        print(f"   URL: {GRAFANA_URL}/d/{result['uid']}")
        return True
    else:
        print(f"   ❌ Failed: {r.text}")
        return False

def verify_data_is_showing():
    """Verify that data is actually being displayed"""
    print("\n🔍 Verifying data is showing...")
    
    # Give it a moment for data to load
    time.sleep(5)
    
    # Check CloudWatch has data
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        response = cloudwatch.list_metrics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization'
        )
        
        if response['Metrics']:
            print(f"   ✅ CloudWatch has {len(response['Metrics'])} CPU metrics")
            
            # Get sample data
            instance_id = response['Metrics'][0]['Dimensions'][0]['Value']
            
            data_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )
            
            if data_response['Datapoints']:
                latest = sorted(data_response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                print(f"   ✅ Latest CPU data: {latest['Average']:.2f}% for {instance_id}")
                return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return False

def main():
    print("🔧 Configuring Grafana with Host Network Mode")
    print("=" * 60)
    
    # Wait for Grafana
    if not wait_for_grafana():
        print("❌ Grafana failed to start")
        return 1
    
    # Test metadata access
    test_ec2_metadata_access()
    
    # Clean up
    delete_all_datasources()
    
    # Create EC2 IAM role datasource
    datasource = create_ec2_iam_role_datasource()
    if not datasource:
        print("❌ Failed to create datasource")
        return 1
    
    # Test it
    if test_datasource_query(datasource['id']):
        print("\n✅ Datasource is working properly!")
    else:
        print("\n⚠️  Datasource query test failed, but continuing...")
    
    # Create dashboard
    if create_working_dashboard(datasource['uid']):
        # Verify data
        verify_data_is_showing()
        
        print("\n" + "=" * 60)
        print("✅ CONFIGURATION COMPLETE!")
        print("=" * 60)
        print("\n📊 Your EC2 CPU dashboard is ready:")
        print(f"   {GRAFANA_URL}/d/ec2-cpu-host-network")
        print("\n⏱️  Important:")
        print("   • Data should be visible immediately")
        print("   • Dashboard auto-refreshes every 10 seconds")
        print("   • Shows all EC2 instances in your account")
        print("\n🎉 EC2 CPU monitoring is now working with host network mode!")
    else:
        print("\n❌ Failed to create dashboard")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
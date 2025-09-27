#!/usr/bin/env python3
"""
Fix Grafana to use default authentication with host network
"""

import requests
import json
import time
import boto3

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"  
GRAFANA_PASS = "admin123"

def delete_all_datasources():
    """Delete all datasources"""
    print("🗑️  Cleaning up datasources...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
    if r.status_code == 200:
        for ds in r.json():
            if ds['type'] == 'cloudwatch':
                print(f"   Deleting: {ds['name']}")
                requests.delete(f"{GRAFANA_URL}/api/datasources/{ds['id']}", auth=auth)

def create_default_datasource():
    """Create datasource with default auth"""
    print("\n📊 Creating CloudWatch datasource with default auth...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    datasource = {
        "name": "CloudWatch",
        "type": "cloudwatch",
        "access": "proxy",
        "isDefault": True,
        "jsonData": {
            "authType": "default",
            "defaultRegion": "us-east-1"
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
        
        # Test it immediately
        print("\n🧪 Testing datasource...")
        test_r = requests.post(
            f"{GRAFANA_URL}/api/datasources/{result['id']}/health",
            auth=auth
        )
        print(f"   Health check status: {test_r.status_code}")
        if test_r.status_code == 200:
            print("   ✅ Datasource is healthy!")
        else:
            print(f"   Response: {test_r.text}")
        
        # Get full details
        detail_r = requests.get(f"{GRAFANA_URL}/api/datasources/{result['id']}", auth=auth)
        if detail_r.status_code == 200:
            return detail_r.json()
        return result
    else:
        print(f"   ❌ Failed: {r.text}")
        return None

def create_simple_dashboard(ds_uid):
    """Create a simple dashboard"""
    print("\n📈 Creating simple dashboard...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    dashboard = {
        "dashboard": {
            "title": "EC2 CPU - Simple",
            "uid": "ec2-cpu-simple-final",
            "panels": [{
                "id": 1,
                "datasource": {
                    "type": "cloudwatch",
                    "uid": ds_uid
                },
                "targets": [{
                    "alias": "",
                    "datasource": {
                        "type": "cloudwatch",
                        "uid": ds_uid
                    },
                    "dimensions": {},
                    "expression": "",
                    "id": "",
                    "label": "",
                    "matchExact": False,
                    "metricEditorMode": 0,
                    "metricName": "CPUUtilization",
                    "metricQueryType": 0,
                    "namespace": "AWS/EC2",
                    "period": "",
                    "queryMode": "Metrics",
                    "refId": "A",
                    "region": "default",
                    "sqlExpression": "",
                    "statistic": "Average"
                }],
                "title": "EC2 CPU Usage",
                "type": "timeseries",
                "gridPos": {"h": 12, "w": 24, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "min": 0,
                        "max": 100
                    }
                }
            }],
            "refresh": "30s",
            "time": {"from": "now-6h", "to": "now"}
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
        print("   ✅ Dashboard created")
        print(f"   URL: {GRAFANA_URL}/d/{result['uid']}")
        return True
    else:
        print(f"   ❌ Failed: {r.text}")
        return False

def test_actual_query(ds_id):
    """Test an actual metric query"""
    print("\n🔍 Testing actual CloudWatch query...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # First, get an instance ID from CloudWatch
    ec2 = boto3.client('ec2', region_name='us-east-1')
    instances = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    instance_id = None
    for res in instances['Reservations']:
        for inst in res['Instances']:
            instance_id = inst['InstanceId']
            break
        if instance_id:
            break
    
    if not instance_id:
        print("   ❌ No running instances found")
        return False
    
    print(f"   Testing with instance: {instance_id}")
    
    # Query through Grafana
    query = {
        "queries": [{
            "refId": "A",
            "datasourceId": ds_id,
            "intervalMs": 60000,
            "maxDataPoints": 960,
            "region": "us-east-1",
            "namespace": "AWS/EC2",
            "metricName": "CPUUtilization",
            "dimensions": {"InstanceId": instance_id},
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
    
    print(f"   Query response: {r.status_code}")
    
    if r.status_code == 200:
        try:
            data = r.json()
            if 'results' in data:
                for key, result in data['results'].items():
                    if 'error' not in result:
                        print("   ✅ Query successful - data is flowing!")
                        return True
                    else:
                        print(f"   ❌ Error: {result['error'][:100]}...")
        except:
            pass
    
    return False

def main():
    print("🔧 Fixing Grafana with Default Authentication")
    print("=" * 50)
    
    # Wait for Grafana
    print("⏳ Waiting for Grafana...")
    time.sleep(3)
    
    # Clean up
    delete_all_datasources()
    
    # Create datasource
    datasource = create_default_datasource()
    if not datasource:
        print("❌ Failed to create datasource")
        return 1
    
    # Test query
    test_actual_query(datasource['id'])
    
    # Create dashboard
    create_simple_dashboard(datasource['uid'])
    
    print("\n✅ Configuration complete!")
    print("\n📊 Dashboards available at:")
    print(f"   • Simple: {GRAFANA_URL}/d/ec2-cpu-simple-final")
    print(f"   • Full: {GRAFANA_URL}/d/ec2-cpu-host-network")
    print("\n⏱️ Wait 30-60 seconds for data to appear")
    print("🔄 Dashboards refresh every 30 seconds")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
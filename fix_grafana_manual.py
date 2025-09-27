#!/usr/bin/env python3
"""
Manual fix for Grafana CloudWatch access
"""

import os
import json
import time
import requests
import subprocess
import boto3
from datetime import datetime

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def get_fresh_credentials():
    """Get fresh AWS credentials"""
    print("🔑 Getting fresh AWS credentials...")
    
    try:
        # Use boto3 to get credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        creds = credentials.get_frozen_credentials()
        
        print("   ✅ Got credentials from boto3")
        return {
            "access_key": creds.access_key,
            "secret_key": creds.secret_key,
            "session_token": creds.token
        }
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def update_grafana_env(creds):
    """Update Grafana environment file"""
    print("\n📄 Updating Grafana environment...")
    
    env_content = f"""AWS_ACCESS_KEY_ID={creds['access_key']}
AWS_SECRET_ACCESS_KEY={creds['secret_key']}
AWS_SESSION_TOKEN={creds['session_token']}
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
"""
    
    with open('/home/ec2-user/sre/sre_mcp/grafana.env', 'w') as f:
        f.write(env_content)
    
    print("   ✅ Updated grafana.env with credentials")

def restart_grafana():
    """Restart Grafana container"""
    print("\n🔄 Restarting Grafana...")
    
    os.chdir('/home/ec2-user/sre/sre_mcp')
    
    # Stop
    subprocess.run(['docker-compose', 'stop', 'grafana'], capture_output=True)
    time.sleep(2)
    
    # Start  
    subprocess.run(['docker-compose', 'up', '-d', 'grafana'], capture_output=True)
    
    # Wait
    print("   ⏳ Waiting for Grafana...")
    for i in range(30):
        try:
            r = requests.get(f"{GRAFANA_URL}/api/health")
            if r.status_code == 200:
                print("   ✅ Grafana is ready")
                return True
        except:
            pass
        time.sleep(1)
    
    return False

def delete_all_datasources():
    """Delete all CloudWatch datasources"""
    print("\n🗑️  Cleaning up datasources...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
    
    if r.status_code == 200:
        for ds in r.json():
            if ds['type'] == 'cloudwatch':
                print(f"   Deleting: {ds['name']}")
                requests.delete(f"{GRAFANA_URL}/api/datasources/{ds['id']}", auth=auth)

def create_working_datasource(creds):
    """Create datasource with explicit credentials"""
    print("\n📊 Creating CloudWatch datasource...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    datasource = {
        "name": "CloudWatch-Manual",
        "type": "cloudwatch",
        "access": "proxy",
        "jsonData": {
            "authType": "keys",
            "defaultRegion": "us-east-1"
        },
        "secureJsonData": {
            "accessKey": creds['access_key'],
            "secretKey": creds['secret_key'],
            "sessionToken": creds['session_token']
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
        return result
    else:
        print(f"   ❌ Failed: {r.text}")
        return None

def test_datasource_query(ds_id):
    """Test if datasource can query"""
    print("\n🧪 Testing datasource...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # Simple test query
    test_query = {
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
        "from": str(int((datetime.now().timestamp() - 3600) * 1000)),
        "to": str(int(datetime.now().timestamp() * 1000))
    }
    
    r = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        auth=auth,
        json=test_query
    )
    
    print(f"   Query response: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        if 'results' in data:
            for key, result in data['results'].items():
                if 'error' not in result:
                    print("   ✅ Query successful!")
                    return True
                else:
                    print(f"   ❌ Query error: {result.get('error', 'Unknown')}")
    
    return False

def create_simple_dashboard(ds_uid):
    """Create a simple working dashboard"""
    print("\n📈 Creating dashboard...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    dashboard = {
        "dashboard": {
            "title": "EC2 CPU - Manual Fix",
            "uid": "ec2-cpu-manual",
            "panels": [{
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
                "title": "All EC2 Instances CPU",
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
                            "stacking": {
                                "mode": "none",
                                "group": "A"
                            },
                            "axisPlacement": "auto",
                            "axisLabel": "",
                            "axisColorMode": "text",
                            "scaleDistribution": {
                                "type": "linear"
                            },
                            "axisCenteredZero": False,
                            "hideFrom": {
                                "tooltip": False,
                                "viz": False,
                                "legend": False
                            },
                            "thresholdsStyle": {
                                "mode": "off"
                            }
                        }
                    }
                },
                "options": {
                    "tooltip": {
                        "mode": "multi",
                        "sort": "none"
                    },
                    "legend": {
                        "showLegend": True,
                        "displayMode": "table",
                        "placement": "bottom",
                        "calcs": ["last", "mean", "max"]
                    }
                }
            }],
            "schemaVersion": 39,
            "refresh": "10s",
            "time": {"from": "now-1h", "to": "now"}
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

def verify_metrics():
    """Verify CloudWatch has metrics"""
    print("\n🔍 Verifying CloudWatch metrics...")
    
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        response = cloudwatch.list_metrics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization'
        )
        
        if response['Metrics']:
            print(f"   ✅ Found {len(response['Metrics'])} CPU metrics")
            
            # Get sample data
            from datetime import datetime, timedelta
            
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
                print(f"   ✅ Latest data for {instance_id}: {latest['Average']:.2f}%")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    print("🔧 Manual Fix for Grafana CloudWatch")
    print("=" * 50)
    
    # Get credentials
    creds = get_fresh_credentials()
    if not creds:
        print("\n❌ Cannot get AWS credentials")
        return 1
    
    # Update env file
    update_grafana_env(creds)
    
    # Restart Grafana
    if not restart_grafana():
        print("\n❌ Grafana failed to start")
        return 1
    
    # Clean up
    delete_all_datasources()
    
    # Create datasource
    datasource = create_working_datasource(creds)
    if not datasource:
        print("\n❌ Failed to create datasource")
        return 1
    
    # Test it
    test_datasource_query(datasource['id'])
    
    # Create dashboard
    create_simple_dashboard(datasource['uid'])
    
    # Verify metrics exist
    verify_metrics()
    
    print("\n✅ Manual fix complete!")
    print("\n📊 Dashboard URL:")
    print(f"   {GRAFANA_URL}/d/ec2-cpu-manual")
    print("\n⏱️  Important:")
    print("   - Data should appear within 30-60 seconds")
    print("   - Time range: Last 1 hour")
    print("   - Auto-refresh: Every 10 seconds")
    print("\n⚠️  Note: AWS credentials expire in ~6 hours")
    print("   Re-run this script if data stops appearing")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
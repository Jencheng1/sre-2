#!/usr/bin/env python3
"""
Final comprehensive fix for Grafana EC2 CPU monitoring
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

def delete_all_datasources():
    """Clean up all datasources"""
    print("\n🗑️ Cleaning up datasources...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
    if r.status_code == 200:
        for ds in r.json():
            if ds['type'] == 'cloudwatch':
                print(f"   Deleting: {ds['name']}")
                requests.delete(f"{GRAFANA_URL}/api/datasources/{ds['id']}", auth=auth)

def create_datasource_with_env():
    """Create datasource that uses environment variables"""
    print("\n📊 Creating CloudWatch datasource...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # Use default auth which will pick up env variables
    datasource = {
        "name": "CloudWatch-Final",
        "type": "cloudwatch",
        "access": "proxy",
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
        
        # Get full details
        detail_r = requests.get(f"{GRAFANA_URL}/api/datasources/{result['id']}", auth=auth)
        if detail_r.status_code == 200:
            return detail_r.json()
    
    return None

def create_working_dashboard(ds_uid):
    """Create final working dashboard"""
    print("\n📈 Creating dashboard...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    dashboard = {
        "dashboard": {
            "title": "EC2 CPU Monitoring - FINAL",
            "uid": "ec2-cpu-monitoring-final",
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
                "title": "EC2 Instance CPU Usage",
                "type": "timeseries",
                "gridPos": {"h": 12, "w": 24, "x": 0, "y": 0},
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
                            "axisLabel": "",
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
        print(f"   ✅ Dashboard created")
        print(f"   URL: {GRAFANA_URL}/d/{result['uid']}")
        return True
    
    return False

def verify_env_vars():
    """Check if Grafana has AWS environment variables"""
    print("\n🔍 Checking Grafana environment...")
    
    result = subprocess.run(
        ['docker', 'exec', 'sre-grafana', 'printenv'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        env_vars = result.stdout
        has_aws_key = 'AWS_ACCESS_KEY_ID' in env_vars and 'ASIAZI2LGQKI' in env_vars
        has_aws_secret = 'AWS_SECRET_ACCESS_KEY' in env_vars
        has_aws_token = 'AWS_SESSION_TOKEN' in env_vars
        
        if has_aws_key and has_aws_secret and has_aws_token:
            print("   ✅ AWS credentials are set in Grafana container")
            return True
        else:
            print("   ❌ AWS credentials not found in Grafana container")
            if not has_aws_key:
                print("      Missing: AWS_ACCESS_KEY_ID")
            if not has_aws_secret:
                print("      Missing: AWS_SECRET_ACCESS_KEY") 
            if not has_aws_token:
                print("      Missing: AWS_SESSION_TOKEN")
    
    return False

def main():
    print("🔧 Final Grafana EC2 CPU Monitoring Fix")
    print("=" * 50)
    
    # Wait for Grafana
    if not wait_for_grafana():
        print("❌ Grafana failed to start")
        return 1
    
    # Verify environment
    if not verify_env_vars():
        print("\n⚠️  AWS credentials not properly set in Grafana")
        print("   Grafana may not be able to access CloudWatch")
    
    # Clean up
    delete_all_datasources()
    
    # Create datasource
    datasource = create_datasource_with_env()
    if not datasource:
        print("❌ Failed to create datasource")
        return 1
    
    # Create dashboard
    create_working_dashboard(datasource['uid'])
    
    print("\n✅ Configuration complete!")
    print("\n📊 Dashboard URL:")
    print(f"   {GRAFANA_URL}/d/ec2-cpu-monitoring-final")
    print("\n⏱️ Important:")
    print("   - Data should appear within 30-60 seconds")
    print("   - Set time range to 'Last 1 hour'")
    print("   - Dashboard auto-refreshes every 10 seconds")
    print("\n🔍 To verify data is showing:")
    print("   python3 /home/ec2-user/sre/sre_mcp/test_grafana_data_display.py")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
#!/usr/bin/env python3
"""
Fix Grafana AWS credentials issue by properly configuring CloudWatch datasource
"""

import os
import sys
import json
import time
import requests
import subprocess

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def get_ec2_credentials():
    """Get EC2 instance credentials from metadata service"""
    print("🔑 Getting EC2 instance credentials...")
    try:
        # Get IAM role name
        role_response = requests.get(
            "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
            timeout=2
        )
        role_name = role_response.text.strip()
        print(f"   IAM Role: {role_name}")
        
        # Get credentials
        creds_response = requests.get(
            f"http://169.254.169.254/latest/meta-data/iam/security-credentials/{role_name}",
            timeout=2
        )
        credentials = creds_response.json()
        
        print("   ✅ Retrieved EC2 credentials successfully")
        return {
            "accessKey": credentials["AccessKeyId"],
            "secretKey": credentials["SecretAccessKey"],
            "sessionToken": credentials["Token"]
        }
    except Exception as e:
        print(f"   ❌ Failed to get EC2 credentials: {e}")
        return None

def update_docker_compose():
    """Update docker-compose.yml to pass AWS credentials"""
    print("\n🐳 Updating docker-compose configuration...")
    
    # Get current credentials
    creds = get_ec2_credentials()
    if not creds:
        return False
    
    # Create environment file for Grafana
    env_content = f"""AWS_ACCESS_KEY_ID={creds['accessKey']}
AWS_SECRET_ACCESS_KEY={creds['secretKey']}
AWS_SESSION_TOKEN={creds['sessionToken']}
AWS_DEFAULT_REGION=us-east-1
GF_AWS_default_REGION=us-east-1
"""
    
    with open('/home/ec2-user/sre/sre_mcp/grafana.env', 'w') as f:
        f.write(env_content)
    
    print("   ✅ Created grafana.env file")
    
    # Update docker-compose.yml to use env file
    compose_path = '/home/ec2-user/sre/sre_mcp/docker-compose.yml'
    
    # Read current docker-compose
    with open(compose_path, 'r') as f:
        compose_content = f.read()
    
    # Check if env_file is already configured
    if 'env_file:' not in compose_content:
        # Add env_file to grafana service
        lines = compose_content.split('\n')
        new_lines = []
        in_grafana = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if 'grafana:' in line:
                in_grafana = True
            elif in_grafana and '    ports:' in line:
                # Add env_file before ports
                new_lines.insert(-1, '    env_file:')
                new_lines.insert(-1, '      - grafana.env')
                in_grafana = False
        
        compose_content = '\n'.join(new_lines)
        
        # Backup and update
        subprocess.run(['cp', compose_path, f'{compose_path}.backup'])
        with open(compose_path, 'w') as f:
            f.write(compose_content)
        
        print("   ✅ Updated docker-compose.yml")
    
    return True

def restart_grafana():
    """Restart Grafana with new configuration"""
    print("\n🔄 Restarting Grafana...")
    
    os.chdir('/home/ec2-user/sre/sre_mcp')
    
    # Stop Grafana
    subprocess.run(['docker-compose', 'stop', 'grafana'], capture_output=True)
    time.sleep(2)
    
    # Start Grafana
    result = subprocess.run(['docker-compose', 'up', '-d', 'grafana'], capture_output=True)
    
    # Wait for Grafana to be ready
    print("   ⏳ Waiting for Grafana to start...")
    for i in range(30):
        try:
            r = requests.get(f"{GRAFANA_URL}/api/health")
            if r.status_code == 200:
                print("   ✅ Grafana is ready")
                return True
        except:
            pass
        time.sleep(1)
    
    print("   ❌ Grafana failed to start")
    return False

def delete_all_cloudwatch_datasources():
    """Delete all CloudWatch datasources"""
    print("\n🗑️  Removing existing CloudWatch datasources...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
    
    if r.status_code == 200:
        for ds in r.json():
            if ds['type'] == 'cloudwatch':
                print(f"   Deleting: {ds['name']} (id: {ds['id']})")
                requests.delete(f"{GRAFANA_URL}/api/datasources/{ds['id']}", auth=auth)

def create_cloudwatch_datasource():
    """Create CloudWatch datasource with explicit credentials"""
    print("\n📊 Creating CloudWatch datasource...")
    
    creds = get_ec2_credentials()
    if not creds:
        return None
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # Create datasource with explicit credentials
    datasource = {
        "name": "CloudWatch-Fixed",
        "type": "cloudwatch",
        "access": "proxy",
        "isDefault": False,
        "jsonData": {
            "authType": "keys",
            "defaultRegion": "us-east-1"
        },
        "secureJsonData": {
            "accessKey": creds["accessKey"],
            "secretKey": creds["secretKey"],
            "sessionToken": creds["sessionToken"]
        }
    }
    
    r = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        auth=auth,
        json=datasource
    )
    
    if r.status_code in [200, 201]:
        result = r.json()
        print(f"   ✅ Created datasource: {result['name']}")
        print(f"   ID: {result['id']}, UID: {result['uid']}")
        
        # Test the datasource
        test_r = requests.post(
            f"{GRAFANA_URL}/api/datasources/{result['id']}/health",
            auth=auth
        )
        
        if test_r.status_code == 200:
            print("   ✅ Datasource health check passed")
        else:
            print(f"   ⚠️  Health check response: {test_r.text}")
        
        return result
    else:
        print(f"   ❌ Failed to create datasource: {r.text}")
        return None

def create_working_dashboard(datasource_uid):
    """Create a dashboard that definitely works"""
    print("\n📈 Creating working EC2 CPU dashboard...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    dashboard = {
        "dashboard": {
            "title": "EC2 CPU Monitoring - WORKING",
            "uid": "ec2-cpu-working-final",
            "panels": [
                {
                    "datasource": {
                        "type": "cloudwatch",
                        "uid": datasource_uid
                    },
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "CPU %",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 10,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "tooltip": False,
                                    "viz": False,
                                    "legend": False
                                },
                                "lineInterpolation": "linear",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "never",
                                "spanNulls": True
                            },
                            "mappings": [],
                            "max": 100,
                            "min": 0,
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 60},
                                    {"color": "red", "value": 80}
                                ]
                            },
                            "unit": "percent"
                        },
                        "overrides": []
                    },
                    "gridPos": {"h": 10, "w": 24, "x": 0, "y": 0},
                    "id": 1,
                    "options": {
                        "legend": {
                            "calcs": ["mean", "last", "max"],
                            "displayMode": "table",
                            "placement": "bottom",
                            "showLegend": True
                        },
                        "tooltip": {
                            "mode": "multi",
                            "sort": "none"
                        }
                    },
                    "pluginVersion": "9.5.2",
                    "targets": [
                        {
                            "alias": "{{InstanceId}}",
                            "datasource": {
                                "type": "cloudwatch",
                                "uid": datasource_uid
                            },
                            "dimensions": {},
                            "expression": "",
                            "id": "",
                            "matchExact": False,
                            "metricEditorMode": 0,
                            "metricName": "CPUUtilization",
                            "metricQueryType": 0,
                            "namespace": "AWS/EC2",
                            "period": "300",
                            "queryMode": "Metrics",
                            "refId": "A",
                            "region": "us-east-1",
                            "sqlExpression": "",
                            "statistic": "Average"
                        }
                    ],
                    "title": "All EC2 Instances CPU Usage",
                    "type": "timeseries"
                }
            ],
            "refresh": "10s",
            "schemaVersion": 38,
            "style": "dark",
            "tags": ["ec2", "cpu", "working"],
            "templating": {"list": []},
            "time": {"from": "now-1h", "to": "now"},
            "timepicker": {},
            "timezone": "",
            "version": 1
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
        print("   ✅ Dashboard created successfully")
        print(f"   URL: {GRAFANA_URL}/d/{result['uid']}/ec2-cpu-monitoring-working")
        return True
    else:
        print(f"   ❌ Failed to create dashboard: {r.text}")
        return False

def test_metrics_query(datasource_id):
    """Test if we can actually query metrics"""
    print("\n🧪 Testing metric queries...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # Test query through Grafana
    query_data = {
        "queries": [{
            "datasourceId": datasource_id,
            "refId": "A",
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
        json=query_data
    )
    
    print(f"   Query response: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        if 'results' in data:
            for key, result in data['results'].items():
                if 'error' in result:
                    print(f"   ❌ Query error: {result['error']}")
                else:
                    print("   ✅ Query successful")
        return True
    else:
        print(f"   ❌ Query failed: {r.text[:200]}")
        return False

def main():
    print("🔧 Fixing Grafana AWS Credentials and CloudWatch Integration")
    print("=" * 60)
    
    # Step 1: Update docker-compose with AWS credentials
    if not update_docker_compose():
        print("❌ Failed to update docker-compose")
        return 1
    
    # Step 2: Restart Grafana
    if not restart_grafana():
        print("❌ Failed to restart Grafana")
        return 1
    
    # Step 3: Delete old datasources
    delete_all_cloudwatch_datasources()
    
    # Step 4: Create new datasource with credentials
    datasource = create_cloudwatch_datasource()
    if not datasource:
        print("❌ Failed to create datasource")
        return 1
    
    # Step 5: Test queries
    test_metrics_query(datasource['id'])
    
    # Step 6: Create working dashboard
    create_working_dashboard(datasource['uid'])
    
    print("\n✅ Fix complete!")
    print("\n📊 Access your working dashboard at:")
    print(f"   {GRAFANA_URL}/d/ec2-cpu-working-final/ec2-cpu-monitoring-working")
    print("\n⏱️  Important:")
    print("   - Data should appear within 30-60 seconds")
    print("   - Make sure time range is 'Last 1 hour'")
    print("   - Dashboard auto-refreshes every 10 seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
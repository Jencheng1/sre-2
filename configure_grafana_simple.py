#!/usr/bin/env python3
"""Configure Grafana with CloudWatch datasource using boto3"""

import requests
import json
import time
import sys

# Grafana configuration
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def wait_for_grafana():
    """Wait for Grafana to be ready"""
    print("Waiting for Grafana to be ready...")
    for _ in range(30):
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health")
            if response.status_code == 200:
                print("✓ Grafana is ready")
                return True
        except:
            pass
        time.sleep(2)
    return False

def configure_cloudwatch_datasource():
    """Configure CloudWatch datasource with IAM role"""
    print("\nConfiguring CloudWatch datasource...")
    
    # First, check if datasource exists
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources/name/CloudWatch",
            auth=(GRAFANA_USER, GRAFANA_PASS)
        )
        if response.status_code == 200:
            # Delete existing datasource
            print("Removing existing CloudWatch datasource...")
            delete_response = requests.delete(
                f"{GRAFANA_URL}/api/datasources/name/CloudWatch",
                auth=(GRAFANA_USER, GRAFANA_PASS)
            )
    except:
        pass
    
    # Create new CloudWatch datasource with IAM role authentication
    datasource_config = {
        "name": "CloudWatch",
        "type": "cloudwatch",
        "access": "proxy",
        "jsonData": {
            "authType": "ec2_iam_role",
            "defaultRegion": "us-east-1",
            "assumeRoleArn": "",
            "externalId": ""
        }
    }
    
    response = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        data=json.dumps(datasource_config)
    )
    
    if response.status_code in [200, 201]:
        print("✓ CloudWatch datasource created successfully")
        ds_id = response.json().get('id')
        
        # Test the datasource
        test_response = requests.post(
            f"{GRAFANA_URL}/api/datasources/{ds_id}/health",
            auth=(GRAFANA_USER, GRAFANA_PASS)
        )
        
        if test_response.status_code == 200:
            print("✓ CloudWatch datasource test passed")
        else:
            print(f"⚠ CloudWatch datasource test status: {test_response.status_code}")
    else:
        print(f"✗ Failed to create CloudWatch datasource: {response.text}")
        return False
    
    return True

def import_dashboard():
    """Import the EC2 CPU monitoring dashboard"""
    print("\nImporting EC2 CPU monitoring dashboard...")
    
    # Read the dashboard JSON
    with open("/home/ec2-user/sre/sre_mcp/grafana/dashboards/ec2-cpu-monitoring.json", "r") as f:
        dashboard_json = json.load(f)
    
    # Create import payload
    import_payload = {
        "dashboard": dashboard_json,
        "overwrite": True,
        "inputs": [
            {
                "name": "DS_CLOUDWATCH",
                "type": "datasource",
                "pluginId": "cloudwatch",
                "value": "CloudWatch"
            },
            {
                "name": "DS_PROMETHEUS",
                "type": "datasource",
                "pluginId": "prometheus",
                "value": "Prometheus"
            }
        ]
    }
    
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/import",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        data=json.dumps(import_payload)
    )
    
    if response.status_code == 200:
        print("✓ Dashboard imported successfully")
        dashboard_uid = response.json().get('uid')
        print(f"  Dashboard URL: {GRAFANA_URL}/d/{dashboard_uid}/ec2-cpu-monitoring")
        return True
    else:
        print(f"✗ Failed to import dashboard: {response.text}")
        return False

def main():
    print("=== Grafana Configuration Script ===")
    
    if not wait_for_grafana():
        print("✗ Grafana is not ready. Please ensure it's running.")
        sys.exit(1)
    
    # Configure datasource
    if configure_cloudwatch_datasource():
        # Import dashboard
        import_dashboard()
        
        print("\n✅ Configuration complete!")
        print(f"Access Grafana at: {GRAFANA_URL}")
        print("Username: admin")
        print("Password: admin123")
        print("\nAvailable dashboards:")
        print("- EC2 CPU Monitoring")
        print("- Node Exporter (Local CPU)")
    else:
        print("\n✗ Configuration failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Reconfigure CloudWatch datasource to ensure it works properly"""

import requests
import json
import time

# Grafana configuration
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def delete_cloudwatch_datasources():
    """Delete all existing CloudWatch datasources"""
    print("🗑️  Removing existing CloudWatch datasources...")
    
    response = requests.get(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASS)
    )
    
    if response.status_code == 200:
        datasources = response.json()
        for ds in datasources:
            if ds['type'] == 'cloudwatch':
                print(f"   Deleting: {ds['name']} (id: {ds['id']})")
                delete_response = requests.delete(
                    f"{GRAFANA_URL}/api/datasources/{ds['id']}",
                    auth=(GRAFANA_USER, GRAFANA_PASS)
                )
                if delete_response.status_code == 200:
                    print("   ✓ Deleted successfully")
                else:
                    print(f"   ✗ Failed to delete: {delete_response.text}")

def create_cloudwatch_datasource():
    """Create a new CloudWatch datasource with proper configuration"""
    print("\n📊 Creating new CloudWatch datasource...")
    
    # CloudWatch datasource configuration for EC2 IAM role
    datasource_config = {
        "name": "CloudWatch",
        "type": "cloudwatch",
        "access": "proxy",
        "isDefault": False,
        "jsonData": {
            "authType": "ec2_iam_role",
            "defaultRegion": "us-east-1",
            "assumeRoleArn": "",
            "externalId": "",
            "endpoint": "",
            "customMetricsNamespaces": "",
            "logsTimeout": "30m"
        },
        "secureJsonFields": {},
        "version": 1,
        "readOnly": False
    }
    
    response = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        data=json.dumps(datasource_config)
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print("   ✓ CloudWatch datasource created successfully")
        print(f"   ID: {result.get('id')}")
        print(f"   UID: {result.get('uid')}")
        
        # Wait a moment for datasource to initialize
        time.sleep(2)
        
        # Test the datasource
        test_datasource(result.get('id'))
        
        return result.get('uid')
    else:
        print(f"   ✗ Failed to create datasource: {response.text}")
        return None

def test_datasource(datasource_id):
    """Test the CloudWatch datasource"""
    print("\n🧪 Testing CloudWatch datasource...")
    
    # Method 1: Health check
    health_response = requests.post(
        f"{GRAFANA_URL}/api/datasources/{datasource_id}/health",
        auth=(GRAFANA_USER, GRAFANA_PASS)
    )
    
    print(f"   Health check status: {health_response.status_code}")
    if health_response.status_code == 200:
        print("   ✓ Datasource is healthy")
    else:
        print(f"   Health response: {health_response.text}")
    
    # Method 2: Test query
    print("\n📈 Testing metric query...")
    test_response = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        data=json.dumps({
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
        })
    )
    
    print(f"   Query test status: {test_response.status_code}")
    if test_response.status_code == 200:
        print("   ✓ Query test successful")
    else:
        print(f"   Query response: {test_response.text}")

def update_dashboard_datasource(cloudwatch_uid):
    """Update the dashboard to use the new datasource"""
    print("\n🔄 Updating dashboard datasource references...")
    
    # Get the fixed dashboard
    response = requests.get(
        f"{GRAFANA_URL}/api/dashboards/uid/ec2-cpu-monitoring-fixed",
        auth=(GRAFANA_USER, GRAFANA_PASS)
    )
    
    if response.status_code == 200:
        dashboard_data = response.json()
        dashboard = dashboard_data['dashboard']
        
        # Update all CloudWatch datasource references
        for panel in dashboard.get('panels', []):
            if panel.get('datasource', {}).get('type') == 'cloudwatch':
                panel['datasource']['uid'] = cloudwatch_uid
                
            for target in panel.get('targets', []):
                if target.get('datasource', {}).get('type') == 'cloudwatch':
                    target['datasource']['uid'] = cloudwatch_uid
        
        # Save the updated dashboard
        update_payload = {
            "dashboard": dashboard,
            "overwrite": True,
            "message": "Updated datasource references"
        }
        
        update_response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            auth=(GRAFANA_USER, GRAFANA_PASS),
            headers={"Content-Type": "application/json"},
            data=json.dumps(update_payload)
        )
        
        if update_response.status_code in [200, 201]:
            print("   ✓ Dashboard updated successfully")
        else:
            print(f"   ✗ Failed to update dashboard: {update_response.text}")

def main():
    print("🔧 Reconfiguring CloudWatch Datasource")
    print("=" * 50)
    
    # Step 1: Delete existing CloudWatch datasources
    delete_cloudwatch_datasources()
    
    # Step 2: Create new CloudWatch datasource
    cloudwatch_uid = create_cloudwatch_datasource()
    
    if cloudwatch_uid:
        # Step 3: Update dashboard
        update_dashboard_datasource(cloudwatch_uid)
        
        print("\n✅ CloudWatch datasource reconfiguration complete!")
        print("\n📊 Next steps:")
        print("1. Go to Grafana: http://localhost:3000")
        print("2. Navigate to 'EC2 CPU Monitoring - Fixed' dashboard")
        print("3. CPU metrics should now be displaying correctly")
        print("\nIf metrics still don't appear:")
        print("- Wait 1-2 minutes for data to populate")
        print("- Try refreshing the dashboard (F5)")
        print("- Check time range is set to 'Last 30 minutes'")
    else:
        print("\n❌ Failed to reconfigure CloudWatch datasource")

if __name__ == "__main__":
    main()
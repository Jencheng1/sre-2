#!/usr/bin/env python3
"""
Test that verifies Grafana is actually displaying EC2 CPU data
"""

import requests
import json
import time
import boto3
from datetime import datetime, timedelta

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def test_grafana_data_display():
    """Comprehensive test for data display"""
    print("🧪 Testing Grafana EC2 CPU Data Display")
    print("=" * 50)
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # 1. Check Grafana health
    print("\n1️⃣ Testing Grafana health...")
    r = requests.get(f"{GRAFANA_URL}/api/health")
    if r.status_code == 200:
        print("   ✅ Grafana is healthy")
    else:
        print("   ❌ Grafana is not accessible")
        return False
    
    # 2. Get CloudWatch datasource
    print("\n2️⃣ Finding CloudWatch datasource...")
    r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
    
    datasource = None
    if r.status_code == 200:
        for ds in r.json():
            if ds['type'] == 'cloudwatch':
                datasource = ds
                print(f"   ✅ Found: {ds['name']} (ID: {ds['id']}, UID: {ds['uid']})")
                break
    
    if not datasource:
        print("   ❌ No CloudWatch datasource found")
        return False
    
    # 3. Test datasource with actual query
    print("\n3️⃣ Testing datasource query...")
    
    # Get current timestamp in milliseconds
    now = int(datetime.now().timestamp() * 1000)
    hour_ago = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
    
    query = {
        "queries": [{
            "refId": "A",
            "datasourceId": datasource['id'],
            "intervalMs": 60000,
            "maxDataPoints": 960,
            "region": "us-east-1",
            "namespace": "AWS/EC2",
            "metricName": "CPUUtilization",
            "dimensions": {},
            "statistic": "Average",
            "period": "300",
            "expression": "",
            "id": "",
            "alias": "",
            "matchExact": False,
            "metricQueryType": 0,
            "metricEditorMode": 0,
            "queryMode": "Metrics"
        }],
        "from": str(hour_ago),
        "to": str(now),
    }
    
    r = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        auth=auth,
        json=query,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Response status: {r.status_code}")
    
    has_data = False
    if r.status_code == 200:
        try:
            response_data = r.json()
            
            if 'results' in response_data:
                for key, result in response_data['results'].items():
                    if 'error' in result:
                        print(f"   ❌ Query error: {result['error']}")
                    elif 'frames' in result and result['frames']:
                        # Check if frames have data
                        for frame in result['frames']:
                            if 'data' in frame and frame['data'].get('values'):
                                values = frame['data']['values']
                                if len(values) > 0 and len(values[0]) > 0:
                                    has_data = True
                                    print(f"   ✅ Data found: {len(values[0])} data points")
                                    break
                    elif 'series' in result and result['series']:
                        has_data = True
                        print(f"   ✅ Data found: {len(result['series'])} series")
        except Exception as e:
            print(f"   ❌ Error parsing response: {e}")
    else:
        print(f"   ❌ Query failed: {r.text[:200]}")
    
    # 4. Check specific dashboard
    print("\n4️⃣ Checking dashboard configuration...")
    
    dashboards_to_check = [
        'ec2-cpu-manual',
        'ec2-cpu-final', 
        'ec2-cpu-working-v2'
    ]
    
    dashboard_found = False
    for dash_uid in dashboards_to_check:
        r = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{dash_uid}", auth=auth)
        
        if r.status_code == 200:
            dashboard_found = True
            dash_data = r.json()
            dashboard = dash_data['dashboard']
            
            print(f"   ✅ Found dashboard: {dashboard['title']}")
            
            # Check panels
            if 'panels' in dashboard:
                for panel in dashboard['panels']:
                    if panel.get('datasource', {}).get('uid') == datasource['uid']:
                        print(f"      ✓ Panel '{panel.get('title', 'Untitled')}' uses correct datasource")
            break
    
    if not dashboard_found:
        print("   ❌ No configured dashboards found")
    
    # 5. Verify CloudWatch has data
    print("\n5️⃣ Verifying CloudWatch has data...")
    
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Get metrics
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            StartTime=datetime.utcnow() - timedelta(hours=1),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=['Average']
        )
        
        if response['Datapoints']:
            print(f"   ✅ CloudWatch has {len(response['Datapoints'])} data points")
            latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
            print(f"      Latest: {latest['Average']:.2f}% at {latest['Timestamp']}")
        else:
            print("   ❌ No data in CloudWatch")
            
    except Exception as e:
        print(f"   ❌ CloudWatch error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if has_data:
        print("\n✅ SUCCESS: Grafana is displaying EC2 CPU data!")
        print("\n📊 Dashboard URLs:")
        print(f"   - {GRAFANA_URL}/d/ec2-cpu-manual")
        print(f"   - {GRAFANA_URL}/d/ec2-cpu-final")
        print(f"   - {GRAFANA_URL}/d/ec2-cpu-working-v2")
        print("\n💡 Tips:")
        print("   - Ensure time range is 'Last 1 hour' or more")
        print("   - Dashboard should auto-refresh every 10-30 seconds")
        print("   - Data updates every 5 minutes (CloudWatch period)")
    else:
        print("\n❌ FAILED: No data is being displayed in Grafana")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check Grafana logs: docker logs sre-grafana --tail 50")
        print("2. Verify credentials: cat /home/ec2-user/sre/sre_mcp/grafana.env")
        print("3. Re-run fix: python3 /home/ec2-user/sre/sre_mcp/fix_grafana_manual.py")
        print("4. Check AWS access: aws sts get-caller-identity")
        print("5. Restart Grafana: docker-compose restart grafana")
    
    return has_data

def main():
    """Run the test"""
    import sys
    
    success = test_grafana_data_display()
    
    # Save test result
    result = {
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "grafana_url": GRAFANA_URL
    }
    
    with open(f"grafana_data_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
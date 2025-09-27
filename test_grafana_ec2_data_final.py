#!/usr/bin/env python3
"""
Final test to verify EC2 CPU data is displaying in Grafana
"""

import requests
import json
import time
import boto3
from datetime import datetime, timedelta

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def test_grafana_ec2_cpu_data():
    """Comprehensive test for EC2 CPU data in Grafana"""
    print("🧪 Final Test: EC2 CPU Data in Grafana")
    print("=" * 60)
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    all_tests_passed = True
    
    # 1. Check Grafana health
    print("\n1️⃣ Grafana Health Check...")
    r = requests.get(f"{GRAFANA_URL}/api/health")
    if r.status_code == 200:
        print("   ✅ Grafana is healthy")
    else:
        print("   ❌ Grafana is not accessible")
        all_tests_passed = False
    
    # 2. Check datasource
    print("\n2️⃣ CloudWatch Datasource Check...")
    r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
    
    datasource = None
    if r.status_code == 200:
        datasources = r.json()
        for ds in datasources:
            if ds['type'] == 'cloudwatch':
                datasource = ds
                print(f"   ✅ Found: {ds['name']}")
                print(f"      Type: {ds['type']}")
                print(f"      Auth: {ds.get('jsonData', {}).get('authType', 'unknown')}")
                break
    
    if not datasource:
        print("   ❌ No CloudWatch datasource found")
        all_tests_passed = False
    
    # 3. Test actual data query
    print("\n3️⃣ Testing Data Query...")
    
    if datasource:
        # Query for all EC2 CPU metrics
        query = {
            "queries": [{
                "refId": "A",
                "datasourceId": datasource['id'],
                "region": "us-east-1",
                "namespace": "AWS/EC2",
                "metricName": "CPUUtilization",
                "dimensions": {},
                "statistic": "Average",
                "period": "300",
                "queryMode": "Metrics"
            }],
            "from": "now-1h",
            "to": "now"
        }
        
        r = requests.post(
            f"{GRAFANA_URL}/api/ds/query",
            auth=auth,
            json=query
        )
        
        has_data = False
        if r.status_code == 200:
            try:
                response_data = r.json()
                
                if 'results' in response_data:
                    for key, result in response_data['results'].items():
                        if 'error' in result:
                            print(f"   ❌ Query error: {result['error'][:100]}...")
                            all_tests_passed = False
                        elif 'frames' in result and result['frames']:
                            # Check frames for data
                            for frame in result['frames']:
                                if 'data' in frame and frame['data'].get('values'):
                                    values = frame['data']['values']
                                    if len(values) > 0 and len(values[0]) > 0:
                                        has_data = True
                                        print(f"   ✅ Data retrieved: {len(values[0])} data points")
                                        
                                        # Show sample data
                                        if 'fields' in frame:
                                            for field in frame['fields']:
                                                if field.get('name') and 'i-' in field.get('name', ''):
                                                    print(f"      Instance: {field['name']}")
                                                    break
                                        break
                        elif 'series' in result and result['series']:
                            has_data = True
                            print(f"   ✅ Data retrieved: {len(result['series'])} series")
                            for series in result['series'][:2]:
                                if 'name' in series:
                                    print(f"      Series: {series['name']}")
            except Exception as e:
                print(f"   ❌ Error parsing response: {e}")
                all_tests_passed = False
        else:
            print(f"   ❌ Query failed with status: {r.status_code}")
            all_tests_passed = False
        
        if not has_data:
            print("   ⚠️  No data returned from query")
            all_tests_passed = False
    
    # 4. Check dashboard
    print("\n4️⃣ Dashboard Check...")
    
    r = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/ec2-cpu-host-network", auth=auth)
    
    if r.status_code == 200:
        dash_data = r.json()
        dashboard = dash_data['dashboard']
        print(f"   ✅ Dashboard found: {dashboard['title']}")
        print(f"      Panels: {len(dashboard.get('panels', []))}")
        print(f"      Tags: {', '.join(dashboard.get('tags', []))}")
    else:
        print("   ❌ Dashboard not found")
        all_tests_passed = False
    
    # 5. Verify CloudWatch has recent data
    print("\n5️⃣ CloudWatch Data Verification...")
    
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Get recent metrics
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            StartTime=datetime.utcnow() - timedelta(minutes=30),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=['Average']
        )
        
        if response['Datapoints']:
            print(f"   ✅ CloudWatch has {len(response['Datapoints'])} recent data points")
            latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
            time_diff = datetime.utcnow() - latest['Timestamp'].replace(tzinfo=None)
            print(f"      Latest data: {time_diff.total_seconds()/60:.0f} minutes ago")
            print(f"      Value: {latest['Average']:.2f}%")
        else:
            print("   ⚠️  No recent data in CloudWatch")
            
    except Exception as e:
        print(f"   ❌ CloudWatch error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if all_tests_passed and has_data:
        print("\n✅ SUCCESS: EC2 CPU data is displaying in Grafana!")
        print("\n🎉 Everything is working correctly!")
        print(f"\n📊 View your dashboard at:")
        print(f"   {GRAFANA_URL}/d/ec2-cpu-host-network")
        print("\n💡 Features:")
        print("   • Real-time EC2 CPU metrics for all instances")
        print("   • Auto-refresh every 10 seconds")
        print("   • Individual instance CPU gauges")
        print("   • Historical data for the last hour")
    else:
        print("\n❌ FAILED: Issues detected")
        print("\n🔧 Troubleshooting:")
        print("1. Check Grafana logs: docker logs sre-grafana --tail 50")
        print("2. Verify host network: docker inspect sre-grafana | grep -i network")
        print("3. Test metadata: curl http://169.254.169.254/latest/meta-data/instance-id")
        print("4. Re-run configuration: python3 configure_grafana_with_host_network.py")
    
    return all_tests_passed and has_data

def save_test_report(success):
    """Save test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test": "EC2 CPU Data in Grafana",
        "success": success,
        "grafana_url": GRAFANA_URL,
        "dashboard_url": f"{GRAFANA_URL}/d/ec2-cpu-host-network"
    }
    
    filename = f"grafana_ec2_final_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Test report saved to: {filename}")

def main():
    """Run the test"""
    success = test_grafana_ec2_cpu_data()
    save_test_report(success)
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
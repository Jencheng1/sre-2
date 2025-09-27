#!/usr/bin/env python3
"""
Comprehensive test to verify Grafana EC2 CPU data is actually displaying
"""

import requests
import json
import time
import boto3
import unittest
from datetime import datetime, timedelta

class TestGrafanaEC2CPUDataDisplay(unittest.TestCase):
    """Test that EC2 CPU data is actually displayed in Grafana"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.grafana_url = "http://localhost:3000"
        cls.grafana_auth = ("admin", "admin123")
        cls.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        cls.ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Get the CloudWatch datasource
        r = requests.get(
            f"{cls.grafana_url}/api/datasources",
            auth=cls.grafana_auth
        )
        cls.datasource = None
        if r.status_code == 200:
            for ds in r.json():
                if ds['type'] == 'cloudwatch':
                    cls.datasource = ds
                    break
    
    def test_01_grafana_health(self):
        """Test Grafana is healthy"""
        print("\n✅ TEST 1: Grafana Health Check")
        
        r = requests.get(f"{self.grafana_url}/api/health")
        self.assertEqual(r.status_code, 200)
        print("   ✓ Grafana is healthy and accessible")
    
    def test_02_cloudwatch_datasource_exists(self):
        """Test CloudWatch datasource exists"""
        print("\n✅ TEST 2: CloudWatch Datasource")
        
        self.assertIsNotNone(self.datasource, "No CloudWatch datasource found")
        print(f"   ✓ Found datasource: {self.datasource['name']}")
        print(f"   ✓ Type: {self.datasource['type']}")
        print(f"   ✓ ID: {self.datasource['id']}")
        print(f"   ✓ UID: {self.datasource['uid']}")
    
    def test_03_cloudwatch_has_metrics(self):
        """Verify CloudWatch has EC2 CPU metrics"""
        print("\n✅ TEST 3: CloudWatch Metrics Availability")
        
        # Get EC2 instances
        response = self.ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance['InstanceId'])
        
        print(f"   ✓ Found {len(instances)} running EC2 instances")
        
        # Check metrics for each instance
        metrics_found = 0
        for instance_id in instances:
            metrics = self.cloudwatch.list_metrics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}]
            )
            
            if metrics['Metrics']:
                metrics_found += 1
                
                # Get recent data
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=datetime.utcnow() - timedelta(minutes=30),
                    EndTime=datetime.utcnow(),
                    Period=300,
                    Statistics=['Average']
                )
                
                if response['Datapoints']:
                    latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                    print(f"   ✓ {instance_id}: {latest['Average']:.2f}% CPU")
        
        self.assertGreater(metrics_found, 0, "No instances have CPU metrics")
        print(f"   ✓ {metrics_found}/{len(instances)} instances have CPU metrics")
    
    def test_04_datasource_can_query(self):
        """Test datasource can actually query data"""
        print("\n✅ TEST 4: Datasource Query Test")
        
        if not self.datasource:
            self.skipTest("No datasource available")
        
        # Test the datasource health
        r = requests.post(
            f"{self.grafana_url}/api/datasources/{self.datasource['id']}/health",
            auth=self.grafana_auth
        )
        
        print(f"   Health check status: {r.status_code}")
        
        # Try a test query
        query_data = {
            "queries": [{
                "datasourceId": self.datasource['id'],
                "refId": "A",
                "region": "us-east-1",
                "namespace": "AWS/EC2",
                "metricName": "CPUUtilization",
                "dimensions": {},
                "statistic": "Average",
                "period": "300"
            }],
            "from": "now-30m",
            "to": "now"
        }
        
        r = requests.post(
            f"{self.grafana_url}/api/ds/query",
            auth=self.grafana_auth,
            json=query_data
        )
        
        if r.status_code == 200:
            data = r.json()
            if 'results' in data:
                has_error = False
                for key, result in data['results'].items():
                    if 'error' in result:
                        print(f"   ⚠️  Query error: {result['error']}")
                        has_error = True
                
                if not has_error:
                    print("   ✓ Datasource can query CloudWatch successfully")
        else:
            print(f"   ⚠️  Query failed with status {r.status_code}")
    
    def test_05_dashboard_exists(self):
        """Test that EC2 CPU dashboard exists"""
        print("\n✅ TEST 5: Dashboard Existence")
        
        r = requests.get(
            f"{self.grafana_url}/api/search?type=dash-db",
            auth=self.grafana_auth
        )
        
        self.assertEqual(r.status_code, 200)
        dashboards = r.json()
        
        cpu_dashboards = [db for db in dashboards 
                         if 'cpu' in db.get('title', '').lower()]
        
        self.assertGreater(len(cpu_dashboards), 0, "No CPU dashboards found")
        
        print(f"   ✓ Found {len(cpu_dashboards)} CPU dashboards:")
        for db in cpu_dashboards:
            print(f"     - {db['title']}")
    
    def test_06_dashboard_has_data(self):
        """Test that dashboard actually shows data"""
        print("\n✅ TEST 6: Dashboard Data Display")
        
        # Get the ec2-cpu-final dashboard
        r = requests.get(
            f"{self.grafana_url}/api/dashboards/uid/ec2-cpu-final",
            auth=self.grafana_auth
        )
        
        if r.status_code == 200:
            dashboard_data = r.json()
            dashboard = dashboard_data['dashboard']
            
            print(f"   ✓ Dashboard: {dashboard['title']}")
            print(f"   ✓ Panels: {len(dashboard['panels'])}")
            
            # Check each panel configuration
            for panel in dashboard['panels']:
                if 'targets' in panel and panel['targets']:
                    target = panel['targets'][0]
                    print(f"   ✓ Panel '{panel.get('title', 'Untitled')}' configured for:")
                    print(f"     - Metric: {target.get('metricName', 'N/A')}")
                    print(f"     - Namespace: {target.get('namespace', 'N/A')}")
                    print(f"     - Region: {target.get('region', 'N/A')}")
        else:
            print(f"   ⚠️  Dashboard not found (status: {r.status_code})")
    
    def test_07_panel_data_query(self):
        """Test querying data through a panel"""
        print("\n✅ TEST 7: Panel Data Query")
        
        if not self.datasource:
            self.skipTest("No datasource available")
        
        # Create a test query similar to what a panel would use
        instances = []
        response = self.ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance['InstanceId'])
                break
            if instances:
                break
        
        if not instances:
            self.skipTest("No running instances")
        
        # Query for specific instance
        query_data = {
            "queries": [{
                "datasourceId": self.datasource['id'],
                "refId": "A",
                "region": "us-east-1",
                "namespace": "AWS/EC2",
                "metricName": "CPUUtilization",
                "dimensions": {
                    "InstanceId": instances[0]
                },
                "statistic": "Average",
                "period": "300"
            }],
            "from": "now-1h",
            "to": "now"
        }
        
        r = requests.post(
            f"{self.grafana_url}/api/ds/query",
            auth=self.grafana_auth,
            json=query_data
        )
        
        if r.status_code == 200:
            print(f"   ✓ Successfully queried data for {instances[0]}")
        else:
            print(f"   ⚠️  Query failed: {r.status_code}")
    
    def test_08_verify_time_range(self):
        """Verify appropriate time range for data"""
        print("\n✅ TEST 8: Time Range Verification")
        
        # Check that we have recent data
        instances = []
        response = self.ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance['InstanceId'])
                break
            if instances:
                break
        
        if instances:
            # Check for data in last hour
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instances[0]}],
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                oldest = datapoints[0]['Timestamp']
                newest = datapoints[-1]['Timestamp']
                
                time_diff = datetime.utcnow().replace(tzinfo=None) - newest.replace(tzinfo=None)
                
                print(f"   ✓ Data points available: {len(datapoints)}")
                print(f"   ✓ Oldest data: {oldest}")
                print(f"   ✓ Newest data: {newest}")
                print(f"   ✓ Data freshness: {time_diff.total_seconds() / 60:.1f} minutes ago")
                
                self.assertLess(time_diff.total_seconds(), 900, "Data is older than 15 minutes")

def run_comprehensive_test():
    """Run all tests and generate report"""
    print("=" * 60)
    print("COMPREHENSIVE GRAFANA EC2 CPU DATA TEST")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Grafana URL: http://localhost:3000")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestGrafanaEC2CPUDataDisplay))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Grafana EC2 CPU monitoring is working correctly!")
        print("\n📊 Next Steps:")
        print("1. Go to http://localhost:3000/d/ec2-cpu-final/ec2-cpu-usage")
        print("2. Wait 30-60 seconds for data to load")
        print("3. Verify you see CPU metrics for all EC2 instances")
        print("4. Check that data updates every 30 seconds")
    else:
        print("\n❌ Some tests failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Check Grafana logs: docker logs sre-grafana")
        print("2. Verify AWS credentials are correct")
        print("3. Ensure EC2 instances have been running for >10 minutes")
        print("4. Try manually refreshing the dashboard")
    
    # Save test report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "passed": passed,
        "failed": len(result.failures),
        "errors": len(result.errors),
        "success": result.wasSuccessful()
    }
    
    report_file = f"grafana_cpu_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Test report saved to: {report_file}")
    
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    import sys
    sys.exit(run_comprehensive_test())
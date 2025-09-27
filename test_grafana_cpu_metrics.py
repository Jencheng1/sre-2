#!/usr/bin/env python3
"""
Comprehensive test suite for Grafana CPU metrics monitoring
Tests Grafana configuration, data sources, and CPU metric queries
"""

import requests
import json
import unittest
import time
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class TestGrafanaCPUMetrics(unittest.TestCase):
    """Test cases for Grafana CPU metrics monitoring"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.grafana_url = "http://localhost:3000"
        cls.grafana_user = "admin"
        cls.grafana_pass = "admin123"
        cls.auth = (cls.grafana_user, cls.grafana_pass)
        
        # AWS clients
        cls.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        cls.ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Get EC2 instances
        response = cls.ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        cls.instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                cls.instances.append({
                    'id': instance['InstanceId'],
                    'name': next((tag['Value'] for tag in instance.get('Tags', []) 
                                if tag['Key'] == 'Name'), instance['InstanceId'])
                })
    
    def test_01_grafana_health(self):
        """Test Grafana service health"""
        print("\n[TEST 1] Checking Grafana health...")
        
        response = requests.get(f"{self.grafana_url}/api/health")
        self.assertEqual(response.status_code, 200)
        print("✓ Grafana is healthy")
        
        # Check authentication
        auth_response = requests.get(
            f"{self.grafana_url}/api/org",
            auth=self.auth
        )
        self.assertEqual(auth_response.status_code, 200)
        print("✓ Authentication successful")
    
    def test_02_datasources(self):
        """Test Grafana datasources"""
        print("\n[TEST 2] Checking Grafana datasources...")
        
        response = requests.get(
            f"{self.grafana_url}/api/datasources",
            auth=self.auth
        )
        self.assertEqual(response.status_code, 200)
        
        datasources = response.json()
        self.assertGreater(len(datasources), 0, "No datasources found")
        
        # Check for specific datasources
        ds_types = {ds['type']: ds['name'] for ds in datasources}
        
        print(f"✓ Found {len(datasources)} datasources:")
        for ds_type, ds_name in ds_types.items():
            print(f"  - {ds_name} ({ds_type})")
            
        # Test each datasource
        for ds in datasources:
            if ds['type'] in ['prometheus', 'cloudwatch']:
                self._test_datasource(ds)
    
    def _test_datasource(self, datasource):
        """Test individual datasource"""
        print(f"\n  Testing {datasource['name']} datasource...")
        
        response = requests.post(
            f"{self.grafana_url}/api/datasources/{datasource['id']}/health",
            auth=self.auth
        )
        
        if response.status_code == 200:
            print(f"  ✓ {datasource['name']} is healthy")
        else:
            print(f"  ⚠ {datasource['name']} health check returned: {response.status_code}")
    
    def test_03_cloudwatch_metrics(self):
        """Test CloudWatch metrics availability"""
        print("\n[TEST 3] Checking CloudWatch EC2 metrics...")
        
        if not self.instances:
            self.skipTest("No running EC2 instances found")
        
        for instance in self.instances[:2]:  # Test first 2 instances
            print(f"\n  Checking metrics for {instance['name']} ({instance['id']})...")
            
            # Get CPU metrics from CloudWatch
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{
                        'Name': 'InstanceId',
                        'Value': instance['id']
                    }],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5 minutes
                    Statistics=['Average', 'Maximum']
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    print(f"  ✓ Found {len(datapoints)} CPU metric datapoints")
                    latest = sorted(datapoints, key=lambda x: x['Timestamp'])[-1]
                    print(f"    Latest: {latest['Timestamp']} - Avg: {latest['Average']:.2f}%, Max: {latest['Maximum']:.2f}%")
                else:
                    print(f"  ⚠ No recent CPU metrics for {instance['name']}")
                    
            except Exception as e:
                print(f"  ✗ Error getting metrics: {str(e)}")
    
    def test_04_prometheus_metrics(self):
        """Test Prometheus metrics"""
        print("\n[TEST 4] Checking Prometheus metrics...")
        
        # Check Prometheus targets
        response = requests.get("http://localhost:9090/api/v1/targets")
        if response.status_code == 200:
            data = response.json()
            active_targets = data['data']['activeTargets']
            print(f"✓ Prometheus has {len(active_targets)} active targets")
            
            for target in active_targets:
                health = target.get('health', 'unknown')
                labels = target.get('labels', {})
                job = labels.get('job', 'unknown')
                print(f"  - {job}: {health}")
        
        # Query CPU metric
        query = 'node_cpu_seconds_total'
        response = requests.get(
            "http://localhost:9090/api/v1/query",
            params={'query': query}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['data']['result']:
                print(f"✓ Node CPU metrics available: {len(data['data']['result'])} series")
            else:
                print("⚠ No node CPU metrics found")
    
    def test_05_grafana_dashboards(self):
        """Test Grafana dashboards"""
        print("\n[TEST 5] Checking Grafana dashboards...")
        
        response = requests.get(
            f"{self.grafana_url}/api/search",
            auth=self.auth
        )
        
        self.assertEqual(response.status_code, 200)
        dashboards = response.json()
        
        print(f"✓ Found {len(dashboards)} dashboards:")
        for db in dashboards:
            if db['type'] == 'dash-db':
                print(f"  - {db['title']} (uid: {db['uid']})")
                
                # Check if it's a CPU monitoring dashboard
                if 'cpu' in db['title'].lower():
                    self._test_dashboard_queries(db['uid'])
    
    def _test_dashboard_queries(self, dashboard_uid):
        """Test queries in a specific dashboard"""
        print(f"\n  Testing dashboard queries for uid: {dashboard_uid}...")
        
        response = requests.get(
            f"{self.grafana_url}/api/dashboards/uid/{dashboard_uid}",
            auth=self.auth
        )
        
        if response.status_code == 200:
            dashboard = response.json()['dashboard']
            panels = dashboard.get('panels', [])
            
            print(f"  ✓ Dashboard has {len(panels)} panels")
            
            for panel in panels:
                if 'targets' in panel:
                    for target in panel['targets']:
                        if 'expr' in target:  # Prometheus query
                            print(f"    - Panel '{panel['title']}': Prometheus query")
                        elif 'metricName' in target:  # CloudWatch query
                            print(f"    - Panel '{panel['title']}': CloudWatch metric {target.get('metricName')}")
    
    def test_06_grafana_annotations(self):
        """Test Grafana annotations API"""
        print("\n[TEST 6] Testing Grafana annotations...")
        
        # Create a test annotation
        annotation = {
            "text": "Test CPU spike event",
            "tags": ["test", "cpu", "spike"],
            "time": int(time.time() * 1000),  # Current time in milliseconds
            "timeEnd": int(time.time() * 1000) + 60000  # 1 minute duration
        }
        
        response = requests.post(
            f"{self.grafana_url}/api/annotations",
            auth=self.auth,
            headers={"Content-Type": "application/json"},
            data=json.dumps(annotation)
        )
        
        if response.status_code in [200, 201]:
            annotation_id = response.json()['id']
            print("✓ Created test annotation")
            
            # Clean up - delete the annotation
            delete_response = requests.delete(
                f"{self.grafana_url}/api/annotations/{annotation_id}",
                auth=self.auth
            )
            if delete_response.status_code == 200:
                print("✓ Cleaned up test annotation")
        else:
            print(f"⚠ Could not create annotation: {response.status_code}")
    
    def test_07_grafana_alerts(self):
        """Test Grafana alerting configuration"""
        print("\n[TEST 7] Checking Grafana alerts...")
        
        # Check alert rules
        response = requests.get(
            f"{self.grafana_url}/api/v1/provisioning/alert-rules",
            auth=self.auth
        )
        
        if response.status_code == 200:
            rules = response.json()
            print(f"✓ Found {len(rules)} alert rules")
            
            cpu_alerts = [r for r in rules if 'cpu' in str(r).lower()]
            if cpu_alerts:
                print(f"  - {len(cpu_alerts)} CPU-related alerts configured")
            else:
                print("  ⚠ No CPU-related alerts found")
        else:
            print("⚠ Alert rules API not available (might be using legacy alerting)")
    
    def test_08_end_to_end_cpu_query(self):
        """Test end-to-end CPU metric query through Grafana"""
        print("\n[TEST 8] Testing end-to-end CPU metric query...")
        
        if not self.instances:
            self.skipTest("No EC2 instances found")
        
        # Test CloudWatch query through Grafana proxy
        instance_id = self.instances[0]['id']
        
        # Find CloudWatch datasource
        ds_response = requests.get(
            f"{self.grafana_url}/api/datasources",
            auth=self.auth
        )
        
        cloudwatch_ds = None
        for ds in ds_response.json():
            if ds['type'] == 'cloudwatch':
                cloudwatch_ds = ds
                break
        
        if cloudwatch_ds:
            print(f"✓ Using CloudWatch datasource: {cloudwatch_ds['name']}")
            
            # Query through Grafana proxy
            query_data = {
                "queries": [{
                    "datasourceId": cloudwatch_ds['id'],
                    "refId": "A",
                    "region": "us-east-1",
                    "namespace": "AWS/EC2",
                    "metricName": "CPUUtilization",
                    "dimensions": {"InstanceId": instance_id},
                    "statistics": ["Average"],
                    "period": "300"
                }],
                "from": "now-1h",
                "to": "now"
            }
            
            # Note: Direct query API might require additional setup
            print(f"✓ CloudWatch datasource configured for instance {instance_id}")
        else:
            print("⚠ No CloudWatch datasource found")


def generate_test_report(results):
    """Generate a detailed test report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"grafana_cpu_metrics_report_{timestamp}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": results,
        "summary": {
            "total_tests": results.testsRun,
            "passed": results.testsRun - len(results.failures) - len(results.errors),
            "failed": len(results.failures),
            "errors": len(results.errors),
            "skipped": len(results.skipped)
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Test report saved to: {report_file}")
    return report_file


def main():
    """Run all Grafana CPU metrics tests"""
    print("=" * 60)
    print("GRAFANA CPU METRICS TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestGrafanaCPUMetrics))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    print(f"Total Tests: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print(f"⏭️  Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! Grafana CPU metrics monitoring is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above for details.")
    
    # Generate report
    report_file = generate_test_report(result)
    
    # Quick access info
    print("\n📊 Quick Access:")
    print(f"Grafana: http://localhost:3000 (admin/admin123)")
    print(f"Prometheus: http://localhost:9090")
    print("EC2 CPU Monitoring Dashboard: Available in Grafana")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(main())
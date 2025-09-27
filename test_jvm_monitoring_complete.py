#!/usr/bin/env python3
"""
Comprehensive Test Cases for JVM Monitoring with Grafana
Tests all components of the Java monitoring and correlation system
"""

import boto3
import json
import requests
import time
from datetime import datetime, timedelta
import sys

class JVMMonitoringTestSuite:
    def __init__(self):
        self.cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.logs_client = boto3.client('logs', region_name='us-east-1')
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        self.instance_id = "i-02bef13982a179478"  # SRE-DEMO
        self.grafana_url = "http://localhost:3000"
        self.grafana_user = "admin"
        self.grafana_pass = "admin123"
        
        self.test_results = []
        
    def run_test(self, test_name, test_func):
        """Run a test and track results"""
        print(f"\n🧪 Running: {test_name}")
        print("-" * 60)
        
        try:
            result = test_func()
            status = "✅ PASSED" if result else "❌ FAILED"
            self.test_results.append((test_name, result))
            print(f"Result: {status}")
            return result
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            self.test_results.append((test_name, False))
            return False
            
    def test_grafana_connectivity(self):
        """Test 1: Verify Grafana is accessible"""
        try:
            r = requests.get(f"{self.grafana_url}/api/health")
            if r.status_code == 200:
                print("✓ Grafana is accessible")
                return True
            else:
                print(f"✗ Grafana returned status: {r.status_code}")
                return False
        except Exception as e:
            print(f"✗ Cannot connect to Grafana: {e}")
            return False
            
    def test_grafana_dashboards(self):
        """Test 2: Verify all dashboards are created"""
        auth = (self.grafana_user, self.grafana_pass)
        required_dashboards = [
            "java-app-monitoring",
            "change-management",
            "ec2-max-cpu"
        ]
        
        try:
            r = requests.get(f"{self.grafana_url}/api/search?type=dash-db", auth=auth)
            if r.status_code != 200:
                print(f"✗ Failed to list dashboards: {r.status_code}")
                return False
                
            dashboards = r.json()
            dashboard_uids = [d.get('uid', '') for d in dashboards]
            
            all_found = True
            for required in required_dashboards:
                if required in dashboard_uids:
                    print(f"✓ Found dashboard: {required}")
                else:
                    print(f"✗ Missing dashboard: {required}")
                    all_found = False
                    
            return all_found
            
        except Exception as e:
            print(f"✗ Error checking dashboards: {e}")
            return False
            
    def test_jvm_metrics_in_cloudwatch(self):
        """Test 3: Verify JVM metrics are being collected"""
        namespace = 'JavaApp/SpringBoot'
        
        try:
            # List metrics in the namespace
            response = self.cloudwatch_client.list_metrics(
                Namespace=namespace,
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': self.instance_id}
                ]
            )
            
            expected_metrics = [
                'JVM_HeapUsedPercent',
                'HeapMemoryUsed',
                'CPUUtilization',
                'GCPauseTime'
            ]
            
            found_metrics = [m['MetricName'] for m in response.get('Metrics', [])]
            
            all_found = True
            for metric in expected_metrics:
                if metric in found_metrics:
                    print(f"✓ Found metric: {metric}")
                else:
                    print(f"✗ Missing metric: {metric}")
                    all_found = False
                    
            # Check for recent data
            if found_metrics:
                test_metric = found_metrics[0]
                data_response = self.cloudwatch_client.get_metric_statistics(
                    Namespace=namespace,
                    MetricName=test_metric,
                    Dimensions=[{'Name': 'InstanceId', 'Value': self.instance_id}],
                    StartTime=datetime.utcnow() - timedelta(hours=1),
                    EndTime=datetime.utcnow(),
                    Period=300,
                    Statistics=['Average']
                )
                
                if data_response.get('Datapoints'):
                    print(f"✓ Recent data available: {len(data_response['Datapoints'])} points")
                else:
                    print("✗ No recent metric data found")
                    all_found = False
                    
            return all_found
            
        except Exception as e:
            print(f"✗ Error checking CloudWatch metrics: {e}")
            return False
            
    def test_change_records(self):
        """Test 4: Verify change records exist in SSM OpsCenter"""
        try:
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Title',
                        'Values': ['[CHANGE]'],
                        'Operator': 'Contains'
                    },
                    {
                        'Key': 'CreatedTime',
                        'Values': [(datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')],
                        'Operator': 'GreaterThan'
                    }
                ],
                MaxResults=10
            )
            
            ops_items = response.get('OpsItemSummaries', [])
            
            if ops_items:
                print(f"✓ Found {len(ops_items)} change records")
                for item in ops_items[:3]:
                    print(f"  - {item['Title']}")
                return True
            else:
                print("✗ No change records found")
                return False
                
        except Exception as e:
            print(f"✗ Error checking change records: {e}")
            return False
            
    def test_application_logs(self):
        """Test 5: Verify application logs are being generated"""
        log_group = '/aws/ec2/payment-service'
        
        try:
            # Check if log group exists
            response = self.logs_client.describe_log_groups(
                logGroupNamePrefix=log_group,
                limit=1
            )
            
            if not response.get('logGroups'):
                print(f"✗ Log group {log_group} not found")
                return False
                
            print(f"✓ Log group exists: {log_group}")
            
            # Check for recent logs
            response = self.logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=int((datetime.utcnow() - timedelta(hours=1)).timestamp() * 1000),
                limit=10
            )
            
            events = response.get('events', [])
            if events:
                print(f"✓ Found {len(events)} recent log entries")
                
                # Check for specific patterns
                has_info = any('[INFO]' in e['message'] for e in events)
                has_warn = any('[WARN]' in e['message'] for e in events)
                
                if has_info:
                    print("✓ Found INFO level logs")
                if has_warn:
                    print("✓ Found WARN level logs (memory warnings)")
                    
                return True
            else:
                print("✗ No recent log entries found")
                return False
                
        except self.logs_client.exceptions.ResourceNotFoundException:
            print(f"✗ Log group {log_group} does not exist")
            return False
        except Exception as e:
            print(f"✗ Error checking logs: {e}")
            return False
            
    def test_grafana_data_display(self):
        """Test 6: Verify Grafana dashboards show data"""
        auth = (self.grafana_user, self.grafana_pass)
        
        try:
            # Query Java dashboard data
            dashboard_uid = "java-app-monitoring"
            
            # Get dashboard
            r = requests.get(f"{self.grafana_url}/api/dashboards/uid/{dashboard_uid}", auth=auth)
            
            if r.status_code != 200:
                print(f"✗ Cannot fetch dashboard: {r.status_code}")
                return False
                
            print(f"✓ Dashboard accessible: {dashboard_uid}")
            
            # Query panel data
            query = {
                "queries": [{
                    "datasourceId": 1,
                    "queryType": "timeSeriesQuery",
                    "namespace": "JavaApp/SpringBoot",
                    "metricName": "JVM_HeapUsedPercent",
                    "dimensions": {"InstanceId": self.instance_id},
                    "statistic": "Average",
                    "period": "300",
                    "region": "us-east-1"
                }],
                "from": "now-1h",
                "to": "now"
            }
            
            r = requests.post(f"{self.grafana_url}/api/ds/query", auth=auth, json=query)
            
            if r.status_code == 200:
                print("✓ Dashboard query successful")
                return True
            else:
                print(f"✗ Dashboard query failed: {r.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error testing Grafana data: {e}")
            return False
            
    def test_supervisor_correlation(self):
        """Test 7: Verify supervisor Lambda can perform correlation analysis"""
        try:
            # Get a recent incident OpsItem
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Title',
                        'Values': ['High CPU Alert'],
                        'Operator': 'Contains'
                    },
                    {
                        'Key': 'Status',
                        'Values': ['Open', 'InProgress'],
                        'Operator': 'Equal'
                    }
                ],
                MaxResults=1
            )
            
            if not response.get('OpsItemSummaries'):
                print("✗ No incident OpsItems found for testing")
                return False
                
            ops_item_id = response['OpsItemSummaries'][0]['OpsItemId']
            print(f"✓ Found test OpsItem: {ops_item_id}")
            
            # Invoke supervisor Lambda
            payload = {
                'action': 'analyze',
                'incident_description': 'Test correlation analysis',
                'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'service': 'payment-service',
                'environment': 'test',
                'additional_context': {
                    'ops_item_id': ops_item_id
                }
            }
            
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                print("✓ Supervisor Lambda invoked successfully")
                body = json.loads(result['body']) if isinstance(result.get('body'), str) else result.get('body', {})
                
                if 'root_cause_analysis' in body:
                    print("✓ Root cause analysis generated")
                    return True
                else:
                    print("✗ No root cause analysis in response")
                    return False
            else:
                print(f"✗ Supervisor Lambda failed: {result.get('statusCode')}")
                return False
                
        except Exception as e:
            print(f"✗ Error testing supervisor correlation: {e}")
            return False
            
    def test_change_correlation(self):
        """Test 8: Verify change-incident correlation"""
        try:
            # Check for incidents with related changes
            response = self.ssm_client.describe_ops_items(
                MaxResults=10
            )
            
            correlated_items = 0
            for item in response.get('OpsItemSummaries', []):
                ops_data = item.get('OperationalData', {})
                if 'RelatedChangeId' in ops_data:
                    correlated_items += 1
                    
            if correlated_items > 0:
                print(f"✓ Found {correlated_items} incidents correlated with changes")
                return True
            else:
                print("✗ No change-incident correlations found")
                return False
                
        except Exception as e:
            print(f"✗ Error checking correlations: {e}")
            return False
            
    def test_memory_leak_pattern(self):
        """Test 9: Verify memory leak pattern in metrics"""
        try:
            # Get heap memory metrics
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='JavaApp/SpringBoot',
                MetricName='HeapMemoryUsed',
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': self.instance_id}
                ],
                StartTime=datetime.utcnow() - timedelta(hours=3),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )
            
            datapoints = sorted(response.get('Datapoints', []), key=lambda x: x['Timestamp'])
            
            if len(datapoints) >= 2:
                # Check if memory is increasing
                first_value = datapoints[0]['Average']
                last_value = datapoints[-1]['Average']
                
                if last_value > first_value:
                    increase_pct = ((last_value - first_value) / first_value) * 100
                    print(f"✓ Memory increase detected: {increase_pct:.1f}%")
                    return True
                else:
                    print("✗ No memory increase pattern detected")
                    return False
            else:
                print(f"✗ Insufficient data points: {len(datapoints)}")
                return False
                
        except Exception as e:
            print(f"✗ Error checking memory pattern: {e}")
            return False
            
    def run_all_tests(self):
        """Run all test cases"""
        print("🚀 JVM Monitoring Test Suite")
        print("=" * 80)
        print(f"Instance: {self.instance_id}")
        print(f"Grafana: {self.grafana_url}")
        print("=" * 80)
        
        # Run all tests
        self.run_test("Test 1: Grafana Connectivity", self.test_grafana_connectivity)
        self.run_test("Test 2: Grafana Dashboards", self.test_grafana_dashboards)
        self.run_test("Test 3: JVM CloudWatch Metrics", self.test_jvm_metrics_in_cloudwatch)
        self.run_test("Test 4: Change Records in SSM", self.test_change_records)
        self.run_test("Test 5: Application Logs", self.test_application_logs)
        self.run_test("Test 6: Grafana Data Display", self.test_grafana_data_display)
        self.run_test("Test 7: Supervisor Correlation", self.test_supervisor_correlation)
        self.run_test("Test 8: Change-Incident Correlation", self.test_change_correlation)
        self.run_test("Test 9: Memory Leak Pattern", self.test_memory_leak_pattern)
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
            
        print("\n" + "-" * 80)
        print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("\nThe JVM monitoring system is fully operational:")
            print("✓ Grafana dashboards configured")
            print("✓ JVM metrics flowing to CloudWatch")
            print("✓ Change management integrated")
            print("✓ Application logs collected")
            print("✓ Correlation analysis working")
            print("✓ Memory leak patterns detectable")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the failed components.")
            
        return passed == total

def main():
    """Run the test suite"""
    tester = JVMMonitoringTestSuite()
    success = tester.run_all_tests()
    
    print("\n📊 Next Steps:")
    print("1. View Grafana dashboards:")
    print("   - Java Monitoring: http://localhost:3000/d/java-app-monitoring")
    print("   - Change Management: http://localhost:3000/d/change-management")
    print("   - CPU Dashboard: http://localhost:3000/d/ec2-max-cpu")
    print("\n2. Check Streamlit CPU Spike Demo for correlation analysis")
    print("\n3. Monitor the memory leak progression in real-time")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
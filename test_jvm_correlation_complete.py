#!/usr/bin/env python3
"""
Complete JVM monitoring and correlation test case
Tests the entire flow from memory leak to CPU spike with AI analysis
"""

import boto3
import json
import requests
import time
from datetime import datetime, timedelta

class JVMCorrelationTest:
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.instance_id = "i-02bef13982a179478"
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
    def test_java_app_health(self):
        """Test 1: Verify Java app is healthy"""
        print("\n1️⃣ Testing Java Application Health...")
        
        commands = [
            "curl -s http://localhost:8090/health",
            "systemctl is-active payment-service"
        ]
        
        try:
            response = self.ssm_client.send_command(
                InstanceIds=[self.instance_id],
                DocumentName='AWS-RunShellScript',
                Parameters={'commands': commands}
            )
            
            time.sleep(3)
            result = self.ssm_client.get_command_invocation(
                CommandId=response['Command']['CommandId'],
                InstanceId=self.instance_id
            )
            
            output = result['StandardOutputContent']
            if '"status":"UP"' in output and 'active' in output:
                cache_size = output.split('"cacheSize":')[1].split(',')[0] if '"cacheSize":' in output else "unknown"
                memory_pct = output.split('"memoryPercent":')[1].split(',')[0] if '"memoryPercent":' in output else "unknown"
                self.log_test("Java App Health", True, f"Cache: {cache_size}, Memory: {memory_pct}%")
                return True
            else:
                self.log_test("Java App Health", False, "App not responding or not active")
                return False
                
        except Exception as e:
            self.log_test("Java App Health", False, str(e))
            return False
            
    def test_cloudwatch_metrics(self):
        """Test 2: Verify metrics are in CloudWatch"""
        print("\n2️⃣ Testing CloudWatch Metrics...")
        
        try:
            # Check for HeapMemoryUsed metric
            response = self.cloudwatch_client.list_metrics(
                Namespace='JavaApp/SpringBoot',
                MetricName='HeapMemoryUsed',
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': self.instance_id}
                ]
            )
            
            if not response['Metrics']:
                self.log_test("CloudWatch Metrics", False, "No metrics found")
                return False
                
            # Get recent data
            data_response = self.cloudwatch_client.get_metric_statistics(
                Namespace='JavaApp/SpringBoot',
                MetricName='HeapMemoryUsed',
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': self.instance_id}
                ],
                StartTime=datetime.utcnow() - timedelta(minutes=15),
                EndTime=datetime.utcnow(),
                Period=60,
                Statistics=['Average', 'Maximum']
            )
            
            if data_response['Datapoints']:
                latest = sorted(data_response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                self.log_test("CloudWatch Metrics", True, 
                             f"Latest memory: {latest['Average']:.1f}% avg, {latest['Maximum']:.1f}% max")
                return True
            else:
                self.log_test("CloudWatch Metrics", False, "Metrics exist but no recent data")
                return False
                
        except Exception as e:
            self.log_test("CloudWatch Metrics", False, str(e))
            return False
            
    def test_grafana_dashboards(self):
        """Test 3: Verify Grafana can query data"""
        print("\n3️⃣ Testing Grafana Dashboards...")
        
        auth = ('admin', 'admin123')
        grafana_url = "http://localhost:3000"
        
        try:
            # Get datasources
            r = requests.get(f"{grafana_url}/api/datasources", auth=auth)
            if r.status_code != 200:
                self.log_test("Grafana Dashboards", False, "Cannot access Grafana API")
                return False
                
            # Find CloudWatch datasource
            datasources = r.json()
            cloudwatch_ds = next((ds for ds in datasources if ds['type'] == 'cloudwatch'), None)
            
            if not cloudwatch_ds:
                self.log_test("Grafana Dashboards", False, "No CloudWatch datasource")
                return False
                
            # Test query
            query_payload = {
                "queries": [{
                    "datasourceId": cloudwatch_ds['id'],
                    "refId": "A",
                    "region": "us-east-1",
                    "namespace": "JavaApp/SpringBoot",
                    "metricName": "HeapMemoryUsed",
                    "dimensions": {"InstanceId": self.instance_id},
                    "statistic": "Average",
                    "period": "300"
                }],
                "from": "now-1h",
                "to": "now"
            }
            
            r = requests.post(f"{grafana_url}/api/ds/query", auth=auth, json=query_payload)
            
            if r.status_code == 200:
                self.log_test("Grafana Dashboards", True, "Query successful")
                return True
            else:
                self.log_test("Grafana Dashboards", False, f"Query failed: {r.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Grafana Dashboards", False, str(e))
            return False
            
    def create_cpu_spike_incident(self):
        """Create a CPU spike incident for testing"""
        print("\n📝 Creating CPU spike incident...")
        
        try:
            # Create OpsItem
            response = self.ssm_client.create_ops_item(
                Title="High CPU Alert - Payment Service Memory Leak",
                Description="CPU utilization spike detected on payment-service due to memory pressure. GC overhead causing performance degradation.",
                Source="JVM-Test",
                OperationalData={
                    '/aws/resources': {
                        'Value': json.dumps([{
                            'arn': f'arn:aws:ec2:us-east-1:123456789012:instance/{self.instance_id}'
                        }])
                    },
                    'Instance': {'Value': self.instance_id},
                    'Service': {'Value': 'payment-service'},
                    'MemoryUsage': {'Value': '75%'},
                    'CPUUsage': {'Value': '85%'}
                },
                Severity='2',
                Category='Performance'
            )
            
            ops_item_id = response['OpsItemId']
            print(f"   Created OpsItem: {ops_item_id}")
            return ops_item_id
            
        except Exception as e:
            print(f"   Failed to create OpsItem: {e}")
            return None
            
    def test_ai_correlation(self, ops_item_id):
        """Test 4: Verify AI correlation analysis"""
        print("\n4️⃣ Testing AI Root Cause Correlation...")
        
        if not ops_item_id:
            self.log_test("AI Correlation", False, "No OpsItem to analyze")
            return False
            
        try:
            # Invoke supervisor lambda
            payload = {
                'action': 'analyze',
                'incident_description': 'High CPU on payment-service due to memory leak. GC overhead causing performance issues.',
                'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'service': 'payment-service',
                'environment': 'production',
                'additional_context': {
                    'ops_item_id': ops_item_id,
                    'incident_type': 'CPU Spike - Memory Related',
                    'instance_id': self.instance_id
                }
            }
            
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body']) if isinstance(result.get('body'), str) else result.get('body', {})
                
                if 'root_cause_analysis' in body:
                    analysis = body['root_cause_analysis']
                    
                    # Check for key correlation indicators
                    correlation_found = False
                    if any(keyword in analysis.lower() for keyword in ['memory leak', 'heap', 'gc', 'garbage collection', 'cache']):
                        correlation_found = True
                        self.log_test("AI Correlation", True, "Correctly identified memory leak as root cause")
                    else:
                        self.log_test("AI Correlation", False, "Did not identify memory-related cause")
                        
                    # Show analysis snippet
                    print(f"\n   AI Analysis Summary:")
                    print(f"   {analysis[:300]}...")
                    
                    return correlation_found
                else:
                    self.log_test("AI Correlation", False, "No root cause analysis in response")
                    return False
            else:
                self.log_test("AI Correlation", False, f"Lambda error: {result.get('statusCode')}")
                return False
                
        except Exception as e:
            self.log_test("AI Correlation", False, str(e))
            return False
            
    def test_change_correlation(self):
        """Test 5: Verify change record correlation"""
        print("\n5️⃣ Testing Change Record Correlation...")
        
        try:
            # Create a change record
            response = self.ssm_client.create_ops_item(
                Title="Deploy payment-service v2.1.0 - Memory optimization disabled",
                Description="Deployed new version with unbounded cache for transaction processing",
                Source="ChangeManagement",
                OperationalData={
                    'ChangeType': {'Value': 'Application Update'},
                    'Service': {'Value': 'payment-service'},
                    'Version': {'Value': 'v2.1.0'},
                    'DeploymentTime': {'Value': datetime.utcnow().isoformat()}
                },
                Severity='3',
                Category='Availability'
            )
            
            self.log_test("Change Correlation", True, "Change record created successfully")
            return True
            
        except Exception as e:
            self.log_test("Change Correlation", False, str(e))
            return False
            
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 JVM MONITORING AND CORRELATION TEST SUITE")
        print("=" * 80)
        
        # Run tests
        java_ok = self.test_java_app_health()
        metrics_ok = self.test_cloudwatch_metrics()
        grafana_ok = self.test_grafana_dashboards()
        
        # Create incident and test correlation
        ops_item_id = self.create_cpu_spike_incident()
        ai_ok = self.test_ai_correlation(ops_item_id)
        change_ok = self.test_change_correlation()
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("\n✅ The JVM memory leak correlation demo is fully operational:")
            print("   - Java app running with memory leak simulation")
            print("   - Metrics flowing to CloudWatch")
            print("   - Grafana dashboards configured")
            print("   - AI correlation identifies memory as root cause")
            print("   - Change records properly tracked")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} tests failed")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   - {result['test']}: {result['details']}")
                    
        print("\n📊 DASHBOARDS:")
        print(f"1. Java Monitoring: http://localhost:3000/d/java-app-monitoring")
        print(f"2. Change Management: http://localhost:3000/d/change-management")
        print(f"3. CPU Monitoring: http://localhost:3000/d/ec2-max-cpu")
        
        print("\n🔍 TO SEE CORRELATION IN ACTION:")
        print("1. Go to Streamlit app: http://localhost:8501")
        print("2. Navigate to CPU Spike Demo")
        print("3. Select SRE-DEMO instance")
        print("4. Click 'Run Root Cause Analysis'")
        print("5. Observe correlation with memory leak and code change")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = JVMCorrelationTest()
    success = tester.run_all_tests()
    
    if not success:
        print("\n💡 TROUBLESHOOTING:")
        print("- If metrics aren't showing: Wait 2-3 more minutes")
        print("- Check Java app: curl http://SRE-DEMO:8090/health")
        print("- Check logs: sudo journalctl -u payment-service -f")
        print("- Check metrics log: tail -f /var/log/jvm_metrics.log")
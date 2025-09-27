#!/usr/bin/env python3
"""
Verify the final deployment and run comprehensive tests
"""

import boto3
import json
import requests
import time
from datetime import datetime, timedelta

def verify_java_app_on_8090():
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"
    
    print("🔍 Verifying Java Application on Port 8090")
    print("=" * 60)
    
    commands = [
        "echo '=== Process Check ==='",
        "ps aux | grep -v grep | grep PaymentService | head -5",
        "echo",
        "echo '=== Port Check ==='",
        "netstat -tlpn | grep 8090",
        "echo",
        "echo '=== Service Status ==='",
        "systemctl status payment-service --no-pager | head -20",
        "echo",
        "echo '=== API Test ==='",
        "curl -s http://localhost:8090/ | python -m json.tool",
        "echo",
        "curl -s http://localhost:8090/health | python -m json.tool",
        "echo",
        "echo '=== Recent Logs ==='",
        "journalctl -u payment-service -n 20 --no-pager | tail -10",
        "echo",
        "echo '=== Metrics Collection Log ==='",
        "tail -10 /var/log/jvm_metrics.log 2>/dev/null || echo 'No metrics log yet'"
    ]
    
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': commands}
        )
        
        command_id = response['Command']['CommandId']
        time.sleep(5)
        
        result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        print("\n📋 Verification Results:")
        print("-" * 60)
        print(result['StandardOutputContent'])
        
        return 'payment-service' in result['StandardOutputContent'] and '"status":"running"' in result['StandardOutputContent']
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def check_cloudwatch_metrics():
    """Check if metrics are in CloudWatch"""
    cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
    
    print("\n📊 Checking CloudWatch Metrics...")
    print("-" * 60)
    
    try:
        # List metrics
        response = cloudwatch_client.list_metrics(
            Namespace='JavaApp/SpringBoot',
            MetricName='HeapMemoryUsed',
            Dimensions=[
                {'Name': 'InstanceId', 'Value': 'i-02bef13982a179478'}
            ]
        )
        
        if response['Metrics']:
            print("✅ HeapMemoryUsed metric found in CloudWatch")
            
            # Get recent data
            data_response = cloudwatch_client.get_metric_statistics(
                Namespace='JavaApp/SpringBoot',
                MetricName='HeapMemoryUsed',
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': 'i-02bef13982a179478'}
                ],
                StartTime=datetime.utcnow() - timedelta(minutes=10),
                EndTime=datetime.utcnow(),
                Period=60,
                Statistics=['Average', 'Maximum']
            )
            
            if data_response['Datapoints']:
                print(f"✅ Found {len(data_response['Datapoints'])} data points")
                latest = sorted(data_response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                print(f"   Latest: {latest['Average']:.1f}% (avg), {latest['Maximum']:.1f}% (max)")
                print(f"   Time: {latest['Timestamp']}")
                return True
            else:
                print("⚠️ Metric exists but no recent data")
                return False
        else:
            print("❌ HeapMemoryUsed metric not found")
            return False
            
    except Exception as e:
        print(f"❌ CloudWatch error: {e}")
        return False

def test_grafana_query():
    """Test if Grafana can query the data"""
    print("\n🔍 Testing Grafana Dashboard...")
    print("-" * 60)
    
    auth = ('admin', 'admin123')
    grafana_url = "http://localhost:3000"
    
    try:
        # Get datasources
        r = requests.get(f"{grafana_url}/api/datasources", auth=auth)
        if r.status_code != 200:
            print("❌ Cannot get datasources")
            return False
            
        datasources = r.json()
        cloudwatch_ds = None
        for ds in datasources:
            if ds['type'] == 'cloudwatch':
                cloudwatch_ds = ds
                break
                
        if not cloudwatch_ds:
            print("❌ No CloudWatch datasource found")
            return False
            
        print(f"✅ Found CloudWatch datasource: {cloudwatch_ds['name']}")
        
        # Test query
        query_payload = {
            "queries": [{
                "datasourceId": cloudwatch_ds['id'],
                "refId": "A",
                "region": "us-east-1",
                "namespace": "JavaApp/SpringBoot",
                "metricName": "HeapMemoryUsed",
                "dimensions": {"InstanceId": "i-02bef13982a179478"},
                "statistic": "Average",
                "period": "300"
            }],
            "from": "now-1h",
            "to": "now"
        }
        
        r = requests.post(f"{grafana_url}/api/ds/query", auth=auth, json=query_payload)
        
        if r.status_code == 200:
            print("✅ Grafana query successful")
            return True
        else:
            print(f"❌ Grafana query failed: {r.status_code}")
            print(f"Response: {r.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Grafana test error: {e}")
        return False

def run_final_test_suite():
    """Run all tests and generate AI analysis"""
    print("\n🧪 FINAL TEST SUITE")
    print("=" * 80)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Java App Running
    print("\n1️⃣ Testing Java Application...")
    if verify_java_app_on_8090():
        print("✅ PASSED - Java app running on port 8090")
        tests_passed += 1
    else:
        print("❌ FAILED - Java app not running properly")
        
    # Test 2: CloudWatch Metrics
    print("\n2️⃣ Testing CloudWatch Metrics...")
    if check_cloudwatch_metrics():
        print("✅ PASSED - Metrics flowing to CloudWatch")
        tests_passed += 1
    else:
        print("❌ FAILED - No metrics in CloudWatch")
        
    # Test 3: Grafana Dashboard
    print("\n3️⃣ Testing Grafana Integration...")
    if test_grafana_query():
        print("✅ PASSED - Grafana can query metrics")
        tests_passed += 1
    else:
        print("❌ FAILED - Grafana query issues")
        
    # Test 4: Run AI Analysis
    print("\n4️⃣ Testing AI Root Cause Analysis...")
    try:
        # Get the most recent CPU spike incident
        ssm_client = boto3.client('ssm', region_name='us-east-1')
        response = ssm_client.describe_ops_items(
            OpsItemFilters=[
                {
                    'Key': 'Title',
                    'Values': ['High CPU Alert'],
                    'Operator': 'Contains'
                }
            ],
            MaxResults=1
        )
        
        if response['OpsItemSummaries']:
            ops_item_id = response['OpsItemSummaries'][0]['OpsItemId']
            print(f"   Found incident: {ops_item_id}")
            
            # Invoke supervisor
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            payload = {
                'action': 'analyze',
                'incident_description': 'High CPU on payment-service with memory leak',
                'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'service': 'payment-service',
                'environment': 'production',
                'additional_context': {
                    'ops_item_id': ops_item_id,
                    'incident_type': 'CPU Spike - Memory Related'
                }
            }
            
            response = lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                print("✅ PASSED - AI analysis completed")
                tests_passed += 1
                
                # Show analysis snippet
                body = json.loads(result['body']) if isinstance(result.get('body'), str) else result.get('body', {})
                if 'root_cause_analysis' in body:
                    analysis = body['root_cause_analysis']
                    print("\n   📋 AI Analysis (snippet):")
                    print("   " + analysis[:200] + "...")
            else:
                print("❌ FAILED - AI analysis error")
        else:
            print("❌ FAILED - No incidents found for analysis")
            
    except Exception as e:
        print(f"❌ FAILED - AI analysis error: {e}")
        
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {tests_passed}/{total_tests} ({tests_passed/total_tests*100:.0f}%)")
    
    if tests_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ The JVM memory leak demo is fully operational:")
        print("   - Java app running with memory leak simulation")
        print("   - Metrics flowing to CloudWatch")
        print("   - Grafana dashboards displaying data")
        print("   - AI correlation analysis working")
    else:
        print(f"\n⚠️ {total_tests - tests_passed} tests failed")
        print("Please check the failed components")
        
    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_final_test_suite()
    
    print("\n📊 DASHBOARDS:")
    print("1. Java Monitoring: http://localhost:3000/d/java-app-monitoring")
    print("2. Change Management: http://localhost:3000/d/change-management")
    print("3. CPU Monitoring: http://localhost:3000/d/ec2-max-cpu")
    
    print("\n🔍 VIEW CORRELATION:")
    print("1. Go to Streamlit CPU Spike Demo")
    print("2. Select SRE-DEMO instance")
    print("3. Click 'Run Root Cause Analysis'")
    print("4. See correlation with code changes and memory leak")
    
    if not success:
        print("\n💡 If metrics aren't showing yet:")
        print("   - Wait 2-3 more minutes")
        print("   - Refresh Grafana dashboards")
        print("   - Check time range is 'Last 1 hour'")
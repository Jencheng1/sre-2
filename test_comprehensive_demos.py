#!/usr/bin/env python3
"""
Test script for comprehensive demo scenarios
Verifies all demo incidents create proper AWS resources and correlations
"""

import boto3
import time
import json
from datetime import datetime, timedelta
from comprehensive_demo_scenarios import ComprehensiveDemoScenarios

class ComprehensiveDemoTester:
    def __init__(self):
        self.demo_generator = ComprehensiveDemoScenarios()
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
        self.logs_client = boto3.client('logs', region_name='us-east-1')
        
        self.test_results = []
        
    def run_all_tests(self):
        """Run all comprehensive demo tests."""
        print("\n" + "="*60)
        print("🧪 COMPREHENSIVE DEMO SCENARIO TESTS")
        print("="*60)
        
        tests = [
            self.test_change_correlation,
            self.test_defect_correlation,
            self.test_jms_timeout,
            self.test_vpc_cloudtrail_correlation
        ]
        
        for test in tests:
            test()
            time.sleep(2)  # Avoid API throttling
        
        # Print summary
        self.print_test_summary()
    
    def test_change_correlation(self):
        """Test change-induced incident creation and correlation."""
        print("\n📌 Testing Change Correlation Demo...")
        test_name = "Change Correlation"
        
        try:
            # Create the incident
            result = self.demo_generator.create_demo_incident('change_correlation')
            
            # Verify incident created
            assert 'incident_id' in result, "No incident ID returned"
            assert 'change_id' in result, "No change ID returned"
            
            incident_id = result['incident_id']
            change_id = result['change_id']
            
            print(f"  ✅ Created incident: {incident_id}")
            print(f"  ✅ Created change: {change_id}")
            
            # Verify incident exists
            incident = self.ssm_client.get_ops_item(OpsItemId=incident_id)['OpsItem']
            assert incident is not None, "Incident not found"
            
            # Verify change exists
            change = self.ssm_client.get_ops_item(OpsItemId=change_id)['OpsItem']
            assert change is not None, "Change not found"
            assert '[CHANGE]' in change['Title'], "Change not properly tagged"
            
            # Verify correlation data
            assert 'relatedChange' in incident['OperationalData'], "No change correlation in incident"
            
            # Verify metrics exist
            metrics = self.verify_metrics_exist(['DatabaseConnectionErrors', 'ApplicationResponseTime'])
            assert all(metrics.values()), "Not all metrics created"
            
            # Verify logs exist
            logs_exist = self.verify_logs_exist('/aws/sre-demo/application', 'application')
            assert logs_exist, "CloudWatch logs not created"
            
            print(f"  ✅ All verifications passed for {test_name}")
            self.test_results.append((test_name, True, "All checks passed"))
            
        except Exception as e:
            print(f"  ❌ Test failed: {str(e)}")
            self.test_results.append((test_name, False, str(e)))
    
    def test_defect_correlation(self):
        """Test defect-correlated incident creation."""
        print("\n🐛 Testing Defect Correlation Demo...")
        test_name = "Defect Correlation"
        
        try:
            # Create the incident
            result = self.demo_generator.create_demo_incident('defect_correlation')
            
            # Verify incident created
            assert 'incident_id' in result, "No incident ID returned"
            assert 'defect_id' in result, "No defect ID returned"
            
            incident_id = result['incident_id']
            print(f"  ✅ Created incident: {incident_id}")
            print(f"  ✅ Linked to defect: {result['defect_id']}")
            
            # Verify incident exists
            incident = self.ssm_client.get_ops_item(OpsItemId=incident_id)['OpsItem']
            assert incident is not None, "Incident not found"
            
            # Verify defect correlation
            assert 'knownDefect' in incident['OperationalData'], "No defect correlation"
            assert incident['OperationalData']['knownDefect']['Value'] == 'DEF-4521', "Wrong defect ID"
            
            # Verify memory metrics
            metrics = self.verify_metrics_exist(['PaymentServiceMemoryUsage'])
            assert metrics['PaymentServiceMemoryUsage'], "Memory metrics not created"
            
            # Verify logs with defect reference
            logs_exist = self.verify_logs_exist('/aws/sre-demo/application', 'application')
            assert logs_exist, "CloudWatch logs not created"
            
            print(f"  ✅ All verifications passed for {test_name}")
            self.test_results.append((test_name, True, "All checks passed"))
            
        except Exception as e:
            print(f"  ❌ Test failed: {str(e)}")
            self.test_results.append((test_name, False, str(e)))
    
    def test_jms_timeout(self):
        """Test JMS timeout incident with detailed metrics."""
        print("\n📬 Testing JMS Timeout Demo...")
        test_name = "JMS Timeout"
        
        try:
            # Create the incident
            result = self.demo_generator.create_demo_incident('jms_timeout')
            
            # Verify incident created
            assert 'incident_id' in result, "No incident ID returned"
            
            incident_id = result['incident_id']
            print(f"  ✅ Created incident: {incident_id}")
            
            # Verify incident exists
            incident = self.ssm_client.get_ops_item(OpsItemId=incident_id)['OpsItem']
            assert incident is not None, "Incident not found"
            
            # Verify JMS-specific data
            ops_data = incident['OperationalData']
            assert 'queue' in ops_data, "No queue information"
            assert 'broker' in ops_data, "No broker information"
            assert ops_data['queue']['Value'] == 'order.processing', "Wrong queue name"
            
            # Verify JMS metrics
            jms_metrics = self.verify_metrics_exist([
                'JMSQueueDepth',
                'JMSSessionTimeouts',
                'JMSMessageProcessingTime'
            ])
            assert all(jms_metrics.values()), "Not all JMS metrics created"
            
            # Verify JMS logs
            logs_exist = self.verify_logs_exist('/aws/sre-demo/application', 'jms-processor')
            assert logs_exist, "JMS logs not created"
            
            print(f"  ✅ All verifications passed for {test_name}")
            self.test_results.append((test_name, True, "All checks passed"))
            
        except Exception as e:
            print(f"  ❌ Test failed: {str(e)}")
            self.test_results.append((test_name, False, str(e)))
    
    def test_vpc_cloudtrail_correlation(self):
        """Test VPC/CloudTrail correlation incident."""
        print("\n🔐 Testing VPC/CloudTrail Correlation Demo...")
        test_name = "VPC/CloudTrail Correlation"
        
        try:
            # Create the incident
            result = self.demo_generator.create_demo_incident('vpc_cloudtrail')
            
            # Verify incident created
            assert 'incident_id' in result, "No incident ID returned"
            
            incident_id = result['incident_id']
            print(f"  ✅ Created incident: {incident_id}")
            
            # Verify incident exists
            incident = self.ssm_client.get_ops_item(OpsItemId=incident_id)['OpsItem']
            assert incident is not None, "Incident not found"
            
            # Verify security correlation data
            ops_data = incident['OperationalData']
            assert 'suspiciousIP' in ops_data, "No suspicious IP data"
            assert 'vpcFlowLogsAvailable' in ops_data, "No VPC logs indicator"
            assert 'cloudTrailLogsAvailable' in ops_data, "No CloudTrail indicator"
            assert ops_data['correlationFound']['Value'] == 'true', "No correlation found"
            
            # Verify network metrics
            network_metrics = self.verify_metrics_exist([
                'NetworkOutBytes',
                'ActiveConnections'
            ])
            assert all(network_metrics.values()), "Not all network metrics created"
            
            # Verify VPC Flow Logs
            vpc_logs = self.verify_logs_exist('/aws/vpc/flowlogs', 'vpc-flow-logs')
            assert vpc_logs, "VPC Flow Logs not created"
            
            # Verify CloudTrail logs
            trail_logs = self.verify_logs_exist('/aws/cloudtrail/events', 'cloudtrail-events')
            assert trail_logs, "CloudTrail logs not created"
            
            print(f"  ✅ All verifications passed for {test_name}")
            self.test_results.append((test_name, True, "All checks passed"))
            
        except Exception as e:
            print(f"  ❌ Test failed: {str(e)}")
            self.test_results.append((test_name, False, str(e)))
    
    def verify_metrics_exist(self, metric_names):
        """Verify CloudWatch metrics exist."""
        results = {}
        
        for metric_name in metric_names:
            try:
                response = self.cloudwatch_client.list_metrics(
                    Namespace='SREDemo/Application',
                    MetricName=metric_name
                )
                results[metric_name] = len(response['Metrics']) > 0
                print(f"    - Metric {metric_name}: {'✓' if results[metric_name] else '✗'}")
            except Exception as e:
                results[metric_name] = False
                print(f"    - Metric {metric_name}: ✗ ({str(e)})")
        
        return results
    
    def verify_logs_exist(self, log_group, log_stream):
        """Verify CloudWatch logs exist."""
        try:
            response = self.logs_client.describe_log_streams(
                logGroupName=log_group,
                logStreamNamePrefix=log_stream,
                limit=1
            )
            exists = len(response['logStreams']) > 0
            print(f"    - Logs {log_group}/{log_stream}: {'✓' if exists else '✗'}")
            return exists
        except Exception as e:
            print(f"    - Logs {log_group}/{log_stream}: ✗ ({str(e)})")
            return False
    
    def print_test_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, passed, message in self.test_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {test_name}: {message}")
        
        print("\n" + "="*60)
        
        # Demo value summary
        print("\n🌟 DEMO VALUE DEMONSTRATED:")
        print("="*60)
        print("✅ Change Correlation: Shows how config changes directly cause incidents")
        print("✅ Defect Correlation: Links incidents to known defects with evidence")
        print("✅ JMS Analysis: Provides detailed queue metrics and session diagnostics")
        print("✅ Security Correlation: Correlates VPC + CloudTrail for security incidents")
        print("\n📈 Key Capabilities:")
        print("  - Real AWS resource creation (OpsItems, Metrics, Logs)")
        print("  - Multi-source correlation (VPC, CloudTrail, CloudWatch)")
        print("  - Timeline analysis (change → incident progression)")
        print("  - Root cause identification with evidence")
        print("  - Automated defect linking")
        print("  - Security threat detection and correlation")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = ComprehensiveDemoTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All comprehensive demo tests passed!")
        print("🚀 Ready for demonstration!")
    else:
        print("\n⚠️ Some tests failed. Please check the logs.")
        
    # Additional demo instructions
    print("\n" + "="*60)
    print("📝 DEMO INSTRUCTIONS")
    print("="*60)
    print("1. Access the dashboard: http://52.2.131.112")
    print("2. Click 'Incident Management' in sidebar")
    print("3. Select '🌟 Comprehensive Demo' from category dropdown")
    print("4. Choose a demo scenario and click 'Generate Real Incident'")
    print("5. After incident is created, click 'Analyze Incident'")
    print("6. Select the created OpsItem and click 'Analyze Root Cause'")
    print("7. Review the comprehensive analysis showing correlations")
    print("\n🎯 Each scenario demonstrates specific SRE capabilities!")
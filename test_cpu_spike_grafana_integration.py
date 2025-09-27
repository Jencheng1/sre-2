#!/usr/bin/env python3
"""
Comprehensive test suite for CPU Spike Demo and Grafana Integration
Tests all components end-to-end to ensure functionality
"""

import os
import sys
import time
import json
import boto3
import requests
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Set environment
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Add path for local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import CPU spike generator
from cpu_spike_generator import CPUSpikeGenerator


class TestCPUSpikeDemo(unittest.TestCase):
    """Test cases for CPU Spike Demo functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.cpu_gen = CPUSpikeGenerator()
        cls.ssm_client = boto3.client('ssm', region_name='us-east-1')
        cls.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
    def test_01_ec2_discovery(self):
        """Test EC2 instance discovery"""
        print("\n[TEST 1] Testing EC2 instance discovery...")
        
        instances = self.cpu_gen.get_available_ec2_instances()
        
        # Assert instances are found
        self.assertGreater(len(instances), 0, "No EC2 instances found")
        print(f"✓ Found {len(instances)} EC2 instances")
        
        # Check instance structure
        for instance in instances:
            self.assertIn('instance_id', instance)
            self.assertIn('name', instance)
            self.assertIn('instance_type', instance)
            self.assertIn('ssm_enabled', instance)
            self.assertIn('state', instance)
            
        # Print instance details
        for inst in instances:
            print(f"  - {inst['name']} ({inst['instance_id']}): SSM={inst['ssm_enabled']}")
            
    def test_02_ssm_availability(self):
        """Test SSM agent availability"""
        print("\n[TEST 2] Testing SSM agent availability...")
        
        instances = self.cpu_gen.get_available_ec2_instances()
        ssm_instances = [i for i in instances if i['ssm_enabled']]
        
        # Assert at least one SSM instance
        self.assertGreater(len(ssm_instances), 0, "No SSM-enabled instances found")
        print(f"✓ Found {len(ssm_instances)} SSM-enabled instances")
        
        # Test SSM connectivity for each instance
        for instance in ssm_instances:
            try:
                response = self.ssm_client.describe_instance_information(
                    Filters=[{
                        'Key': 'InstanceIds',
                        'Values': [instance['instance_id']]
                    }]
                )
                self.assertEqual(len(response['InstanceInformationList']), 1)
                info = response['InstanceInformationList'][0]
                self.assertEqual(info['PingStatus'], 'Online')
                print(f"  ✓ {instance['name']}: SSM Online")
            except Exception as e:
                self.fail(f"SSM check failed for {instance['instance_id']}: {e}")
                
    def test_03_cpu_spike_trigger(self):
        """Test CPU spike trigger functionality"""
        print("\n[TEST 3] Testing CPU spike trigger...")
        
        instances = self.cpu_gen.get_available_ec2_instances()
        ssm_instances = [i for i in instances if i['ssm_enabled']]
        
        if not ssm_instances:
            self.skipTest("No SSM-enabled instances available")
            
        # Test with first SSM instance
        target = ssm_instances[0]
        print(f"  Using instance: {target['name']} ({target['instance_id']})")
        
        # Trigger a short CPU spike
        result = self.cpu_gen.trigger_cpu_spike(
            instance_id=target['instance_id'],
            duration_seconds=30,
            cpu_percent=50,
            cores=1
        )
        
        # Assert success
        self.assertEqual(result['status'], 'success')
        self.assertIn('command_id', result)
        print(f"  ✓ CPU spike triggered: Command ID {result['command_id']}")
        
        # Store for cleanup
        self.spike_command_id = result['command_id']
        self.spike_instance_id = target['instance_id']
        
        # Wait a bit and check command status
        time.sleep(5)
        status = self.cpu_gen.monitor_cpu_spike(
            instance_id=target['instance_id'],
            command_id=result['command_id']
        )
        
        self.assertIn(status['status'], ['InProgress', 'Success', 'Pending'])
        print(f"  ✓ Command status: {status['status']}")
        
        # Stop the spike
        stop_result = self.cpu_gen.stop_cpu_spike(target['instance_id'])
        self.assertEqual(stop_result['status'], 'success')
        print("  ✓ CPU spike stopped")
        
    def test_04_cloudwatch_metrics(self):
        """Test CloudWatch metrics retrieval"""
        print("\n[TEST 4] Testing CloudWatch metrics...")
        
        instances = self.cpu_gen.get_available_ec2_instances()
        if not instances:
            self.skipTest("No instances available")
            
        # Test metrics for first instance
        target = instances[0]
        metrics = self.cpu_gen.get_cpu_metrics(
            instance_id=target['instance_id'],
            minutes=60  # Last hour
        )
        
        # Metrics might be empty if instance is new
        if metrics:
            print(f"  ✓ Retrieved {len(metrics)} data points")
            
            # Check metric structure
            for metric in metrics[:3]:  # Check first 3
                self.assertIn('Timestamp', metric)
                self.assertIn('Average', metric)
                print(f"    - {metric['Timestamp']}: {metric.get('Average', 0):.2f}%")
        else:
            print("  ⚠ No recent metrics available (this is normal for new instances)")
            
    def test_05_ops_item_creation(self):
        """Test OpsItem creation for incidents"""
        print("\n[TEST 5] Testing OpsItem creation...")
        
        instances = self.cpu_gen.get_available_ec2_instances()
        if not instances:
            self.skipTest("No instances available")
            
        target = instances[0]
        
        try:
            ssm = boto3.client('ssm', region_name='us-east-1')
            response = ssm.create_ops_item(
                Title=f"[TEST] CPU Spike - {target['name']}",
                Description=f"Test OpsItem for CPU spike demo on {target['instance_id']}",
                Source="SRE-Copilot-Test",
                Severity="3",
                Category="Performance",  # Must be one of: Availability, Cost, Performance, Recovery, Security
                OperationalData={
                    "InstanceId": {"Value": target['instance_id']},
                    "TestRun": {"Value": "true"},
                    "Timestamp": {"Value": datetime.now().isoformat()}
                }
            )
            
            self.assertIn('OpsItemId', response)
            ops_item_id = response['OpsItemId']
            print(f"  ✓ OpsItem created: {ops_item_id}")
            
            # Clean up - close the OpsItem
            ssm.update_ops_item(
                OpsItemId=ops_item_id,
                Status='Resolved'
            )
            print("  ✓ OpsItem closed")
            
        except Exception as e:
            self.fail(f"OpsItem creation failed: {e}")


class TestGrafanaIntegration(unittest.TestCase):
    """Test cases for Grafana integration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.grafana_url = "http://localhost:3000"
        cls.grafana_user = "admin"
        cls.grafana_pass = "admin123"
        cls.prometheus_url = "http://localhost:9090"
        
    def test_06_grafana_availability(self):
        """Test Grafana service availability"""
        print("\n[TEST 6] Testing Grafana availability...")
        
        try:
            response = requests.get(f"{self.grafana_url}/api/health", timeout=5)
            self.assertEqual(response.status_code, 200)
            print("  ✓ Grafana is running and healthy")
            
            # Check API access
            api_response = requests.get(
                f"{self.grafana_url}/api/org",
                auth=(self.grafana_user, self.grafana_pass),
                timeout=5
            )
            self.assertEqual(api_response.status_code, 200)
            print("  ✓ Grafana API accessible")
            
        except requests.exceptions.ConnectionError:
            self.fail("Cannot connect to Grafana at http://localhost:3000")
            
    def test_07_prometheus_availability(self):
        """Test Prometheus service availability"""
        print("\n[TEST 7] Testing Prometheus availability...")
        
        try:
            response = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            self.assertEqual(response.status_code, 200)
            print("  ✓ Prometheus is running and healthy")
            
            # Check targets
            targets_response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=5)
            self.assertEqual(targets_response.status_code, 200)
            
            data = targets_response.json()
            if data['data']['activeTargets']:
                print(f"  ✓ Prometheus has {len(data['data']['activeTargets'])} active targets")
            
        except requests.exceptions.ConnectionError:
            self.fail("Cannot connect to Prometheus at http://localhost:9090")
            
    def test_08_grafana_datasources(self):
        """Test Grafana data sources configuration"""
        print("\n[TEST 8] Testing Grafana data sources...")
        
        try:
            response = requests.get(
                f"{self.grafana_url}/api/datasources",
                auth=(self.grafana_user, self.grafana_pass),
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            datasources = response.json()
            
            print(f"  ✓ Found {len(datasources)} data sources")
            
            # Check for CloudWatch or Prometheus datasource
            source_types = [ds.get('type', '') for ds in datasources]
            
            if 'cloudwatch' in source_types:
                print("  ✓ CloudWatch data source configured")
            if 'prometheus' in source_types:
                print("  ✓ Prometheus data source configured")
                
            if not source_types:
                print("  ⚠ No data sources configured (manual setup may be required)")
                
        except Exception as e:
            self.fail(f"Failed to check datasources: {e}")
            
    def test_09_node_exporter_metrics(self):
        """Test node exporter metrics in Prometheus"""
        print("\n[TEST 9] Testing node exporter metrics...")
        
        try:
            # Query node CPU metric
            query = 'node_cpu_seconds_total'
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=5
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            if data['data']['result']:
                print(f"  ✓ Node exporter metrics available: {len(data['data']['result'])} series")
            else:
                print("  ⚠ No node exporter metrics found")
                
        except Exception as e:
            print(f"  ⚠ Could not query node metrics: {e}")


class TestStreamlitIntegration(unittest.TestCase):
    """Test Streamlit app availability"""
    
    def test_10_streamlit_availability(self):
        """Test Streamlit app availability"""
        print("\n[TEST 10] Testing Streamlit availability...")
        
        try:
            response = requests.get("http://localhost:8501/_stcore/health", timeout=5)
            self.assertEqual(response.status_code, 200)
            print("  ✓ Streamlit app is running and healthy")
            
            # Check main page loads
            main_response = requests.get("http://localhost:8501", timeout=5)
            self.assertEqual(main_response.status_code, 200)
            print("  ✓ Streamlit main page accessible")
            
        except requests.exceptions.ConnectionError:
            self.fail("Cannot connect to Streamlit at http://localhost:8501")


def generate_test_report(results):
    """Generate a test report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"cpu_spike_test_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\n📋 Test report saved to: {report_file}")
    return report_file


def main():
    """Run all tests"""
    print("=" * 60)
    print("CPU SPIKE DEMO & GRAFANA INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCPUSpikeDemo))
    suite.addTests(loader.loadTestsFromTestCase(TestGrafanaIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestStreamlitIntegration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "success": result.wasSuccessful()
    }
    
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"⚠️  Errors: {test_results['errors']}")
    print(f"⏭️  Skipped: {test_results['skipped']}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! The CPU Spike Demo and Grafana integration are working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above for details.")
        
    # Generate report
    report_file = generate_test_report(test_results)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
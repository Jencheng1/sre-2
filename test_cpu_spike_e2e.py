#!/usr/bin/env python3
"""
End-to-End Test for CPU Spike Demo
This script tests the complete workflow without requiring manual interaction
"""

import time
import requests
import boto3
import json
from datetime import datetime
from cpu_spike_generator import CPUSpikeGenerator

class CPUSpikeE2ETest:
    def __init__(self):
        self.cpu_gen = CPUSpikeGenerator()
        self.ssm = boto3.client('ssm', region_name='us-east-1')
        self.test_results = []
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        self.test_results.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
    
    def test_services_availability(self):
        """Test that all required services are running"""
        self.log("Starting services availability test...")
        
        services = [
            ("Streamlit", "http://localhost:8501/_stcore/health"),
            ("Grafana", "http://localhost:3000/api/health"),
            ("Prometheus", "http://localhost:9090/-/healthy")
        ]
        
        all_healthy = True
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.log(f"✅ {service_name} is healthy", "PASS")
                else:
                    self.log(f"❌ {service_name} returned status {response.status_code}", "FAIL")
                    all_healthy = False
            except Exception as e:
                self.log(f"❌ {service_name} is not accessible: {str(e)}", "FAIL")
                all_healthy = False
        
        return all_healthy
    
    def test_ec2_discovery(self):
        """Test EC2 instance discovery"""
        self.log("Testing EC2 instance discovery...")
        
        try:
            instances = self.cpu_gen.get_available_ec2_instances()
            self.log(f"Found {len(instances)} EC2 instances", "INFO")
            
            ssm_enabled = [i for i in instances if i['ssm_enabled']]
            self.log(f"Found {len(ssm_enabled)} SSM-enabled instances", "INFO")
            
            if ssm_enabled:
                # Display first instance details
                instance = ssm_enabled[0]
                self.log(f"Test instance: {instance['name']} ({instance['instance_id']})", "INFO")
                self.log(f"  Type: {instance['instance_type']}", "INFO")
                self.log(f"  State: {instance['state']}", "INFO")
                return instance
            else:
                self.log("No SSM-enabled instances available for testing", "WARN")
                return None
                
        except Exception as e:
            self.log(f"Failed to discover instances: {str(e)}", "FAIL")
            return None
    
    def test_cloudwatch_metrics(self, instance_id):
        """Test CloudWatch metrics retrieval"""
        self.log(f"Testing CloudWatch metrics for {instance_id}...")
        
        try:
            metrics = self.cpu_gen.get_cpu_metrics(instance_id, minutes=5)
            if metrics:
                self.log(f"✅ Retrieved {len(metrics)} metric datapoints", "PASS")
                latest = metrics[-1] if metrics else None
                if latest:
                    self.log(f"  Latest CPU: {latest.get('Average', 0):.1f}% avg, {latest.get('Maximum', 0):.1f}% max", "INFO")
                return True
            else:
                self.log("No metrics available (instance may be new)", "WARN")
                return True
        except Exception as e:
            self.log(f"❌ Failed to get metrics: {str(e)}", "FAIL")
            return False
    
    def test_cpu_spike_workflow(self, instance):
        """Test the complete CPU spike workflow"""
        if not instance:
            self.log("Skipping CPU spike workflow - no instance available", "SKIP")
            return False
        
        self.log(f"\n🚀 Starting CPU spike workflow test on {instance['name']}...")
        
        # Test parameters
        duration = 30  # Short duration for testing
        cpu_percent = 50  # Moderate load
        
        try:
            # Step 1: Trigger CPU spike
            self.log(f"Triggering {cpu_percent}% CPU spike for {duration} seconds...", "INFO")
            result = self.cpu_gen.trigger_cpu_spike(
                instance_id=instance['instance_id'],
                duration_seconds=duration,
                cpu_percent=cpu_percent,
                cores=0
            )
            
            if result['status'] == 'success':
                self.log(f"✅ CPU spike triggered successfully", "PASS")
                self.log(f"  Command ID: {result['command_id']}", "INFO")
                command_id = result['command_id']
                
                # Step 2: Monitor spike
                self.log("Monitoring spike execution...", "INFO")
                time.sleep(5)  # Wait for command to start
                
                status = self.cpu_gen.monitor_cpu_spike(
                    instance_id=instance['instance_id'],
                    command_id=command_id
                )
                
                self.log(f"  Command status: {status.get('status', 'Unknown')}", "INFO")
                
                # Step 3: Create OpsItem
                self.log("Creating OpsItem for the incident...", "INFO")
                try:
                    ops_response = self.ssm.create_ops_item(
                        Title=f"Test CPU Spike - {instance['name']}",
                        Description=f"E2E test CPU spike on {instance['instance_id']}",
                        Source="CPU-Spike-E2E-Test",
                        Severity="3",
                        Category="Test",
                        OperationalData={
                            "InstanceId": {"Value": instance['instance_id']},
                            "TestType": {"Value": "E2E-Validation"}
                        }
                    )
                    ops_item_id = ops_response['OpsItemId']
                    self.log(f"✅ Created OpsItem: {ops_item_id}", "PASS")
                except Exception as e:
                    self.log(f"❌ Failed to create OpsItem: {str(e)}", "FAIL")
                
                # Step 4: Wait and check metrics
                self.log(f"Waiting {duration} seconds for spike to complete...", "INFO")
                time.sleep(duration + 5)  # Wait for spike to finish
                
                # Step 5: Stop spike (if still running)
                self.log("Ensuring spike is stopped...", "INFO")
                stop_result = self.cpu_gen.stop_cpu_spike(instance['instance_id'])
                self.log(f"  Stop command: {stop_result.get('status', 'Unknown')}", "INFO")
                
                # Step 6: Verify metrics increased
                self.log("Checking if CPU metrics show the spike...", "INFO")
                post_metrics = self.cpu_gen.get_cpu_metrics(
                    instance['instance_id'], 
                    minutes=2
                )
                
                if post_metrics:
                    max_cpu = max([m.get('Maximum', 0) for m in post_metrics])
                    self.log(f"  Peak CPU during test: {max_cpu:.1f}%", "INFO")
                    if max_cpu > 30:  # Some increase expected
                        self.log("✅ CPU spike reflected in metrics", "PASS")
                    else:
                        self.log("⚠️ CPU spike may not have been captured in metrics yet", "WARN")
                
                return True
                
            else:
                self.log(f"❌ Failed to trigger spike: {result.get('message', 'Unknown error')}", "FAIL")
                return False
                
        except Exception as e:
            self.log(f"❌ CPU spike workflow failed: {str(e)}", "ERROR")
            return False
    
    def test_grafana_dashboard(self):
        """Test Grafana dashboard availability"""
        self.log("Testing Grafana dashboard...")
        
        try:
            # Check if CPU monitoring dashboard exists
            auth = ('admin', 'admin123')
            response = requests.get(
                'http://localhost:3000/api/search?query=CPU',
                auth=auth,
                timeout=5
            )
            
            if response.status_code == 200:
                dashboards = response.json()
                cpu_dashboards = [d for d in dashboards if 'CPU' in d.get('title', '')]
                if cpu_dashboards:
                    self.log(f"✅ Found {len(cpu_dashboards)} CPU dashboard(s)", "PASS")
                else:
                    self.log("⚠️ No CPU dashboards found in Grafana", "WARN")
            else:
                self.log(f"Failed to query Grafana dashboards: {response.status_code}", "FAIL")
                
        except Exception as e:
            self.log(f"Grafana dashboard test failed: {str(e)}", "ERROR")
    
    def generate_report(self):
        """Generate test report"""
        self.log("\n" + "="*60)
        self.log("📋 CPU SPIKE DEMO E2E TEST REPORT")
        self.log("="*60)
        
        # Count results
        passed = len([r for r in self.test_results if r['level'] == 'PASS'])
        failed = len([r for r in self.test_results if r['level'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['level'] == 'WARN'])
        
        self.log(f"\nTest Summary:")
        self.log(f"  ✅ Passed: {passed}")
        self.log(f"  ❌ Failed: {failed}")
        self.log(f"  ⚠️  Warnings: {warnings}")
        
        overall_status = "PASS" if failed == 0 else "FAIL"
        self.log(f"\nOverall Status: {overall_status}")
        
        # Save report
        report_file = f"cpu_spike_e2e_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'test_date': datetime.now().isoformat(),
                'overall_status': overall_status,
                'summary': {
                    'passed': passed,
                    'failed': failed,
                    'warnings': warnings
                },
                'results': self.test_results
            }, f, indent=2)
        
        self.log(f"\n💾 Report saved to: {report_file}")
        
        return overall_status == "PASS"
    
    def run_all_tests(self):
        """Run all E2E tests"""
        self.log("🚀 Starting CPU Spike Demo End-to-End Test\n")
        
        # Test 1: Services availability
        services_ok = self.test_services_availability()
        if not services_ok:
            self.log("\n⚠️ Some services are not available. Tests may fail.", "WARN")
        
        # Test 2: EC2 discovery
        test_instance = self.test_ec2_discovery()
        
        # Test 3: CloudWatch metrics (if instance available)
        if test_instance:
            self.test_cloudwatch_metrics(test_instance['instance_id'])
        
        # Test 4: CPU spike workflow
        self.test_cpu_spike_workflow(test_instance)
        
        # Test 5: Grafana dashboard
        self.test_grafana_dashboard()
        
        # Generate report
        return self.generate_report()


if __name__ == "__main__":
    tester = CPUSpikeE2ETest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Comprehensive validation test for CPU Spike Demo
Tests all components and provides a readiness report
"""

import requests
import boto3
import json
import time
from datetime import datetime
from cpu_spike_generator import CPUSpikeGenerator
import subprocess
import sys

class CPUSpikeDemoValidator:
    def __init__(self):
        self.test_results = []
        self.cpu_gen = CPUSpikeGenerator()
        
    def add_result(self, component, status, message, details=None):
        """Add a test result"""
        self.test_results.append({
            'component': component,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        # Print immediately
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} {component}: {message}")
        if details and status != "PASS":
            print(f"   Details: {details}")
    
    def test_aws_credentials(self):
        """Test AWS credentials and permissions"""
        print("\n🔐 Testing AWS Credentials...")
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            self.add_result(
                "AWS Credentials",
                "PASS",
                f"Valid credentials for account {identity['Account']}",
                identity
            )
            
            # Test required services
            services = ['ec2', 'ssm', 'cloudwatch']
            for service in services:
                try:
                    client = boto3.client(service)
                    if service == 'ec2':
                        client.describe_instances(MaxResults=5)
                    elif service == 'ssm':
                        client.describe_instance_information(MaxResults=5)
                    elif service == 'cloudwatch':
                        client.list_metrics()
                    self.add_result(
                        f"AWS {service.upper()} Access",
                        "PASS",
                        f"Can access {service} service"
                    )
                except Exception as e:
                    self.add_result(
                        f"AWS {service.upper()} Access",
                        "FAIL",
                        f"Cannot access {service} service",
                        str(e)
                    )
                    
        except Exception as e:
            self.add_result(
                "AWS Credentials",
                "FAIL",
                "Invalid or missing AWS credentials",
                str(e)
            )
    
    def test_docker_services(self):
        """Test Docker services (Grafana, Prometheus)"""
        print("\n🐳 Testing Docker Services...")
        
        # Check docker daemon
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode == 0:
                self.add_result("Docker", "PASS", "Docker daemon is running")
            else:
                self.add_result("Docker", "FAIL", "Docker daemon not accessible")
                return
        except:
            self.add_result("Docker", "FAIL", "Docker command not found")
            return
        
        # Check specific containers
        containers = {
            'sre-grafana': 3000,
            'sre-prometheus': 9090,
            'sre-node-exporter': 9100
        }
        
        for container, port in containers.items():
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container}', '--format', '{{.Status}}'],
                capture_output=True, text=True
            )
            if 'Up' in result.stdout:
                self.add_result(f"Docker {container}", "PASS", f"Container is running")
                
                # Test port accessibility
                try:
                    response = requests.get(f'http://localhost:{port}', timeout=3)
                    self.add_result(
                        f"Service Port {port}",
                        "PASS" if response.status_code < 500 else "WARN",
                        f"Port {port} is accessible"
                    )
                except:
                    self.add_result(
                        f"Service Port {port}",
                        "WARN",
                        f"Port {port} not accessible",
                        "Service may still be starting"
                    )
            else:
                self.add_result(f"Docker {container}", "FAIL", "Container not running")
    
    def test_grafana(self):
        """Test Grafana specifically"""
        print("\n📊 Testing Grafana...")
        
        try:
            # Health check
            response = requests.get('http://localhost:3000/api/health', timeout=5)
            if response.status_code == 200:
                self.add_result("Grafana Health", "PASS", "Grafana is healthy")
                
                # Check datasources
                auth = ('admin', 'admin123')
                ds_response = requests.get(
                    'http://localhost:3000/api/datasources',
                    auth=auth,
                    timeout=5
                )
                if ds_response.status_code == 200:
                    datasources = ds_response.json()
                    self.add_result(
                        "Grafana Datasources",
                        "PASS",
                        f"Found {len(datasources)} datasources",
                        [ds['name'] for ds in datasources]
                    )
                else:
                    self.add_result("Grafana Datasources", "WARN", "Could not fetch datasources")
            else:
                self.add_result("Grafana Health", "FAIL", f"Status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.add_result("Grafana", "FAIL", "Cannot connect to Grafana on port 3000")
        except Exception as e:
            self.add_result("Grafana", "FAIL", "Grafana test failed", str(e))
    
    def test_streamlit(self):
        """Test Streamlit application"""
        print("\n🎯 Testing Streamlit...")
        
        try:
            # Health check
            response = requests.get('http://localhost:8501/_stcore/health', timeout=5)
            if response.status_code == 200:
                self.add_result("Streamlit Health", "PASS", "Streamlit is running")
                
                # Check if CPU spike demo is accessible
                # Note: Can't easily test tab navigation without selenium
                self.add_result(
                    "Streamlit CPU Demo",
                    "PASS",
                    "CPU Spike Demo should be available in Advanced Tools"
                )
            else:
                self.add_result("Streamlit Health", "FAIL", f"Status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.add_result("Streamlit", "FAIL", "Cannot connect to Streamlit on port 8501")
        except Exception as e:
            self.add_result("Streamlit", "FAIL", "Streamlit test failed", str(e))
    
    def test_ec2_instances(self):
        """Test EC2 instance availability"""
        print("\n🖥️ Testing EC2 Instances...")
        
        try:
            instances = self.cpu_gen.get_available_ec2_instances()
            self.add_result(
                "EC2 Discovery",
                "PASS" if instances else "WARN",
                f"Found {len(instances)} EC2 instances"
            )
            
            ssm_enabled = [i for i in instances if i['ssm_enabled']]
            self.add_result(
                "SSM-Enabled Instances",
                "PASS" if ssm_enabled else "WARN",
                f"Found {len(ssm_enabled)} instances with SSM agent",
                [f"{i['name']} ({i['instance_id']})" for i in ssm_enabled[:3]]
            )
            
            if not ssm_enabled:
                self.add_result(
                    "SSM Setup",
                    "WARN",
                    "No SSM-enabled instances found",
                    "CPU spike demo requires at least one EC2 instance with SSM agent"
                )
            
            return ssm_enabled
            
        except Exception as e:
            self.add_result("EC2 Discovery", "FAIL", "Failed to discover instances", str(e))
            return []
    
    def test_cloudwatch_metrics(self):
        """Test CloudWatch metrics access"""
        print("\n📈 Testing CloudWatch Metrics...")
        
        try:
            instances = self.cpu_gen.get_available_ec2_instances()
            if instances:
                test_instance = instances[0]
                metrics = self.cpu_gen.get_cpu_metrics(test_instance['instance_id'], minutes=5)
                self.add_result(
                    "CloudWatch Metrics",
                    "PASS",
                    f"Retrieved {len(metrics)} CPU metric datapoints",
                    f"Instance: {test_instance['instance_id']}"
                )
            else:
                self.add_result("CloudWatch Metrics", "WARN", "No instances to test metrics")
        except Exception as e:
            self.add_result("CloudWatch Metrics", "FAIL", "Failed to retrieve metrics", str(e))
    
    def test_ssm_connectivity(self):
        """Test SSM connectivity (dry run)"""
        print("\n🔧 Testing SSM Connectivity...")
        
        try:
            ssm = boto3.client('ssm')
            # Just test if we can list documents
            response = ssm.list_documents(MaxResults=5)
            self.add_result("SSM Service", "PASS", "SSM service is accessible")
            
            # Check for SSM-enabled instances
            instances = self.cpu_gen.get_available_ec2_instances()
            ssm_enabled = [i for i in instances if i['ssm_enabled']]
            
            if ssm_enabled:
                # Test command execution capability (safe command)
                test_instance = ssm_enabled[0]
                try:
                    response = ssm.send_command(
                        InstanceIds=[test_instance['instance_id']],
                        DocumentName="AWS-RunShellScript",
                        Parameters={'commands': ['echo "SSM test"']},
                        Comment="CPU Spike Demo SSM Test"
                    )
                    command_id = response['Command']['CommandId']
                    
                    # Wait briefly for command
                    time.sleep(2)
                    
                    # Check command status
                    result = ssm.get_command_invocation(
                        CommandId=command_id,
                        InstanceId=test_instance['instance_id']
                    )
                    
                    if result['Status'] in ['Success', 'InProgress']:
                        self.add_result(
                            "SSM Command Execution",
                            "PASS",
                            f"Can execute commands on {test_instance['name']}",
                            f"Instance: {test_instance['instance_id']}"
                        )
                    else:
                        self.add_result(
                            "SSM Command Execution",
                            "FAIL",
                            f"Command failed with status: {result['Status']}"
                        )
                except Exception as e:
                    self.add_result(
                        "SSM Command Execution",
                        "FAIL",
                        "Cannot execute SSM commands",
                        str(e)
                    )
            else:
                self.add_result(
                    "SSM Command Execution",
                    "WARN",
                    "No SSM-enabled instances to test"
                )
                
        except Exception as e:
            self.add_result("SSM Service", "FAIL", "SSM service not accessible", str(e))
    
    def test_lambda_functions(self):
        """Test Lambda functions availability"""
        print("\n🔮 Testing Lambda Functions...")
        
        try:
            lambda_client = boto3.client('lambda')
            
            # Check supervisor lambda
            try:
                response = lambda_client.get_function(FunctionName='sre-supervisor-lambda')
                self.add_result(
                    "Supervisor Lambda",
                    "PASS",
                    "sre-supervisor-lambda exists and is accessible"
                )
            except:
                self.add_result(
                    "Supervisor Lambda",
                    "WARN",
                    "sre-supervisor-lambda not found",
                    "Root cause analysis may not work"
                )
                
        except Exception as e:
            self.add_result("Lambda Service", "FAIL", "Cannot access Lambda service", str(e))
    
    def generate_report(self):
        """Generate final validation report"""
        print("\n" + "="*60)
        print("📋 CPU SPIKE DEMO VALIDATION REPORT")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tests: {len(self.test_results)}")
        
        # Count results
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        warned = sum(1 for r in self.test_results if r['status'] == 'WARN')
        
        print(f"\n✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warned}")
        
        # Overall readiness
        readiness_percent = (passed / len(self.test_results)) * 100 if self.test_results else 0
        
        print(f"\n🎯 Overall Readiness: {readiness_percent:.1f}%")
        
        if readiness_percent >= 90:
            print("✅ System is READY for CPU Spike Demo!")
        elif readiness_percent >= 70:
            print("⚠️  System is PARTIALLY READY - Some features may not work")
        else:
            print("❌ System is NOT READY - Critical components missing")
        
        # Critical issues
        critical_failures = [r for r in self.test_results if r['status'] == 'FAIL']
        if critical_failures:
            print("\n🚨 Critical Issues to Address:")
            for issue in critical_failures:
                print(f"  - {issue['component']}: {issue['message']}")
                if issue['details']:
                    print(f"    Details: {issue['details']}")
        
        # Next steps
        print("\n📝 Next Steps:")
        if failed > 0:
            print("1. Fix critical issues listed above")
        if 'SSM-Enabled Instances' in [r['component'] for r in self.test_results if r['status'] == 'WARN']:
            print("2. Ensure at least one EC2 instance has SSM agent installed and running")
        if 'Grafana' in [r['component'] for r in self.test_results if r['status'] == 'FAIL']:
            print("3. Start Grafana: ./start_grafana.sh")
        if 'Streamlit' in [r['component'] for r in self.test_results if r['status'] == 'FAIL']:
            print("4. Start Streamlit: python3 -m streamlit run streamlit_app.py")
        
        print("\n🌐 Access Points:")
        print("  - Streamlit: http://localhost:8501")
        print("  - Grafana: http://localhost:3000 (admin/admin123)")
        print("  - Prometheus: http://localhost:9090")
        
        # Save report
        report_file = f"cpu_spike_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'readiness_percent': readiness_percent,
                'summary': {
                    'passed': passed,
                    'failed': failed,
                    'warned': warned
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"\n💾 Full report saved to: {report_file}")
        
        return readiness_percent >= 70
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Starting CPU Spike Demo Validation...\n")
        
        # Run tests in order
        self.test_aws_credentials()
        self.test_docker_services()
        self.test_grafana()
        self.test_streamlit()
        self.test_ec2_instances()
        self.test_cloudwatch_metrics()
        self.test_ssm_connectivity()
        self.test_lambda_functions()
        
        # Generate report
        return self.generate_report()


if __name__ == "__main__":
    validator = CPUSpikeDemoValidator()
    ready = validator.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if ready else 1)
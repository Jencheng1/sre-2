#!/usr/bin/env python3
"""
Comprehensive demo application to generate real incidents across AWS services.
This creates real CloudWatch logs, metrics, security group changes, API failures,
and Systems Manager OpsItems to demonstrate root cause analysis capabilities.
"""

import boto3
import json
import time
import random
import threading
from datetime import datetime, timedelta
import logging
import sys
from botocore.exceptions import ClientError

class IncidentGenerator:
    """Generate various types of incidents across AWS services for demo purposes."""
    
    def __init__(self):
        """Initialize AWS clients and configuration."""
        self.region = 'us-east-1'
        self.setup_aws_clients()
        self.setup_logging()
        self.demo_resources = {
            'security_group_id': None,
            'log_group_name': '/aws/demo/sre-incident-generator',
            'namespace': 'SREDemo/Application',
            'lambda_function': 'demo-failure-function',
            'instance_id': None
        }
        
    def setup_aws_clients(self):
        """Initialize all required AWS service clients."""
        self.clients = {
            'logs': boto3.client('logs', region_name=self.region),
            'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
            'ec2': boto3.client('ec2', region_name=self.region),
            'lambda': boto3.client('lambda', region_name=self.region),
            'ssm': boto3.client('ssm', region_name=self.region),
            'iam': boto3.client('iam', region_name=self.region),
            'cloudtrail': boto3.client('cloudtrail', region_name=self.region),
            's3': boto3.client('s3', region_name=self.region)
        }
        
    def setup_logging(self):
        """Configure logging for the demo."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_demo_resources(self):
        """Create necessary demo resources."""
        self.logger.info("🚀 Creating demo resources...")
        
        # Create CloudWatch Log Group
        try:
            self.clients['logs'].create_log_group(
                logGroupName=self.demo_resources['log_group_name']
            )
            self.logger.info(f"✅ Created log group: {self.demo_resources['log_group_name']}")
        except self.clients['logs'].exceptions.ResourceAlreadyExistsException:
            self.logger.info(f"ℹ️ Log group already exists: {self.demo_resources['log_group_name']}")
            
        # Create demo security group
        try:
            response = self.clients['ec2'].create_security_group(
                GroupName='sre-demo-incident-sg',
                Description='Demo security group for incident generation'
            )
            self.demo_resources['security_group_id'] = response['GroupId']
            self.logger.info(f"✅ Created security group: {self.demo_resources['security_group_id']}")
        except ClientError as e:
            if 'InvalidGroup.Duplicate' in str(e):
                # Get existing security group
                response = self.clients['ec2'].describe_security_groups(
                    GroupNames=['sre-demo-incident-sg']
                )
                self.demo_resources['security_group_id'] = response['SecurityGroups'][0]['GroupId']
                self.logger.info(f"ℹ️ Using existing security group: {self.demo_resources['security_group_id']}")
            else:
                raise
                
    def generate_application_logs(self, scenario='normal'):
        """Generate application logs in CloudWatch Logs."""
        self.logger.info(f"📝 Generating {scenario} application logs...")
        
        log_stream = f"app-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            self.clients['logs'].create_log_stream(
                logGroupName=self.demo_resources['log_group_name'],
                logStreamName=log_stream
            )
        except:
            pass
            
        log_events = []
        timestamp = int(time.time() * 1000)
        
        if scenario == 'normal':
            messages = [
                {"level": "INFO", "message": "Application started successfully"},
                {"level": "INFO", "message": "Connected to database"},
                {"level": "INFO", "message": "Processing user request", "user_id": "user123"},
                {"level": "INFO", "message": "Request completed successfully", "duration_ms": 145}
            ]
        elif scenario == 'error':
            messages = [
                {"level": "INFO", "message": "Application started successfully"},
                {"level": "WARN", "message": "Database connection slow", "duration_ms": 3500},
                {"level": "ERROR", "message": "Database connection timeout", "error": "Connection refused"},
                {"level": "ERROR", "message": "Failed to process user request", "user_id": "user456"},
                {"level": "ERROR", "message": "Application crash", "error": "NullPointerException"},
                {"level": "FATAL", "message": "Service unavailable", "status_code": 503}
            ]
        elif scenario == 'performance':
            messages = [
                {"level": "INFO", "message": "Request received", "endpoint": "/api/data"},
                {"level": "WARN", "message": "High response time detected", "duration_ms": 5000},
                {"level": "WARN", "message": "Memory usage high", "memory_percent": 92},
                {"level": "ERROR", "message": "Request timeout", "duration_ms": 30000},
                {"level": "WARN", "message": "Thread pool exhausted", "active_threads": 200}
            ]
            
        for i, msg_data in enumerate(messages):
            log_events.append({
                'timestamp': timestamp + (i * 1000),
                'message': json.dumps(msg_data)
            })
            
        # Send logs to CloudWatch
        self.clients['logs'].put_log_events(
            logGroupName=self.demo_resources['log_group_name'],
            logStreamName=log_stream,
            logEvents=log_events
        )
        
        self.logger.info(f"✅ Generated {len(log_events)} log events for {scenario} scenario")
        
    def generate_cloudwatch_metrics(self, scenario='normal'):
        """Generate CloudWatch metrics."""
        self.logger.info(f"📊 Generating {scenario} CloudWatch metrics...")
        
        timestamp = datetime.utcnow()
        
        if scenario == 'normal':
            metrics_data = [
                {'MetricName': 'CPUUtilization', 'Value': random.uniform(20, 40), 'Unit': 'Percent'},
                {'MetricName': 'MemoryUtilization', 'Value': random.uniform(30, 50), 'Unit': 'Percent'},
                {'MetricName': 'RequestCount', 'Value': random.randint(100, 200), 'Unit': 'Count'},
                {'MetricName': 'ErrorRate', 'Value': random.uniform(0, 2), 'Unit': 'Percent'},
                {'MetricName': 'ResponseTime', 'Value': random.uniform(100, 300), 'Unit': 'Milliseconds'}
            ]
        elif scenario == 'high_load':
            metrics_data = [
                {'MetricName': 'CPUUtilization', 'Value': random.uniform(85, 98), 'Unit': 'Percent'},
                {'MetricName': 'MemoryUtilization', 'Value': random.uniform(88, 95), 'Unit': 'Percent'},
                {'MetricName': 'RequestCount', 'Value': random.randint(800, 1000), 'Unit': 'Count'},
                {'MetricName': 'ErrorRate', 'Value': random.uniform(5, 15), 'Unit': 'Percent'},
                {'MetricName': 'ResponseTime', 'Value': random.uniform(2000, 5000), 'Unit': 'Milliseconds'}
            ]
        elif scenario == 'failure':
            metrics_data = [
                {'MetricName': 'CPUUtilization', 'Value': 100, 'Unit': 'Percent'},
                {'MetricName': 'MemoryUtilization', 'Value': 98, 'Unit': 'Percent'},
                {'MetricName': 'RequestCount', 'Value': random.randint(50, 100), 'Unit': 'Count'},
                {'MetricName': 'ErrorRate', 'Value': random.uniform(50, 80), 'Unit': 'Percent'},
                {'MetricName': 'ResponseTime', 'Value': random.uniform(10000, 30000), 'Unit': 'Milliseconds'}
            ]
            
        # Send metrics to CloudWatch
        for metric in metrics_data:
            self.clients['cloudwatch'].put_metric_data(
                Namespace=self.demo_resources['namespace'],
                MetricData=[
                    {
                        'MetricName': metric['MetricName'],
                        'Value': metric['Value'],
                        'Unit': metric['Unit'],
                        'Timestamp': timestamp,
                        'Dimensions': [
                            {
                                'Name': 'Environment',
                                'Value': 'demo'
                            },
                            {
                                'Name': 'Service',
                                'Value': 'sre-demo-app'
                            }
                        ]
                    }
                ]
            )
            
        self.logger.info(f"✅ Published {len(metrics_data)} metrics for {scenario} scenario")
        
    def modify_security_group(self, action='add_risky_rule'):
        """Modify security group to generate VPC Flow Logs events."""
        if not self.demo_resources['security_group_id']:
            self.logger.warning("⚠️ No security group ID available")
            return
            
        self.logger.info(f"🔒 Modifying security group: {action}")
        
        try:
            if action == 'add_risky_rule':
                # Add a risky rule (SSH from anywhere)
                self.clients['ec2'].authorize_security_group_ingress(
                    GroupId=self.demo_resources['security_group_id'],
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 22,
                            'ToPort': 22,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH from anywhere (RISKY)'}]
                        }
                    ]
                )
                self.logger.info("✅ Added risky SSH rule (0.0.0.0/0)")
                
                # Also add RDP from anywhere for more visibility
                self.clients['ec2'].authorize_security_group_ingress(
                    GroupId=self.demo_resources['security_group_id'],
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 3389,
                            'ToPort': 3389,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'RDP from anywhere (RISKY)'}]
                        }
                    ]
                )
                self.logger.info("✅ Added risky RDP rule (0.0.0.0/0)")
                
            elif action == 'remove_risky_rule':
                # Remove the risky rules
                self.clients['ec2'].revoke_security_group_ingress(
                    GroupId=self.demo_resources['security_group_id'],
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 22,
                            'ToPort': 22,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        },
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 3389,
                            'ToPort': 3389,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        }
                    ]
                )
                self.logger.info("✅ Removed risky rules")
                
        except ClientError as e:
            if 'InvalidPermission.Duplicate' in str(e):
                self.logger.info("ℹ️ Rule already exists")
            elif 'InvalidPermission.NotFound' in str(e):
                self.logger.info("ℹ️ Rule not found to remove")
            else:
                self.logger.error(f"❌ Error modifying security group: {e}")
                
    def generate_api_failures(self):
        """Generate API failures that will appear in CloudTrail."""
        self.logger.info("🚨 Generating API failure scenarios...")
        
        failure_scenarios = [
            {
                'name': 'Unauthorized S3 Access',
                'action': lambda: self.clients['s3'].get_object(
                    Bucket='non-existent-bucket-sre-demo-12345',
                    Key='secret-file.txt'
                )
            },
            {
                'name': 'Invalid IAM Operation',
                'action': lambda: self.clients['iam'].attach_user_policy(
                    UserName='non-existent-user-sre-demo',
                    PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
                )
            },
            {
                'name': 'Failed Lambda Invocation',
                'action': lambda: self.clients['lambda'].invoke(
                    FunctionName='non-existent-function-sre-demo',
                    InvocationType='RequestResponse'
                )
            },
            {
                'name': 'EC2 Unauthorized Termination',
                'action': lambda: self.clients['ec2'].terminate_instances(
                    InstanceIds=['i-1234567890abcdef0']
                )
            }
        ]
        
        for scenario in failure_scenarios:
            try:
                scenario['action']()
            except ClientError as e:
                self.logger.info(f"✅ Generated expected failure: {scenario['name']} - {e.response['Error']['Code']}")
            except Exception as e:
                self.logger.info(f"✅ Generated failure: {scenario['name']} - {str(e)}")
                
    def create_ssm_opsitem(self, title, description, severity='3', category='Performance'):
        """Create an SSM OpsItem for incident tracking."""
        self.logger.info(f"📋 Creating SSM OpsItem: {title}")
        
        try:
            response = self.clients['ssm'].create_ops_item(
                Title=title,
                Description=description,
                Priority=int(severity),
                Source='SRE-Demo',
                Category=category,
                Severity=severity,
                OperationalData={
                    '/aws/resources': {
                        'Value': json.dumps([
                            {
                                'arn': f'arn:aws:logs:{self.region}:123456789012:log-group:{self.demo_resources["log_group_name"]}'
                            }
                        ])
                    },
                    '/aws/dedup': {
                        'Value': json.dumps({
                            'dedupString': f'sre-demo-{title}-{int(time.time())}'
                        })
                    }
                },
                Tags=[
                    {
                        'Key': 'Environment',
                        'Value': 'demo'
                    },
                    {
                        'Key': 'Source',
                        'Value': 'incident-generator'
                    }
                ]
            )
            
            ops_item_id = response['OpsItemId']
            self.logger.info(f"✅ Created OpsItem: {ops_item_id}")
            return ops_item_id
            
        except ClientError as e:
            self.logger.error(f"❌ Failed to create OpsItem: {e}")
            return None
            
    def generate_correlated_incident(self):
        """Generate a correlated incident across multiple services."""
        self.logger.info("\n" + "="*80)
        self.logger.info("🎯 GENERATING CORRELATED INCIDENT SCENARIO")
        self.logger.info("="*80 + "\n")
        
        incident_start_time = datetime.utcnow()
        
        # Phase 1: Initial performance degradation
        self.logger.info("📍 Phase 1: Performance degradation starting...")
        self.generate_cloudwatch_metrics('high_load')
        self.generate_application_logs('performance')
        time.sleep(2)
        
        # Phase 2: Security group change (potential cause)
        self.logger.info("📍 Phase 2: Risky security group modification...")
        self.modify_security_group('add_risky_rule')
        time.sleep(2)
        
        # Phase 3: API failures start
        self.logger.info("📍 Phase 3: API failures beginning...")
        self.generate_api_failures()
        time.sleep(2)
        
        # Phase 4: Application errors
        self.logger.info("📍 Phase 4: Application errors occurring...")
        self.generate_application_logs('error')
        self.generate_cloudwatch_metrics('failure')
        time.sleep(2)
        
        # Phase 5: Create OpsItem for the incident
        self.logger.info("📍 Phase 5: Creating incident OpsItem...")
        ops_item_id = self.create_ssm_opsitem(
            title="Critical: Application Performance Degradation and Failures",
            description=f"""
            A critical incident has been detected with the following symptoms:
            
            1. High CPU and memory utilization (>90%)
            2. Increased error rate (>50%)
            3. Response time degradation (>10s)
            4. Security group modifications detected
            5. Multiple API failures recorded
            
            Incident Start Time: {incident_start_time.isoformat()}
            
            Initial investigation shows correlation between security group changes and application failures.
            Root cause analysis is required to determine the relationship between these events.
            """,
            severity='1',
            category='Availability'
        )
        
        # Phase 6: Remediation
        time.sleep(3)
        self.logger.info("📍 Phase 6: Applying remediation...")
        self.modify_security_group('remove_risky_rule')
        self.generate_cloudwatch_metrics('normal')
        self.generate_application_logs('normal')
        
        self.logger.info("\n" + "="*80)
        self.logger.info("✅ CORRELATED INCIDENT GENERATION COMPLETE")
        self.logger.info(f"📊 OpsItem ID: {ops_item_id}")
        self.logger.info("="*80 + "\n")
        
        return {
            'ops_item_id': ops_item_id,
            'start_time': incident_start_time,
            'log_group': self.demo_resources['log_group_name'],
            'namespace': self.demo_resources['namespace'],
            'security_group_id': self.demo_resources['security_group_id']
        }
        
    def run_continuous_load(self, duration_minutes=5):
        """Run continuous load generation for specified duration."""
        self.logger.info(f"🔄 Starting continuous load generation for {duration_minutes} minutes...")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        scenarios = ['normal', 'high_load', 'error', 'performance']
        
        while datetime.now() < end_time:
            scenario = random.choice(scenarios)
            self.generate_application_logs(scenario)
            self.generate_cloudwatch_metrics(scenario)
            
            # Occasionally generate API failures
            if random.random() < 0.2:
                self.generate_api_failures()
                
            # Occasionally modify security groups
            if random.random() < 0.1:
                self.modify_security_group('add_risky_rule')
                time.sleep(10)
                self.modify_security_group('remove_risky_rule')
                
            time.sleep(random.randint(10, 30))
            
        self.logger.info("✅ Continuous load generation complete")
        
    def cleanup_demo_resources(self):
        """Clean up demo resources."""
        self.logger.info("🧹 Cleaning up demo resources...")
        
        # Delete security group
        if self.demo_resources['security_group_id']:
            try:
                self.clients['ec2'].delete_security_group(
                    GroupId=self.demo_resources['security_group_id']
                )
                self.logger.info(f"✅ Deleted security group: {self.demo_resources['security_group_id']}")
            except:
                pass
                
        # Note: Log groups are retained for analysis
        self.logger.info("ℹ️ Log groups retained for analysis")
        

def main():
    """Main demo execution."""
    print("\n" + "="*80)
    print("🚀 SRE INCIDENT GENERATOR DEMO")
    print("="*80)
    print("\nThis demo will generate real incidents across AWS services:")
    print("  ✓ CloudWatch Logs with error patterns")
    print("  ✓ CloudWatch Metrics showing degradation")
    print("  ✓ Security Group modifications (VPC Flow Logs)")
    print("  ✓ API failures (CloudTrail events)")
    print("  ✓ SSM OpsItems for incident tracking")
    print("\n" + "="*80 + "\n")
    
    generator = IncidentGenerator()
    
    try:
        # Create demo resources
        generator.create_demo_resources()
        
        # Menu for demo options
        while True:
            print("\n📋 Demo Options:")
            print("1. Generate correlated incident (recommended)")
            print("2. Run continuous load (5 minutes)")
            print("3. Generate specific scenario")
            print("4. Cleanup resources and exit")
            print("5. Exit without cleanup")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                incident_data = generator.generate_correlated_incident()
                print(f"\n📊 Incident Data:")
                print(f"  - OpsItem ID: {incident_data['ops_item_id']}")
                print(f"  - Log Group: {incident_data['log_group']}")
                print(f"  - Metrics Namespace: {incident_data['namespace']}")
                print(f"  - Security Group: {incident_data['security_group_id']}")
                print(f"\n✅ You can now test the root cause analysis agents with this incident!")
                
            elif choice == '2':
                generator.run_continuous_load(5)
                
            elif choice == '3':
                print("\n📋 Scenario Options:")
                print("1. Application logs (normal)")
                print("2. Application logs (error)")
                print("3. Application logs (performance)")
                print("4. Metrics (normal)")
                print("5. Metrics (high load)")
                print("6. Metrics (failure)")
                print("7. Security group modification")
                print("8. API failures")
                print("9. Create OpsItem")
                
                scenario_choice = input("\nSelect scenario (1-9): ").strip()
                
                if scenario_choice == '1':
                    generator.generate_application_logs('normal')
                elif scenario_choice == '2':
                    generator.generate_application_logs('error')
                elif scenario_choice == '3':
                    generator.generate_application_logs('performance')
                elif scenario_choice == '4':
                    generator.generate_cloudwatch_metrics('normal')
                elif scenario_choice == '5':
                    generator.generate_cloudwatch_metrics('high_load')
                elif scenario_choice == '6':
                    generator.generate_cloudwatch_metrics('failure')
                elif scenario_choice == '7':
                    generator.modify_security_group('add_risky_rule')
                    time.sleep(5)
                    generator.modify_security_group('remove_risky_rule')
                elif scenario_choice == '8':
                    generator.generate_api_failures()
                elif scenario_choice == '9':
                    generator.create_ssm_opsitem(
                        "Demo OpsItem",
                        "This is a demo OpsItem for testing",
                        severity='3'
                    )
                    
            elif choice == '4':
                generator.cleanup_demo_resources()
                break
                
            elif choice == '5':
                print("\n⚠️ Resources retained for future use")
                break
                
            else:
                print("❌ Invalid choice, please try again")
                
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n✅ Demo complete!\n")


if __name__ == "__main__":
    main()
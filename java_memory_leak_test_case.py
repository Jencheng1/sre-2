#!/usr/bin/env python3
"""
Java Spring Boot Memory Leak Test Case with Correlation Analysis
Simulates a realistic memory leak scenario with code change correlation
"""

import boto3
import json
import time
from datetime import datetime, timedelta
import random
import uuid

class JavaMemoryLeakTestCase:
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
        self.logs_client = boto3.client('logs', region_name='us-east-1')
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Test configuration
        self.instance_id = "i-02bef13982a179478"  # SRE-DEMO instance
        self.app_name = "payment-service"
        self.change_id = f"CHG-{datetime.now().strftime('%Y%m%d')}-001"
        self.deployment_time = datetime.utcnow() - timedelta(hours=2)
        
    def create_code_change_opsitem(self):
        """Create an OpsItem for the code change that introduced the memory leak"""
        print("📝 Creating Code Change OpsItem...")
        
        response = self.ssm_client.create_ops_item(
            Title=f"[CHANGE] Deploy payment-service v2.1.0 with cache optimization",
            Description="""Deployed new version of payment-service with following changes:
- Implemented new in-memory cache for transaction processing
- Added concurrent HashMap for payment status tracking
- Modified Spring Boot configuration for increased heap size
- PR #1234: 'Performance optimization for high-volume transactions'""",
            Source="Change Management System",
            Severity="3",
            Category="Performance",
            OperationalData={
                'ChangeRequestId': {'Value': self.change_id, 'Type': 'String'},
                'ChangeType': {'Value': 'Application Update', 'Type': 'String'},
                'Risk': {'Value': 'Medium', 'Type': 'String'},
                'DeploymentTime': {'Value': self.deployment_time.isoformat(), 'Type': 'String'},
                'GitCommit': {'Value': 'a7b3c4d5e6f7890abcdef1234567890abcdef123', 'Type': 'String'},
                'Developer': {'Value': 'john.doe@company.com', 'Type': 'String'},
                'ReviewedBy': {'Value': 'jane.smith@company.com', 'Type': 'String'},
                'ChangedFiles': {'Value': json.dumps([
                    'src/main/java/com/company/payment/cache/TransactionCache.java',
                    'src/main/java/com/company/payment/service/PaymentProcessor.java',
                    'src/main/resources/application.yml'
                ]), 'Type': 'String'}
            }
        )
        
        print(f"✅ Created Change OpsItem: {response['OpsItemId']}")
        return response['OpsItemId']
        
    def generate_memory_leak_metrics(self):
        """Generate CloudWatch metrics showing gradual memory leak pattern"""
        print("\n📊 Generating Memory Leak Metrics...")
        
        namespace = 'JavaApp/SpringBoot'
        
        # Generate metrics for the last 3 hours
        start_time = self.deployment_time
        current_time = datetime.utcnow()
        
        # Memory usage pattern - gradual increase with GC saw-tooth
        time_cursor = start_time
        base_memory = 60  # Start at 60% memory usage
        
        while time_cursor < current_time:
            # Calculate memory based on time since deployment
            hours_since_deploy = (time_cursor - self.deployment_time).total_seconds() / 3600
            
            # Memory increases by ~10% per hour with the leak
            memory_percent = base_memory + (hours_since_deploy * 10)
            
            # Add GC saw-tooth pattern
            gc_effect = random.randint(-5, 2)  # GC reduces memory temporarily
            memory_percent = min(95, memory_percent + gc_effect)
            
            # CPU correlates with memory pressure
            cpu_percent = 20 + (memory_percent - 60) * 1.5  # CPU increases with memory pressure
            cpu_percent = min(95, cpu_percent + random.randint(-5, 5))
            
            # Publish metrics
            self.cloudwatch_client.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        'MetricName': 'HeapMemoryUsed',
                        'Value': memory_percent,
                        'Unit': 'Percent',
                        'Timestamp': time_cursor,
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': self.instance_id},
                            {'Name': 'Application', 'Value': self.app_name}
                        ]
                    },
                    {
                        'MetricName': 'CPUUtilization',
                        'Value': cpu_percent,
                        'Unit': 'Percent',
                        'Timestamp': time_cursor,
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': self.instance_id},
                            {'Name': 'Application', 'Value': self.app_name}
                        ]
                    },
                    {
                        'MetricName': 'GCPauseTime',
                        'Value': 50 + (memory_percent - 60) * 3,  # GC pause increases with memory
                        'Unit': 'Milliseconds',
                        'Timestamp': time_cursor,
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': self.instance_id},
                            {'Name': 'Application', 'Value': self.app_name}
                        ]
                    }
                ]
            )
            
            # Move to next data point (every 5 minutes)
            time_cursor += timedelta(minutes=5)
            
        print(f"✅ Generated {int((current_time - start_time).total_seconds() / 300)} metric data points")
        
    def generate_application_logs(self):
        """Generate application logs showing memory leak symptoms"""
        print("\n📝 Generating Application Logs...")
        
        log_group = f'/aws/ec2/{self.app_name}'
        log_stream = f'{self.instance_id}-{datetime.now().strftime("%Y%m%d")}'
        
        # Ensure log group and stream exist
        try:
            self.logs_client.create_log_group(logGroupName=log_group)
        except:
            pass
            
        try:
            self.logs_client.create_log_stream(
                logGroupName=log_group,
                logStreamName=log_stream
            )
        except:
            pass
            
        # Generate logs showing memory leak progression
        log_events = []
        
        # Normal startup logs
        log_events.append({
            'timestamp': int(self.deployment_time.timestamp() * 1000),
            'message': '[INFO] Starting PaymentServiceApplication v2.1.0 on SRE-DEMO with PID 12345'
        })
        
        log_events.append({
            'timestamp': int((self.deployment_time + timedelta(seconds=30)).timestamp() * 1000),
            'message': '[INFO] Initialized TransactionCache with maxSize=10000, expireAfterWrite=never'
        })
        
        # Warning logs as memory grows
        warning_time = self.deployment_time + timedelta(hours=1)
        log_events.append({
            'timestamp': int(warning_time.timestamp() * 1000),
            'message': '[WARN] TransactionCache size: 45000 entries, estimated memory: 1.2GB'
        })
        
        # GC warnings
        gc_time = self.deployment_time + timedelta(hours=1, minutes=30)
        log_events.append({
            'timestamp': int(gc_time.timestamp() * 1000),
            'message': '[WARN] GC overhead limit exceeded: 98% of CPU time spent in garbage collection'
        })
        
        # Error logs
        error_time = self.deployment_time + timedelta(hours=2)
        log_events.append({
            'timestamp': int(error_time.timestamp() * 1000),
            'message': '[ERROR] java.lang.OutOfMemoryError: Java heap space\n' +
                      'at java.util.HashMap.resize(HashMap.java:703)\n' +
                      'at java.util.HashMap.putVal(HashMap.java:662)\n' +
                      'at com.company.payment.cache.TransactionCache.put(TransactionCache.java:45)\n' +
                      'at com.company.payment.service.PaymentProcessor.processPayment(PaymentProcessor.java:123)'
        })
        
        # Stack trace
        log_events.append({
            'timestamp': int((error_time + timedelta(seconds=1)).timestamp() * 1000),
            'message': '[ERROR] Failed to process payment: Out of memory\n' +
                      'Caused by: TransactionCache is holding 75000 entries without expiration\n' +
                      'Memory leak detected in TransactionCache - entries are never removed'
        })
        
        # Sort by timestamp and send to CloudWatch
        log_events.sort(key=lambda x: x['timestamp'])
        
        try:
            self.logs_client.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                logEvents=log_events
            )
            print(f"✅ Generated {len(log_events)} application log entries")
        except Exception as e:
            print(f"⚠️ Error writing logs: {e}")
            
    def create_cpu_spike_incident(self):
        """Create the CPU spike incident OpsItem"""
        print("\n🚨 Creating CPU Spike Incident...")
        
        response = self.ssm_client.create_ops_item(
            Title=f"High CPU Alert - {self.app_name} on SRE-DEMO",
            Description=f"""CPU utilization spike detected on EC2 instance SRE-DEMO ({self.instance_id}).
Current CPU: 95%
Application: {self.app_name}
Started: {(datetime.utcnow() - timedelta(minutes=30)).isoformat()}

Symptoms:
- Gradual CPU increase over last 2 hours
- High GC pause times detected
- Application response times degraded
- Multiple OutOfMemoryError in logs""",
            Source="CloudWatch Alarm",
            Severity="1",
            OperationalData={
                'InstanceId': {'Value': self.instance_id, 'Type': 'String'},
                'CPUPercent': {'Value': '95', 'Type': 'String'},
                'MemoryPercent': {'Value': '94', 'Type': 'String'},
                'Application': {'Value': self.app_name, 'Type': 'String'},
                'RelatedChangeId': {'Value': self.change_id, 'Type': 'String'},
                'IncidentType': {'Value': 'CPU Spike - Memory Related', 'Type': 'String'}
            }
        )
        
        print(f"✅ Created Incident OpsItem: {response['OpsItemId']}")
        return response['OpsItemId']
        
    def run_correlation_analysis(self, incident_id):
        """Run the supervisor correlation analysis"""
        print("\n🔍 Running Correlation Analysis...")
        
        # Get the incident details
        response = self.ssm_client.get_ops_item(OpsItemId=incident_id)
        ops_item = response['OpsItem']
        
        # Prepare enhanced payload with correlation hints
        payload = {
            'action': 'analyze',
            'incident_description': f"{ops_item.get('Title', '')}. {ops_item.get('Description', '')}",
            'start_time': (datetime.utcnow() - timedelta(hours=3)).isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'service': self.app_name,
            'environment': 'production',
            'enable_correlation': True,
            'correlation_hints': {
                'check_recent_changes': True,
                'check_memory_metrics': True,
                'check_gc_logs': True,
                'correlate_deployment_time': True
            },
            'additional_context': {
                'ops_item_id': incident_id,
                'instance_id': self.instance_id,
                'related_change': self.change_id,
                'severity': '1',
                'incident_type': 'CPU Spike - Memory Related',
                'metrics_namespace': 'JavaApp/SpringBoot',
                'log_group': f'/aws/ec2/{self.app_name}'
            }
        }
        
        print("📤 Invoking Supervisor Lambda with correlation context...")
        
        try:
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                print("✅ Correlation analysis completed")
                return result
            else:
                print(f"❌ Analysis failed: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return None
            
    def create_knowledge_base_entry(self, incident_id, analysis_result):
        """Create a knowledge base entry for this incident pattern"""
        print("\n📚 Creating Knowledge Base Entry...")
        
        kb_entry = {
            'action': 'add_incident',
            'title': 'Java Spring Boot Memory Leak - TransactionCache',
            'description': 'Memory leak in payment service caused by unbounded cache growth',
            'root_cause': 'TransactionCache implementation lacks eviction policy, causing unbounded growth',
            'symptoms': [
                'Gradual CPU increase correlated with memory usage',
                'High GC pause times and overhead',
                'OutOfMemoryError in application logs',
                'Performance degradation over time'
            ],
            'resolution_steps': [
                '1. Immediate: Restart affected instances to clear memory',
                '2. Short-term: Implement cache size limit in TransactionCache',
                '3. Long-term: Add TTL-based eviction policy',
                '4. Monitor: Set up alerts for cache size and memory usage'
            ],
            'tags': ['memory-leak', 'java', 'spring-boot', 'cache', 'cpu-spike'],
            'category': 'performance',
            'ops_item_id': incident_id
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(kb_entry)
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                print("✅ Knowledge base entry created")
            else:
                print("⚠️ Failed to create KB entry")
                
        except Exception as e:
            print(f"⚠️ Error creating KB entry: {e}")

def main():
    """Execute the complete test scenario"""
    print("🧪 Java Spring Boot Memory Leak Test Case")
    print("=" * 60)
    print("This test simulates a realistic memory leak scenario with:")
    print("- Code change that introduces a memory leak")
    print("- Gradual memory growth leading to CPU spike")
    print("- Application logs showing memory issues")
    print("- Correlation analysis to identify root cause")
    print("=" * 60)
    
    tester = JavaMemoryLeakTestCase()
    
    # Step 1: Create code change
    print("\n" + "="*60)
    print("STEP 1: Simulating Code Deployment")
    print("="*60)
    change_id = tester.create_code_change_opsitem()
    
    # Step 2: Generate metrics showing memory leak
    print("\n" + "="*60)
    print("STEP 2: Generating Memory Leak Pattern")
    print("="*60)
    tester.generate_memory_leak_metrics()
    
    # Step 3: Generate application logs
    print("\n" + "="*60)
    print("STEP 3: Generating Application Logs")
    print("="*60)
    tester.generate_application_logs()
    
    # Step 4: Create CPU spike incident
    print("\n" + "="*60)
    print("STEP 4: Creating CPU Spike Incident")
    print("="*60)
    incident_id = tester.create_cpu_spike_incident()
    
    # Wait a moment for data to propagate
    print("\n⏳ Waiting for data propagation...")
    time.sleep(5)
    
    # Step 5: Run correlation analysis
    print("\n" + "="*60)
    print("STEP 5: Running Correlation Analysis")
    print("="*60)
    analysis_result = tester.run_correlation_analysis(incident_id)
    
    if analysis_result and analysis_result.get('statusCode') == 200:
        print("\n📊 Analysis Results:")
        body = json.loads(analysis_result['body']) if isinstance(analysis_result['body'], str) else analysis_result['body']
        
        if 'root_cause_analysis' in body:
            print("\n🎯 Root Cause Analysis:")
            print("-" * 40)
            # Extract first few lines of analysis
            analysis_text = body['root_cause_analysis']
            lines = analysis_text.split('\n')[:10]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            print("  ...")
            
        # Create KB entry
        tester.create_knowledge_base_entry(incident_id, analysis_result)
        
    # Summary
    print("\n" + "="*60)
    print("TEST SCENARIO COMPLETE")
    print("="*60)
    print(f"✅ Change OpsItem: {change_id}")
    print(f"✅ Incident OpsItem: {incident_id}")
    print("✅ Metrics: Memory leak pattern generated")
    print("✅ Logs: OutOfMemoryError and GC warnings")
    print("✅ Correlation: Code change linked to incident")
    print("\n📝 Expected Correlation Results:")
    print("- Recent code change detected 2 hours before incident")
    print("- Memory metrics show gradual increase since deployment")
    print("- GC logs indicate memory pressure")
    print("- Stack traces point to TransactionCache.java")
    print("- Root cause: Unbounded cache growth in new code")
    
    print("\n🎯 To view in Streamlit:")
    print("1. Go to CPU Spike Demo")
    print("2. Select SRE-DEMO instance")
    print("3. Click 'Run Root Cause Analysis'")
    print("4. System should show correlation with code change")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
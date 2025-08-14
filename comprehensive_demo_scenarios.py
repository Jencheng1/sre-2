#!/usr/bin/env python3
"""
Comprehensive Demo Scenarios for SRE Copilot
Demonstrates real AWS integration with actual logs, metrics, and correlations
"""

import boto3
import json
import time
import random
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ComprehensiveDemoScenarios:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.ssm_client = boto3.client('ssm', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
        self.cloudtrail_client = boto3.client('cloudtrail', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        
        # Demo namespace for metrics
        self.namespace = 'SREDemo/Application'
        self.log_group = '/aws/sre-demo/application'
        
    def create_demo_incident(self, scenario_type):
        """Create a demo incident based on scenario type."""
        scenarios = {
            'change_correlation': self._create_change_correlation_incident,
            'defect_correlation': self._create_defect_correlation_incident,
            'jms_timeout': self._create_jms_timeout_incident,
            'vpc_cloudtrail': self._create_vpc_cloudtrail_incident
        }
        
        if scenario_type not in scenarios:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
        
        return scenarios[scenario_type]()
    
    def _create_change_correlation_incident(self):
        """Create incident caused by a change to demonstrate change correlation."""
        logger.info("Creating change correlation demo incident...")
        
        # Step 1: Create a change record
        change_time = datetime.now() - timedelta(minutes=30)
        change_id = f"CHG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        change_response = self.ssm_client.create_ops_item(
            Title=f"[CHANGE] Database connection pool configuration update",
            Description=f"""Change Request: {change_id}
Type: Configuration Change
Component: Database Connection Pool
Changes Made:
- Reduced max connections from 100 to 50
- Changed timeout from 30s to 10s
- Modified retry policy from exponential to linear

Approver: DevOps Team
Implementation Time: {change_time.strftime('%Y-%m-%d %H:%M:%S')}
Risk Level: Medium
Rollback Plan: Revert configuration file""",
            Priority=3,
            Source='Change Management System',
            Category='Performance',
            Severity='3',
            OperationalData={
                'ChangeRequestId': {'Value': change_id},
                'ChangeType': {'Value': 'Configuration'},
                'Component': {'Value': 'Database'},
                'ImplementationTime': {'Value': change_time.isoformat()},
                'RiskLevel': {'Value': 'Medium'}
            },
            Tags=[
                {'Key': 'Type', 'Value': 'Change'},
                {'Key': 'Component', 'Value': 'Database'},
                {'Key': 'ChangeId', 'Value': change_id}
            ]
        )
        
        change_ops_item_id = change_response['OpsItemId']
        logger.info(f"Created change record: {change_ops_item_id}")
        
        # Step 2: Create metrics showing impact after change
        self._create_performance_metrics(
            start_time=change_time + timedelta(minutes=10),
            metric_name='DatabaseConnectionErrors',
            values=[5, 15, 25, 30, 28, 35, 40, 38, 42, 45],
            unit='Count'
        )
        
        self._create_performance_metrics(
            start_time=change_time + timedelta(minutes=10),
            metric_name='ApplicationResponseTime',
            values=[200, 350, 500, 800, 1200, 1500, 1800, 2000, 2200, 2500],
            unit='Milliseconds'
        )
        
        # Step 3: Create CloudWatch logs showing errors
        self._create_cloudwatch_logs([
            {
                'timestamp': int((change_time + timedelta(minutes=15)).timestamp() * 1000),
                'message': '[ERROR] Database connection pool exhausted - MaxPoolSize: 50, ActiveConnections: 50'
            },
            {
                'timestamp': int((change_time + timedelta(minutes=16)).timestamp() * 1000),
                'message': '[ERROR] Failed to acquire database connection - Timeout after 10s'
            },
            {
                'timestamp': int((change_time + timedelta(minutes=17)).timestamp() * 1000),
                'message': '[WARN] Connection retry failed - Linear backoff insufficient for current load'
            },
            {
                'timestamp': int((change_time + timedelta(minutes=18)).timestamp() * 1000),
                'message': '[ERROR] Application timeout - Unable to serve requests due to database connection issues'
            }
        ])
        
        # Step 4: Create the incident
        incident_response = self.ssm_client.create_ops_item(
            Title="Database connection pool exhaustion causing application timeouts",
            Description=f"""Severe performance degradation detected after recent configuration change.

Symptoms:
- Database connection pool reaching maximum capacity
- Application response times increased from 200ms to 2500ms
- Multiple connection timeout errors
- User complaints about slow page loads

Timeline:
- {change_time.strftime('%H:%M')} - Configuration change implemented
- {(change_time + timedelta(minutes=10)).strftime('%H:%M')} - First errors detected
- {(change_time + timedelta(minutes=15)).strftime('%H:%M')} - Connection pool exhausted
- {(change_time + timedelta(minutes=20)).strftime('%H:%M')} - Incident escalated

Impact:
- 85% of users experiencing timeouts
- Order processing delayed
- Revenue impact estimated at $50K/hour

Related Change: {change_id}""",
            Priority=1,
            Source='Monitoring Alert',
            Category='Performance',
            Severity='1',
            OperationalData={
                'service': {'Value': 'order-processing-api'},
                'environment': {'Value': 'production'},
                'region': {'Value': self.region},
                'relatedChange': {'Value': change_id},
                'metricsAvailable': {'Value': 'true'},
                'logsAvailable': {'Value': 'true'}
            },
            Tags=[
                {'Key': 'Type', 'Value': 'Performance'},
                {'Key': 'Component', 'Value': 'Database'},
                {'Key': 'Severity', 'Value': 'Critical'},
                {'Key': 'RelatedChange', 'Value': change_id}
            ]
        )
        
        incident_id = incident_response['OpsItemId']
        logger.info(f"Created incident: {incident_id}")
        
        return {
            'incident_id': incident_id,
            'change_id': change_ops_item_id,
            'type': 'change_correlation',
            'message': f"✅ Created change-correlated incident: {incident_id} (Related to change: {change_ops_item_id})"
        }
    
    def _create_defect_correlation_incident(self):
        """Create incident caused by a known defect."""
        logger.info("Creating defect correlation demo incident...")
        
        # Step 1: Reference known defects (these would exist in ALM/Jira)
        known_defects = [
            {
                'id': 'DEF-4521',
                'title': 'Memory leak in payment service under high load',
                'component': 'payment-service',
                'severity': 'High',
                'status': 'Open'
            },
            {
                'id': 'JIRA-892',
                'title': 'Race condition in order processing',
                'component': 'order-service',
                'severity': 'Critical',
                'status': 'In Progress'
            }
        ]
        
        # Step 2: Create metrics showing memory growth
        start_time = datetime.now() - timedelta(hours=2)
        memory_values = [
            1024, 1100, 1200, 1350, 1500, 1700, 1900, 2100,
            2400, 2700, 3000, 3300, 3600, 3900, 4200, 4500,
            4800, 5100, 5400, 5700, 6000, 6300, 6600, 6900
        ]
        
        self._create_performance_metrics(
            start_time=start_time,
            metric_name='PaymentServiceMemoryUsage',
            values=memory_values,
            unit='Megabytes',
            interval_minutes=5
        )
        
        # Step 3: Create logs showing memory errors
        self._create_cloudwatch_logs([
            {
                'timestamp': int((datetime.now() - timedelta(minutes=30)).timestamp() * 1000),
                'message': '[WARN] Payment service memory usage at 75% - Current: 5.7GB, Max: 7.5GB'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=20)).timestamp() * 1000),
                'message': '[ERROR] Java heap space - OutOfMemoryError in PaymentProcessor.processTransaction()'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=15)).timestamp() * 1000),
                'message': '[ERROR] Memory allocation failed - Known issue DEF-4521: Memory leak under high transaction volume'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=10)).timestamp() * 1000),
                'message': '[CRITICAL] Payment service crashed - Automatic restart initiated'
            }
        ])
        
        # Step 4: Create the incident
        incident_response = self.ssm_client.create_ops_item(
            Title="Payment service OutOfMemoryError - Known defect DEF-4521",
            Description=f"""Payment service crashed due to known memory leak issue.

Known Defect: DEF-4521 - Memory leak in payment service under high load
Status: Open defect, workaround available

Symptoms:
- Gradual memory increase over 2 hours
- Memory usage grew from 1GB to 6.9GB
- OutOfMemoryError in PaymentProcessor
- Service crash and automatic restart

Impact:
- Payment processing unavailable for 5 minutes
- 450 transactions failed
- Estimated revenue loss: $25,000

Workaround Applied:
- Service restarted automatically
- Memory limit increased to 8GB temporarily
- Scheduled restarts every 4 hours until fix deployed

Related Defects:
- DEF-4521: Memory leak in payment service (PRIMARY)
- JIRA-892: Race condition in order processing (SECONDARY)

Root Cause:
The memory leak occurs when processing high volumes of transactions due to 
improper cleanup of transaction cache. This is a known issue tracked in DEF-4521.""",
            Priority=1,
            Source='Monitoring Alert',
            Category='Performance',
            Severity='1',
            OperationalData={
                'service': {'Value': 'payment-service'},
                'environment': {'Value': 'production'},
                'knownDefect': {'Value': 'DEF-4521'},
                'defectStatus': {'Value': 'Open'},
                'workaroundApplied': {'Value': 'true'},
                'metricsAvailable': {'Value': 'true'},
                'logsAvailable': {'Value': 'true'}
            },
            Tags=[
                {'Key': 'Type', 'Value': 'Defect'},
                {'Key': 'Component', 'Value': 'PaymentService'},
                {'Key': 'DefectId', 'Value': 'DEF-4521'},
                {'Key': 'KnownIssue', 'Value': 'true'}
            ]
        )
        
        incident_id = incident_response['OpsItemId']
        logger.info(f"Created defect-correlated incident: {incident_id}")
        
        return {
            'incident_id': incident_id,
            'defect_id': 'DEF-4521',
            'type': 'defect_correlation',
            'message': f"✅ Created defect-correlated incident: {incident_id} (Related to defect: DEF-4521)"
        }
    
    def _create_jms_timeout_incident(self):
        """Create JMS session timeout incident with real CloudWatch data."""
        logger.info("Creating JMS timeout demo incident...")
        
        # Step 1: Create JMS-specific metrics
        start_time = datetime.now() - timedelta(hours=1)
        
        # JMS Queue Depth increasing
        self._create_performance_metrics(
            start_time=start_time,
            metric_name='JMSQueueDepth',
            values=[10, 15, 25, 50, 100, 200, 350, 500, 750, 1000, 1500, 2000],
            unit='Count',
            interval_minutes=5
        )
        
        # JMS Session Timeouts
        self._create_performance_metrics(
            start_time=start_time,
            metric_name='JMSSessionTimeouts',
            values=[0, 1, 2, 5, 10, 15, 25, 30, 45, 60, 80, 100],
            unit='Count',
            interval_minutes=5
        )
        
        # Message Processing Time increasing
        self._create_performance_metrics(
            start_time=start_time,
            metric_name='JMSMessageProcessingTime',
            values=[100, 150, 200, 300, 500, 800, 1200, 1800, 2500, 3000, 3500, 4000],
            unit='Milliseconds',
            interval_minutes=5
        )
        
        # Step 2: Create detailed JMS logs
        self._create_cloudwatch_logs([
            {
                'timestamp': int((datetime.now() - timedelta(minutes=45)).timestamp() * 1000),
                'message': '[INFO] JMS Connection established - Broker: amq-broker-1.aws.internal:61616'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=40)).timestamp() * 1000),
                'message': '[WARN] JMS Queue depth increasing - Queue: order.processing, Depth: 200'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=35)).timestamp() * 1000),
                'message': '[ERROR] JMS Session timeout - Session ID: jms-session-42a8c9, Timeout: 30000ms'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=30)).timestamp() * 1000),
                'message': '[ERROR] javax.jms.JMSException: Failed to create session: Connection timed out'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=25)).timestamp() * 1000),
                'message': '[ERROR] Message consumer disconnected - Queue: order.processing, Consumer: consumer-1'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=20)).timestamp() * 1000),
                'message': '[CRITICAL] JMS Broker unreachable - Connection refused to amq-broker-1.aws.internal:61616'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=15)).timestamp() * 1000),
                'message': '[ERROR] Message redelivery limit exceeded - Message ID: MSG-789456, Redeliveries: 5'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=10)).timestamp() * 1000),
                'message': '[WARN] Dead Letter Queue size increasing - DLQ: order.processing.DLQ, Size: 450'
            }
        ], log_stream='jms-processor')
        
        # Step 3: Create CloudWatch alarm history
        self.cloudwatch_client.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    'MetricName': 'JMSBrokerHealth',
                    'Value': 0,
                    'Unit': 'Count',
                    'Timestamp': datetime.now() - timedelta(minutes=20)
                }
            ]
        )
        
        # Step 4: Create the incident
        incident_response = self.ssm_client.create_ops_item(
            Title="JMS session timeouts causing message processing failures",
            Description=f"""Critical JMS infrastructure issue affecting order processing.

Symptoms:
- JMS session timeouts increasing (100+ in last hour)
- Queue depth growing exponentially (2000+ messages)
- Message processing time degraded (100ms → 4000ms)
- Broker connection failures
- Messages moving to Dead Letter Queue

Timeline:
- {(start_time).strftime('%H:%M')} - Normal operation
- {(start_time + timedelta(minutes=15)).strftime('%H:%M')} - Queue depth started increasing
- {(start_time + timedelta(minutes=30)).strftime('%H:%M')} - First session timeouts
- {(start_time + timedelta(minutes=40)).strftime('%H:%M')} - Broker connection issues
- {(start_time + timedelta(minutes=50)).strftime('%H:%M')} - Critical - DLQ filling up

Impact:
- Order processing delayed by 30+ minutes
- 450 orders in dead letter queue
- Customer complaints about order status
- Potential SLA breach for premium customers

Technical Details:
- Broker: amq-broker-1.aws.internal:61616
- Queue: order.processing
- Session Timeout: 30000ms
- Max Redeliveries: 5
- Current Queue Depth: 2000
- DLQ Size: 450

Metrics Available:
- JMSQueueDepth
- JMSSessionTimeouts  
- JMSMessageProcessingTime
- JMSBrokerHealth""",
            Priority=1,
            Source='JMS Monitoring',
            Category='Availability',
            Severity='1',
            OperationalData={
                'service': {'Value': 'order-processing-service'},
                'component': {'Value': 'JMS'},
                'broker': {'Value': 'amq-broker-1.aws.internal'},
                'queue': {'Value': 'order.processing'},
                'metricsAvailable': {'Value': 'true'},
                'logsAvailable': {'Value': 'true'},
                'queueDepth': {'Value': '2000'},
                'dlqSize': {'Value': '450'}
            },
            Tags=[
                {'Key': 'Type', 'Value': 'Infrastructure'},
                {'Key': 'Component', 'Value': 'JMS'},
                {'Key': 'Severity', 'Value': 'Critical'},
                {'Key': 'Queue', 'Value': 'order.processing'}
            ]
        )
        
        incident_id = incident_response['OpsItemId']
        logger.info(f"Created JMS timeout incident: {incident_id}")
        
        return {
            'incident_id': incident_id,
            'type': 'jms_timeout',
            'message': f"✅ Created JMS timeout incident: {incident_id} with CloudWatch metrics and logs"
        }
    
    def _create_vpc_cloudtrail_incident(self):
        """Create incident requiring VPC Flow Logs and CloudTrail correlation."""
        logger.info("Creating VPC/CloudTrail correlation demo incident...")
        
        # Step 1: Create suspicious network traffic metrics
        start_time = datetime.now() - timedelta(hours=2)
        
        # Unusual outbound traffic
        self._create_performance_metrics(
            start_time=start_time,
            metric_name='NetworkOutBytes',
            values=[1000000, 1200000, 1500000, 2000000, 5000000, 10000000, 
                   15000000, 20000000, 25000000, 30000000, 35000000, 40000000],
            unit='Bytes',
            interval_minutes=10
        )
        
        # Connection count spike
        self._create_performance_metrics(
            start_time=start_time,
            metric_name='ActiveConnections',
            values=[50, 60, 80, 100, 200, 500, 800, 1200, 1500, 1800, 2000, 2200],
            unit='Count',
            interval_minutes=10
        )
        
        # Step 2: Create VPC Flow Logs (simulated)
        vpc_flow_logs = [
            {
                'timestamp': int((datetime.now() - timedelta(minutes=90)).timestamp() * 1000),
                'message': '2 123456789012 eni-1a2b3c4d 10.0.1.140 52.94.224.123 43521 443 6 15 8000 1234567890 1234567900 ACCEPT OK'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=85)).timestamp() * 1000),
                'message': '2 123456789012 eni-1a2b3c4d 10.0.1.140 198.51.100.45 43522 22 6 25 12000 1234567910 1234567920 ACCEPT OK'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=80)).timestamp() * 1000),
                'message': '2 123456789012 eni-1a2b3c4d 10.0.1.140 203.0.113.78 43523 3389 6 50 25000 1234567930 1234567940 REJECT REJECTED'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=75)).timestamp() * 1000),
                'message': '2 123456789012 eni-1a2b3c4d 10.0.1.140 192.0.2.99 43524 1433 6 100 50000 1234567950 1234567960 ACCEPT OK'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=70)).timestamp() * 1000),
                'message': '2 123456789012 eni-1a2b3c4d 10.0.1.140 93.184.216.34 43525 80 6 500 2500000 1234567970 1234567980 ACCEPT OK'
            }
        ]
        
        self._create_cloudwatch_logs(vpc_flow_logs, log_stream='vpc-flow-logs', log_group='/aws/vpc/flowlogs')
        
        # Step 3: Create CloudTrail events (simulated)
        cloudtrail_events = [
            {
                'timestamp': int((datetime.now() - timedelta(minutes=95)).timestamp() * 1000),
                'message': json.dumps({
                    'eventTime': (datetime.now() - timedelta(minutes=95)).isoformat(),
                    'eventName': 'AssumeRole',
                    'eventSource': 'sts.amazonaws.com',
                    'userIdentity': {'type': 'IAMUser', 'userName': 'suspicious-user'},
                    'sourceIPAddress': '198.51.100.45',
                    'requestParameters': {'roleArn': 'arn:aws:iam::123456789012:role/AdminRole'}
                })
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=90)).timestamp() * 1000),
                'message': json.dumps({
                    'eventTime': (datetime.now() - timedelta(minutes=90)).isoformat(),
                    'eventName': 'DescribeInstances',
                    'eventSource': 'ec2.amazonaws.com',
                    'userIdentity': {'type': 'AssumedRole', 'sessionContext': {'sessionIssuer': {'userName': 'suspicious-user'}}},
                    'sourceIPAddress': '198.51.100.45',
                    'requestParameters': {}
                })
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=85)).timestamp() * 1000),
                'message': json.dumps({
                    'eventTime': (datetime.now() - timedelta(minutes=85)).isoformat(),
                    'eventName': 'GetSecretValue',
                    'eventSource': 'secretsmanager.amazonaws.com',
                    'userIdentity': {'type': 'AssumedRole', 'sessionContext': {'sessionIssuer': {'userName': 'suspicious-user'}}},
                    'sourceIPAddress': '198.51.100.45',
                    'requestParameters': {'secretId': 'prod/database/credentials'},
                    'errorCode': 'AccessDenied'
                })
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=80)).timestamp() * 1000),
                'message': json.dumps({
                    'eventTime': (datetime.now() - timedelta(minutes=80)).isoformat(),
                    'eventName': 'CreateAccessKey',
                    'eventSource': 'iam.amazonaws.com',
                    'userIdentity': {'type': 'AssumedRole', 'sessionContext': {'sessionIssuer': {'userName': 'suspicious-user'}}},
                    'sourceIPAddress': '198.51.100.45',
                    'requestParameters': {'userName': 'application-user'}
                })
            }
        ]
        
        self._create_cloudwatch_logs(cloudtrail_events, log_stream='cloudtrail-events', log_group='/aws/cloudtrail/events')
        
        # Step 4: Create security logs
        self._create_cloudwatch_logs([
            {
                'timestamp': int((datetime.now() - timedelta(minutes=75)).timestamp() * 1000),
                'message': '[SECURITY] Suspicious activity detected - Multiple port scans from 10.0.1.140'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=70)).timestamp() * 1000),
                'message': '[ALERT] Unusual outbound data transfer - 40GB in 2 hours from instance i-1234567890'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=65)).timestamp() * 1000),
                'message': '[CRITICAL] Potential data exfiltration - Large volume transfer to unknown IP 93.184.216.34'
            },
            {
                'timestamp': int((datetime.now() - timedelta(minutes=60)).timestamp() * 1000),
                'message': '[SECURITY] IAM role assumption from suspicious IP - Role: AdminRole, IP: 198.51.100.45'
            }
        ], log_stream='security-events')
        
        # Step 5: Create the incident
        incident_response = self.ssm_client.create_ops_item(
            Title="Potential security breach - Unusual network activity and API calls detected",
            Description=f"""Security incident detected with correlated suspicious activities across VPC and CloudTrail.

Alert Summary:
- Massive outbound data transfer detected (40GB in 2 hours)
- Suspicious API calls from unknown IP addresses
- Port scanning activity observed
- Unauthorized access attempts to secrets

VPC Flow Logs Analysis:
- Source: 10.0.1.140 (Internal EC2 instance)
- Unusual destinations: 198.51.100.45, 203.0.113.78, 93.184.216.34
- Protocols: SSH (22), RDP (3389), SQL (1433), HTTP (80)
- Data volume: 40GB outbound
- Rejected connections to RDP ports

CloudTrail Analysis:
- Suspicious user: suspicious-user
- Actions performed:
  * AssumeRole to AdminRole
  * DescribeInstances (reconnaissance)
  * GetSecretValue attempt (DENIED)
  * CreateAccessKey for application-user
- Source IP: 198.51.100.45 (Non-corporate IP)

Correlation Findings:
1. Same IP (198.51.100.45) appears in both VPC logs and CloudTrail
2. Timeline shows reconnaissance → privilege escalation → data access attempt
3. Large data transfer after API activities
4. Port scanning preceded the attack

Impact Assessment:
- Potential data breach in progress
- Compromised credentials suspected
- 40GB of data potentially exfiltrated
- Security posture compromised

Immediate Actions Required:
1. Isolate instance 10.0.1.140
2. Revoke credentials for suspicious-user
3. Block IP 198.51.100.45
4. Review all recent API calls from compromised instance
5. Initiate incident response protocol""",
            Priority=1,
            Source='Security Monitoring',
            Category='Security',
            Severity='1',
            OperationalData={
                'service': {'Value': 'infrastructure'},
                'suspiciousIP': {'Value': '198.51.100.45'},
                'compromisedInstance': {'Value': 'i-1234567890'},
                'dataTransferred': {'Value': '40GB'},
                'vpcFlowLogsAvailable': {'Value': 'true'},
                'cloudTrailLogsAvailable': {'Value': 'true'},
                'correlationFound': {'Value': 'true'}
            },
            Tags=[
                {'Key': 'Type', 'Value': 'Security'},
                {'Key': 'IncidentType', 'Value': 'DataExfiltration'},
                {'Key': 'Severity', 'Value': 'Critical'},
                {'Key': 'RequiresCorrelation', 'Value': 'true'}
            ]
        )
        
        incident_id = incident_response['OpsItemId']
        logger.info(f"Created VPC/CloudTrail correlation incident: {incident_id}")
        
        return {
            'incident_id': incident_id,
            'type': 'vpc_cloudtrail',
            'message': f"✅ Created security incident: {incident_id} requiring VPC Flow Logs and CloudTrail correlation"
        }
    
    def _create_performance_metrics(self, start_time, metric_name, values, unit, interval_minutes=5):
        """Create CloudWatch metrics."""
        metric_data = []
        for i, value in enumerate(values):
            metric_data.append({
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': start_time + timedelta(minutes=i * interval_minutes)
            })
        
        # CloudWatch accepts max 20 metrics per request
        for i in range(0, len(metric_data), 20):
            batch = metric_data[i:i+20]
            self.cloudwatch_client.put_metric_data(
                Namespace=self.namespace,
                MetricData=batch
            )
            time.sleep(0.1)  # Avoid throttling
        
        logger.info(f"Created {len(values)} data points for metric: {metric_name}")
    
    def _create_cloudwatch_logs(self, log_entries, log_stream='application', log_group=None):
        """Create CloudWatch log entries."""
        if log_group is None:
            log_group = self.log_group
            
        # Ensure log group exists
        try:
            self.logs_client.create_log_group(logGroupName=log_group)
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        
        # Ensure log stream exists
        try:
            self.logs_client.create_log_stream(
                logGroupName=log_group,
                logStreamName=log_stream
            )
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        
        # Put log events
        try:
            self.logs_client.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                logEvents=log_entries
            )
            logger.info(f"Created {len(log_entries)} log entries in {log_group}/{log_stream}")
        except Exception as e:
            logger.error(f"Error creating logs: {str(e)}")
    
    def get_demo_scenarios(self):
        """Return list of available demo scenarios."""
        return [
            {
                'id': 'change_correlation',
                'name': '🔧 Change-Induced Incident',
                'description': 'Database config change causing connection pool exhaustion',
                'category': 'Change Management',
                'severity': 'Critical',
                'duration': '30 minutes'
            },
            {
                'id': 'defect_correlation',
                'name': '🐛 Known Defect Incident',
                'description': 'Memory leak in payment service (DEF-4521)',
                'category': 'Defect Management',
                'severity': 'Critical',
                'duration': '2 hours'
            },
            {
                'id': 'jms_timeout',
                'name': '📬 JMS Session Timeout',
                'description': 'JMS broker issues with queue buildup and timeouts',
                'category': 'Infrastructure',
                'severity': 'Critical',
                'duration': '1 hour'
            },
            {
                'id': 'vpc_cloudtrail',
                'name': '🔐 Security Correlation',
                'description': 'Data exfiltration attempt requiring VPC/CloudTrail analysis',
                'category': 'Security',
                'severity': 'Critical',
                'duration': '2 hours'
            }
        ]
"""
Synthetic Transaction Generator
Generates synthetic transactions to reproduce incidents and create corresponding logs/metrics
"""

import json
import boto3
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import uuid
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionType(Enum):
    API_CALL = "api_call"
    DATABASE_QUERY = "database_query"
    FILE_OPERATION = "file_operation"
    NETWORK_REQUEST = "network_request"
    AUTHENTICATION = "authentication"
    DATA_PROCESSING = "data_processing"


@dataclass
class SyntheticTransaction:
    """Represents a synthetic transaction"""
    transaction_id: str
    type: TransactionType
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[int]
    status: str
    error_message: Optional[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'transaction_id': self.transaction_id,
            'type': self.type.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'status': self.status,
            'error_message': self.error_message,
            'metadata': self.metadata
        }


class SyntheticTransactionGenerator:
    """Generates synthetic transactions based on incident patterns"""
    
    def __init__(self):
        self.cloudwatch_client = boto3.client('logs', region_name='us-east-1')
        self.cloudwatch_metrics = boto3.client('cloudwatch', region_name='us-east-1')
        self.cloudtrail_client = boto3.client('cloudtrail', region_name='us-east-1')
        self.log_group_name = '/aws/lambda/sre-synthetic-transactions'
        self.namespace = 'SREDemo/SyntheticTransactions'
        
        # Ensure log group exists
        self._ensure_log_group()
    
    def _ensure_log_group(self):
        """Ensure CloudWatch log group exists"""
        try:
            self.cloudwatch_client.create_log_group(logGroupName=self.log_group_name)
            logger.info(f"Created log group: {self.log_group_name}")
        except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            logger.info(f"Log group already exists: {self.log_group_name}")
    
    def generate_transactions_for_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic transactions based on incident characteristics"""
        
        incident_type = incident_data.get('type', 'unknown')
        service = incident_data.get('service', 'application')
        
        # Determine transaction patterns based on incident
        if 'performance' in incident_type.lower():
            transactions = self._generate_performance_issue_transactions()
        elif 'security' in incident_type.lower():
            transactions = self._generate_security_issue_transactions()
        elif 'availability' in incident_type.lower() or 'outage' in incident_type.lower():
            transactions = self._generate_availability_issue_transactions()
        elif 'database' in incident_type.lower():
            transactions = self._generate_database_issue_transactions()
        else:
            transactions = self._generate_generic_issue_transactions()
        
        # Generate logs and metrics
        logs_generated = self._generate_cloudwatch_logs(transactions, incident_data)
        metrics_generated = self._generate_cloudwatch_metrics(transactions, incident_data)
        vpc_logs_generated = self._generate_vpc_flow_logs(transactions, incident_data)
        cloudtrail_events = self._generate_cloudtrail_events(transactions, incident_data)
        
        return {
            'transactions': [t.to_dict() for t in transactions],
            'logs': logs_generated,
            'metrics': metrics_generated,
            'vpc_flow_logs': vpc_logs_generated,
            'cloudtrail_events': cloudtrail_events,
            'summary': {
                'total_transactions': len(transactions),
                'failed_transactions': sum(1 for t in transactions if t.status == 'failed'),
                'average_duration_ms': sum(t.duration_ms or 0 for t in transactions) / len(transactions) if transactions else 0
            }
        }
    
    def _generate_performance_issue_transactions(self) -> List[SyntheticTransaction]:
        """Generate transactions simulating performance issues"""
        transactions = []
        base_time = datetime.now() - timedelta(minutes=30)
        
        for i in range(50):
            # Gradually increasing response times
            duration = 100 + (i * 50) + random.randint(-20, 100)
            
            transaction = SyntheticTransaction(
                transaction_id=str(uuid.uuid4()),
                type=random.choice(list(TransactionType)),
                start_time=base_time + timedelta(seconds=i*30),
                end_time=base_time + timedelta(seconds=i*30, milliseconds=duration),
                duration_ms=duration,
                status='success' if duration < 3000 else 'timeout',
                error_message='Request timeout' if duration >= 3000 else None,
                metadata={
                    'endpoint': f'/api/v1/{random.choice(["users", "orders", "products"])}/{random.randint(1, 1000)}',
                    'method': random.choice(['GET', 'POST', 'PUT']),
                    'response_size_bytes': random.randint(1000, 50000)
                }
            )
            transactions.append(transaction)
        
        return transactions
    
    def _generate_security_issue_transactions(self) -> List[SyntheticTransaction]:
        """Generate transactions simulating security issues"""
        transactions = []
        base_time = datetime.now() - timedelta(minutes=20)
        
        # Normal transactions
        for i in range(30):
            transaction = SyntheticTransaction(
                transaction_id=str(uuid.uuid4()),
                type=TransactionType.AUTHENTICATION,
                start_time=base_time + timedelta(seconds=i*20),
                end_time=base_time + timedelta(seconds=i*20, milliseconds=50),
                duration_ms=50,
                status='success',
                error_message=None,
                metadata={
                    'user': f'user_{random.randint(1, 100)}@example.com',
                    'ip_address': f'192.168.1.{random.randint(1, 254)}',
                    'auth_method': 'password'
                }
            )
            transactions.append(transaction)
        
        # Suspicious failed login attempts
        suspicious_ip = '10.0.0.99'
        for i in range(20):
            transaction = SyntheticTransaction(
                transaction_id=str(uuid.uuid4()),
                type=TransactionType.AUTHENTICATION,
                start_time=base_time + timedelta(minutes=10, seconds=i*2),
                end_time=base_time + timedelta(minutes=10, seconds=i*2, milliseconds=30),
                duration_ms=30,
                status='failed',
                error_message='Invalid credentials',
                metadata={
                    'user': f'admin_{random.randint(1, 10)}',
                    'ip_address': suspicious_ip,
                    'auth_method': 'password',
                    'failed_attempts': i + 1
                }
            )
            transactions.append(transaction)
        
        return transactions
    
    def _generate_availability_issue_transactions(self) -> List[SyntheticTransaction]:
        """Generate transactions simulating availability issues"""
        transactions = []
        base_time = datetime.now() - timedelta(minutes=15)
        
        # Normal period
        for i in range(20):
            transaction = SyntheticTransaction(
                transaction_id=str(uuid.uuid4()),
                type=random.choice(list(TransactionType)),
                start_time=base_time + timedelta(seconds=i*20),
                end_time=base_time + timedelta(seconds=i*20, milliseconds=100),
                duration_ms=100,
                status='success',
                error_message=None,
                metadata={
                    'endpoint': '/health',
                    'status_code': 200
                }
            )
            transactions.append(transaction)
        
        # Outage period - all requests fail
        for i in range(30):
            transaction = SyntheticTransaction(
                transaction_id=str(uuid.uuid4()),
                type=random.choice(list(TransactionType)),
                start_time=base_time + timedelta(minutes=7, seconds=i*10),
                end_time=base_time + timedelta(minutes=7, seconds=i*10, milliseconds=5000),
                duration_ms=5000,
                status='failed',
                error_message='Connection refused',
                metadata={
                    'endpoint': random.choice(['/api/users', '/api/orders', '/health']),
                    'status_code': 503,
                    'retry_count': 3
                }
            )
            transactions.append(transaction)
        
        return transactions
    
    def _generate_database_issue_transactions(self) -> List[SyntheticTransaction]:
        """Generate transactions simulating database issues"""
        transactions = []
        base_time = datetime.now() - timedelta(minutes=25)
        
        for i in range(40):
            # Simulate slow queries and lock timeouts
            is_slow_query = i % 3 == 0
            duration = 5000 + random.randint(0, 10000) if is_slow_query else random.randint(50, 500)
            
            transaction = SyntheticTransaction(
                transaction_id=str(uuid.uuid4()),
                type=TransactionType.DATABASE_QUERY,
                start_time=base_time + timedelta(seconds=i*30),
                end_time=base_time + timedelta(seconds=i*30, milliseconds=duration),
                duration_ms=duration,
                status='timeout' if duration > 10000 else 'success',
                error_message='Query timeout - possible lock contention' if duration > 10000 else None,
                metadata={
                    'query_type': random.choice(['SELECT', 'UPDATE', 'INSERT']),
                    'table': random.choice(['users', 'orders', 'products', 'sessions']),
                    'rows_affected': random.randint(1, 1000),
                    'lock_wait_ms': duration - 100 if is_slow_query else 0
                }
            )
            transactions.append(transaction)
        
        return transactions
    
    def _generate_generic_issue_transactions(self) -> List[SyntheticTransaction]:
        """Generate generic transaction patterns"""
        transactions = []
        base_time = datetime.now() - timedelta(minutes=20)
        
        for i in range(30):
            transaction = SyntheticTransaction(
                transaction_id=str(uuid.uuid4()),
                type=random.choice(list(TransactionType)),
                start_time=base_time + timedelta(seconds=i*40),
                end_time=base_time + timedelta(seconds=i*40, milliseconds=random.randint(50, 500)),
                duration_ms=random.randint(50, 500),
                status=random.choice(['success', 'success', 'success', 'failed']),
                error_message='Generic error' if random.random() < 0.1 else None,
                metadata={
                    'component': random.choice(['frontend', 'backend', 'database', 'cache']),
                    'action': random.choice(['read', 'write', 'update', 'delete'])
                }
            )
            transactions.append(transaction)
        
        return transactions
    
    def _generate_cloudwatch_logs(self, transactions: List[SyntheticTransaction], incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CloudWatch logs for transactions"""
        log_stream_name = f"synthetic-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            self.cloudwatch_client.create_log_stream(
                logGroupName=self.log_group_name,
                logStreamName=log_stream_name
            )
        except:
            pass
        
        log_events = []
        for transaction in transactions:
            severity = 'ERROR' if transaction.status == 'failed' else 'INFO'
            message = {
                'timestamp': transaction.start_time.isoformat(),
                'severity': severity,
                'transaction_id': transaction.transaction_id,
                'type': transaction.type.value,
                'duration_ms': transaction.duration_ms,
                'status': transaction.status,
                'error': transaction.error_message,
                'metadata': transaction.metadata,
                'incident_context': {
                    'incident_id': incident_data.get('id'),
                    'incident_type': incident_data.get('type')
                }
            }
            
            log_events.append({
                'timestamp': int(transaction.start_time.timestamp() * 1000),
                'message': json.dumps(message)
            })
        
        # Sort by timestamp
        log_events.sort(key=lambda x: x['timestamp'])
        
        # Send logs in batches
        batch_size = 100
        for i in range(0, len(log_events), batch_size):
            batch = log_events[i:i+batch_size]
            try:
                self.cloudwatch_client.put_log_events(
                    logGroupName=self.log_group_name,
                    logStreamName=log_stream_name,
                    logEvents=batch
                )
            except Exception as e:
                logger.error(f"Error sending logs: {e}")
        
        return {
            'log_group': self.log_group_name,
            'log_stream': log_stream_name,
            'events_count': len(log_events)
        }
    
    def _generate_cloudwatch_metrics(self, transactions: List[SyntheticTransaction], incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CloudWatch metrics for transactions"""
        metrics_data = []
        
        # Group transactions by type
        for transaction_type in TransactionType:
            type_transactions = [t for t in transactions if t.type == transaction_type]
            if not type_transactions:
                continue
            
            # Calculate metrics
            success_count = sum(1 for t in type_transactions if t.status == 'success')
            failed_count = sum(1 for t in type_transactions if t.status == 'failed')
            avg_duration = sum(t.duration_ms or 0 for t in type_transactions) / len(type_transactions)
            
            # Add metric data
            metrics_data.extend([
                {
                    'MetricName': 'TransactionCount',
                    'Value': len(type_transactions),
                    'Unit': 'Count',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'TransactionType', 'Value': transaction_type.value},
                        {'Name': 'IncidentId', 'Value': incident_data.get('id', 'unknown')}
                    ]
                },
                {
                    'MetricName': 'SuccessRate',
                    'Value': (success_count / len(type_transactions)) * 100,
                    'Unit': 'Percent',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'TransactionType', 'Value': transaction_type.value},
                        {'Name': 'IncidentId', 'Value': incident_data.get('id', 'unknown')}
                    ]
                },
                {
                    'MetricName': 'AverageDuration',
                    'Value': avg_duration,
                    'Unit': 'Milliseconds',
                    'Timestamp': datetime.now(),
                    'Dimensions': [
                        {'Name': 'TransactionType', 'Value': transaction_type.value},
                        {'Name': 'IncidentId', 'Value': incident_data.get('id', 'unknown')}
                    ]
                }
            ])
        
        # Send metrics in batches
        batch_size = 20
        for i in range(0, len(metrics_data), batch_size):
            batch = metrics_data[i:i+batch_size]
            try:
                self.cloudwatch_metrics.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
            except Exception as e:
                logger.error(f"Error sending metrics: {e}")
        
        return {
            'namespace': self.namespace,
            'metrics_count': len(metrics_data),
            'metric_names': list(set(m['MetricName'] for m in metrics_data))
        }
    
    def _generate_vpc_flow_logs(self, transactions: List[SyntheticTransaction], incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simulated VPC Flow Logs"""
        flow_logs = []
        
        for transaction in transactions:
            # Extract IP information from metadata if available
            src_ip = transaction.metadata.get('ip_address', f'10.0.{random.randint(1, 254)}.{random.randint(1, 254)}')
            dst_ip = f'10.0.{random.randint(1, 254)}.{random.randint(1, 254)}'
            
            flow_log = {
                'version': 2,
                'account_id': '123456789012',
                'interface_id': f'eni-{uuid.uuid4().hex[:8]}',
                'src_addr': src_ip,
                'dst_addr': dst_ip,
                'src_port': random.randint(1024, 65535),
                'dst_port': 443 if transaction.type == TransactionType.API_CALL else random.choice([80, 443, 3306, 5432]),
                'protocol': 6,  # TCP
                'packets': random.randint(10, 1000),
                'bytes': random.randint(1000, 100000),
                'start_time': int(transaction.start_time.timestamp()),
                'end_time': int((transaction.end_time or transaction.start_time).timestamp()),
                'action': 'REJECT' if transaction.status == 'failed' and 'security' in incident_data.get('type', '').lower() else 'ACCEPT',
                'log_status': 'OK'
            }
            flow_logs.append(flow_log)
        
        # Save flow logs to file
        flow_logs_file = f'/home/ec2-user/sre/sre_mcp/vpc_flow_logs_{datetime.now().strftime("%Y%m%d%H%M%S")}.json'
        with open(flow_logs_file, 'w') as f:
            json.dump(flow_logs, f, indent=2)
        
        return {
            'file': flow_logs_file,
            'logs_count': len(flow_logs),
            'rejected_count': sum(1 for log in flow_logs if log['action'] == 'REJECT')
        }
    
    def _generate_cloudtrail_events(self, transactions: List[SyntheticTransaction], incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simulated CloudTrail events"""
        events = []
        
        for transaction in transactions:
            if transaction.type in [TransactionType.AUTHENTICATION, TransactionType.API_CALL]:
                event = {
                    'eventTime': transaction.start_time.isoformat(),
                    'eventName': self._get_cloudtrail_event_name(transaction),
                    'eventSource': 'sts.amazonaws.com' if transaction.type == TransactionType.AUTHENTICATION else 'ec2.amazonaws.com',
                    'userIdentity': {
                        'type': 'IAMUser',
                        'principalId': f'AIDA{uuid.uuid4().hex[:10].upper()}',
                        'arn': f'arn:aws:iam::123456789012:user/{transaction.metadata.get("user", "unknown")}',
                        'accountId': '123456789012',
                        'userName': transaction.metadata.get('user', 'unknown')
                    },
                    'sourceIPAddress': transaction.metadata.get('ip_address', '192.168.1.1'),
                    'userAgent': 'aws-cli/2.0.0',
                    'requestParameters': transaction.metadata,
                    'responseElements': {
                        'status': transaction.status,
                        'error': transaction.error_message
                    },
                    'errorCode': 'AccessDenied' if transaction.status == 'failed' else None,
                    'errorMessage': transaction.error_message,
                    'requestID': transaction.transaction_id,
                    'eventID': str(uuid.uuid4()),
                    'eventType': 'AwsApiCall',
                    'recipientAccountId': '123456789012'
                }
                events.append(event)
        
        # Save CloudTrail events to file
        cloudtrail_file = f'/home/ec2-user/sre/sre_mcp/cloudtrail_events_{datetime.now().strftime("%Y%m%d%H%M%S")}.json'
        with open(cloudtrail_file, 'w') as f:
            json.dump(events, f, indent=2)
        
        return {
            'file': cloudtrail_file,
            'events_count': len(events),
            'error_events': sum(1 for e in events if e.get('errorCode'))
        }
    
    def _get_cloudtrail_event_name(self, transaction: SyntheticTransaction) -> str:
        """Get appropriate CloudTrail event name based on transaction"""
        if transaction.type == TransactionType.AUTHENTICATION:
            return 'AssumeRole' if transaction.status == 'success' else 'AssumeRoleFailure'
        elif transaction.type == TransactionType.API_CALL:
            method = transaction.metadata.get('method', 'GET')
            if method == 'GET':
                return 'DescribeInstances'
            elif method == 'POST':
                return 'RunInstances'
            elif method == 'PUT':
                return 'ModifyInstanceAttribute'
            else:
                return 'TerminateInstances'
        else:
            return 'UnknownOperation'
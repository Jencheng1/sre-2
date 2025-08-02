"""
SQS Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon SQS.
It detects issues related to queue health, message processing, and dead letter queues.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class SQSMonitoringAgent(A2AAgent):
    """Agent for monitoring SQS and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the SQS monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "sqs_monitoring",
            "queue_health",
            "message_processing",
            "dead_letter_queue_analysis"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "SQS"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_queues(self) -> List[Dict[str, Any]]:
        """Get list of SQS queues."""
        try:
            queues = []
            paginator = self.sqs.get_paginator('list_queues')
            
            for page in paginator.paginate():
                for queue_url in page.get('QueueUrls', []):
                    # Get queue attributes
                    attributes = self.sqs.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=[
                            'All',
                            'ApproximateNumberOfMessages',
                            'ApproximateNumberOfMessagesDelayed',
                            'ApproximateNumberOfMessagesNotVisible',
                            'CreatedTimestamp',
                            'DelaySeconds',
                            'LastModifiedTimestamp',
                            'MaximumMessageSize',
                            'MessageRetentionPeriod',
                            'Policy',
                            'QueueArn',
                            'ReceiveMessageWaitTimeSeconds',
                            'VisibilityTimeout',
                            'RedrivePolicy'
                        ]
                    )
                    
                    queues.append({
                        'QueueUrl': queue_url,
                        'Attributes': attributes.get('Attributes', {})
                    })
            
            return queues
        except Exception as e:
            print(f"Error retrieving SQS queues: {e}")
            self.send_notification(
                content=f"Error retrieving SQS queues: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_queue_metrics(self, queue_name: str) -> Dict[str, Any]:
        """Get CloudWatch metrics for a queue."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            metrics = {}
            metric_names = [
                'NumberOfMessagesReceived',
                'NumberOfMessagesSent',
                'NumberOfMessagesDeleted',
                'NumberOfEmptyReceives',
                'NumberOfMessagesDelayed',
                'NumberOfMessagesNotVisible',
                'SentMessageSize',
                'ApproximateAgeOfOldestMessage',
                'NumberOfMessagesReceived',
                'NumberOfMessagesSent',
                'NumberOfMessagesDeleted',
                'NumberOfEmptyReceives',
                'NumberOfMessagesDelayed',
                'NumberOfMessagesNotVisible',
                'SentMessageSize',
                'ApproximateAgeOfOldestMessage'
            ]
            
            for metric_name in metric_names:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/SQS',
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'QueueName', 'Value': queue_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Sum', 'Maximum']
                )
                
                if response.get('Datapoints'):
                    metrics[metric_name] = response['Datapoints'][0]
            
            return metrics
        except Exception as e:
            print(f"Error retrieving metrics for queue {queue_name}: {e}")
            return {}
    
    def analyze_queue_health(self, queue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze the health of an SQS queue."""
        issues = []
        
        try:
            queue_url = queue.get('QueueUrl')
            attributes = queue.get('Attributes', {})
            queue_name = queue_url.split('/')[-1]
            
            # Check message count
            approx_messages = int(attributes.get('ApproximateNumberOfMessages', 0))
            if approx_messages > 10000:  # High message count
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'queue_url': queue_url,
                    'queue_name': queue_name,
                    'severity': 'high',
                    'issue_type': 'high_message_count',
                    'description': f"SQS queue {queue_name} has {approx_messages} messages"
                }
                issues.append(issue)
            
            # Check delayed messages
            delayed_messages = int(attributes.get('ApproximateNumberOfMessagesDelayed', 0))
            if delayed_messages > 1000:  # High delayed message count
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'queue_url': queue_url,
                    'queue_name': queue_name,
                    'severity': 'medium',
                    'issue_type': 'high_delayed_messages',
                    'description': f"SQS queue {queue_name} has {delayed_messages} delayed messages"
                }
                issues.append(issue)
            
            # Check visibility timeout
            visibility_timeout = int(attributes.get('VisibilityTimeout', 30))
            if visibility_timeout < 30:  # Low visibility timeout
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'queue_url': queue_url,
                    'queue_name': queue_name,
                    'severity': 'low',
                    'issue_type': 'low_visibility_timeout',
                    'description': f"SQS queue {queue_name} has low visibility timeout: {visibility_timeout} seconds"
                }
                issues.append(issue)
            
            # Check message retention
            retention_period = int(attributes.get('MessageRetentionPeriod', 345600))  # 4 days default
            if retention_period < 86400:  # Less than 1 day
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'queue_url': queue_url,
                    'queue_name': queue_name,
                    'severity': 'medium',
                    'issue_type': 'low_retention_period',
                    'description': f"SQS queue {queue_name} has low message retention period: {retention_period} seconds"
                }
                issues.append(issue)
            
            # Check dead letter queue
            redrive_policy = attributes.get('RedrivePolicy')
            if not redrive_policy:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'queue_url': queue_url,
                    'queue_name': queue_name,
                    'severity': 'medium',
                    'issue_type': 'no_dlq',
                    'description': f"SQS queue {queue_name} has no dead letter queue configured"
                }
                issues.append(issue)
            
            # Check metrics
            metrics = self.get_queue_metrics(queue_name)
            if metrics:
                # Check message age
                oldest_message_age = metrics.get('ApproximateAgeOfOldestMessage', {}).get('Maximum', 0)
                if oldest_message_age > 3600:  # Messages older than 1 hour
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'queue_url': queue_url,
                        'queue_name': queue_name,
                        'severity': 'high',
                        'issue_type': 'old_messages',
                        'description': f"SQS queue {queue_name} has messages older than {oldest_message_age} seconds"
                    }
                    issues.append(issue)
                
                # Check message processing rate
                messages_received = metrics.get('NumberOfMessagesReceived', {}).get('Sum', 0)
                messages_deleted = metrics.get('NumberOfMessagesDeleted', {}).get('Sum', 0)
                if messages_received > 0 and messages_deleted == 0:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'queue_url': queue_url,
                        'queue_name': queue_name,
                        'severity': 'high',
                        'issue_type': 'no_message_processing',
                        'description': f"SQS queue {queue_name} has received {messages_received} messages but none have been processed"
                    }
                    issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing queue {queue.get('QueueUrl')}: {e}")
            return []
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze SQS issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | Queue: {issue.get('queue_name')} | " +
            f"Severity: {issue.get('severity')} | Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following SQS issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on message processing and system reliability
        3. Root causes and patterns
        4. Recommended remediation steps
        
        Format your response as JSON with the following structure:
        {{
            "critical_issues": [list of issues with reasons],
            "potential_impacts": [list of impacts],
            "root_causes": [list of root causes],
            "remediation_steps": [list of steps]
        }}
        """
        
        try:
            # Call Claude 3 Haiku via Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read().decode('utf-8'))
            content = response_body['content'][0]['text']
            
            # Extract JSON from the response
            try:
                # Find JSON in the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    analysis = json.loads(json_str)
                else:
                    analysis = {"error": "Could not extract JSON from response"}
            except json.JSONDecodeError:
                analysis = {"error": "Invalid JSON in response"}
            
            return analysis
        
        except Exception as e:
            print(f"Error analyzing with Bedrock: {e}")
            return {"error": str(e)}
    
    def report_issues(self, issues: List[Dict[str, Any]], analysis: Dict[str, Any]) -> None:
        """Report detected issues to the supervisor."""
        if not issues:
            return
        
        # Prepare the report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "service": "SQS",
            "issues": issues,
            "analysis": analysis
        }
        
        # Send the report
        self.send_notification(
            content=json.dumps(report),
            notification_type="monitoring_alert",
            severity="high" if any(issue.get('severity') == 'high' for issue in issues) else "medium",
            recipient_id=self.supervisor_id
        )
    
    def handle_query(self, message: MCPMessage) -> Optional[str]:
        """Handle queries from other agents."""
        try:
            data = json.loads(message.content)
            query_type = data.get("query_type")
            
            if query_type == "queue_health":
                queue_url = data.get("queue_url")
                if queue_url:
                    queues = self.get_queues()
                    queue = next((q for q in queues if q.get('QueueUrl') == queue_url), None)
                    if queue:
                        issues = self.analyze_queue_health(queue)
                        analysis = self.analyze_with_bedrock(issues)
                        return json.dumps({
                            "queue_url": queue_url,
                            "queue_name": queue_url.split('/')[-1],
                            "issues": issues,
                            "analysis": analysis
                        })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all SQS queues."""
        try:
            all_issues = []
            
            # Check queues
            queues = self.get_queues()
            for queue in queues:
                issues = self.analyze_queue_health(queue)
                all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in SQS monitoring cycle: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
    
    def run_monitoring(self, interval: int = 300, max_runtime: Optional[int] = None) -> None:
        """Run continuous monitoring with specified interval."""
        start_time = time.time()
        
        while True:
            try:
                # Run monitoring cycle
                self.monitor_cycle()
                
                # Check if we've exceeded max runtime
                if max_runtime and (time.time() - start_time) > max_runtime:
                    print("Max runtime exceeded, stopping monitoring")
                    break
                
                # Wait for next interval
                time.sleep(interval)
            
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait a minute before retrying


def create_sqs_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> SQSMonitoringAgent:
    """Create an SQS monitoring agent."""
    broker = A2AMessageBroker()
    return SQSMonitoringAgent(agent_id, broker, supervisor_id, region_name) 
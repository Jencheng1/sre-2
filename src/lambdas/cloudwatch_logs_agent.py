"""
CloudWatch Logs Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon CloudWatch Logs.
It detects error patterns, log volume spikes, and analyzes log content.
"""

import json
import boto3
import time
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class CloudWatchLogsMonitoringAgent(A2AAgent):
    """Agent for monitoring Amazon CloudWatch Logs and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the CloudWatch Logs monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.logs = boto3.client('logs', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define error patterns to monitor
        self.error_patterns = [
            r'error',
            r'exception',
            r'fail',
            r'timeout',
            r'denied',
            r'fatal',
            r'critical',
            r'crash',
            r'out of memory',
            r'stack trace'
        ]
        
        # Define metrics to monitor
        self.metrics = [
            "IncomingLogEvents",
            "IncomingBytes",
            "ForwardedLogEvents",
            "ForwardedBytes",
            "DeliveryErrors",
            "DeliveryThrottling"
        ]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def get_log_groups(self) -> List[Dict[str, Any]]:
        """Get list of log groups."""
        log_groups = []
        paginator = self.logs.get_paginator('describe_log_groups')
        
        for page in paginator.paginate():
            log_groups.extend(page['logGroups'])
        
        return log_groups
    
    def get_log_streams(self, log_group_name: str) -> List[Dict[str, Any]]:
        """Get recent log streams for a log group."""
        log_streams = []
        paginator = self.logs.get_paginator('describe_log_streams')
        
        for page in paginator.paginate(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True
        ):
            log_streams.extend(page['logStreams'])
            if len(log_streams) >= 10:  # Limit to 10 most recent streams
                break
        
        return log_streams[:10]
    
    def get_log_events(self, log_group_name: str, log_stream_name: str) -> List[Dict[str, Any]]:
        """Get recent log events from a log stream."""
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = end_time - (60 * 60 * 1000)  # Last hour
        
        events = []
        paginator = self.logs.get_paginator('filter_log_events')
        
        for page in paginator.paginate(
            logGroupName=log_group_name,
            logStreamNames=[log_stream_name],
            startTime=start_time,
            endTime=end_time
        ):
            events.extend(page['events'])
        
        return events
    
    def get_log_metrics(self, log_group_name: str) -> Dict[str, Any]:
        """Get CloudWatch metrics for a log group."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        metric_data = {}
        for metric in self.metrics:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Logs',
                MetricName=metric,
                Dimensions=[{'Name': 'LogGroupName', 'Value': log_group_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum', 'Average']
            )
            metric_data[metric] = response['Datapoints']
        
        return metric_data
    
    def analyze_log_content(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze log events for patterns and issues."""
        issues = []
        error_counts = {}
        
        for event in events:
            message = event['message'].lower()
            timestamp = event['timestamp']
            
            # Check for error patterns
            for pattern in self.error_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    error_type = pattern
                    error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Report high frequency errors
        for error_type, count in error_counts.items():
            if count > 10:  # More than 10 occurrences in the time window
                issues.append({
                    'type': 'error_pattern',
                    'severity': 'high',
                    'pattern': error_type,
                    'count': count,
                    'description': f"High frequency of '{error_type}' pattern ({count} occurrences)"
                })
        
        return issues
    
    def analyze_log_group_health(self, log_group_name: str) -> List[Dict[str, Any]]:
        """Analyze log group health and detect issues."""
        issues = []
        
        # Get recent log streams
        streams = self.get_log_streams(log_group_name)
        
        # Analyze each stream
        all_events = []
        for stream in streams:
            events = self.get_log_events(log_group_name, stream['logStreamName'])
            all_events.extend(events)
            
            # Check stream health
            if stream.get('storedBytes', 0) > 1024 * 1024 * 1024:  # More than 1GB
                issues.append({
                    'type': 'storage',
                    'severity': 'medium',
                    'log_group': log_group_name,
                    'stream': stream['logStreamName'],
                    'size': stream['storedBytes'],
                    'description': f"Large log stream size ({stream['storedBytes'] / (1024*1024*1024):.2f}GB)"
                })
        
        # Analyze log content
        content_issues = self.analyze_log_content(all_events)
        for issue in content_issues:
            issue['log_group'] = log_group_name
            issues.append(issue)
        
        # Check metrics
        metrics = self.get_log_metrics(log_group_name)
        for metric, datapoints in metrics.items():
            if datapoints:
                latest = max(datapoints, key=lambda x: x['Timestamp'])
                
                # Check delivery errors
                if metric == 'DeliveryErrors' and latest['Sum'] > 0:
                    issues.append({
                        'type': 'delivery',
                        'severity': 'high',
                        'log_group': log_group_name,
                        'metric': metric,
                        'value': latest['Sum'],
                        'description': f"Log delivery errors detected ({latest['Sum']} errors)"
                    })
                
                # Check throttling
                elif metric == 'DeliveryThrottling' and latest['Sum'] > 0:
                    issues.append({
                        'type': 'throttling',
                        'severity': 'medium',
                        'log_group': log_group_name,
                        'metric': metric,
                        'value': latest['Sum'],
                        'description': f"Log delivery throttling detected ({latest['Sum']} events)"
                    })
                
                # Check incoming volume
                elif metric == 'IncomingBytes':
                    bytes_per_second = latest['Average']
                    if bytes_per_second > 1024 * 1024:  # More than 1MB/s
                        issues.append({
                            'type': 'volume',
                            'severity': 'medium',
                            'log_group': log_group_name,
                            'metric': metric,
                            'value': bytes_per_second,
                            'description': f"High log volume ({bytes_per_second / (1024*1024):.2f}MB/s)"
                        })
        
        return issues
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze CloudWatch Logs issues."""
        if not issues:
            return {"analysis": "No CloudWatch Logs issues to analyze"}
        
        # Prepare issues for analysis
        issues_text = "\n".join([
            f"Type: {issue['type']} | Severity: {issue['severity']} | " +
            f"Log Group: {issue['log_group']} | Description: {issue['description']}"
            for issue in issues[:20]  # Limit to 20 issues for prompt size
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following Amazon CloudWatch Logs issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Common error patterns and their implications
        3. Potential system health concerns
        4. Recommended actions for remediation
        
        Format your response as JSON with the following structure:
        {{
            "critical_issues": [list of issues with reasons],
            "error_patterns": [list of patterns with analysis],
            "system_health": [list of concerns],
            "recommended_actions": [list of actions]
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
    
    def handle_query(self, message: MCPMessage) -> Optional[str]:
        """Handle queries from other agents."""
        query_type = message.metadata.get("query_type")
        
        if query_type == "get_log_group_health":
            try:
                log_group_name = message.content
                issues = self.analyze_log_group_health(log_group_name)
                analysis = self.analyze_with_bedrock(issues)
                
                return self.send_response(
                    recipient_id=message.sender_id,
                    content=json.dumps({
                        "issues": issues,
                        "analysis": analysis
                    }),
                    in_response_to=message.message_id,
                    conversation_id=message.conversation_id
                )
            except Exception as e:
                return self.send_response(
                    recipient_id=message.sender_id,
                    content=json.dumps({"error": str(e)}),
                    in_response_to=message.message_id,
                    status="error",
                    conversation_id=message.conversation_id
                )
        
        return super().handle_query(message)
    
    def monitor_cycle(self) -> None:
        """Run a single monitoring cycle."""
        all_issues = []
        
        # Get all log groups
        log_groups = self.get_log_groups()
        
        # Check each log group
        for log_group in log_groups:
            log_group_name = log_group['logGroupName']
            issues = self.analyze_log_group_health(log_group_name)
            all_issues.extend(issues)
        
        # If issues found, perform deeper analysis with Bedrock
        analysis = {}
        if all_issues:
            analysis = self.analyze_with_bedrock(all_issues)
        
        # Report any issues found
        self.report_issues(all_issues, analysis)
    
    def run_monitoring(self, interval: int = 300, max_runtime: Optional[int] = None) -> None:
        """Run continuous monitoring with the specified interval."""
        start_time = time.time()
        
        try:
            while True:
                # Process any incoming messages
                self.process_messages()
                
                # Run a monitoring cycle
                self.monitor_cycle()
                
                # Sleep until next cycle
                time.sleep(interval)
                
                # Check if max runtime exceeded
                if max_runtime and (time.time() - start_time) > max_runtime:
                    break
        
        except KeyboardInterrupt:
            print(f"CloudWatch Logs monitoring agent {self.agent_id} stopped by user.")
        except Exception as e:
            print(f"Error in CloudWatch Logs monitoring: {e}")
            self.send_notification(
                content=f"CloudWatch Logs monitoring error: {e}",
                notification_type="agent_error",
                severity="error",
                recipient_id=self.supervisor_id
            ) 
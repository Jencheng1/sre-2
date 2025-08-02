"""
CloudWatch Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon CloudWatch.
It detects issues related to metrics, alarms, and log groups.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class CloudWatchMonitoringAgent(A2AAgent):
    """Agent for monitoring CloudWatch and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the CloudWatch monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.logs = boto3.client('logs', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "cloudwatch_monitoring",
            "metrics_analysis",
            "alarm_management",
            "log_analysis"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "CloudWatch"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_alarms(self) -> List[Dict[str, Any]]:
        """Get list of CloudWatch alarms."""
        try:
            alarms = []
            paginator = self.cloudwatch.get_paginator('describe_alarms')
            
            for page in paginator.paginate():
                for alarm in page.get('MetricAlarms', []):
                    alarms.append({
                        'AlarmName': alarm.get('AlarmName'),
                        'AlarmArn': alarm.get('AlarmArn'),
                        'MetricName': alarm.get('MetricName'),
                        'Namespace': alarm.get('Namespace'),
                        'Statistic': alarm.get('Statistic'),
                        'Period': alarm.get('Period'),
                        'EvaluationPeriods': alarm.get('EvaluationPeriods'),
                        'Threshold': alarm.get('Threshold'),
                        'ComparisonOperator': alarm.get('ComparisonOperator'),
                        'StateValue': alarm.get('StateValue'),
                        'StateReason': alarm.get('StateReason'),
                        'StateUpdatedTimestamp': alarm.get('StateUpdatedTimestamp'),
                        'ActionsEnabled': alarm.get('ActionsEnabled'),
                        'OKActions': alarm.get('OKActions', []),
                        'AlarmActions': alarm.get('AlarmActions', []),
                        'InsufficientDataActions': alarm.get('InsufficientDataActions', []),
                        'Dimensions': alarm.get('Dimensions', []),
                        'TreatMissingData': alarm.get('TreatMissingData')
                    })
            
            return alarms
        except Exception as e:
            print(f"Error retrieving CloudWatch alarms: {e}")
            self.send_notification(
                content=f"Error retrieving CloudWatch alarms: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_log_groups(self) -> List[Dict[str, Any]]:
        """Get list of CloudWatch Log groups."""
        try:
            log_groups = []
            paginator = self.logs.get_paginator('describe_log_groups')
            
            for page in paginator.paginate():
                for group in page.get('logGroups', []):
                    log_groups.append({
                        'LogGroupName': group.get('logGroupName'),
                        'CreationTime': group.get('creationTime'),
                        'RetentionInDays': group.get('retentionInDays'),
                        'MetricFilterCount': group.get('metricFilterCount', 0),
                        'StoredBytes': group.get('storedBytes', 0),
                        'KmsKeyId': group.get('kmsKeyId'),
                        'Arn': group.get('arn')
                    })
            
            return log_groups
        except Exception as e:
            print(f"Error retrieving CloudWatch Log groups: {e}")
            self.send_notification(
                content=f"Error retrieving CloudWatch Log groups: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_metric_data(self, namespace: str, metric_name: str, 
                       dimensions: List[Dict[str, str]], period: int = 300) -> Dict[str, Any]:
        """Get CloudWatch metric data."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=['Average', 'Maximum', 'Minimum', 'Sum']
            )
            
            return response.get('Datapoints', [])
        except Exception as e:
            print(f"Error retrieving metric data for {namespace}/{metric_name}: {e}")
            return []
    
    def analyze_alarm_health(self, alarm: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze the health of a CloudWatch alarm."""
        issues = []
        
        try:
            alarm_name = alarm.get('AlarmName')
            
            # Check alarm state
            if alarm.get('StateValue') == 'ALARM':
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'alarm_name': alarm_name,
                    'severity': 'high',
                    'issue_type': 'alarm_triggered',
                    'description': f"CloudWatch alarm {alarm_name} is in ALARM state: {alarm.get('StateReason')}"
                }
                issues.append(issue)
            
            # Check alarm actions
            if not alarm.get('ActionsEnabled', True):
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'alarm_name': alarm_name,
                    'severity': 'medium',
                    'issue_type': 'actions_disabled',
                    'description': f"CloudWatch alarm {alarm_name} has actions disabled"
                }
                issues.append(issue)
            
            # Check alarm configuration
            if not alarm.get('AlarmActions'):
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'alarm_name': alarm_name,
                    'severity': 'medium',
                    'issue_type': 'no_alarm_actions',
                    'description': f"CloudWatch alarm {alarm_name} has no alarm actions configured"
                }
                issues.append(issue)
            
            # Check evaluation period
            if alarm.get('EvaluationPeriods', 1) < 2:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'alarm_name': alarm_name,
                    'severity': 'low',
                    'issue_type': 'short_evaluation',
                    'description': f"CloudWatch alarm {alarm_name} has short evaluation period: {alarm.get('EvaluationPeriods')}"
                }
                issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing alarm {alarm.get('AlarmName')}: {e}")
            return []
    
    def analyze_log_group_health(self, log_group: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze the health of a CloudWatch Log group."""
        issues = []
        
        try:
            group_name = log_group.get('LogGroupName')
            
            # Check retention period
            retention = log_group.get('RetentionInDays')
            if retention is None:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'log_group': group_name,
                    'severity': 'high',
                    'issue_type': 'no_retention',
                    'description': f"CloudWatch Log group {group_name} has no retention period set"
                }
                issues.append(issue)
            elif retention < 7:  # Less than 7 days
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'log_group': group_name,
                    'severity': 'medium',
                    'issue_type': 'short_retention',
                    'description': f"CloudWatch Log group {group_name} has short retention period: {retention} days"
                }
                issues.append(issue)
            
            # Check storage
            stored_bytes = log_group.get('StoredBytes', 0)
            if stored_bytes > 10 * 1024 * 1024 * 1024:  # More than 10GB
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'log_group': group_name,
                    'severity': 'medium',
                    'issue_type': 'high_storage',
                    'description': f"CloudWatch Log group {group_name} has high storage usage: {stored_bytes/1024/1024/1024:.1f}GB"
                }
                issues.append(issue)
            
            # Check encryption
            if not log_group.get('KmsKeyId'):
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'log_group': group_name,
                    'severity': 'low',
                    'issue_type': 'no_encryption',
                    'description': f"CloudWatch Log group {group_name} is not encrypted with KMS"
                }
                issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing log group {log_group.get('LogGroupName')}: {e}")
            return []
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze CloudWatch issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | Resource: {issue.get('alarm_name', issue.get('log_group'))} | " +
            f"Severity: {issue.get('severity')} | Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following CloudWatch issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on monitoring and observability
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
            "service": "CloudWatch",
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
            
            if query_type == "alarm_health":
                alarm_name = data.get("alarm_name")
                if alarm_name:
                    alarms = self.get_alarms()
                    alarm = next((a for a in alarms if a.get('AlarmName') == alarm_name), None)
                    if alarm:
                        issues = self.analyze_alarm_health(alarm)
                        analysis = self.analyze_with_bedrock(issues)
                        return json.dumps({
                            "alarm_name": alarm_name,
                            "issues": issues,
                            "analysis": analysis
                        })
            
            elif query_type == "log_group_health":
                group_name = data.get("log_group")
                if group_name:
                    log_groups = self.get_log_groups()
                    log_group = next((g for g in log_groups if g.get('LogGroupName') == group_name), None)
                    if log_group:
                        issues = self.analyze_log_group_health(log_group)
                        analysis = self.analyze_with_bedrock(issues)
                        return json.dumps({
                            "log_group": group_name,
                            "issues": issues,
                            "analysis": analysis
                        })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all CloudWatch resources."""
        try:
            all_issues = []
            
            # Check alarms
            alarms = self.get_alarms()
            for alarm in alarms:
                issues = self.analyze_alarm_health(alarm)
                all_issues.extend(issues)
            
            # Check log groups
            log_groups = self.get_log_groups()
            for log_group in log_groups:
                issues = self.analyze_log_group_health(log_group)
                all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in CloudWatch monitoring cycle: {e}",
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


def create_cloudwatch_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> CloudWatchMonitoringAgent:
    """Create a CloudWatch monitoring agent."""
    broker = A2AMessageBroker()
    return CloudWatchMonitoringAgent(agent_id, broker, supervisor_id, region_name) 
"""
DynamoDB Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon DynamoDB.
It detects issues related to table health, capacity, and performance.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class DynamoDBMonitoringAgent(A2AAgent):
    """Agent for monitoring DynamoDB and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the DynamoDB monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.dynamodb = boto3.client('dynamodb', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "dynamodb_monitoring",
            "table_health",
            "capacity_analysis",
            "performance_monitoring"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "DynamoDB"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_tables(self) -> List[Dict[str, Any]]:
        """Get list of DynamoDB tables."""
        try:
            tables = []
            paginator = self.dynamodb.get_paginator('list_tables')
            
            for page in paginator.paginate():
                for table_name in page.get('TableNames', []):
                    table_info = self.dynamodb.describe_table(TableName=table_name)
                    table = table_info.get('Table', {})
                    tables.append({
                        'TableName': table.get('TableName'),
                        'TableArn': table.get('TableArn'),
                        'TableStatus': table.get('TableStatus'),
                        'TableSizeBytes': table.get('TableSizeBytes'),
                        'ItemCount': table.get('ItemCount'),
                        'ProvisionedThroughput': table.get('ProvisionedThroughput'),
                        'GlobalSecondaryIndexes': table.get('GlobalSecondaryIndexes', []),
                        'LocalSecondaryIndexes': table.get('LocalSecondaryIndexes', []),
                        'StreamSpecification': table.get('StreamSpecification'),
                        'SSEDescription': table.get('SSEDescription'),
                        'TimeToLiveDescription': table.get('TimeToLiveDescription'),
                        'BillingModeSummary': table.get('BillingModeSummary')
                    })
            
            return tables
        except Exception as e:
            print(f"Error retrieving DynamoDB tables: {e}")
            self.send_notification(
                content=f"Error retrieving DynamoDB tables: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_table_metrics(self, table_name: str) -> Dict[str, Any]:
        """Get CloudWatch metrics for a DynamoDB table."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            metrics = {}
            metric_names = [
                'ConsumedReadCapacityUnits',
                'ConsumedWriteCapacityUnits',
                'ProvisionedReadCapacityUnits',
                'ProvisionedWriteCapacityUnits',
                'ReadThrottleEvents',
                'WriteThrottleEvents',
                'SystemErrors',
                'UserErrors',
                'ReturnedItemCount',
                'ReturnedBytes',
                'SuccessfulRequestLatency',
                'ThrottledRequests'
            ]
            
            for metric_name in metric_names:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/DynamoDB',
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'TableName', 'Value': table_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum', 'Sum']
                )
                metrics[metric_name] = response.get('Datapoints', [])
            
            return metrics
        except Exception as e:
            print(f"Error retrieving metrics for table {table_name}: {e}")
            return {}
    
    def analyze_table_health(self, table: Dict[str, Any], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze the health of a DynamoDB table."""
        issues = []
        
        try:
            # Check table status
            if table.get('TableStatus') != 'ACTIVE':
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'table_name': table.get('TableName'),
                    'severity': 'high',
                    'issue_type': 'table_status',
                    'description': f"DynamoDB table {table.get('TableName')} is not ACTIVE: {table.get('TableStatus')}"
                }
                issues.append(issue)
            
            # Check provisioned capacity
            if table.get('BillingModeSummary', {}).get('BillingMode') == 'PROVISIONED':
                provisioned = table.get('ProvisionedThroughput', {})
                read_capacity = provisioned.get('ReadCapacityUnits', 0)
                write_capacity = provisioned.get('WriteCapacityUnits', 0)
                
                if read_capacity == 0 or write_capacity == 0:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'table_name': table.get('TableName'),
                        'severity': 'medium',
                        'issue_type': 'zero_capacity',
                        'description': f"DynamoDB table {table.get('TableName')} has zero provisioned capacity"
                    }
                    issues.append(issue)
            
            # Check throttling
            read_throttles = metrics.get('ReadThrottleEvents', [])
            write_throttles = metrics.get('WriteThrottleEvents', [])
            
            if read_throttles or write_throttles:
                total_throttles = sum(point.get('Sum', 0) for point in read_throttles + write_throttles)
                if total_throttles > 0:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'table_name': table.get('TableName'),
                        'severity': 'high',
                        'issue_type': 'throttling',
                        'description': f"DynamoDB table {table.get('TableName')} has {total_throttles} throttle events in the last hour"
                    }
                    issues.append(issue)
            
            # Check errors
            system_errors = metrics.get('SystemErrors', [])
            user_errors = metrics.get('UserErrors', [])
            
            if system_errors or user_errors:
                total_errors = sum(point.get('Sum', 0) for point in system_errors + user_errors)
                if total_errors > 0:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'table_name': table.get('TableName'),
                        'severity': 'high',
                        'issue_type': 'errors',
                        'description': f"DynamoDB table {table.get('TableName')} has {total_errors} errors in the last hour"
                    }
                    issues.append(issue)
            
            # Check latency
            latency = metrics.get('SuccessfulRequestLatency', [])
            if latency:
                max_latency = max(point.get('Maximum', 0) for point in latency)
                if max_latency > 100:  # 100ms threshold
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'table_name': table.get('TableName'),
                        'severity': 'medium',
                        'issue_type': 'high_latency',
                        'description': f"DynamoDB table {table.get('TableName')} has high latency: {max_latency}ms"
                    }
                    issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing table {table.get('TableName')}: {e}")
            return []
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze DynamoDB issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | Table: {issue.get('table_name')} | " +
            f"Severity: {issue.get('severity')} | Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following DynamoDB issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on application performance and reliability
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
            "service": "DynamoDB",
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
            
            if query_type == "table_health":
                table_name = data.get("table_name")
                if table_name:
                    tables = self.get_tables()
                    table = next((t for t in tables if t.get('TableName') == table_name), None)
                    if table:
                        metrics = self.get_table_metrics(table_name)
                        issues = self.analyze_table_health(table, metrics)
                        analysis = self.analyze_with_bedrock(issues)
                        return json.dumps({
                            "table_name": table_name,
                            "issues": issues,
                            "analysis": analysis
                        })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all DynamoDB tables."""
        try:
            all_issues = []
            
            # Get all tables
            tables = self.get_tables()
            
            # Check each table
            for table in tables:
                metrics = self.get_table_metrics(table.get('TableName'))
                issues = self.analyze_table_health(table, metrics)
                all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in DynamoDB monitoring cycle: {e}",
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


def create_dynamodb_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> DynamoDBMonitoringAgent:
    """Create a DynamoDB monitoring agent."""
    broker = A2AMessageBroker()
    return DynamoDBMonitoringAgent(agent_id, broker, supervisor_id, region_name) 
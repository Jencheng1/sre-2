"""
RDS Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon RDS.
It detects database performance issues, backup status, and maintenance events.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class RDSMonitoringAgent(A2AAgent):
    """Agent for monitoring Amazon RDS and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the RDS monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.rds = boto3.client('rds', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define metrics to monitor
        self.metrics = [
            "CPUUtilization",
            "FreeableMemory",
            "FreeStorageSpace",
            "DatabaseConnections",
            "ReadIOPS",
            "WriteIOPS",
            "ReadLatency",
            "WriteLatency",
            "SwapUsage",
            "BinLogDiskUsage",
            "ReplicaLag"
        ]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "rds_monitoring",
            "performance_analysis",
            "backup_monitoring",
            "maintenance_tracking"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "RDS"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_db_instances(self) -> List[Dict[str, Any]]:
        """Get list of RDS instances."""
        try:
            response = self.rds.describe_db_instances()
            return response.get('DBInstances', [])
        except Exception as e:
            print(f"Error retrieving RDS instances: {e}")
            self.send_notification(
                content=f"Error retrieving RDS instances: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_metric_data(self, instance_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get CloudWatch metrics for a DB instance."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            metric_data = {}
            for metric in self.metrics:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName=metric,
                    Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum']
                )
                metric_data[metric] = response.get('Datapoints', [])
            
            return metric_data
        except Exception as e:
            print(f"Error retrieving metrics for instance {instance_id}: {e}")
            return {}
    
    def get_backup_status(self, instance_id: str) -> Dict[str, Any]:
        """Get backup status for a DB instance."""
        try:
            response = self.rds.describe_db_instances(DBInstanceIdentifier=instance_id)
            instance = response['DBInstances'][0]
            
            return {
                'backup_retention_period': instance.get('BackupRetentionPeriod', 0),
                'latest_restorable_time': instance.get('LatestRestorableTime', ''),
                'auto_minor_version_upgrade': instance.get('AutoMinorVersionUpgrade', False),
                'maintenance_window': instance.get('PreferredMaintenanceWindow', ''),
                'backup_window': instance.get('PreferredBackupWindow', '')
            }
        except Exception as e:
            print(f"Error retrieving backup status for instance {instance_id}: {e}")
            return {}
    
    def analyze_instance_health(self, instance_id: str) -> List[Dict[str, Any]]:
        """Analyze the health of an RDS instance."""
        issues = []
        
        try:
            # Get instance details
            response = self.rds.describe_db_instances(DBInstanceIdentifier=instance_id)
            instance = response['DBInstances'][0]
            
            # Check instance status
            status = instance.get('DBInstanceStatus', '')
            if status != 'available':
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'instance_id': instance_id,
                    'status': status,
                    'severity': 'high',
                    'issue_type': 'instance_status',
                    'description': f"RDS instance {instance_id} is in {status} state"
                }
                issues.append(issue)
            
            # Check backup configuration
            backup_status = self.get_backup_status(instance_id)
            if backup_status.get('backup_retention_period', 0) < 7:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'instance_id': instance_id,
                    'retention_period': backup_status['backup_retention_period'],
                    'severity': 'medium',
                    'issue_type': 'backup_configuration',
                    'description': f"RDS instance {instance_id} has short backup retention period: {backup_status['backup_retention_period']} days"
                }
                issues.append(issue)
            
            # Check metrics
            metrics = self.get_metric_data(instance_id)
            for metric, datapoints in metrics.items():
                if not datapoints:
                    continue
                
                latest = max(datapoints, key=lambda x: x['Timestamp'])
                average = latest.get('Average', 0)
                maximum = latest.get('Maximum', 0)
                
                if metric == 'CPUUtilization' and average > 80:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'instance_id': instance_id,
                        'metric': metric,
                        'value': average,
                        'threshold': 80,
                        'severity': 'medium',
                        'issue_type': 'high_cpu',
                        'description': f"RDS instance {instance_id} has high CPU utilization: {average}%"
                    }
                    issues.append(issue)
                
                elif metric == 'FreeableMemory' and average < 1000000000:  # Less than 1GB
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'instance_id': instance_id,
                        'metric': metric,
                        'value': average,
                        'threshold': 1000000000,
                        'severity': 'medium',
                        'issue_type': 'low_memory',
                        'description': f"RDS instance {instance_id} has low freeable memory: {average} bytes"
                    }
                    issues.append(issue)
                
                elif metric == 'FreeStorageSpace' and average < 10000000000:  # Less than 10GB
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'instance_id': instance_id,
                        'metric': metric,
                        'value': average,
                        'threshold': 10000000000,
                        'severity': 'high',
                        'issue_type': 'low_storage',
                        'description': f"RDS instance {instance_id} has low free storage space: {average} bytes"
                    }
                    issues.append(issue)
                
                elif metric == 'DatabaseConnections' and average > instance.get('MaxConnections', 1000) * 0.8:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'instance_id': instance_id,
                        'metric': metric,
                        'value': average,
                        'threshold': instance.get('MaxConnections', 1000) * 0.8,
                        'severity': 'medium',
                        'issue_type': 'high_connections',
                        'description': f"RDS instance {instance_id} has high number of connections: {average}"
                    }
                    issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing instance health for {instance_id}: {e}")
            return []
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze RDS issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | Instance: {issue.get('instance_id')} | " +
            f"Severity: {issue.get('severity')} | Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following Amazon RDS issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on database availability and performance
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
            "service": "RDS",
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
            
            if query_type == "instance_health":
                instance_id = data.get("instance_id")
                if instance_id:
                    issues = self.analyze_instance_health(instance_id)
                    analysis = self.analyze_with_bedrock(issues)
                    return json.dumps({
                        "instance_id": instance_id,
                        "issues": issues,
                        "analysis": analysis
                    })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all instances."""
        try:
            # Get all instances
            instances = self.get_db_instances()
            
            all_issues = []
            for instance in instances:
                instance_id = instance.get('DBInstanceIdentifier')
                if instance_id:
                    # Analyze instance health
                    issues = self.analyze_instance_health(instance_id)
                    all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in RDS monitoring cycle: {e}",
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


def create_rds_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> RDSMonitoringAgent:
    """Create an RDS monitoring agent."""
    broker = A2AMessageBroker()
    return RDSMonitoringAgent(agent_id, broker, supervisor_id, region_name) 
"""
ECS Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon ECS.
It detects service health, task status, and container insights.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class ECSMonitoringAgent(A2AAgent):
    """Agent for monitoring Amazon ECS and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the ECS monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.ecs = boto3.client('ecs', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define metrics to monitor
        self.metrics = [
            "CPUUtilization",
            "MemoryUtilization",
            "RunningTaskCount",
            "PendingTaskCount",
            "ActiveServiceCount",
            "NetworkRxBytes",
            "NetworkTxBytes"
        ]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "ecs_monitoring",
            "service_health_detection",
            "task_status_monitoring",
            "container_insights_analysis"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "ECS"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_clusters(self) -> List[str]:
        """Get list of ECS clusters."""
        try:
            response = self.ecs.list_clusters()
            return response.get('clusterArns', [])
        except Exception as e:
            print(f"Error retrieving ECS clusters: {e}")
            self.send_notification(
                content=f"Error retrieving ECS clusters: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_services(self, cluster: str) -> List[Dict[str, Any]]:
        """Get services in a cluster."""
        try:
            response = self.ecs.list_services(cluster=cluster)
            service_arns = response.get('serviceArns', [])
            
            if not service_arns:
                return []
            
            # Get detailed service information
            services_response = self.ecs.describe_services(
                cluster=cluster,
                services=service_arns
            )
            return services_response.get('services', [])
        except Exception as e:
            print(f"Error retrieving services for cluster {cluster}: {e}")
            return []
    
    def get_tasks(self, cluster: str) -> List[Dict[str, Any]]:
        """Get tasks in a cluster."""
        try:
            response = self.ecs.list_tasks(cluster=cluster)
            task_arns = response.get('taskArns', [])
            
            if not task_arns:
                return []
            
            # Get detailed task information
            tasks_response = self.ecs.describe_tasks(
                cluster=cluster,
                tasks=task_arns
            )
            return tasks_response.get('tasks', [])
        except Exception as e:
            print(f"Error retrieving tasks for cluster {cluster}: {e}")
            return []
    
    def get_metric_data(self, cluster: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get CloudWatch metrics for a cluster."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            metric_data = {}
            for metric in self.metrics:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/ECS',
                    MetricName=metric,
                    Dimensions=[{'Name': 'ClusterName', 'Value': cluster}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum']
                )
                metric_data[metric] = response.get('Datapoints', [])
            
            return metric_data
        except Exception as e:
            print(f"Error retrieving metrics for cluster {cluster}: {e}")
            return {}
    
    def analyze_cluster_health(self, cluster: str) -> List[Dict[str, Any]]:
        """Analyze the health of an ECS cluster."""
        issues = []
        
        # Get cluster services and tasks
        services = self.get_services(cluster)
        tasks = self.get_tasks(cluster)
        metrics = self.get_metric_data(cluster)
        
        # Check service health
        for service in services:
            service_name = service.get('serviceName', '')
            desired_count = service.get('desiredCount', 0)
            running_count = service.get('runningCount', 0)
            
            if running_count < desired_count:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'cluster': cluster,
                    'service': service_name,
                    'desired_count': desired_count,
                    'running_count': running_count,
                    'severity': 'high',
                    'issue_type': 'service_health',
                    'description': f"Service {service_name} has {running_count} running tasks, expected {desired_count}"
                }
                issues.append(issue)
        
        # Check task health
        for task in tasks:
            task_id = task.get('taskArn', '').split('/')[-1]
            last_status = task.get('lastStatus', '')
            desired_status = task.get('desiredStatus', '')
            
            if last_status == 'STOPPED' and desired_status == 'RUNNING':
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'cluster': cluster,
                    'task_id': task_id,
                    'last_status': last_status,
                    'desired_status': desired_status,
                    'severity': 'medium',
                    'issue_type': 'task_health',
                    'description': f"Task {task_id} is stopped but should be running"
                }
                issues.append(issue)
        
        # Check metrics
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
                    'cluster': cluster,
                    'metric': metric,
                    'value': average,
                    'threshold': 80,
                    'severity': 'medium',
                    'issue_type': 'high_cpu',
                    'description': f"Cluster {cluster} has high CPU utilization: {average}%"
                }
                issues.append(issue)
            
            elif metric == 'MemoryUtilization' and average > 80:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'cluster': cluster,
                    'metric': metric,
                    'value': average,
                    'threshold': 80,
                    'severity': 'medium',
                    'issue_type': 'high_memory',
                    'description': f"Cluster {cluster} has high memory utilization: {average}%"
                }
                issues.append(issue)
        
        return issues
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze ECS issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | Cluster: {issue.get('cluster')} | " +
            f"Severity: {issue.get('severity')} | Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following Amazon ECS issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on application availability
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
            "service": "ECS",
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
            
            if query_type == "cluster_health":
                cluster = data.get("cluster")
                if cluster:
                    issues = self.analyze_cluster_health(cluster)
                    analysis = self.analyze_with_bedrock(issues)
                    return json.dumps({
                        "cluster": cluster,
                        "issues": issues,
                        "analysis": analysis
                    })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all clusters."""
        try:
            # Get all clusters
            clusters = self.get_clusters()
            
            all_issues = []
            for cluster in clusters:
                # Analyze cluster health
                issues = self.analyze_cluster_health(cluster)
                all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in ECS monitoring cycle: {e}",
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


def create_ecs_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> ECSMonitoringAgent:
    """Create an ECS monitoring agent."""
    broker = A2AMessageBroker()
    return ECSMonitoringAgent(agent_id, broker, supervisor_id, region_name) 
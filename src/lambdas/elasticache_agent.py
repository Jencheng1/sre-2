"""
ElastiCache Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon ElastiCache.
It detects issues related to cache performance, evictions, and memory pressure.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class ElastiCacheMonitoringAgent(A2AAgent):
    """Agent for monitoring ElastiCache and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the ElastiCache monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.elasticache = boto3.client('elasticache', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define metrics to monitor
        self.metrics = [
            "CPUUtilization",
            "FreeableMemory",
            "SwapUsage",
            "CurrConnections",
            "NewConnections",
            "CacheHits",
            "CacheMisses",
            "Evictions",
            "BytesUsedForCache",
            "NetworkBytesIn",
            "NetworkBytesOut",
            "ReplicationLag"
        ]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "cache_monitoring",
            "performance_analysis",
            "memory_monitoring",
            "replication_monitoring"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "ElastiCache"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_cache_clusters(self) -> List[Dict[str, Any]]:
        """Get list of cache clusters."""
        try:
            clusters = []
            paginator = self.elasticache.get_paginator('describe_cache_clusters')
            
            for page in paginator.paginate():
                clusters.extend(page.get('CacheClusters', []))
            
            return clusters
        except Exception as e:
            print(f"Error retrieving cache clusters: {e}")
            self.send_notification(
                content=f"Error retrieving cache clusters: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_cluster_metrics(self, cluster_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get CloudWatch metrics for a cache cluster."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            metric_data = {}
            for metric in self.metrics:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/ElastiCache',
                    MetricName=metric,
                    Dimensions=[
                        {'Name': 'CacheClusterId', 'Value': cluster_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum', 'Sum']
                )
                metric_data[metric] = response.get('Datapoints', [])
            
            return metric_data
        except Exception as e:
            print(f"Error retrieving metrics for cluster {cluster_id}: {e}")
            return {}
    
    def analyze_cluster_health(self, cluster_id: str) -> List[Dict[str, Any]]:
        """Analyze the health of a cache cluster."""
        issues = []
        
        try:
            # Get cluster details
            cluster = self.elasticache.describe_cache_clusters(
                CacheClusterId=cluster_id
            ).get('CacheClusters', [{}])[0]
            
            # Check cluster status
            if cluster.get('CacheClusterStatus') != 'available':
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'cluster_id': cluster_id,
                    'status': cluster.get('CacheClusterStatus'),
                    'severity': 'high',
                    'issue_type': 'cluster_status',
                    'description': f"Cache cluster {cluster_id} is in {cluster.get('CacheClusterStatus')} state"
                }
                issues.append(issue)
            
            # Get cluster metrics
            metrics = self.get_cluster_metrics(cluster_id)
            
            for metric, datapoints in metrics.items():
                if not datapoints:
                    continue
                
                latest = max(datapoints, key=lambda x: x['Timestamp'])
                average = latest.get('Average', 0)
                maximum = latest.get('Maximum', 0)
                total = latest.get('Sum', 0)
                
                if metric == 'CPUUtilization' and average > 80:  # 80% CPU utilization
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'cluster_id': cluster_id,
                        'metric': metric,
                        'value': average,
                        'threshold': 80,
                        'severity': 'high',
                        'issue_type': 'high_cpu',
                        'description': f"Cache cluster {cluster_id} has high CPU utilization: {average}%"
                    }
                    issues.append(issue)
                
                elif metric == 'FreeableMemory' and average < 100 * 1024 * 1024:  # Less than 100MB free
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'cluster_id': cluster_id,
                        'metric': metric,
                        'value': average,
                        'threshold': 100 * 1024 * 1024,
                        'severity': 'high',
                        'issue_type': 'low_memory',
                        'description': f"Cache cluster {cluster_id} has low free memory: {average / (1024 * 1024):.2f}MB"
                    }
                    issues.append(issue)
                
                elif metric == 'SwapUsage' and average > 0:  # Any swap usage
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'cluster_id': cluster_id,
                        'metric': metric,
                        'value': average,
                        'threshold': 0,
                        'severity': 'high',
                        'issue_type': 'swap_usage',
                        'description': f"Cache cluster {cluster_id} is using swap: {average / (1024 * 1024):.2f}MB"
                    }
                    issues.append(issue)
                
                elif metric == 'Evictions' and total > 1000:  # High number of evictions
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'cluster_id': cluster_id,
                        'metric': metric,
                        'value': total,
                        'threshold': 1000,
                        'severity': 'medium',
                        'issue_type': 'high_evictions',
                        'description': f"Cache cluster {cluster_id} has high number of evictions: {total}"
                    }
                    issues.append(issue)
                
                elif metric == 'ReplicationLag' and average > 300:  # More than 5 minutes lag
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'cluster_id': cluster_id,
                        'metric': metric,
                        'value': average,
                        'threshold': 300,
                        'severity': 'high',
                        'issue_type': 'replication_lag',
                        'description': f"Cache cluster {cluster_id} has high replication lag: {average} seconds"
                    }
                    issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing cluster health for {cluster_id}: {e}")
            return []
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze ElastiCache issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | Cluster: {issue.get('cluster_id')} | " +
            f"Severity: {issue.get('severity')} | Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following ElastiCache issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on cache performance and reliability
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
            "service": "ElastiCache",
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
                cluster_id = data.get("cluster_id")
                if cluster_id:
                    issues = self.analyze_cluster_health(cluster_id)
                    analysis = self.analyze_with_bedrock(issues)
                    return json.dumps({
                        "cluster_id": cluster_id,
                        "issues": issues,
                        "analysis": analysis
                    })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all cache clusters."""
        try:
            # Get all cache clusters
            clusters = self.get_cache_clusters()
            
            all_issues = []
            for cluster in clusters:
                cluster_id = cluster['CacheClusterId']
                # Analyze cluster health
                issues = self.analyze_cluster_health(cluster_id)
                all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in ElastiCache monitoring cycle: {e}",
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


def create_elasticache_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> ElastiCacheMonitoringAgent:
    """Create an ElastiCache monitoring agent."""
    broker = A2AMessageBroker()
    return ElastiCacheMonitoringAgent(agent_id, broker, supervisor_id, region_name) 
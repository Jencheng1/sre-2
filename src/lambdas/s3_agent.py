"""
S3 Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon S3.
It detects issues related to bucket metrics, access patterns, and lifecycle policies.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class S3MonitoringAgent(A2AAgent):
    """Agent for monitoring Amazon S3 and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the S3 monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.s3 = boto3.client('s3', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define metrics to monitor
        self.metrics = [
            "BucketSizeBytes",
            "NumberOfObjects",
            "AllRequests",
            "GetRequests",
            "PutRequests",
            "DeleteRequests",
            "4xxErrors",
            "5xxErrors",
            "FirstByteLatency",
            "TotalRequestLatency"
        ]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "s3_monitoring",
            "bucket_metrics",
            "access_patterns",
            "lifecycle_policies"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "S3"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_buckets(self) -> List[str]:
        """Get list of S3 buckets."""
        try:
            response = self.s3.list_buckets()
            return [bucket['Name'] for bucket in response.get('Buckets', [])]
        except Exception as e:
            print(f"Error retrieving S3 buckets: {e}")
            self.send_notification(
                content=f"Error retrieving S3 buckets: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_bucket_metrics(self, bucket_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get CloudWatch metrics for a bucket."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            metric_data = {}
            for metric in self.metrics:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/S3',
                    MetricName=metric,
                    Dimensions=[{'Name': 'BucketName', 'Value': bucket_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum']
                )
                metric_data[metric] = response.get('Datapoints', [])
            
            return metric_data
        except Exception as e:
            print(f"Error retrieving metrics for bucket {bucket_name}: {e}")
            return {}
    
    def get_bucket_policy(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket policy."""
        try:
            response = self.s3.get_bucket_policy(Bucket=bucket_name)
            return json.loads(response['Policy'])
        except self.s3.exceptions.NoSuchBucketPolicy:
            return {}
        except Exception as e:
            print(f"Error retrieving policy for bucket {bucket_name}: {e}")
            return {}
    
    def get_bucket_lifecycle(self, bucket_name: str) -> List[Dict[str, Any]]:
        """Get bucket lifecycle configuration."""
        try:
            response = self.s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            return response.get('Rules', [])
        except self.s3.exceptions.NoSuchLifecycleConfiguration:
            return []
        except Exception as e:
            print(f"Error retrieving lifecycle config for bucket {bucket_name}: {e}")
            return []
    
    def get_bucket_versioning(self, bucket_name: str) -> bool:
        """Check if bucket versioning is enabled."""
        try:
            response = self.s3.get_bucket_versioning(Bucket=bucket_name)
            return response.get('Status') == 'Enabled'
        except Exception as e:
            print(f"Error checking versioning for bucket {bucket_name}: {e}")
            return False
    
    def analyze_bucket_health(self, bucket_name: str) -> List[Dict[str, Any]]:
        """Analyze the health of an S3 bucket."""
        issues = []
        
        try:
            # Check bucket policy
            policy = self.get_bucket_policy(bucket_name)
            if not policy:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'bucket_name': bucket_name,
                    'severity': 'medium',
                    'issue_type': 'no_policy',
                    'description': f"S3 bucket {bucket_name} has no bucket policy"
                }
                issues.append(issue)
            
            # Check versioning
            if not self.get_bucket_versioning(bucket_name):
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'bucket_name': bucket_name,
                    'severity': 'medium',
                    'issue_type': 'no_versioning',
                    'description': f"S3 bucket {bucket_name} has versioning disabled"
                }
                issues.append(issue)
            
            # Check lifecycle rules
            lifecycle_rules = self.get_bucket_lifecycle(bucket_name)
            if not lifecycle_rules:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'bucket_name': bucket_name,
                    'severity': 'low',
                    'issue_type': 'no_lifecycle',
                    'description': f"S3 bucket {bucket_name} has no lifecycle rules"
                }
                issues.append(issue)
            
            # Check metrics
            metrics = self.get_bucket_metrics(bucket_name)
            for metric, datapoints in metrics.items():
                if not datapoints:
                    continue
                
                latest = max(datapoints, key=lambda x: x['Timestamp'])
                average = latest.get('Average', 0)
                maximum = latest.get('Maximum', 0)
                
                if metric == '5xxErrors' and average > 0:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'bucket_name': bucket_name,
                        'metric': metric,
                        'value': average,
                        'threshold': 0,
                        'severity': 'high',
                        'issue_type': 'server_errors',
                        'description': f"S3 bucket {bucket_name} has server errors: {average}"
                    }
                    issues.append(issue)
                
                elif metric == '4xxErrors' and average > 100:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'bucket_name': bucket_name,
                        'metric': metric,
                        'value': average,
                        'threshold': 100,
                        'severity': 'medium',
                        'issue_type': 'client_errors',
                        'description': f"S3 bucket {bucket_name} has high client errors: {average}"
                    }
                    issues.append(issue)
                
                elif metric == 'FirstByteLatency' and average > 100:  # 100ms
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'bucket_name': bucket_name,
                        'metric': metric,
                        'value': average,
                        'threshold': 100,
                        'severity': 'medium',
                        'issue_type': 'high_latency',
                        'description': f"S3 bucket {bucket_name} has high latency: {average}ms"
                    }
                    issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing bucket health for {bucket_name}: {e}")
            return []
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze S3 issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | Bucket: {issue.get('bucket_name')} | " +
            f"Severity: {issue.get('severity')} | Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following Amazon S3 issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on data accessibility and performance
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
            "service": "S3",
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
            
            if query_type == "bucket_health":
                bucket_name = data.get("bucket_name")
                if bucket_name:
                    issues = self.analyze_bucket_health(bucket_name)
                    analysis = self.analyze_with_bedrock(issues)
                    return json.dumps({
                        "bucket_name": bucket_name,
                        "issues": issues,
                        "analysis": analysis
                    })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all buckets."""
        try:
            # Get all buckets
            buckets = self.get_buckets()
            
            all_issues = []
            for bucket_name in buckets:
                # Analyze bucket health
                issues = self.analyze_bucket_health(bucket_name)
                all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in S3 monitoring cycle: {e}",
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


def create_s3_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> S3MonitoringAgent:
    """Create an S3 monitoring agent."""
    broker = A2AMessageBroker()
    return S3MonitoringAgent(agent_id, broker, supervisor_id, region_name) 
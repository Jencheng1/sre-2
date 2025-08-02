"""
API Gateway Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon API Gateway.
It detects issues related to API performance, errors, latency, and resource utilization.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class APIGatewayMonitoringAgent(A2AAgent):
    """Agent for monitoring API Gateway and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the API Gateway monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.apigateway_client = boto3.client('apigateway', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define metrics to monitor
        self.metrics = [
            "Count",
            "4XXError",
            "5XXError",
            "Latency",
            "IntegrationLatency",
            "CacheHitCount",
            "CacheMissCount",
            "DataProcessed",
            "ThrottleCount"
        ]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "api_monitoring",
            "performance_analysis",
            "error_detection",
            "latency_monitoring"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "API Gateway"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_apis(self) -> List[Dict[str, Any]]:
        """Get list of REST APIs."""
        try:
            apis = []
            paginator = self.apigateway_client.get_paginator('get_rest_apis')
            
            for page in paginator.paginate():
                apis.extend(page.get('items', []))
            
            return apis
        except Exception as e:
            print(f"Error retrieving APIs: {e}")
            self.send_notification(
                content=f"Error retrieving APIs: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_api_stages(self, api_id: str) -> List[Dict[str, Any]]:
        """Get stages for a REST API."""
        try:
            response = self.apigateway_client.get_stages(
                restApiId=api_id
            )
            return response.get('item', [])
        except Exception as e:
            print(f"Error retrieving stages for API {api_id}: {e}")
            return []
    
    def get_api_resources(self, api_id: str) -> List[Dict[str, Any]]:
        """Get resources for a REST API."""
        try:
            resources = []
            paginator = self.apigateway_client.get_paginator('get_resources')
            
            for page in paginator.paginate(restApiId=api_id):
                resources.extend(page.get('items', []))
            
            return resources
        except Exception as e:
            print(f"Error retrieving resources for API {api_id}: {e}")
            return []
    
    def get_api_metrics(self, api_id: str, stage: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get CloudWatch metrics for an API stage."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            metric_data = {}
            for metric in self.metrics:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/ApiGateway',
                    MetricName=metric,
                    Dimensions=[
                        {'Name': 'ApiId', 'Value': api_id},
                        {'Name': 'Stage', 'Value': stage}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum', 'Sum']
                )
                metric_data[metric] = response.get('Datapoints', [])
            
            return metric_data
        except Exception as e:
            print(f"Error retrieving metrics for API {api_id} stage {stage}: {e}")
            return {}
    
    def analyze_api_health(self, api_id: str, stage: str) -> List[Dict[str, Any]]:
        """Analyze the health of an API stage."""
        issues = []
        
        try:
            # Get API metrics
            metrics = self.get_api_metrics(api_id, stage)
            
            for metric, datapoints in metrics.items():
                if not datapoints:
                    continue
                
                latest = max(datapoints, key=lambda x: x['Timestamp'])
                average = latest.get('Average', 0)
                maximum = latest.get('Maximum', 0)
                total = latest.get('Sum', 0)
                
                if metric == '5XXError' and total > 0:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'api_id': api_id,
                        'stage': stage,
                        'metric': metric,
                        'value': total,
                        'threshold': 0,
                        'severity': 'high',
                        'issue_type': 'server_error',
                        'description': f"API {api_id} stage {stage} has server errors: {total}"
                    }
                    issues.append(issue)
                
                elif metric == '4XXError' and total > 0:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'api_id': api_id,
                        'stage': stage,
                        'metric': metric,
                        'value': total,
                        'threshold': 0,
                        'severity': 'medium',
                        'issue_type': 'client_error',
                        'description': f"API {api_id} stage {stage} has client errors: {total}"
                    }
                    issues.append(issue)
                
                elif metric == 'Latency' and average > 1000:  # 1 second
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'api_id': api_id,
                        'stage': stage,
                        'metric': metric,
                        'value': average,
                        'threshold': 1000,
                        'severity': 'high',
                        'issue_type': 'high_latency',
                        'description': f"API {api_id} stage {stage} has high latency: {average}ms"
                    }
                    issues.append(issue)
                
                elif metric == 'IntegrationLatency' and average > 1000:  # 1 second
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'api_id': api_id,
                        'stage': stage,
                        'metric': metric,
                        'value': average,
                        'threshold': 1000,
                        'severity': 'high',
                        'issue_type': 'high_integration_latency',
                        'description': f"API {api_id} stage {stage} has high integration latency: {average}ms"
                    }
                    issues.append(issue)
                
                elif metric == 'ThrottleCount' and total > 0:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'api_id': api_id,
                        'stage': stage,
                        'metric': metric,
                        'value': total,
                        'threshold': 0,
                        'severity': 'high',
                        'issue_type': 'throttling',
                        'description': f"API {api_id} stage {stage} is being throttled: {total} times"
                    }
                    issues.append(issue)
                
                elif metric == 'CacheMissCount' and total > 1000:  # High cache misses
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'api_id': api_id,
                        'stage': stage,
                        'metric': metric,
                        'value': total,
                        'threshold': 1000,
                        'severity': 'medium',
                        'issue_type': 'high_cache_misses',
                        'description': f"API {api_id} stage {stage} has high cache misses: {total}"
                    }
                    issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing API health for {api_id} stage {stage}: {e}")
            return []
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze API Gateway issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | API: {issue.get('api_id')} | " +
            f"Stage: {issue.get('stage')} | Severity: {issue.get('severity')} | " +
            f"Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following API Gateway issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on API performance and reliability
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
            "service": "API Gateway",
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
            
            if query_type == "api_health":
                api_id = data.get("api_id")
                stage = data.get("stage")
                if api_id and stage:
                    issues = self.analyze_api_health(api_id, stage)
                    analysis = self.analyze_with_bedrock(issues)
                    return json.dumps({
                        "api_id": api_id,
                        "stage": stage,
                        "issues": issues,
                        "analysis": analysis
                    })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all APIs."""
        try:
            # Get all APIs
            apis = self.get_apis()
            
            all_issues = []
            for api in apis:
                api_id = api['id']
                # Get stages for the API
                stages = self.get_api_stages(api_id)
                
                for stage in stages:
                    stage_name = stage['stageName']
                    # Analyze API health
                    issues = self.analyze_api_health(api_id, stage_name)
                    all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in API Gateway monitoring cycle: {e}",
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


def create_apigateway_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> APIGatewayMonitoringAgent:
    """Create an API Gateway monitoring agent."""
    broker = A2AMessageBroker()
    return APIGatewayMonitoringAgent(agent_id, broker, supervisor_id, region_name) 
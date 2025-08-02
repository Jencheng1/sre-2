"""
CloudFront Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon CloudFront.
It detects issues related to CDN performance, distributions, and edge locations.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class CloudFrontMonitoringAgent(A2AAgent):
    """Agent for monitoring CloudFront and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the CloudFront monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.cloudfront = boto3.client('cloudfront', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "cloudfront_monitoring",
            "cdn_performance",
            "distribution_analysis",
            "edge_location_monitoring"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "CloudFront"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_distributions(self) -> List[Dict[str, Any]]:
        """Get list of CloudFront distributions."""
        try:
            distributions = []
            paginator = self.cloudfront.get_paginator('list_distributions')
            
            for page in paginator.paginate():
                distributions.extend(page.get('DistributionList', {}).get('Items', []))
            
            return distributions
        except Exception as e:
            print(f"Error retrieving CloudFront distributions: {e}")
            self.send_notification(
                content=f"Error retrieving CloudFront distributions: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_distribution_metrics(self, distribution_id: str) -> Dict[str, Any]:
        """Get CloudWatch metrics for a distribution."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            metrics = {
                'Requests': self._get_metric('Requests', distribution_id, start_time, end_time),
                'BytesDownloaded': self._get_metric('BytesDownloaded', distribution_id, start_time, end_time),
                'BytesUploaded': self._get_metric('BytesUploaded', distribution_id, start_time, end_time),
                '4xxErrorRate': self._get_metric('4xxErrorRate', distribution_id, start_time, end_time),
                '5xxErrorRate': self._get_metric('5xxErrorRate', distribution_id, start_time, end_time),
                'TotalErrorRate': self._get_metric('TotalErrorRate', distribution_id, start_time, end_time),
                'OriginLatency': self._get_metric('OriginLatency', distribution_id, start_time, end_time),
                'CacheHitRate': self._get_metric('CacheHitRate', distribution_id, start_time, end_time)
            }
            
            return metrics
        except Exception as e:
            print(f"Error retrieving metrics for distribution {distribution_id}: {e}")
            return {}
    
    def _get_metric(self, metric_name: str, distribution_id: str, 
                   start_time: datetime, end_time: datetime) -> float:
        """Get a specific CloudWatch metric for a distribution."""
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/CloudFront',
                MetricName=metric_name,
                Dimensions=[{'Name': 'DistributionId', 'Value': distribution_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                return response['Datapoints'][0]['Average']
            return 0.0
        except Exception as e:
            print(f"Error retrieving metric {metric_name} for distribution {distribution_id}: {e}")
            return 0.0
    
    def analyze_distribution(self, distribution: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze the health of a CloudFront distribution."""
        issues = []
        
        try:
            distribution_id = distribution.get('Id')
            domain_name = distribution.get('DomainName')
            status = distribution.get('Status')
            config = distribution.get('DistributionConfig', {})
            
            # Check distribution status
            if status != 'Deployed':
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'distribution_id': distribution_id,
                    'domain_name': domain_name,
                    'status': status,
                    'severity': 'high',
                    'issue_type': 'deployment_status',
                    'description': f"CloudFront distribution {domain_name} is not deployed (status: {status})"
                }
                issues.append(issue)
            
            # Check error rates
            metrics = self.get_distribution_metrics(distribution_id)
            
            if metrics.get('5xxErrorRate', 0) > 5.0:  # More than 5% 5xx errors
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'distribution_id': distribution_id,
                    'domain_name': domain_name,
                    'error_rate': metrics['5xxErrorRate'],
                    'severity': 'high',
                    'issue_type': 'high_error_rate',
                    'description': f"CloudFront distribution {domain_name} has high 5xx error rate: {metrics['5xxErrorRate']}%"
                }
                issues.append(issue)
            
            if metrics.get('OriginLatency', 0) > 1000:  # More than 1 second
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'distribution_id': distribution_id,
                    'domain_name': domain_name,
                    'latency': metrics['OriginLatency'],
                    'severity': 'medium',
                    'issue_type': 'high_latency',
                    'description': f"CloudFront distribution {domain_name} has high origin latency: {metrics['OriginLatency']}ms"
                }
                issues.append(issue)
            
            if metrics.get('CacheHitRate', 0) < 50.0:  # Less than 50% cache hits
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'distribution_id': distribution_id,
                    'domain_name': domain_name,
                    'cache_hit_rate': metrics['CacheHitRate'],
                    'severity': 'medium',
                    'issue_type': 'low_cache_hit_rate',
                    'description': f"CloudFront distribution {domain_name} has low cache hit rate: {metrics['CacheHitRate']}%"
                }
                issues.append(issue)
            
            # Check SSL configuration
            ssl_protocol = config.get('ViewerCertificate', {}).get('MinimumProtocolVersion')
            if ssl_protocol and ssl_protocol in ['SSLv3', 'TLSv1']:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'distribution_id': distribution_id,
                    'domain_name': domain_name,
                    'ssl_protocol': ssl_protocol,
                    'severity': 'high',
                    'issue_type': 'weak_ssl',
                    'description': f"CloudFront distribution {domain_name} uses weak SSL protocol: {ssl_protocol}"
                }
                issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing distribution {distribution.get('Id')}: {e}")
            return []
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze CloudFront issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | Domain: {issue.get('domain_name')} | " +
            f"Severity: {issue.get('severity')} | Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following CloudFront issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on CDN performance and user experience
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
            "service": "CloudFront",
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
            
            if query_type == "distribution_health":
                distribution_id = data.get("distribution_id")
                if distribution_id:
                    distributions = self.get_distributions()
                    distribution = next((d for d in distributions if d.get('Id') == distribution_id), None)
                    if distribution:
                        issues = self.analyze_distribution(distribution)
                        analysis = self.analyze_with_bedrock(issues)
                        return json.dumps({
                            "distribution_id": distribution_id,
                            "issues": issues,
                            "analysis": analysis
                        })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all CloudFront distributions."""
        try:
            all_issues = []
            
            # Check distributions
            distributions = self.get_distributions()
            for distribution in distributions:
                issues = self.analyze_distribution(distribution)
                all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in CloudFront monitoring cycle: {e}",
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


def create_cloudfront_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> CloudFrontMonitoringAgent:
    """Create a CloudFront monitoring agent."""
    broker = A2AMessageBroker()
    return CloudFrontMonitoringAgent(agent_id, broker, supervisor_id, region_name) 
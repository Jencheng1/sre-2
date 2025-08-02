"""
Route 53 Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring Amazon Route 53.
It detects issues related to DNS records, health checks, and hosted zones.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class Route53MonitoringAgent(A2AAgent):
    """Agent for monitoring Route 53 and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the Route 53 monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.route53 = boto3.client('route53', region_name=region_name)
        self.route53domains = boto3.client('route53domains', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "route53_monitoring",
            "dns_health",
            "health_check_management",
            "hosted_zone_analysis"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "Route53"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_hosted_zones(self) -> List[Dict[str, Any]]:
        """Get list of Route 53 hosted zones."""
        try:
            hosted_zones = []
            paginator = self.route53.get_paginator('list_hosted_zones')
            
            for page in paginator.paginate():
                for zone in page.get('HostedZones', []):
                    hosted_zones.append({
                        'Id': zone.get('Id'),
                        'Name': zone.get('Name'),
                        'CallerReference': zone.get('CallerReference'),
                        'Config': zone.get('Config', {}),
                        'ResourceRecordSetCount': zone.get('ResourceRecordSetCount', 0)
                    })
            
            return hosted_zones
        except Exception as e:
            print(f"Error retrieving Route 53 hosted zones: {e}")
            self.send_notification(
                content=f"Error retrieving Route 53 hosted zones: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_health_checks(self) -> List[Dict[str, Any]]:
        """Get list of Route 53 health checks."""
        try:
            health_checks = []
            paginator = self.route53.get_paginator('list_health_checks')
            
            for page in paginator.paginate():
                for check in page.get('HealthChecks', []):
                    health_checks.append({
                        'Id': check.get('Id'),
                        'CallerReference': check.get('CallerReference'),
                        'HealthCheckConfig': check.get('HealthCheckConfig', {}),
                        'HealthCheckVersion': check.get('HealthCheckVersion'),
                        'LinkedService': check.get('LinkedService', {})
                    })
            
            return health_checks
        except Exception as e:
            print(f"Error retrieving Route 53 health checks: {e}")
            self.send_notification(
                content=f"Error retrieving Route 53 health checks: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_resource_record_sets(self, hosted_zone_id: str) -> List[Dict[str, Any]]:
        """Get list of resource record sets for a hosted zone."""
        try:
            records = []
            paginator = self.route53.get_paginator('list_resource_record_sets')
            
            for page in paginator.paginate(HostedZoneId=hosted_zone_id):
                for record in page.get('ResourceRecordSets', []):
                    records.append({
                        'Name': record.get('Name'),
                        'Type': record.get('Type'),
                        'TTL': record.get('TTL'),
                        'ResourceRecords': record.get('ResourceRecords', []),
                        'AliasTarget': record.get('AliasTarget', {}),
                        'HealthCheckId': record.get('HealthCheckId'),
                        'TrafficPolicyInstanceId': record.get('TrafficPolicyInstanceId'),
                        'Weight': record.get('Weight'),
                        'SetIdentifier': record.get('SetIdentifier'),
                        'Region': record.get('Region'),
                        'GeoLocation': record.get('GeoLocation', {}),
                        'Failover': record.get('Failover'),
                        'MultiValueAnswer': record.get('MultiValueAnswer', False)
                    })
            
            return records
        except Exception as e:
            print(f"Error retrieving resource record sets for zone {hosted_zone_id}: {e}")
            return []
    
    def analyze_hosted_zone_health(self, zone: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze the health of a Route 53 hosted zone."""
        issues = []
        
        try:
            zone_id = zone.get('Id')
            zone_name = zone.get('Name')
            
            # Check record count
            record_count = zone.get('ResourceRecordSetCount', 0)
            if record_count == 0:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'zone_id': zone_id,
                    'zone_name': zone_name,
                    'severity': 'medium',
                    'issue_type': 'no_records',
                    'description': f"Route 53 hosted zone {zone_name} has no resource records"
                }
                issues.append(issue)
            
            # Check zone configuration
            config = zone.get('Config', {})
            if not config.get('PrivateZone', False):
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'zone_id': zone_id,
                    'zone_name': zone_name,
                    'severity': 'low',
                    'issue_type': 'public_zone',
                    'description': f"Route 53 hosted zone {zone_name} is public"
                }
                issues.append(issue)
            
            # Check resource records
            records = self.get_resource_record_sets(zone_id)
            for record in records:
                # Check TTL
                if record.get('TTL', 0) < 60:  # Less than 1 minute
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'zone_id': zone_id,
                        'zone_name': zone_name,
                        'record_name': record.get('Name'),
                        'record_type': record.get('Type'),
                        'severity': 'low',
                        'issue_type': 'low_ttl',
                        'description': f"Route 53 record {record.get('Name')} has low TTL: {record.get('TTL')} seconds"
                    }
                    issues.append(issue)
                
                # Check health check
                if record.get('Type') in ['A', 'AAAA', 'CNAME'] and not record.get('HealthCheckId'):
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'zone_id': zone_id,
                        'zone_name': zone_name,
                        'record_name': record.get('Name'),
                        'record_type': record.get('Type'),
                        'severity': 'medium',
                        'issue_type': 'no_health_check',
                        'description': f"Route 53 record {record.get('Name')} has no health check"
                    }
                    issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing hosted zone {zone.get('Name')}: {e}")
            return []
    
    def analyze_health_check(self, check: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze the health of a Route 53 health check."""
        issues = []
        
        try:
            check_id = check.get('Id')
            config = check.get('HealthCheckConfig', {})
            
            # Check failure threshold
            failure_threshold = config.get('FailureThreshold', 3)
            if failure_threshold < 3:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'check_id': check_id,
                    'severity': 'low',
                    'issue_type': 'low_failure_threshold',
                    'description': f"Route 53 health check {check_id} has low failure threshold: {failure_threshold}"
                }
                issues.append(issue)
            
            # Check request interval
            request_interval = config.get('RequestInterval', 30)
            if request_interval > 30:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'check_id': check_id,
                    'severity': 'medium',
                    'issue_type': 'high_request_interval',
                    'description': f"Route 53 health check {check_id} has high request interval: {request_interval} seconds"
                }
                issues.append(issue)
            
            # Check timeout
            timeout = config.get('Timeout', 5)
            if timeout > 5:
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'check_id': check_id,
                    'severity': 'medium',
                    'issue_type': 'high_timeout',
                    'description': f"Route 53 health check {check_id} has high timeout: {timeout} seconds"
                }
                issues.append(issue)
            
            return issues
        
        except Exception as e:
            print(f"Error analyzing health check {check.get('Id')}: {e}")
            return []
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze Route 53 issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Type: {issue.get('issue_type')} | Resource: {issue.get('zone_name', issue.get('check_id'))} | " +
            f"Severity: {issue.get('severity')} | Description: {issue.get('description')}"
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following Route 53 issues and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical issues requiring immediate attention
        2. Potential impact on DNS resolution and service availability
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
            "service": "Route53",
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
            
            if query_type == "zone_health":
                zone_id = data.get("zone_id")
                if zone_id:
                    zones = self.get_hosted_zones()
                    zone = next((z for z in zones if z.get('Id') == zone_id), None)
                    if zone:
                        issues = self.analyze_hosted_zone_health(zone)
                        analysis = self.analyze_with_bedrock(issues)
                        return json.dumps({
                            "zone_id": zone_id,
                            "zone_name": zone.get('Name'),
                            "issues": issues,
                            "analysis": analysis
                        })
            
            elif query_type == "health_check_status":
                check_id = data.get("check_id")
                if check_id:
                    checks = self.get_health_checks()
                    check = next((c for c in checks if c.get('Id') == check_id), None)
                    if check:
                        issues = self.analyze_health_check(check)
                        analysis = self.analyze_with_bedrock(issues)
                        return json.dumps({
                            "check_id": check_id,
                            "issues": issues,
                            "analysis": analysis
                        })
            
            return None
        
        except Exception as e:
            print(f"Error handling query: {e}")
            return None
    
    def monitor_cycle(self) -> None:
        """Run a monitoring cycle to check all Route 53 resources."""
        try:
            all_issues = []
            
            # Check hosted zones
            zones = self.get_hosted_zones()
            for zone in zones:
                issues = self.analyze_hosted_zone_health(zone)
                all_issues.extend(issues)
            
            # Check health checks
            checks = self.get_health_checks()
            for check in checks:
                issues = self.analyze_health_check(check)
                all_issues.extend(issues)
            
            # Analyze issues with Bedrock
            analysis = self.analyze_with_bedrock(all_issues)
            
            # Report issues
            self.report_issues(all_issues, analysis)
        
        except Exception as e:
            print(f"Error in monitoring cycle: {e}")
            self.send_notification(
                content=f"Error in Route 53 monitoring cycle: {e}",
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


def create_route53_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> Route53MonitoringAgent:
    """Create a Route 53 monitoring agent."""
    broker = A2AMessageBroker()
    return Route53MonitoringAgent(agent_id, broker, supervisor_id, region_name) 
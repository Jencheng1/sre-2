"""
Trusted Advisor Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring AWS Trusted Advisor.
It detects best practice recommendations, cost optimization opportunities, and service limits.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class TrustedAdvisorMonitoringAgent(A2AAgent):
    """Agent for monitoring AWS Trusted Advisor and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the Trusted Advisor monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.support = boto3.client('support', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define categories to monitor
        self.categories = [
            "cost_optimizing", 
            "performance", 
            "security", 
            "fault_tolerance", 
            "service_limits"
        ]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "trusted_advisor_monitoring",
            "cost_optimization_detection",
            "security_recommendation_analysis",
            "service_limit_monitoring"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "Trusted Advisor"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_trusted_advisor_checks(self) -> Dict[str, Any]:
        """Get all Trusted Advisor checks."""
        try:
            response = self.support.describe_trusted_advisor_checks(
                language='en'
            )
            return response.get('checks', [])
        except Exception as e:
            print(f"Error retrieving Trusted Advisor checks: {e}")
            self.send_notification(
                content=f"Error retrieving Trusted Advisor checks: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_check_results(self, check_id: str) -> Dict[str, Any]:
        """Get results for a specific Trusted Advisor check."""
        try:
            response = self.support.describe_trusted_advisor_check_result(
                checkId=check_id,
                language='en'
            )
            return response.get('result', {})
        except Exception as e:
            print(f"Error retrieving results for check {check_id}: {e}")
            return {}
    
    def get_check_summaries(self, check_ids: List[str]) -> List[Dict[str, Any]]:
        """Get summaries for multiple Trusted Advisor checks."""
        try:
            response = self.support.describe_trusted_advisor_check_summaries(
                checkIds=check_ids
            )
            return response.get('summaries', [])
        except Exception as e:
            print(f"Error retrieving check summaries: {e}")
            return []
    
    def analyze_check_results(self, checks: List[Dict[str, Any]], 
                             summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze Trusted Advisor check results for issues."""
        issues = []
        
        # Create a map of check IDs to check details
        check_map = {check['id']: check for check in checks}
        
        for summary in summaries:
            check_id = summary.get('checkId')
            status = summary.get('status')
            
            # Only process checks with warning or error status
            if status not in ['warning', 'error']:
                continue
            
            # Get the check details
            check = check_map.get(check_id, {})
            category = check.get('category')
            name = check.get('name')
            description = check.get('description')
            
            # Get detailed results for this check
            result = self.get_check_results(check_id)
            resources_flagged = result.get('flaggedResources', [])
            
            # Create an issue for each flagged resource
            for resource in resources_flagged:
                resource_id = resource.get('resourceId', 'unknown')
                region = resource.get('region', 'global')
                
                # Skip if we've recently alerted on this issue
                issue_key = f"{check_id}:{resource_id}"
                if issue_key in self.recent_alerts and \
                   (datetime.utcnow() - self.recent_alerts[issue_key]).total_seconds() < 3600:
                    continue
                
                # Create the issue
                issue = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'check_id': check_id,
                    'check_name': name,
                    'category': category,
                    'status': status,
                    'resource_id': resource_id,
                    'region': region,
                    'description': description,
                    'metadata': resource.get('metadata', []),
                    'severity': 'high' if status == 'error' else 'medium',
                    'issue_type': f"trusted_advisor_{category}"
                }
                
                issues.append(issue)
                self.recent_alerts[issue_key] = datetime.utcnow()
        
        return issues
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze Trusted Advisor issues."""
        if not issues:
            return {"analysis": "No issues to analyze"}
        
        # Prepare issues for analysis (limit to 20 for prompt size)
        issues_text = "\n".join([
            f"Issue: {issue.get('check_name')} | Category: {issue.get('category')} | " +
            f"Resource: {issue.get('resource_id')} | Status: {issue.get('status')} | " +
            f"Region: {issue.get('region')}"
            for issue in issues[:20]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following AWS Trusted Advisor issues and provide recommendations:
        
        {issues_text}
        
        Please identify:
        1. Priority issues that should be addressed immediately
        2. Common patterns or root causes across multiple issues
        3. Potential impact on system reliability, performance, and security
        4. Specific recommendations for remediation
        
        Format your response as JSON with the following structure:
        {{
            "priority_issues": [list of issues with reasons],
            "common_patterns": [list of patterns],
            "potential_impacts": [list of impacts],
            "remediation_recommendations": [list of recommendations]
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
            "service": "Trusted Advisor",
            "issues": issues,
            "analysis": analysis
        }
        
        # Send the report to the supervisor
        self.send_notification(
            content=json.dumps(report),
            notification_type="monitoring_alert",
            severity="info" if not issues else "warning",
            recipient_id=self.supervisor_id
        )
        
        # For high severity issues, send a separate urgent notification
        high_severity_issues = [issue for issue in issues if issue['severity'] == 'high']
        if high_severity_issues:
            self.send_notification(
                content=json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": self.agent_id,
                    "service": "Trusted Advisor",
                    "high_severity_issues": high_severity_issues
                }),
                notification_type="urgent_alert",
                severity="high",
                recipient_id=self.supervisor_id
            )
    
    def handle_query(self, message: MCPMessage) -> Optional[str]:
        """Handle queries from other agents."""
        query_type = message.metadata.get("query_type")
        
        if query_type == "get_trusted_advisor_issues":
            # Return recent Trusted Advisor issues
            checks = self.get_trusted_advisor_checks()
            check_ids = [check['id'] for check in checks]
            summaries = self.get_check_summaries(check_ids)
            issues = self.analyze_check_results(checks, summaries)
            
            return self.send_response(
                recipient_id=message.sender_id,
                content=json.dumps({"issues": issues}),
                in_response_to=message.message_id,
                conversation_id=message.conversation_id
            )
        
        elif query_type == "analyze_category":
            # Analyze issues in a specific category
            try:
                params = json.loads(message.content)
                category = params.get("category")
                
                checks = self.get_trusted_advisor_checks()
                
                # Filter checks by category if specified
                if category:
                    checks = [check for check in checks if check.get('category') == category]
                
                check_ids = [check['id'] for check in checks]
                summaries = self.get_check_summaries(check_ids)
                issues = self.analyze_check_results(checks, summaries)
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
        # Get all Trusted Advisor checks
        checks = self.get_trusted_advisor_checks()
        check_ids = [check['id'] for check in checks]
        
        # Get summaries for all checks
        summaries = self.get_check_summaries(check_ids)
        
        # Analyze check results for issues
        issues = self.analyze_check_results(checks, summaries)
        
        # If issues found, perform deeper analysis with Bedrock
        analysis = {}
        if issues:
            analysis = self.analyze_with_bedrock(issues)
        
        # Report any issues found
        self.report_issues(issues, analysis)
    
    def run_monitoring(self, interval: int = 3600, max_runtime: Optional[int] = None) -> None:
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
            print(f"Trusted Advisor monitoring agent {self.agent_id} stopped by user.")
        except Exception as e:
            print(f"Error in Trusted Advisor monitoring: {e}")
            self.send_notification(
                content=f"Trusted Advisor monitoring error: {e}",
                notification_type="agent_error",
                severity="error",
                recipient_id=self.supervisor_id
            )


# Action group definitions for Trusted Advisor agent
TRUSTED_ADVISOR_ACTION_GROUPS = {
    "GetTrustedAdvisorIssues": {
        "description": "Get issues detected by AWS Trusted Advisor",
        "parameters": {
            "category": {
                "type": "string",
                "description": "Category of checks to focus on (optional)",
                "enum": ["cost_optimizing", "performance", "security", "fault_tolerance", "service_limits"]
            }
        },
        "function": "get_trusted_advisor_issues"
    },
    "AnalyzeServiceLimits": {
        "description": "Analyze service limits that are approaching thresholds",
        "parameters": {},
        "function": "analyze_service_limits"
    },
    "GetSecurityRecommendations": {
        "description": "Get security recommendations from Trusted Advisor",
        "parameters": {},
        "function": "get_security_recommendations"
    }
}


def create_trusted_advisor_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> TrustedAdvisorMonitoringAgent:
    """Factory function to create and configure a Trusted Advisor monitoring agent."""
    broker = A2AMessageBroker(queue_name="aws_monitoring_queue")
    agent = TrustedAdvisorMonitoringAgent(
        agent_id=agent_id,
        broker=broker,
        supervisor_id=supervisor_id,
        region_name=region_name
    )
    return agent

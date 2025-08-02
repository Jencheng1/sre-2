"""
CloudTrail Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring CloudTrail logs.
It detects API errors, throttling events, and unusual patterns in AWS API usage.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class CloudTrailMonitoringAgent(A2AAgent):
    """Agent for monitoring CloudTrail logs and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the CloudTrail monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.cloudtrail = boto3.client('cloudtrail', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define patterns to monitor
        self.error_patterns = [
            "AccessDenied", 
            "ThrottlingException",
            "ValidationException",
            "ResourceNotFoundException",
            "ServiceQuotaExceeded"
        ]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "cloudtrail_monitoring",
            "api_error_detection",
            "throttling_detection",
            "unusual_activity_detection"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "CloudTrail"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_recent_events(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent CloudTrail events."""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            response = self.cloudtrail.lookup_events(
                LookupAttributes=[],
                StartTime=start_time,
                MaxResults=50
            )
            
            return response.get('Events', [])
        except Exception as e:
            print(f"Error retrieving CloudTrail events: {e}")
            self.send_notification(
                content=f"Error retrieving CloudTrail events: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def analyze_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze CloudTrail events for issues."""
        issues = []
        
        for event in events:
            try:
                event_name = event.get('EventName', '')
                event_time = event.get('EventTime', datetime.utcnow())
                event_source = event.get('EventSource', '')
                username = event.get('Username', '')
                
                # Parse the CloudTrail event
                event_data = json.loads(event.get('CloudTrailEvent', '{}'))
                error_code = event_data.get('errorCode', '')
                error_message = event_data.get('errorMessage', '')
                
                # Check for error patterns
                if error_code:
                    for pattern in self.error_patterns:
                        if pattern in error_code:
                            # Create an issue record
                            issue = {
                                'id': str(uuid.uuid4()),
                                'timestamp': event_time.isoformat(),
                                'event_name': event_name,
                                'event_source': event_source,
                                'username': username,
                                'error_code': error_code,
                                'error_message': error_message,
                                'severity': self._determine_severity(error_code),
                                'issue_type': self._determine_issue_type(error_code)
                            }
                            
                            # Check if this is a new issue (not recently alerted)
                            issue_key = f"{event_source}:{event_name}:{error_code}"
                            if issue_key not in self.recent_alerts or \
                               (datetime.utcnow() - self.recent_alerts[issue_key]).total_seconds() > 3600:
                                issues.append(issue)
                                self.recent_alerts[issue_key] = datetime.utcnow()
            
            except Exception as e:
                print(f"Error analyzing event: {e}")
        
        return issues
    
    def _determine_severity(self, error_code: str) -> str:
        """Determine the severity of an error."""
        if "Throttling" in error_code:
            return "warning"
        elif "AccessDenied" in error_code:
            return "high"
        elif "ServiceQuotaExceeded" in error_code:
            return "high"
        elif "NotFound" in error_code:
            return "medium"
        else:
            return "low"
    
    def _determine_issue_type(self, error_code: str) -> str:
        """Determine the type of issue."""
        if "Throttling" in error_code:
            return "api_throttling"
        elif "AccessDenied" in error_code:
            return "access_denied"
        elif "ServiceQuotaExceeded" in error_code:
            return "service_quota_exceeded"
        elif "NotFound" in error_code:
            return "resource_not_found"
        elif "Validation" in error_code:
            return "validation_error"
        else:
            return "general_error"
    
    def analyze_with_bedrock(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze patterns in CloudTrail events."""
        if not events:
            return {"analysis": "No events to analyze"}
        
        # Prepare events for analysis
        events_text = "\n".join([
            f"Event: {e.get('EventName')} | Source: {e.get('EventSource')} | User: {e.get('Username')} | Time: {e.get('EventTime')}"
            for e in events[:20]  # Limit to 20 events for prompt size
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following AWS CloudTrail events for unusual patterns, potential security issues, or operational problems:
        
        {events_text}
        
        Please identify:
        1. Any unusual API call patterns
        2. Potential security concerns
        3. Signs of throttling or quota issues
        4. Recommendations for investigation
        
        Format your response as JSON with the following structure:
        {{
            "patterns_detected": [list of patterns],
            "security_concerns": [list of concerns],
            "throttling_issues": [list of issues],
            "recommendations": [list of recommendations]
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
        if not issues and not analysis.get('patterns_detected'):
            return
        
        # Prepare the report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "service": "CloudTrail",
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
                    "service": "CloudTrail",
                    "high_severity_issues": high_severity_issues
                }),
                notification_type="urgent_alert",
                severity="high",
                recipient_id=self.supervisor_id
            )
    
    def handle_query(self, message: MCPMessage) -> Optional[str]:
        """Handle queries from other agents."""
        query_type = message.metadata.get("query_type")
        
        if query_type == "get_recent_issues":
            # Return recent CloudTrail issues
            events = self.get_recent_events(hours=int(message.content) if message.content.isdigit() else 1)
            issues = self.analyze_events(events)
            
            return self.send_response(
                recipient_id=message.sender_id,
                content=json.dumps({"issues": issues}),
                in_response_to=message.message_id,
                conversation_id=message.conversation_id
            )
        
        elif query_type == "analyze_timeframe":
            # Analyze a specific timeframe
            try:
                params = json.loads(message.content)
                hours = params.get("hours", 1)
                
                events = self.get_recent_events(hours=hours)
                issues = self.analyze_events(events)
                analysis = self.analyze_with_bedrock(events)
                
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
        # Get recent CloudTrail events
        events = self.get_recent_events()
        
        # Analyze events for issues
        issues = self.analyze_events(events)
        
        # If issues found, perform deeper analysis with Bedrock
        analysis = {}
        if issues or len(events) > 10:  # Only analyze if there are issues or sufficient events
            analysis = self.analyze_with_bedrock(events)
        
        # Report any issues found
        self.report_issues(issues, analysis)
    
    def run_monitoring(self, interval: int = 300, max_runtime: Optional[int] = None) -> None:
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
            print(f"CloudTrail monitoring agent {self.agent_id} stopped by user.")
        except Exception as e:
            print(f"Error in CloudTrail monitoring: {e}")
            self.send_notification(
                content=f"CloudTrail monitoring error: {e}",
                notification_type="agent_error",
                severity="error",
                recipient_id=self.supervisor_id
            )


# Action group definitions for CloudTrail agent
CLOUDTRAIL_ACTION_GROUPS = {
    "GetRecentIssues": {
        "description": "Get recent issues detected in CloudTrail logs",
        "parameters": {
            "timeframe_hours": {
                "type": "integer",
                "description": "Number of hours to look back",
                "default": 1
            }
        },
        "function": "get_recent_issues"
    },
    "AnalyzeAPIUsage": {
        "description": "Analyze API usage patterns for anomalies",
        "parameters": {
            "timeframe_hours": {
                "type": "integer",
                "description": "Number of hours to analyze",
                "default": 24
            },
            "service": {
                "type": "string",
                "description": "AWS service to focus on (optional)"
            }
        },
        "function": "analyze_api_usage"
    },
    "InvestigateThrottling": {
        "description": "Investigate API throttling issues",
        "parameters": {
            "service": {
                "type": "string",
                "description": "AWS service experiencing throttling"
            }
        },
        "function": "investigate_throttling"
    }
}


def create_cloudtrail_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> CloudTrailMonitoringAgent:
    """Factory function to create and configure a CloudTrail monitoring agent."""
    broker = A2AMessageBroker(queue_name="aws_monitoring_queue")
    agent = CloudTrailMonitoringAgent(
        agent_id=agent_id,
        broker=broker,
        supervisor_id=supervisor_id,
        region_name=region_name
    )
    return agent

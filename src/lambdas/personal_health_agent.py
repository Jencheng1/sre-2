"""
Personal Health Dashboard Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring AWS Personal Health Dashboard.
It detects service health events, scheduled maintenance, and operational issues affecting AWS resources.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class PersonalHealthMonitoringAgent(A2AAgent):
    """Agent for monitoring AWS Personal Health Dashboard and detecting issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the Personal Health monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.health = boto3.client('health', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define event types to monitor
        self.event_types = [
            "AWS_EC2_INSTANCE_STOP_SCHEDULED",
            "AWS_EC2_INSTANCE_RETIREMENT_SCHEDULED",
            "AWS_EC2_PERSISTENT_INSTANCE_RETIREMENT_SCHEDULED",
            "AWS_RDS_MAINTENANCE_SCHEDULED",
            "AWS_RDS_INSTANCE_RETIREMENT_SCHEDULED",
            "AWS_EBS_VOLUME_DEGRADED",
            "AWS_EBS_VOLUME_LOST",
            "AWS_EC2_OPERATIONAL_ISSUE",
            "AWS_RDS_OPERATIONAL_ISSUE"
        ]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "personal_health_monitoring",
            "service_health_detection",
            "maintenance_notification",
            "operational_issue_detection"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "Personal Health Dashboard"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_health_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent health events from AWS Personal Health Dashboard."""
        try:
            start_time = datetime.utcnow() - timedelta(days=days)
            
            response = self.health.describe_events(
                filter={
                    'startTimes': [
                        {
                            'from': start_time.isoformat()
                        }
                    ]
                }
            )
            
            return response.get('events', [])
        except Exception as e:
            print(f"Error retrieving health events: {e}")
            self.send_notification(
                content=f"Error retrieving health events: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_event_details(self, event_arn: str) -> Dict[str, Any]:
        """Get detailed information about a specific health event."""
        try:
            response = self.health.describe_event_details(
                eventArns=[event_arn]
            )
            
            if response.get('successfulSet'):
                return response['successfulSet'][0]
            return {}
        except Exception as e:
            print(f"Error retrieving event details for {event_arn}: {e}")
            return {}
    
    def get_affected_entities(self, event_arn: str) -> List[Dict[str, Any]]:
        """Get entities affected by a specific health event."""
        try:
            response = self.health.describe_affected_entities(
                filter={
                    'eventArns': [event_arn]
                }
            )
            
            return response.get('entities', [])
        except Exception as e:
            print(f"Error retrieving affected entities for {event_arn}: {e}")
            return []
    
    def analyze_health_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze health events for issues."""
        issues = []
        
        for event in events:
            event_arn = event.get('arn')
            
            # Skip if we've recently alerted on this event
            if event_arn in self.recent_alerts and \
               (datetime.utcnow() - self.recent_alerts[event_arn]).total_seconds() < 3600:
                continue
            
            # Get event details
            event_details = self.get_event_details(event_arn)
            detailed_event = event_details.get('eventDescription', {})
            
            # Get affected entities
            affected_entities = self.get_affected_entities(event_arn)
            
            # Create an issue
            issue = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'event_arn': event_arn,
                'service': event.get('service'),
                'event_type_code': event.get('eventTypeCode'),
                'event_type_category': event.get('eventTypeCategory'),
                'region': event.get('region'),
                'start_time': event.get('startTime'),
                'end_time': event.get('endTime'),
                'status_code': event.get('statusCode'),
                'description': detailed_event.get('latestDescription', ''),
                'affected_entities': [
                    {
                        'entity_arn': entity.get('entityArn'),
                        'entity_value': entity.get('entityValue'),
                        'status_code': entity.get('statusCode')
                    } for entity in affected_entities
                ],
                'severity': self._determine_severity(event),
                'issue_type': self._determine_issue_type(event)
            }
            
            issues.append(issue)
            self.recent_alerts[event_arn] = datetime.utcnow()
        
        return issues
    
    def _determine_severity(self, event: Dict[str, Any]) -> str:
        """Determine the severity of a health event."""
        category = event.get('eventTypeCategory')
        status = event.get('statusCode')
        
        if category == 'issue':
            return 'high'
        elif category == 'scheduledChange':
            if status == 'open':
                return 'medium'
            else:
                return 'low'
        elif category == 'accountNotification':
            return 'medium'
        else:
            return 'low'
    
    def _determine_issue_type(self, event: Dict[str, Any]) -> str:
        """Determine the type of issue."""
        event_type = event.get('eventTypeCode', '')
        
        if 'SCHEDULED' in event_type:
            return 'scheduled_maintenance'
        elif 'RETIREMENT' in event_type:
            return 'resource_retirement'
        elif 'OPERATIONAL_ISSUE' in event_type:
            return 'operational_issue'
        elif 'DEGRADED' in event_type or 'LOST' in event_type:
            return 'resource_degradation'
        else:
            return 'general_notification'
    
    def analyze_with_bedrock(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze health events."""
        if not issues:
            return {"analysis": "No health events to analyze"}
        
        # Prepare issues for analysis (limit to 10 for prompt size)
        issues_text = "\n".join([
            f"Service: {issue.get('service')} | Type: {issue.get('event_type_code')} | " +
            f"Category: {issue.get('event_type_category')} | Region: {issue.get('region')} | " +
            f"Status: {issue.get('status_code')} | Description: {issue.get('description')[:200]}..."
            for issue in issues[:10]
        ])
        
        # Prepare prompt for Claude 3 Haiku
        prompt = f"""
        Analyze the following AWS Personal Health Dashboard events and provide insights:
        
        {issues_text}
        
        Please identify:
        1. Critical events requiring immediate attention
        2. Potential impact on system availability and performance
        3. Recommended actions to mitigate impact
        4. Timeline for addressing each event
        
        Format your response as JSON with the following structure:
        {{
            "critical_events": [list of events with reasons],
            "potential_impacts": [list of impacts],
            "recommended_actions": [list of actions],
            "timeline": [list of timeline items]
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
            "service": "Personal Health Dashboard",
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
                    "service": "Personal Health Dashboard",
                    "high_severity_issues": high_severity_issues
                }),
                notification_type="urgent_alert",
                severity="high",
                recipient_id=self.supervisor_id
            )
    
    def handle_query(self, message: MCPMessage) -> Optional[str]:
        """Handle queries from other agents."""
        query_type = message.metadata.get("query_type")
        
        if query_type == "get_health_events":
            # Return recent health events
            try:
                params = json.loads(message.content) if message.content else {}
                days = params.get("days", 7)
                
                events = self.get_health_events(days=days)
                issues = self.analyze_health_events(events)
                
                return self.send_response(
                    recipient_id=message.sender_id,
                    content=json.dumps({"issues": issues}),
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
        
        elif query_type == "get_affected_resources":
            # Get resources affected by a specific event
            try:
                params = json.loads(message.content)
                event_arn = params.get("event_arn")
                
                if not event_arn:
                    return self.send_response(
                        recipient_id=message.sender_id,
                        content=json.dumps({"error": "No event ARN provided"}),
                        in_response_to=message.message_id,
                        status="error",
                        conversation_id=message.conversation_id
                    )
                
                affected_entities = self.get_affected_entities(event_arn)
                
                return self.send_response(
                    recipient_id=message.sender_id,
                    content=json.dumps({"affected_entities": affected_entities}),
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
        # Get recent health events
        events = self.get_health_events()
        
        # Analyze events for issues
        issues = self.analyze_health_events(events)
        
        # If issues found, perform deeper analysis with Bedrock
        analysis = {}
        if issues:
            analysis = self.analyze_with_bedrock(issues)
        
        # Report any issues found
        self.report_issues(issues, analysis)
    
    def run_monitoring(self, interval: int = 900, max_runtime: Optional[int] = None) -> None:
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
            print(f"Personal Health monitoring agent {self.agent_id} stopped by user.")
        except Exception as e:
            print(f"Error in Personal Health monitoring: {e}")
            self.send_notification(
                content=f"Personal Health monitoring error: {e}",
                notification_type="agent_error",
                severity="error",
                recipient_id=self.supervisor_id
            )


# Action group definitions for Personal Health agent
PERSONAL_HEALTH_ACTION_GROUPS = {
    "GetHealthEvents": {
        "description": "Get recent health events from AWS Personal Health Dashboard",
        "parameters": {
            "days": {
                "type": "integer",
                "description": "Number of days to look back",
                "default": 7
            }
        },
        "function": "get_health_events"
    },
    "GetAffectedResources": {
        "description": "Get resources affected by a specific health event",
        "parameters": {
            "event_arn": {
                "type": "string",
                "description": "ARN of the health event"
            }
        },
        "function": "get_affected_resources"
    },
    "AnalyzeMaintenanceImpact": {
        "description": "Analyze the impact of scheduled maintenance events",
        "parameters": {},
        "function": "analyze_maintenance_impact"
    }
}


def create_personal_health_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> PersonalHealthMonitoringAgent:
    """Factory function to create and configure a Personal Health monitoring agent."""
    broker = A2AMessageBroker(queue_name="aws_monitoring_queue")
    agent = PersonalHealthMonitoringAgent(
        agent_id=agent_id,
        broker=broker,
        supervisor_id=supervisor_id,
        region_name=region_name
    )
    return agent

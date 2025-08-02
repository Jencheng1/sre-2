"""
Supervisor Agent and Correlation Logic for AWS Bedrock Agents

This module implements a supervisor agent that coordinates specialized monitoring agents
and performs correlation analysis to identify root causes of issues across AWS services.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set

from .mcp import MCPMessageFactory
from .a2a import A2ASupervisorAgent, A2AMessageBroker


class AWSMonitoringSupervisorAgent(A2ASupervisorAgent):
    """Supervisor agent that coordinates AWS monitoring agents and correlates events."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, region_name: str = 'us-east-1'):
        """Initialize the AWS monitoring supervisor agent."""
        super().__init__(agent_id, broker)
        self.region_name = region_name
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Store recent issues from each agent
        self.recent_issues: Dict[str, List[Dict[str, Any]]] = {
            "cloudtrail": [],
            "vpc_flow_logs": [],
            "trusted_advisor": [],
            "personal_health": []
        }
        
        # Store correlation results
        self.correlations: List[Dict[str, Any]] = []
        
        # Track when we last ran correlation analysis
        self.last_correlation_time = datetime.utcnow() - timedelta(hours=1)
    
    def handle_notification(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle notification messages from monitoring agents."""
        notification_type = message.metadata.get("notification_type")
        
        if notification_type == "monitoring_alert":
            # Process monitoring alerts from agents
            try:
                data = json.loads(message.content)
                service = data.get("service")
                issues = data.get("issues", [])
                analysis = data.get("analysis", {})
                
                # Map service to category
                category = self._map_service_to_category(service)
                
                if category and issues:
                    # Store the issues
                    self.recent_issues[category] = issues
                    
                    # Check if we should run correlation analysis
                    current_time = datetime.utcnow()
                    if (current_time - self.last_correlation_time).total_seconds() > 300:  # 5 minutes
                        self.correlate_issues()
                        self.last_correlation_time = current_time
            
            except Exception as e:
                print(f"Error processing monitoring alert: {e}")
        
        elif notification_type == "urgent_alert":
            # Process urgent alerts immediately
            try:
                data = json.loads(message.content)
                service = data.get("service")
                high_severity_issues = data.get("high_severity_issues", [])
                
                if high_severity_issues:
                    # Run correlation analysis immediately for high severity issues
                    self.correlate_urgent_issues(service, high_severity_issues)
            
            except Exception as e:
                print(f"Error processing urgent alert: {e}")
        
        return super().handle_notification(message)
    
    def _map_service_to_category(self, service: str) -> Optional[str]:
        """Map service name to category."""
        service_map = {
            "CloudTrail": "cloudtrail",
            "VPC Flow Logs": "vpc_flow_logs",
            "Trusted Advisor": "trusted_advisor",
            "Personal Health Dashboard": "personal_health"
        }
        return service_map.get(service)
    
    def correlate_issues(self) -> None:
        """Correlate issues across different monitoring agents."""
        # Check if we have enough issues to correlate
        total_issues = sum(len(issues) for issues in self.recent_issues.values())
        if total_issues < 2:
            return
        
        # Prepare issues for correlation
        all_issues = []
        for category, issues in self.recent_issues.items():
            for issue in issues:
                issue["source"] = category
                all_issues.append(issue)
        
        # Perform time-based correlation
        time_correlations = self._correlate_by_time(all_issues)
        
        # Perform resource-based correlation
        resource_correlations = self._correlate_by_resource(all_issues)
        
        # Perform service-based correlation
        service_correlations = self._correlate_by_service(all_issues)
        
        # Combine correlations
        combined_correlations = time_correlations + resource_correlations + service_correlations
        
        # Remove duplicates
        unique_correlations = self._deduplicate_correlations(combined_correlations)
        
        # Store correlations
        self.correlations = unique_correlations
        
        # Analyze correlations with Bedrock
        if unique_correlations:
            root_cause_analysis = self._analyze_with_bedrock(unique_correlations, all_issues)
            
            # Create a comprehensive report
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "correlations": unique_correlations,
                "root_cause_analysis": root_cause_analysis
            }
            
            # Broadcast the report to all agents
            self.send_notification(
                content=json.dumps(report),
                notification_type="correlation_report",
                severity="info"
            )
    
    def correlate_urgent_issues(self, service: str, high_severity_issues: List[Dict[str, Any]]) -> None:
        """Correlate urgent issues with recent issues from other agents."""
        # Map service to category
        category = self._map_service_to_category(service)
        if not category:
            return
        
        # Prepare all issues
        all_issues = []
        
        # Add high severity issues
        for issue in high_severity_issues:
            issue["source"] = category
            all_issues.append(issue)
        
        # Add recent issues from other agents
        for other_category, issues in self.recent_issues.items():
            if other_category != category:
                for issue in issues:
                    issue["source"] = other_category
                    all_issues.append(issue)
        
        # Perform correlation
        time_correlations = self._correlate_by_time(all_issues, time_window_minutes=30)
        resource_correlations = self._correlate_by_resource(all_issues)
        service_correlations = self._correlate_by_service(all_issues)
        
        # Combine correlations
        combined_correlations = time_correlations + resource_correlations + service_correlations
        
        # Remove duplicates
        unique_correlations = self._deduplicate_correlations(combined_correlations)
        
        if unique_correlations:
            # Analyze correlations with Bedrock
            root_cause_analysis = self._analyze_with_bedrock(unique_correlations, all_issues)
            
            # Create an urgent report
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "urgent": True,
                "service": service,
                "correlations": unique_correlations,
                "root_cause_analysis": root_cause_analysis
            }
            
            # Broadcast the urgent report
            self.send_notification(
                content=json.dumps(report),
                notification_type="urgent_correlation_report",
                severity="high"
            )
    
    def _correlate_by_time(self, issues: List[Dict[str, Any]], time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """Correlate issues based on time proximity."""
        correlations = []
        
        # Sort issues by timestamp
        sorted_issues = sorted(issues, key=lambda x: x.get("timestamp", ""))
        
        # Group issues within time windows
        for i, issue in enumerate(sorted_issues):
            issue_time = datetime.fromisoformat(issue.get("timestamp", datetime.utcnow().isoformat()))
            related_issues = []
            
            # Look for issues within the time window
            for j, other_issue in enumerate(sorted_issues):
                if i == j:
                    continue
                
                other_time = datetime.fromisoformat(other_issue.get("timestamp", datetime.utcnow().isoformat()))
                time_diff = abs((issue_time - other_time).total_seconds())
                
                if time_diff <= (time_window_minutes * 60):
                    related_issues.append(other_issue)
            
            # If we found related issues, create a correlation
            if related_issues:
                correlation = {
                    "id": str(uuid.uuid4()),
                    "correlation_type": "time_based",
                    "primary_issue": issue,
                    "related_issues": related_issues,
                    "correlation_strength": len(related_issues),
                    "timestamp": datetime.utcnow().isoformat()
                }
                correlations.append(correlation)
        
        return correlations
    
    def _correlate_by_resource(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Correlate issues based on affected resources."""
        correlations = []
        resource_map: Dict[str, List[Dict[str, Any]]] = {}
        
        # Group issues by resource
        for issue in issues:
            # Extract resource identifiers based on issue source
            resource_ids = self._extract_resource_ids(issue)
            
            for resource_id in resource_ids:
                if resource_id not in resource_map:
                    resource_map[resource_id] = []
                resource_map[resource_id].append(issue)
        
        # Create correlations for resources with multiple issues
        for resource_id, resource_issues in resource_map.items():
            if len(resource_issues) > 1:
                # Find issues from different sources
                sources = set(issue.get("source") for issue in resource_issues)
                if len(sources) > 1:
                    primary_issue = resource_issues[0]
                    related_issues = resource_issues[1:]
                    
                    correlation = {
                        "id": str(uuid.uuid4()),
                        "correlation_type": "resource_based",
                        "resource_id": resource_id,
                        "primary_issue": primary_issue,
                        "related_issues": related_issues,
                        "correlation_strength": len(related_issues),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    correlations.append(correlation)
        
        return correlations
    
    def _extract_resource_ids(self, issue: Dict[str, Any]) -> Set[str]:
        """Extract resource identifiers from an issue based on its source."""
        resource_ids = set()
        source = issue.get("source")
        
        if source == "cloudtrail":
            # Extract resource IDs from CloudTrail events
            event_source = issue.get("event_source", "")
            if event_source:
                resource_ids.add(event_source)
        
        elif source == "vpc_flow_logs":
            # Extract resource IDs from VPC Flow Logs
            interface_id = issue.get("interface_id")
            if interface_id:
                resource_ids.add(interface_id)
            
            src_addr = issue.get("src_addr")
            if src_addr:
                resource_ids.add(src_addr)
            
            dst_addr = issue.get("dst_addr")
            if dst_addr:
                resource_ids.add(dst_addr)
        
        elif source == "trusted_advisor":
            # Extract resource IDs from Trusted Advisor
            resource_id = issue.get("resource_id")
            if resource_id:
                resource_ids.add(resource_id)
        
        elif source == "personal_health":
            # Extract resource IDs from Personal Health Dashboard
            for entity in issue.get("affected_entities", []):
                entity_value = entity.get("entity_value")
                if entity_value:
                    resource_ids.add(entity_value)
        
        return resource_ids
    
    def _correlate_by_service(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Correlate issues based on affected services."""
        correlations = []
        service_map: Dict[str, List[Dict[str, Any]]] = {}
        
        # Group issues by service
        for issue in issues:
            service = self._extract_service(issue)
            if service:
                if service not in service_map:
                    service_map[service] = []
                service_map[service].append(issue)
        
        # Create correlations for services with multiple issues
        for service, service_issues in service_map.items():
            if len(service_issues) > 1:
                # Find issues from different sources
                sources = set(issue.get("source") for issue in service_issues)
                if len(sources) > 1:
                    primary_issue = service_issues[0]
                    related_issues = service_issues[1:]
                    
                    correlation = {
                        "id": str(uuid.uuid4()),
                        "correlation_type": "service_based",
                        "service": service,
                        "primary_issue": primary_issue,
                        "related_issues": related_issues,
                        "correlation_strength": len(related_issues),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    correlations.append(correlation)
        
        return correlations
    
    def _extract_service(self, issue: Dict[str, Any]) -> Optional[str]:
        """Extract service information from an issue."""
        source = issue.get("source")
        
        if source == "cloudtrail":
            return issue.get("event_source", "").split(".")[0] if "." in issue.get("event_source", "") else None
        
        elif source == "trusted_advisor":
            return issue.get("check_name", "").split(" ")[0] if " " in issue.get("check_name", "") else None
        
        elif source == "personal_health":
            return issue.get("service")
        
        return None
    
    def _deduplicate_correlations(self, correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate correlations."""
        unique_correlations = []
        seen_issue_pairs = set()
        
        for correlation in correlations:
            primary_id = correlation["primary_issue"].get("id")
            related_ids = tuple(sorted(issue.get("id") for issue in correlation["related_issues"]))
            
            # Create a unique key for this set of issues
            key = (primary_id, related_ids)
            
            if key not in seen_issue_pairs:
                unique_correlations.append(correlation)
                seen_issue_pairs.add(key)
        
        return unique_correlations
    
    def _analyze_with_bedrock(self, correlations: List[Dict[str, Any]], all_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze correlations and identify root causes."""
        if not correlations:
            return {"analysis": "No correlations to analyze"}
        
        # Prepare correlations for analysis (limit to 5 for prompt size)
        correlations_text = ""
        for i, correlation in enumerate(correlations[:5]):
            primary_issue = correlation["primary_issue"]
            related_issues = correlation["related_issues"]
            
            correlations_text += f"Correlation {i+1} ({correlation['correlation_type']}):\n"
            correlations_text += f"Primary Issue: {self._format_issue(primary_issue)}\n"
            correlations_text += "Related Issues:\n"
            
            for j, related in enumerate(related_issues[:3]):  # Limit to 3 related issues
                correlations_text += f"  {j+1}. {self._format_issue(related)}\n"
            
            correlations_text += "\n"
        
        # Prepare prompt for Amazon Nova Pro
        prompt = f"""
        Analyze the following correlations between AWS service issues and identify potential root causes:
        
        {correlations_text}
        
        Please provide:
        1. Likely root causes for each correlation
        2. Potential impact on the overall system
        3. Recommended remediation steps
        4. Priority order for addressing the issues
        
        Format your response as JSON with the following structure:
        {{
            "root_causes": [
                {{
                    "correlation_index": 1,
                    "root_cause": "description of root cause",
                    "confidence": "high/medium/low",
                    "explanation": "detailed explanation"
                }}
            ],
            "system_impact": "description of overall system impact",
            "remediation_steps": [
                {{
                    "step": "description of step",
                    "priority": "high/medium/low"
                }}
            ],
            "priority_order": [list of correlation indices in priority order]
        }}
        """
        
        try:
            # Call Amazon Nova Pro via Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId='amazon.nova-pro-v1',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "prompt": prompt,
                    "temperature": 0.2,
                    "maxTokens": 1500
                })
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read().decode('utf-8'))
            content = response_body.get('output', '')
            
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
    
    def _format_issue(self, issue: Dict[str, Any]) -> str:
        """Format an issue for inclusion in the prompt."""
        source = issue.get("source", "unknown")
        
        if source == "cloudtrail":
            return (f"CloudTrail: {issue.get('event_name', 'Unknown')} - "
                   f"{issue.get('error_code', 'No error')} - "
                   f"{issue.get('issue_type', 'Unknown type')}")
        
        elif source == "vpc_flow_logs":
            return (f"VPC Flow Logs: {issue.get('description', 'Unknown')} - "
                   f"Interface: {issue.get('interface_id', 'Unknown')} - "
                   f"{issue.get('issue_type', 'Unknown type')}")
        
        elif source == "trusted_advisor":
            return (f"Trusted Advisor: {issue.get('check_name', 'Unknown')} - "
                   f"Resource: {issue.get('resource_id', 'Unknown')} - "
                   f"{issue.get('category', 'Unknown category')}")
        
        elif source == "personal_health":
            return (f"Personal Health: {issue.get('event_type_code', 'Unknown')} - "
                   f"Service: {issue.get('service', 'Unknown')} - "
                   f"{issue.get('issue_type', 'Unknown type')}")
        
        return f"Unknown source: {json.dumps(issue)[:100]}..."
    
    def handle_query(self, message: MCPMessage) -> Optional[str]:
        """Handle queries from other agents or users."""
        query_type = message.metadata.get("query_type")
        
        if query_type == "get_correlations":
            # Return recent correlations
            return self.send_response(
                recipient_id=message.sender_id,
                content=json.dumps({"correlations": self.correlations}),
                in_response_to=message.message_id,
                conversation_id=message.conversation_id
            )
        
        elif query_type == "analyze_issue":
            # Analyze a specific issue for correlations
            try:
                issue_data = json.loads(message.content)
                issue = issue_data.get("issue")
                
                if not issue:
                    return self.send_response(
                        recipient_id=message.sender_id,
                        content=json.dumps({"error": "No issue provided"}),
                        in_response_to=message.message_id,
                        status="error",
                        conversation_id=message.conversation_id
                    )
                
                # Get all recent issues
                all_issues = []
                for issues in self.recent_issues.values():
                    all_issues.extend(issues)
                
                # Add the new issue
                all_issues.append(issue)
                
                # Perform correlation
                time_correlations = self._correlate_by_time([issue], time_window_minutes=60)
                resource_correlations = self._correlate_by_resource([issue])
                service_correlations = self._correlate_by_service([issue])
                
                # Combine correlations
                combined_correlations = time_correlations + resource_correlations + service_correlations
                
                # Remove duplicates
                unique_correlations = self._deduplicate_correlations(combined_correlations)
                
                # Analyze with Bedrock if correlations found
                analysis = {}
                if unique_correlations:
                    analysis = self._analyze_with_bedrock(unique_correlations, all_issues)
                
                return self.send_response(
                    recipient_id=message.sender_id,
                    content=json.dumps({
                        "correlations": unique_correlations,
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
    
    def run_supervisor(self, polling_interval: int = 5, correlation_interval: int = 300,
                      health_check_interval: int = 60, max_runtime: Optional[int] = None) -> None:
        """Run the supervisor agent with periodic correlation analysis."""
        start_time = time.time()
        last_correlation_time = start_time
        last_health_check = start_time
        
        try:
            while True:
                # Process messages
                self.process_messages(wait_time=polling_interval)
                
                # Periodic correlation analysis
                current_time = time.time()
                if current_time - last_correlation_time > correlation_interval:
                    self.correlate_issues()
                    last_correlation_time = current_time
                
                # Periodic health check
                if current_time - last_health_check > health_check_interval:
                    self.check_agent_health()
                    last_health_check = current_time
                
                # Check if max runtime exceeded
                if max_runtime and (current_time - start_time) > max_runtime:
                    break
        
        except KeyboardInterrupt:
            print(f"Supervisor agent {self.agent_id} stopped by user.")
        except Exception as e:
            print(f"Error in supervisor agent: {e}")


# Action group definitions for Supervisor agent
SUPERVISOR_ACTION_GROUPS = {
    "GetCorrelations": {
        "description": "Get recent correlations between issues",
        "parameters": {},
        "function": "get_correlations"
    },
    "AnalyzeIssue": {
        "description": "Analyze a specific issue for correlations with other issues",
        "parameters": {
            "issue": {
                "type": "object",
                "description": "Issue to analyze"
            }
        },
        "function": "analyze_issue"
    },
    "GetRootCauseAnalysis": {
        "description": "Get root cause analysis for recent correlations",
        "parameters": {},
        "function": "get_root_cause_analysis"
    }
}


def create_supervisor_agent(agent_id: str, region_name: str = 'us-east-1') -> AWSMonitoringSupervisorAgent:
    """Factory function to create and configure a supervisor agent."""
    broker = A2AMessageBroker(queue_name="aws_monitoring_queue")
    agent = AWSMonitoringSupervisorAgent(
        agent_id=agent_id,
        broker=broker,
        region_name=region_name
    )
    return agent

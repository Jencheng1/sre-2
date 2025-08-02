"""
VPC Flow Logs Monitoring Agent for AWS Bedrock

This module implements a specialized AWS Bedrock agent for monitoring VPC Flow Logs.
It detects network connectivity issues, security concerns, and unusual traffic patterns.
"""

import json
import boto3
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .mcp import MCPMessageFactory
from .a2a import A2AAgent, A2AMessageBroker


class VPCFlowLogsMonitoringAgent(A2AAgent):
    """Agent for monitoring VPC Flow Logs and detecting network issues."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker, 
                 supervisor_id: str, region_name: str = 'us-east-1'):
        """Initialize the VPC Flow Logs monitoring agent."""
        super().__init__(agent_id, broker)
        self.supervisor_id = supervisor_id
        self.region_name = region_name
        self.ec2 = boto3.client('ec2', region_name=region_name)
        self.logs = boto3.client('logs', region_name=region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Register capabilities with supervisor
        self.register_with_supervisor()
        
        # Define patterns to monitor
        self.rejected_patterns = ["REJECT", "DENIED"]
        self.monitored_ports = [22, 3389, 80, 443, 3306, 5432]
        
        # Track recent alerts to avoid duplicates
        self.recent_alerts = {}
    
    def register_with_supervisor(self) -> None:
        """Register this agent with the supervisor."""
        capabilities = [
            "vpc_flow_logs_monitoring",
            "network_connectivity_analysis",
            "security_group_analysis",
            "traffic_pattern_detection"
        ]
        
        registration_data = {
            "agent_type": "monitoring",
            "capabilities": capabilities,
            "monitored_service": "VPC Flow Logs"
        }
        
        self.send_query(
            recipient_id=self.supervisor_id,
            content=json.dumps(registration_data),
            query_type="register"
        )
    
    def get_flow_log_groups(self) -> List[str]:
        """Get VPC Flow Log groups."""
        try:
            response = self.logs.describe_log_groups(
                logGroupNamePrefix='/aws/vpc/flowlogs'
            )
            return [group['logGroupName'] for group in response.get('logGroups', [])]
        except Exception as e:
            print(f"Error retrieving VPC Flow Log groups: {e}")
            self.send_notification(
                content=f"Error retrieving VPC Flow Log groups: {e}",
                notification_type="monitoring_error",
                severity="error",
                recipient_id=self.supervisor_id
            )
            return []
    
    def get_recent_flow_logs(self, log_group_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent VPC Flow Logs from a specific log group."""
        try:
            start_time = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
            end_time = int(datetime.utcnow().timestamp() * 1000)
            
            response = self.logs.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time,
                endTime=end_time,
                limit=100
            )
            
            return response.get('events', [])
        except Exception as e:
            print(f"Error retrieving VPC Flow Logs from {log_group_name}: {e}")
            return []
    
    def parse_flow_log(self, log_event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a VPC Flow Log event."""
        try:
            message = log_event.get('message', '')
            fields = message.split(' ')
            
            # Standard VPC Flow Log format
            if len(fields) >= 13:
                return {
                    'version': fields[0],
                    'account_id': fields[1],
                    'interface_id': fields[2],
                    'src_addr': fields[3],
                    'dst_addr': fields[4],
                    'src_port': int(fields[5]) if fields[5].isdigit() else 0,
                    'dst_port': int(fields[6]) if fields[6].isdigit() else 0,
                    'protocol': int(fields[7]) if fields[7].isdigit() else 0,
                    'packets': int(fields[8]) if fields[8].isdigit() else 0,
                    'bytes': int(fields[9]) if fields[9].isdigit() else 0,
                    'start': int(fields[10]) if fields[10].isdigit() else 0,
                    'end': int(fields[11]) if fields[11].isdigit() else 0,
                    'action': fields[12],
                    'log_status': fields[13] if len(fields) > 13 else ''
                }
            return {}
        except Exception as e:
            print(f"Error parsing flow log: {e}")
            return {}
    
    def analyze_flow_logs(self, flow_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze VPC Flow Logs for issues."""
        issues = []
        parsed_logs = []
        
        # Parse all logs
        for log in flow_logs:
            parsed_log = self.parse_flow_log(log)
            if parsed_log:
                parsed_logs.append(parsed_log)
        
        # Analyze for rejected traffic
        for log in parsed_logs:
            action = log.get('action', '')
            if action in self.rejected_patterns:
                # Check if this is on a monitored port
                dst_port = log.get('dst_port', 0)
                if dst_port in self.monitored_ports:
                    issue = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'interface_id': log.get('interface_id', ''),
                        'src_addr': log.get('src_addr', ''),
                        'dst_addr': log.get('dst_addr', ''),
                        'dst_port': dst_port,
                        'protocol': log.get('protocol', 0),
                        'action': action,
                        'severity': 'medium',
                        'issue_type': 'rejected_traffic',
                        'description': f"Traffic to port {dst_port} was {action}"
                    }
                    
                    # Check if this is a new issue (not recently alerted)
                    issue_key = f"{log.get('src_addr')}:{log.get('dst_addr')}:{dst_port}:{action}"
                    if issue_key not in self.recent_alerts or \
                       (datetime.utcnow() - self.recent_alerts[issue_key]).total_seconds() > 3600:
                        issues.append(issue)
                        self.recent_alerts[issue_key] = datetime.utcnow()
        
        # Analyze for unusual traffic patterns
        # (This would be more sophisticated in a real implementation)
        
        return issues
    
    def analyze_with_bedrock(self, flow_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AWS Bedrock to analyze patterns in VPC Flow Logs."""
        if not flow_logs:
            return {"analysis": "No flow logs to analyze"}
        
        # Prepare logs for analysis (limit to 20 for prompt size)
        parsed_logs = []
        for log in flow_logs[:20]:
            parsed_log = self.parse_flow_log(log)
            if parsed_log:
                parsed_logs.append(parsed_log)
        
        if not parsed_logs:
            return {"analysis": "No valid flow logs to analyze"}
        
        # Convert to text format for the model
        logs_text = "\n".join([
            f"Source: {log.get('src_addr')}:{log.get('src_port')} | " +
            f"Destination: {log.get('dst_addr')}:{log.get('dst_port')} | " +
            f"Protocol: {log.get('protocol')} | Action: {log.get('action')} | " +
            f"Bytes: {log.get('bytes')} | Packets: {log.get('packets')}"
            for log in parsed_logs
        ])
        
        # Prepare prompt for Titan Text Express
        prompt = f"""
        Analyze the following AWS VPC Flow Logs for network issues, security concerns, or unusual patterns:
        
        {logs_text}
        
        Please identify:
        1. Any potential network connectivity issues
        2. Security concerns or suspicious traffic
        3. Unusual traffic patterns
        4. Recommendations for investigation
        
        Format your response as JSON with the following structure:
        {{
            "connectivity_issues": [list of issues],
            "security_concerns": [list of concerns],
            "unusual_patterns": [list of patterns],
            "recommendations": [list of recommendations]
        }}
        """
        
        try:
            # Call Titan Text Express via Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId='amazon.titan-text-express-v1',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 1000,
                        "temperature": 0,
                        "topP": 0.9
                    }
                })
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read().decode('utf-8'))
            content = response_body.get('results', [{}])[0].get('outputText', '')
            
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
        if not issues and not analysis.get('connectivity_issues') and not analysis.get('security_concerns'):
            return
        
        # Prepare the report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "service": "VPC Flow Logs",
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
        high_severity_issues = [issue for issue in issues if issue.get('severity') == 'high']
        if high_severity_issues:
            self.send_notification(
                content=json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": self.agent_id,
                    "service": "VPC Flow Logs",
                    "high_severity_issues": high_severity_issues
                }),
                notification_type="urgent_alert",
                severity="high",
                recipient_id=self.supervisor_id
            )
    
    def handle_query(self, message: MCPMessage) -> Optional[str]:
        """Handle queries from other agents."""
        query_type = message.metadata.get("query_type")
        
        if query_type == "get_network_issues":
            # Return recent network issues
            log_groups = self.get_flow_log_groups()
            all_issues = []
            
            for group in log_groups:
                flow_logs = self.get_recent_flow_logs(group, hours=1)
                issues = self.analyze_flow_logs(flow_logs)
                all_issues.extend(issues)
            
            return self.send_response(
                recipient_id=message.sender_id,
                content=json.dumps({"issues": all_issues}),
                in_response_to=message.message_id,
                conversation_id=message.conversation_id
            )
        
        elif query_type == "analyze_traffic":
            # Analyze traffic for a specific interface or IP
            try:
                params = json.loads(message.content)
                interface_id = params.get("interface_id")
                ip_address = params.get("ip_address")
                hours = params.get("hours", 1)
                
                log_groups = self.get_flow_log_groups()
                all_flow_logs = []
                
                for group in log_groups:
                    flow_logs = self.get_recent_flow_logs(group, hours=hours)
                    all_flow_logs.extend(flow_logs)
                
                # Filter logs if interface or IP specified
                filtered_logs = []
                for log in all_flow_logs:
                    parsed_log = self.parse_flow_log(log)
                    if not parsed_log:
                        continue
                    
                    if interface_id and parsed_log.get('interface_id') == interface_id:
                        filtered_logs.append(log)
                    elif ip_address and (parsed_log.get('src_addr') == ip_address or 
                                         parsed_log.get('dst_addr') == ip_address):
                        filtered_logs.append(log)
                    elif not interface_id and not ip_address:
                        filtered_logs.append(log)
                
                issues = self.analyze_flow_logs(filtered_logs)
                analysis = self.analyze_with_bedrock(filtered_logs)
                
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
        # Get VPC Flow Log groups
        log_groups = self.get_flow_log_groups()
        all_flow_logs = []
        
        # Get flow logs from each group
        for group in log_groups:
            flow_logs = self.get_recent_flow_logs(group)
            all_flow_logs.extend(flow_logs)
        
        # Analyze flow logs for issues
        issues = self.analyze_flow_logs(all_flow_logs)
        
        # If issues found or sufficient logs, perform deeper analysis with Bedrock
        analysis = {}
        if issues or len(all_flow_logs) > 10:
            analysis = self.analyze_with_bedrock(all_flow_logs)
        
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
            print(f"VPC Flow Logs monitoring agent {self.agent_id} stopped by user.")
        except Exception as e:
            print(f"Error in VPC Flow Logs monitoring: {e}")
            self.send_notification(
                content=f"VPC Flow Logs monitoring error: {e}",
                notification_type="agent_error",
                severity="error",
                recipient_id=self.supervisor_id
            )


# Action group definitions for VPC Flow Logs agent
VPC_FLOW_LOGS_ACTION_GROUPS = {
    "GetNetworkIssues": {
        "description": "Get recent network connectivity issues detected in VPC Flow Logs",
        "parameters": {
            "timeframe_hours": {
                "type": "integer",
                "description": "Number of hours to look back",
                "default": 1
            }
        },
        "function": "get_network_issues"
    },
    "AnalyzeTrafficPatterns": {
        "description": "Analyze traffic patterns for a specific interface or IP address",
        "parameters": {
            "interface_id": {
                "type": "string",
                "description": "Network interface ID to analyze (optional)"
            },
            "ip_address": {
                "type": "string",
                "description": "IP address to analyze (optional)"
            },
            "timeframe_hours": {
                "type": "integer",
                "description": "Number of hours to analyze",
                "default": 1
            }
        },
        "function": "analyze_traffic_patterns"
    },
    "InvestigateRejectedTraffic": {
        "description": "Investigate rejected traffic to identify security group or NACL issues",
        "parameters": {
            "destination_port": {
                "type": "integer",
                "description": "Destination port to focus on (optional)"
            }
        },
        "function": "investigate_rejected_traffic"
    }
}


def create_vpc_flow_logs_agent(agent_id: str, supervisor_id: str, region_name: str = 'us-east-1') -> VPCFlowLogsMonitoringAgent:
    """Factory function to create and configure a VPC Flow Logs monitoring agent."""
    broker = A2AMessageBroker(queue_name="aws_monitoring_queue")
    agent = VPCFlowLogsMonitoringAgent(
        agent_id=agent_id,
        broker=broker,
        supervisor_id=supervisor_id,
        region_name=region_name
    )
    return agent

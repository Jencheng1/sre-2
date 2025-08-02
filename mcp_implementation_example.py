#!/usr/bin/env python3
"""
Practical MCP implementation example for SRE Copilot agents.
Shows how to add MCP to your Lambda functions.
"""

import json
import boto3
from datetime import datetime
import sys
import os

# Add MCP to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'lambdas'))
from mcp import MCPMessage, QueryMessage, ResponseMessage, NotificationMessage

class MCPEnabledAgent:
    """Example of an MCP-enabled monitoring agent."""
    
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.lambda_client = boto3.client('lambda')
    
    def send_mcp_message(self, recipient_agent, message):
        """Send MCP message to another agent via Lambda."""
        try:
            # Invoke recipient agent with MCP message
            response = self.lambda_client.invoke(
                FunctionName=f'sre-{recipient_agent}-lambda',
                InvocationType='Event',  # Async for notifications
                Payload=json.dumps({
                    'mcp_message': message.to_dict()
                })
            )
            return True
        except Exception as e:
            print(f"Error sending MCP message: {e}")
            return False
    
    def handle_mcp_message(self, event):
        """Handle incoming MCP messages."""
        if 'mcp_message' in event:
            mcp_data = event['mcp_message']
            
            # Recreate MCP message object
            if mcp_data['message_type'] == 'query':
                message = QueryMessage.from_dict(mcp_data)
                return self.handle_query(message)
            elif mcp_data['message_type'] == 'notification':
                message = NotificationMessage.from_dict(mcp_data)
                return self.handle_notification(message)
            elif mcp_data['message_type'] == 'response':
                message = ResponseMessage.from_dict(mcp_data)
                return self.handle_response(message)
        
        return None
    
    def handle_query(self, query: QueryMessage):
        """Handle incoming query messages."""
        print(f"Received query from {query.sender_id}: {query.content}")
        
        # Process based on query type
        if query.metadata.get('query_type') == 'investigate_incident':
            # Perform investigation
            findings = self.investigate_incident(query.metadata.get('incident_id'))
            
            # Send response
            response = ResponseMessage(
                content=json.dumps(findings),
                sender_id=self.agent_id,
                recipient_id=query.sender_id,
                in_response_to=query.message_id,
                status="completed"
            )
            
            self.send_mcp_message(query.sender_id, response)
            return findings
        
        return None
    
    def handle_notification(self, notification: NotificationMessage):
        """Handle incoming notifications."""
        print(f"Received notification from {notification.sender_id}")
        print(f"Type: {notification.metadata.get('notification_type')}")
        print(f"Severity: {notification.metadata.get('severity')}")
        
        # Take action based on notification
        if notification.metadata.get('severity') == 'high':
            # Escalate or take immediate action
            self.escalate_issue(notification)
        
        return True
    
    def handle_response(self, response: ResponseMessage):
        """Handle response messages."""
        print(f"Received response from {response.sender_id}")
        print(f"Status: {response.metadata.get('status')}")
        
        # Process response data
        if response.metadata.get('status') == 'completed':
            # Handle successful response
            return json.loads(response.content)
        
        return None
    
    def investigate_incident(self, incident_id):
        """Perform incident investigation (example)."""
        # This would contain real investigation logic
        return {
            "incident_id": incident_id,
            "findings": [
                "CPU usage at 95%",
                "Memory pressure detected",
                "No disk space issues"
            ],
            "recommendations": [
                "Scale up instances",
                "Review memory-intensive processes"
            ]
        }
    
    def escalate_issue(self, notification):
        """Escalate high-severity issues."""
        print(f"ESCALATING: {notification.content}")
        # Send to supervisor or trigger alerts

# Example Lambda handler with MCP
def lambda_handler(event, context):
    """Example Lambda handler with MCP support."""
    
    # Initialize agent
    agent = MCPEnabledAgent("example-agent")
    
    # Check if this is an MCP message
    if 'mcp_message' in event:
        result = agent.handle_mcp_message(event)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mcp_handled': True,
                'result': result
            })
        }
    
    # Regular agent logic
    action = event.get('action', 'default')
    
    if action == 'detect_issue':
        # Example: Detect an issue and notify supervisor via MCP
        issue_detected = True  # Your detection logic here
        
        if issue_detected:
            # Create MCP notification
            notification = NotificationMessage(
                content="High memory usage detected on web servers",
                sender_id="example-agent",
                recipient_id="supervisor-agent",
                notification_type="performance_alert",
                severity="high",
                metadata={
                    "memory_usage": 92,
                    "affected_servers": ["web-1", "web-2"],
                    "duration": "10 minutes"
                }
            )
            
            # Send to supervisor
            agent.send_mcp_message("supervisor", notification)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'issue_detected': True,
                    'mcp_notification_sent': True
                })
            }
    
    elif action == 'collaborate':
        # Example: Query another agent for information
        query = QueryMessage(
            content="What is the current AWS Health status?",
            sender_id="example-agent",
            recipient_id="health-agent",
            query_type="status_check"
        )
        
        agent.send_mcp_message("personal-health-agent", query)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'mcp_query_sent': True
            })
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Agent running with MCP support'
        })
    }

# Example: How to add MCP to existing agents
def upgrade_agent_with_mcp():
    """Example of adding MCP to existing agent code."""
    
    print("🔧 ADDING MCP TO EXISTING AGENT")
    print("="*60)
    
    print("\n1. Import MCP classes:")
    print("```python")
    print("from mcp import MCPMessage, QueryMessage, ResponseMessage, NotificationMessage")
    print("```")
    
    print("\n2. Add MCP message handling to lambda_handler:")
    print("```python")
    print("def lambda_handler(event, context):")
    print("    # Check for MCP messages first")
    print("    if 'mcp_message' in event:")
    print("        return handle_mcp_message(event['mcp_message'])")
    print("    ")
    print("    # Regular agent logic...")
    print("```")
    
    print("\n3. Send notifications for important events:")
    print("```python")
    print("if critical_issue_detected:")
    print("    notification = NotificationMessage(")
    print("        content='Critical issue detected',")
    print("        sender_id='my-agent',")
    print("        recipient_id='supervisor-agent',")
    print("        notification_type='alert',")
    print("        severity='high'")
    print("    )")
    print("    send_to_supervisor(notification)")
    print("```")
    
    print("\n4. Respond to queries from other agents:")
    print("```python")
    print("def handle_query(query):")
    print("    if query.metadata['query_type'] == 'status_check':")
    print("        status = get_current_status()")
    print("        response = ResponseMessage(")
    print("            content=json.dumps(status),")
    print("            sender_id='my-agent',")
    print("            recipient_id=query.sender_id,")
    print("            query_id=query.message_id")
    print("        )")
    print("        return response")
    print("```")
    
    print("\n✅ MCP integration complete!")

# Demonstrate MCP patterns
def demonstrate_mcp_patterns():
    """Show common MCP communication patterns."""
    
    print("\n\n🎯 COMMON MCP PATTERNS")
    print("="*60)
    
    # Pattern 1: Alert Chain
    print("\n1️⃣ Alert Chain Pattern")
    print("   CloudWatch → Supervisor → All Agents")
    print("   Used for: Incident detection and response")
    
    # Pattern 2: Information Gathering
    print("\n2️⃣ Information Gathering Pattern")
    print("   Supervisor → Multiple Agents → Supervisor")
    print("   Used for: Collecting data for analysis")
    
    # Pattern 3: Peer Communication
    print("\n3️⃣ Peer Communication Pattern")
    print("   Agent A ↔ Agent B")
    print("   Used for: Direct agent collaboration")
    
    # Pattern 4: Broadcast
    print("\n4️⃣ Broadcast Pattern")
    print("   Supervisor → All Agents")
    print("   Used for: Configuration updates, alerts")

if __name__ == "__main__":
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    print("\n" + "="*80)
    print("MCP IMPLEMENTATION GUIDE")
    print("="*80)
    
    # Show how to upgrade agents
    upgrade_agent_with_mcp()
    
    # Show common patterns
    demonstrate_mcp_patterns()
    
    # Example usage
    print("\n\n📝 EXAMPLE USAGE")
    print("="*60)
    
    # Create example agent
    agent = MCPEnabledAgent("demo-agent")
    
    # Create and show example messages
    examples = [
        NotificationMessage(
            content="Database connection pool at 90% capacity",
            sender_id="demo-agent",
            recipient_id="supervisor-agent",
            notification_type="resource_warning",
            severity="medium"
        ),
        QueryMessage(
            content="Check network latency to us-east-1",
            sender_id="demo-agent",
            recipient_id="vpc-agent",
            query_type="latency_check"
        )
    ]
    
    for msg in examples:
        print(f"\n{msg.message_type.upper()} Message:")
        print(json.dumps(msg.to_dict(), indent=2))
    
    print("\n\n✅ MCP is ready to use in your SRE Copilot agents!")
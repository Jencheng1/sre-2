"""
Agent-to-Agent (A2A) Communication Framework for AWS Bedrock Agents

This module implements the Agent-to-Agent (A2A) communication framework that enables
AWS Bedrock agents to communicate and collaborate effectively. It builds on the
Model Context Protocol (MCP) to provide higher-level communication patterns.
"""

import json
import uuid
import boto3
import time
from typing import Dict, List, Optional, Any, Union, Callable
from .mcp import MCPMessage, MCPMessageFactory, MCPConversation


class A2AMessageBroker:
    """Message broker for A2A communication."""
    
    def __init__(self, queue_name: str = "a2a_message_queue"):
        """Initialize the message broker with an SQS queue."""
        self.sqs = boto3.resource('sqs')
        self.queue_name = queue_name
        try:
            self.queue = self.sqs.get_queue_by_name(QueueName=queue_name)
        except:
            self.queue = self.sqs.create_queue(QueueName=queue_name)
    
    def send_message(self, message: MCPMessage) -> str:
        """Send a message to the queue."""
        response = self.queue.send_message(
            MessageBody=message.to_json(),
            MessageAttributes={
                'sender_id': {
                    'StringValue': message.sender_id,
                    'DataType': 'String'
                },
                'recipient_id': {
                    'StringValue': message.recipient_id or 'broadcast',
                    'DataType': 'String'
                },
                'message_type': {
                    'StringValue': message.message_type,
                    'DataType': 'String'
                }
            }
        )
        return response.get('MessageId')
    
    def receive_messages(self, recipient_id: str, max_messages: int = 10, wait_time: int = 0) -> List[MCPMessage]:
        """Receive messages for a specific recipient."""
        messages = []
        response = self.queue.receive_messages(
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time,
            VisibilityTimeout=30
        )
        
        for sqs_message in response:
            try:
                message_body = sqs_message.body
                message_attributes = sqs_message.message_attributes
                
                # Check if this message is for this recipient or is a broadcast
                target_recipient = message_attributes.get('recipient_id', {}).get('StringValue')
                if target_recipient in [recipient_id, 'broadcast']:
                    mcp_message = MCPMessage.from_json(message_body)
                    messages.append(mcp_message)
                    sqs_message.delete()  # Remove from queue after processing
            except Exception as e:
                print(f"Error processing message: {e}")
        
        return messages


class A2AAgent:
    """Base class for agents that communicate using the A2A framework."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker):
        """Initialize the agent with an ID and message broker."""
        self.agent_id = agent_id
        self.broker = broker
        self.conversations: Dict[str, MCPConversation] = {}
        self.message_handlers: Dict[str, Callable[[MCPMessage], Optional[MCPMessage]]] = {
            "query": self.handle_query,
            "response": self.handle_response,
            "notification": self.handle_notification,
            "context": self.handle_context
        }
    
    def send_query(self, recipient_id: str, content: str, query_type: str, 
                  priority: str = "normal", conversation_id: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send a query to another agent."""
        message = MCPMessageFactory.create_query(
            content=content,
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            query_type=query_type,
            priority=priority,
            conversation_id=conversation_id,
            metadata=metadata
        )
        
        # Add to conversation
        if conversation_id and conversation_id in self.conversations:
            self.conversations[conversation_id].add_message(message)
        else:
            conversation = MCPConversation(conversation_id=message.conversation_id)
            conversation.add_message(message)
            self.conversations[message.conversation_id] = conversation
        
        # Send via broker
        return self.broker.send_message(message)
    
    def send_response(self, recipient_id: str, content: str, in_response_to: str,
                     status: str = "success", conversation_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send a response to another agent."""
        message = MCPMessageFactory.create_response(
            content=content,
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            in_response_to=in_response_to,
            status=status,
            conversation_id=conversation_id,
            metadata=metadata
        )
        
        # Add to conversation
        if conversation_id and conversation_id in self.conversations:
            self.conversations[conversation_id].add_message(message)
        else:
            conversation = MCPConversation(conversation_id=message.conversation_id)
            conversation.add_message(message)
            self.conversations[message.conversation_id] = conversation
        
        # Send via broker
        return self.broker.send_message(message)
    
    def send_notification(self, content: str, notification_type: str,
                         severity: str = "info", recipient_id: Optional[str] = None,
                         conversation_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send a notification to one or more agents."""
        message = MCPMessageFactory.create_notification(
            content=content,
            sender_id=self.agent_id,
            notification_type=notification_type,
            severity=severity,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            metadata=metadata
        )
        
        # Add to conversation if part of one
        if conversation_id and conversation_id in self.conversations:
            self.conversations[conversation_id].add_message(message)
        elif conversation_id:
            conversation = MCPConversation(conversation_id=message.conversation_id)
            conversation.add_message(message)
            self.conversations[message.conversation_id] = conversation
        
        # Send via broker
        return self.broker.send_message(message)
    
    def send_context(self, content: str, context_type: str,
                    ttl: Optional[int] = None, recipient_id: Optional[str] = None,
                    conversation_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send contextual information to one or more agents."""
        message = MCPMessageFactory.create_context(
            content=content,
            sender_id=self.agent_id,
            context_type=context_type,
            ttl=ttl,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            metadata=metadata
        )
        
        # Add to conversation if part of one
        if conversation_id and conversation_id in self.conversations:
            self.conversations[conversation_id].add_message(message)
        elif conversation_id:
            conversation = MCPConversation(conversation_id=message.conversation_id)
            conversation.add_message(message)
            self.conversations[message.conversation_id] = conversation
        
        # Send via broker
        return self.broker.send_message(message)
    
    def receive_messages(self, max_messages: int = 10, wait_time: int = 0) -> List[MCPMessage]:
        """Receive messages addressed to this agent."""
        messages = self.broker.receive_messages(
            recipient_id=self.agent_id,
            max_messages=max_messages,
            wait_time=wait_time
        )
        
        # Process received messages
        for message in messages:
            # Add to conversation if part of one
            if message.conversation_id in self.conversations:
                self.conversations[message.conversation_id].add_message(message)
            else:
                conversation = MCPConversation(conversation_id=message.conversation_id)
                conversation.add_message(message)
                self.conversations[message.conversation_id] = conversation
            
            # Handle message based on type
            if message.message_type in self.message_handlers:
                self.message_handlers[message.message_type](message)
        
        return messages
    
    def handle_query(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle a query message. Override in subclasses."""
        print(f"Agent {self.agent_id} received query: {message.content}")
        return None
    
    def handle_response(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle a response message. Override in subclasses."""
        print(f"Agent {self.agent_id} received response: {message.content}")
        return None
    
    def handle_notification(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle a notification message. Override in subclasses."""
        print(f"Agent {self.agent_id} received notification: {message.content}")
        return None
    
    def handle_context(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle a context message. Override in subclasses."""
        print(f"Agent {self.agent_id} received context: {message.content}")
        return None
    
    def process_messages(self, max_messages: int = 10, wait_time: int = 0) -> None:
        """Process incoming messages."""
        self.receive_messages(max_messages=max_messages, wait_time=wait_time)
    
    def run(self, polling_interval: int = 5, max_runtime: Optional[int] = None) -> None:
        """Run the agent, continuously processing messages."""
        start_time = time.time()
        try:
            while True:
                self.process_messages(wait_time=polling_interval)
                
                # Check if max runtime exceeded
                if max_runtime and (time.time() - start_time) > max_runtime:
                    break
        except KeyboardInterrupt:
            print(f"Agent {self.agent_id} stopped by user.")


class A2ASupervisorAgent(A2AAgent):
    """Supervisor agent that coordinates other agents."""
    
    def __init__(self, agent_id: str, broker: A2AMessageBroker):
        """Initialize the supervisor agent."""
        super().__init__(agent_id, broker)
        self.supervised_agents: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str]) -> None:
        """Register an agent with the supervisor."""
        self.supervised_agents[agent_id] = {
            "agent_type": agent_type,
            "capabilities": capabilities,
            "status": "active",
            "last_seen": time.time()
        }
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the supervisor."""
        if agent_id in self.supervised_agents:
            del self.supervised_agents[agent_id]
    
    def get_agent_by_capability(self, capability: str) -> List[str]:
        """Find agents with a specific capability."""
        return [
            agent_id for agent_id, info in self.supervised_agents.items()
            if capability in info["capabilities"] and info["status"] == "active"
        ]
    
    def handle_query(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle a query message."""
        query_type = message.metadata.get("query_type")
        
        if query_type == "register":
            # Agent registration query
            try:
                agent_data = json.loads(message.content)
                self.register_agent(
                    agent_id=message.sender_id,
                    agent_type=agent_data.get("agent_type", "unknown"),
                    capabilities=agent_data.get("capabilities", [])
                )
                return self.send_response(
                    recipient_id=message.sender_id,
                    content=json.dumps({"status": "registered"}),
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
        
        elif query_type == "find_agent":
            # Query to find agents with specific capabilities
            try:
                query_data = json.loads(message.content)
                capability = query_data.get("capability")
                if capability:
                    agents = self.get_agent_by_capability(capability)
                    return self.send_response(
                        recipient_id=message.sender_id,
                        content=json.dumps({"agents": agents}),
                        in_response_to=message.message_id,
                        conversation_id=message.conversation_id
                    )
                else:
                    return self.send_response(
                        recipient_id=message.sender_id,
                        content=json.dumps({"error": "No capability specified"}),
                        in_response_to=message.message_id,
                        status="error",
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
    
    def handle_notification(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle a notification message."""
        notification_type = message.metadata.get("notification_type")
        
        if notification_type == "heartbeat" and message.sender_id in self.supervised_agents:
            # Update last seen timestamp for the agent
            self.supervised_agents[message.sender_id]["last_seen"] = time.time()
        
        return super().handle_notification(message)
    
    def check_agent_health(self, timeout: int = 60) -> None:
        """Check the health of supervised agents and mark inactive ones."""
        current_time = time.time()
        for agent_id, info in self.supervised_agents.items():
            if current_time - info["last_seen"] > timeout:
                info["status"] = "inactive"
                self.send_notification(
                    content=f"Agent {agent_id} is inactive",
                    notification_type="agent_status",
                    severity="warning"
                )
    
    def run(self, polling_interval: int = 5, health_check_interval: int = 30, 
           max_runtime: Optional[int] = None) -> None:
        """Run the supervisor agent with periodic health checks."""
        start_time = time.time()
        last_health_check = start_time
        
        try:
            while True:
                self.process_messages(wait_time=polling_interval)
                
                # Periodic health check
                current_time = time.time()
                if current_time - last_health_check > health_check_interval:
                    self.check_agent_health()
                    last_health_check = current_time
                
                # Check if max runtime exceeded
                if max_runtime and (current_time - start_time) > max_runtime:
                    break
        except KeyboardInterrupt:
            print(f"Supervisor agent {self.agent_id} stopped by user.")

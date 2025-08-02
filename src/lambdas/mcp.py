"""
Model Context Protocol (MCP) Implementation for AWS Bedrock Agents

This module implements the Model Context Protocol (MCP) for standardized communication
between AWS Bedrock agents. MCP provides a structured format for exchanging context,
queries, and responses between agents, enabling effective collaboration.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union


class MCPMessage:
    """Base class for MCP messages."""
    
    def __init__(
        self,
        message_type: str,
        content: str,
        sender_id: str,
        recipient_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        self.message_id = str(uuid.uuid4())
        self.message_type = message_type
        self.content = content
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "content": self.content,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "conversation_id": self.conversation_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create message from dictionary representation."""
        message = cls(
            message_type=data["message_type"],
            content=data["content"],
            sender_id=data["sender_id"],
            recipient_id=data.get("recipient_id"),
            conversation_id=data.get("conversation_id"),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp")
        )
        message.message_id = data["message_id"]
        return message
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPMessage':
        """Create message from JSON string."""
        return cls.from_dict(json.loads(json_str))


class QueryMessage(MCPMessage):
    """Query message for requesting information or action from another agent."""
    
    def __init__(
        self,
        content: str,
        sender_id: str,
        recipient_id: str,
        query_type: str,
        priority: str = "normal",
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        super().__init__(
            message_type="query",
            content=content,
            sender_id=sender_id,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            metadata=metadata or {},
            timestamp=timestamp
        )
        self.metadata["query_type"] = query_type
        self.metadata["priority"] = priority


class ResponseMessage(MCPMessage):
    """Response message for replying to queries."""
    
    def __init__(
        self,
        content: str,
        sender_id: str,
        recipient_id: str,
        in_response_to: str,
        status: str = "success",
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        super().__init__(
            message_type="response",
            content=content,
            sender_id=sender_id,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            metadata=metadata or {},
            timestamp=timestamp
        )
        self.metadata["in_response_to"] = in_response_to
        self.metadata["status"] = status


class NotificationMessage(MCPMessage):
    """Notification message for broadcasting information to one or more agents."""
    
    def __init__(
        self,
        content: str,
        sender_id: str,
        notification_type: str,
        severity: str = "info",
        recipient_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        super().__init__(
            message_type="notification",
            content=content,
            sender_id=sender_id,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            metadata=metadata or {},
            timestamp=timestamp
        )
        self.metadata["notification_type"] = notification_type
        self.metadata["severity"] = severity


class ContextMessage(MCPMessage):
    """Context message for sharing contextual information between agents."""
    
    def __init__(
        self,
        content: str,
        sender_id: str,
        context_type: str,
        ttl: Optional[int] = None,
        recipient_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        super().__init__(
            message_type="context",
            content=content,
            sender_id=sender_id,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            metadata=metadata or {},
            timestamp=timestamp
        )
        self.metadata["context_type"] = context_type
        if ttl is not None:
            self.metadata["ttl"] = ttl


class MCPMessageFactory:
    """Factory for creating MCP messages."""
    
    @staticmethod
    def create_query(
        content: str,
        sender_id: str,
        recipient_id: str,
        query_type: str,
        priority: str = "normal",
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QueryMessage:
        """Create a query message."""
        return QueryMessage(
            content=content,
            sender_id=sender_id,
            recipient_id=recipient_id,
            query_type=query_type,
            priority=priority,
            conversation_id=conversation_id,
            metadata=metadata
        )
    
    @staticmethod
    def create_response(
        content: str,
        sender_id: str,
        recipient_id: str,
        in_response_to: str,
        status: str = "success",
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResponseMessage:
        """Create a response message."""
        return ResponseMessage(
            content=content,
            sender_id=sender_id,
            recipient_id=recipient_id,
            in_response_to=in_response_to,
            status=status,
            conversation_id=conversation_id,
            metadata=metadata
        )
    
    @staticmethod
    def create_notification(
        content: str,
        sender_id: str,
        notification_type: str,
        severity: str = "info",
        recipient_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationMessage:
        """Create a notification message."""
        return NotificationMessage(
            content=content,
            sender_id=sender_id,
            notification_type=notification_type,
            severity=severity,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            metadata=metadata
        )
    
    @staticmethod
    def create_context(
        content: str,
        sender_id: str,
        context_type: str,
        ttl: Optional[int] = None,
        recipient_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextMessage:
        """Create a context message."""
        return ContextMessage(
            content=content,
            sender_id=sender_id,
            context_type=context_type,
            ttl=ttl,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            metadata=metadata
        )


class MCPConversation:
    """Class for managing a conversation between agents using MCP."""
    
    def __init__(self, conversation_id: Optional[str] = None):
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.messages: List[MCPMessage] = []
    
    def add_message(self, message: MCPMessage) -> None:
        """Add a message to the conversation."""
        if message.conversation_id != self.conversation_id:
            message.conversation_id = self.conversation_id
        self.messages.append(message)
    
    def get_messages(self) -> List[MCPMessage]:
        """Get all messages in the conversation."""
        return self.messages
    
    def get_latest_message(self) -> Optional[MCPMessage]:
        """Get the latest message in the conversation."""
        if not self.messages:
            return None
        return self.messages[-1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary representation."""
        return {
            "conversation_id": self.conversation_id,
            "messages": [message.to_dict() for message in self.messages]
        }
    
    def to_json(self) -> str:
        """Convert conversation to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPConversation':
        """Create conversation from dictionary representation."""
        conversation = cls(conversation_id=data["conversation_id"])
        for message_data in data["messages"]:
            message_type = message_data["message_type"]
            if message_type == "query":
                message = QueryMessage(
                    content=message_data["content"],
                    sender_id=message_data["sender_id"],
                    recipient_id=message_data["recipient_id"],
                    query_type=message_data["metadata"]["query_type"],
                    priority=message_data["metadata"].get("priority", "normal"),
                    conversation_id=message_data["conversation_id"],
                    metadata={k: v for k, v in message_data["metadata"].items() 
                              if k not in ["query_type", "priority"]},
                    timestamp=message_data["timestamp"]
                )
            elif message_type == "response":
                message = ResponseMessage(
                    content=message_data["content"],
                    sender_id=message_data["sender_id"],
                    recipient_id=message_data["recipient_id"],
                    in_response_to=message_data["metadata"]["in_response_to"],
                    status=message_data["metadata"].get("status", "success"),
                    conversation_id=message_data["conversation_id"],
                    metadata={k: v for k, v in message_data["metadata"].items() 
                              if k not in ["in_response_to", "status"]},
                    timestamp=message_data["timestamp"]
                )
            elif message_type == "notification":
                message = NotificationMessage(
                    content=message_data["content"],
                    sender_id=message_data["sender_id"],
                    notification_type=message_data["metadata"]["notification_type"],
                    severity=message_data["metadata"].get("severity", "info"),
                    recipient_id=message_data.get("recipient_id"),
                    conversation_id=message_data["conversation_id"],
                    metadata={k: v for k, v in message_data["metadata"].items() 
                              if k not in ["notification_type", "severity"]},
                    timestamp=message_data["timestamp"]
                )
            elif message_type == "context":
                message = ContextMessage(
                    content=message_data["content"],
                    sender_id=message_data["sender_id"],
                    context_type=message_data["metadata"]["context_type"],
                    ttl=message_data["metadata"].get("ttl"),
                    recipient_id=message_data.get("recipient_id"),
                    conversation_id=message_data["conversation_id"],
                    metadata={k: v for k, v in message_data["metadata"].items() 
                              if k not in ["context_type", "ttl"]},
                    timestamp=message_data["timestamp"]
                )
            else:
                message = MCPMessage.from_dict(message_data)
            
            message.message_id = message_data["message_id"]
            conversation.add_message(message)
        
        return conversation
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPConversation':
        """Create conversation from JSON string."""
        return cls.from_dict(json.loads(json_str))

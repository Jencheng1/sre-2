"""
Base Agent class for Strands Agents implementation
Provides common functionality for all SRE monitoring agents
"""

import os
import boto3
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import logging

# Import mock implementations for now
try:
    from strands import Agent
    from strands_agents_tools import create_custom_tool
except ImportError:
    # Use mock implementations
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from mock_strands import Agent, create_custom_tool

class BaseStrandsAgent(ABC):
    """Base class for all SRE Strands Agents"""
    
    def __init__(
        self, 
        agent_name: str,
        region: str = "us-east-1",
        model: str = "claude-4-sonnet",
        test_mode: bool = True
    ):
        self.agent_name = agent_name
        self.region = region
        self.model = model
        self.test_mode = test_mode
        self.logger = self._setup_logging()
        
        # Initialize AWS clients
        self.session = boto3.Session(region_name=region)
        self.ssm = self.session.client('ssm')
        
        # Create the Strands agent
        self.agent = Agent(
            model=self._get_model_config(),
            system_prompt=self._get_system_prompt(),
            tools=self._create_tools()
        )
        
        self.logger.info(f"Initialized {agent_name} Strands Agent")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the agent"""
        logger = logging.getLogger(f"strands.{self.agent_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _get_model_config(self) -> str:
        """Get model configuration for the agent"""
        if self.test_mode:
            # For testing, might use a lighter model or mock
            return self.model
        else:
            return self.model
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def _create_tools(self) -> List[Any]:
        """Create tools for this agent - must be implemented by subclasses"""
        pass
    
    def get_secret(self, parameter_name: str) -> str:
        """Retrieve secret from AWS Systems Manager Parameter Store"""
        try:
            if not parameter_name.startswith('/'):
                parameter_name = f"/sre-copilot/agents/{self.agent_name}/{parameter_name}"
            
            response = self.ssm.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )
            return response['Parameter']['Value']
        except Exception as e:
            self.logger.error(f"Failed to retrieve secret {parameter_name}: {e}")
            if self.test_mode:
                return f"test_{parameter_name.split('/')[-1]}"
            raise
    
    def store_secret(self, parameter_name: str, value: str) -> bool:
        """Store secret in AWS Systems Manager Parameter Store"""
        try:
            if not parameter_name.startswith('/'):
                parameter_name = f"/sre-copilot/agents/{self.agent_name}/{parameter_name}"
            
            self.ssm.put_parameter(
                Name=parameter_name,
                Value=value,
                Type='SecureString',
                Overwrite=True
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to store secret {parameter_name}: {e}")
            return False
    
    def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a query using the Strands agent"""
        try:
            self.logger.info(f"Executing query: {query}")
            
            # Add context to query if provided
            if context:
                query = f"Context: {context}\n\nQuery: {query}"
            
            # Execute using Strands agent
            response = self.agent(query)
            
            result = {
                "success": True,
                "response": response,
                "agent": self.agent_name,
                "timestamp": datetime.now().isoformat(),
                "context": context
            }
            
            self.logger.info(f"Query executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name,
                "timestamp": datetime.now().isoformat(),
                "context": context
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check for the agent"""
        try:
            # Simple test query to verify agent is working
            test_response = self.agent("Health check - respond with OK")
            
            return {
                "status": "healthy",
                "agent": self.agent_name,
                "model": self.model,
                "test_mode": self.test_mode,
                "timestamp": datetime.now().isoformat(),
                "response_received": bool(test_response)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent": self.agent_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and tool information"""
        tools_info = []
        for tool in self._create_tools():
            tools_info.append({
                "name": getattr(tool, 'name', 'unknown'),
                "description": getattr(tool, 'description', 'No description available')
            })
        
        return {
            "agent_name": self.agent_name,
            "model": self.model,
            "test_mode": self.test_mode,
            "tools": tools_info,
            "system_prompt_length": len(self._get_system_prompt()),
            "capabilities": self._get_specific_capabilities()
        }
    
    @abstractmethod
    def _get_specific_capabilities(self) -> List[str]:
        """Get specific capabilities for this agent - must be implemented by subclasses"""
        pass

class StrandsToolFactory:
    """Factory class for creating Strands tools"""
    
    @staticmethod
    def create_monitoring_tool(
        name: str,
        description: str,
        func,
        parameters: Dict[str, Any]
    ):
        """Create a monitoring tool for Strands agents"""
        return create_custom_tool(
            name=name,
            description=description,
            function=func,
            parameters=parameters
        )
    
    @staticmethod
    def create_search_tool(
        name: str,
        description: str,
        search_func,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """Create a search tool for Strands agents"""
        if parameters is None:
            parameters = {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Maximum results", "default": 10}
            }
        
        return create_custom_tool(
            name=name,
            description=description,
            function=search_func,
            parameters=parameters
        )
    
    @staticmethod
    def create_metrics_tool(
        name: str,
        description: str,
        metrics_func,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """Create a metrics tool for Strands agents"""
        if parameters is None:
            parameters = {
                "metric_type": {"type": "string", "description": "Type of metric to retrieve"},
                "entity": {"type": "string", "description": "Entity to get metrics for"},
                "time_range": {"type": "string", "description": "Time range for metrics", "default": "-1h"}
            }
        
        return create_custom_tool(
            name=name,
            description=description,
            function=metrics_func,
            parameters=parameters
        )
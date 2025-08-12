"""
Unit tests for BaseStrandsAgent
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import boto3

# Import the base agent class
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from base.base_agent import BaseStrandsAgent, StrandsToolFactory

class TestStrandsAgent(BaseStrandsAgent):
    """Test implementation of BaseStrandsAgent for testing"""
    
    def _get_system_prompt(self) -> str:
        return "Test agent for unit testing purposes."
    
    def _create_tools(self):
        return []
    
    def _get_specific_capabilities(self):
        return ["testing", "validation"]

class TestBaseStrandsAgent(unittest.TestCase):
    """Test cases for BaseStrandsAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('boto3.Session'):
            self.agent = TestStrandsAgent(
                agent_name="test_agent",
                region="us-east-1", 
                test_mode=True
            )
    
    def test_initialization(self):
        """Test agent initialization"""
        self.assertEqual(self.agent.agent_name, "test_agent")
        self.assertEqual(self.agent.region, "us-east-1")
        self.assertTrue(self.agent.test_mode)
        self.assertIsNotNone(self.agent.logger)
    
    @patch('boto3.Session')
    def test_get_secret_test_mode(self, mock_session):
        """Test secret retrieval in test mode"""
        secret = self.agent.get_secret("api_token")
        self.assertEqual(secret, "test_api_token")
    
    @patch('boto3.Session')
    def test_get_secret_with_full_path(self, mock_session):
        """Test secret retrieval with full parameter path"""
        secret = self.agent.get_secret("/custom/path/token")
        self.assertEqual(secret, "test_token")
    
    def test_health_check(self):
        """Test health check functionality"""
        with patch.object(self.agent.agent, '__call__', return_value="OK"):
            health = self.agent.health_check()
            
            self.assertEqual(health["status"], "healthy")
            self.assertEqual(health["agent"], "test_agent")
            self.assertTrue(health["response_received"])
            self.assertTrue(health["test_mode"])
    
    def test_health_check_failure(self):
        """Test health check when agent fails"""
        with patch.object(self.agent.agent, '__call__', side_effect=Exception("Agent error")):
            health = self.agent.health_check()
            
            self.assertEqual(health["status"], "unhealthy")
            self.assertIn("error", health)
    
    def test_get_capabilities(self):
        """Test capabilities retrieval"""
        capabilities = self.agent.get_capabilities()
        
        self.assertEqual(capabilities["agent_name"], "test_agent")
        self.assertTrue(capabilities["test_mode"])
        self.assertIn("testing", capabilities["capabilities"])
        self.assertIn("validation", capabilities["capabilities"])
    
    def test_execute_success(self):
        """Test successful query execution"""
        with patch.object(self.agent.agent, '__call__', return_value="Test response"):
            result = self.agent.execute("test query")
            
            self.assertTrue(result["success"])
            self.assertEqual(result["response"], "Test response")
            self.assertEqual(result["agent"], "test_agent")
    
    def test_execute_with_context(self):
        """Test query execution with context"""
        context = {"incident_id": "INC-123", "priority": "high"}
        
        with patch.object(self.agent.agent, '__call__', return_value="Test response"):
            result = self.agent.execute("test query", context)
            
            self.assertTrue(result["success"])
            self.assertEqual(result["context"], context)
    
    def test_execute_failure(self):
        """Test query execution failure"""
        with patch.object(self.agent.agent, '__call__', side_effect=Exception("Execution failed")):
            result = self.agent.execute("test query")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
            self.assertEqual(result["agent"], "test_agent")

class TestStrandsToolFactory(unittest.TestCase):
    """Test cases for StrandsToolFactory"""
    
    def test_create_monitoring_tool(self):
        """Test monitoring tool creation"""
        def test_func(param1, param2="default"):
            return {"param1": param1, "param2": param2}
        
        parameters = {
            "param1": {"type": "string", "description": "Test parameter"},
            "param2": {"type": "string", "description": "Optional parameter", "default": "default"}
        }
        
        with patch('strands_agents_tools.create_custom_tool') as mock_create:
            mock_create.return_value = Mock()
            
            tool = StrandsToolFactory.create_monitoring_tool(
                name="test_tool",
                description="Test monitoring tool",
                func=test_func,
                parameters=parameters
            )
            
            mock_create.assert_called_once_with(
                name="test_tool",
                description="Test monitoring tool", 
                function=test_func,
                parameters=parameters
            )
    
    def test_create_search_tool(self):
        """Test search tool creation"""
        def search_func(query, limit=10):
            return {"query": query, "results": [], "limit": limit}
        
        with patch('strands_agents_tools.create_custom_tool') as mock_create:
            mock_create.return_value = Mock()
            
            tool = StrandsToolFactory.create_search_tool(
                name="test_search",
                description="Test search tool",
                search_func=search_func
            )
            
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            self.assertEqual(call_args[1]["name"], "test_search")
            self.assertEqual(call_args[1]["description"], "Test search tool")
            self.assertEqual(call_args[1]["function"], search_func)
    
    def test_create_metrics_tool(self):
        """Test metrics tool creation"""
        def metrics_func(metric_type, entity, time_range="-1h"):
            return {"metric_type": metric_type, "entity": entity, "time_range": time_range}
        
        with patch('strands_agents_tools.create_custom_tool') as mock_create:
            mock_create.return_value = Mock()
            
            tool = StrandsToolFactory.create_metrics_tool(
                name="test_metrics",
                description="Test metrics tool",
                metrics_func=metrics_func
            )
            
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            self.assertEqual(call_args[1]["name"], "test_metrics")
            self.assertEqual(call_args[1]["description"], "Test metrics tool")

if __name__ == '__main__':
    unittest.main()
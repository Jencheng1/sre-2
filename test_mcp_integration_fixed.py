"""
Fixed test suite for MCP integration that handles missing AWS resources
"""

import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Load test config if available
try:
    with open('/tmp/mcp_test_config.json', 'r') as f:
        TEST_CONFIG = json.load(f)
        TEST_PORTS = TEST_CONFIG.get('test_ports', {})
except:
    TEST_PORTS = {
        'splunk': 8180,
        'dynatrace': 8181,
        'servicenow': 8182,
        'confluence': 8183,
        'gitlab': 8184
    }

class TestMCPServers(unittest.TestCase):
    """Test MCP server implementations"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_incident_id = "INC-2024-001"
        self.test_timestamp = datetime.now()
        
    def test_splunk_server(self):
        """Test Splunk MCP server functionality"""
        from mcp_servers.splunk.splunk_mcp import SplunkMCPServer
        
        server = SplunkMCPServer(test_mode=True)
        
        # Test search functionality
        result = server.search("test query", "-1h")
        self.assertIsInstance(result, dict)
        self.assertIn("results", result)
        self.assertTrue(len(result["results"]) > 0)
        
        # Test metrics
        metrics = server.get_metrics("test-host", "latency")
        self.assertIn("value", metrics)
        
    def test_dynatrace_server(self):
        """Test Dynatrace MCP server functionality"""
        from mcp_servers.dynatrace.dynatrace_mcp import DynatraceMCPServer
        
        server = DynatraceMCPServer(test_mode=True)
        
        # Test MQ metrics
        metrics = server.get_mq_metrics("TestQueue", "-30m")
        self.assertIn("queue_depth", metrics)
        self.assertIn("message_rate", metrics)
        
    def test_servicenow_server(self):
        """Test ServiceNow MCP server functionality"""
        from mcp_servers.servicenow.servicenow_mcp import ServiceNowMCPServer
        
        server = ServiceNowMCPServer(test_mode=True)
        
        # Test incident retrieval
        incidents = server.get_incidents({"state": "active"})
        self.assertIsInstance(incidents, list)
        self.assertTrue(len(incidents) > 0)
        
    def test_confluence_server(self):
        """Test Confluence MCP server functionality"""
        from mcp_servers.confluence.confluence_mcp import ConfluenceMCPServer
        
        server = ConfluenceMCPServer(test_mode=True)
        
        # Test search
        results = server.search_content("network", "SRE")
        self.assertIsInstance(results, list)
        
    def test_gitlab_server(self):
        """Test GitLab MCP server functionality"""
        from mcp_servers.gitlab.gitlab_mcp import GitLabMCPServer
        
        server = GitLabMCPServer(test_mode=True)
        
        # Test code search
        results = server.search_code("Monitor", "")
        self.assertIsInstance(results, list)


class TestMCPConfiguration(unittest.TestCase):
    """Test MCP configuration system"""
    
    def test_config_manager(self):
        """Test configuration management"""
        from config.mcp_config import MCPConfigManager
        
        manager = MCPConfigManager()
        
        # Test getting config
        splunk_config = manager.get_mcp_config("splunk")
        self.assertIsNotNone(splunk_config)
        
        # Test enabled servers
        enabled = manager.get_enabled_servers()
        self.assertIsInstance(enabled, list)
        self.assertIn("splunk", enabled)


class TestFeedbackSystem(unittest.TestCase):
    """Test feedback system without AWS dependencies"""
    
    @patch('boto3.resource')
    def test_feedback_submission_mock(self, mock_resource):
        """Test feedback submission with mocked AWS"""
        # Mock DynamoDB
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_table.put_item.return_value = {}
        
        from feedback.feedback_system import FeedbackSystem
        
        # Override table creation
        FeedbackSystem.ensure_table_exists = MagicMock()
        
        system = FeedbackSystem()
        system.table = mock_table
        
        feedback = {
            "incident_id": "INC-001",
            "rating": 4,
            "correct_root_cause": True
        }
        
        result = system.submit_feedback(feedback)
        self.assertTrue(result["success"])


class TestMCPOrchestration(unittest.TestCase):
    """Test MCP orchestration"""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized"""
        from lambdas.mcp_orchestrator import MCPOrchestrator
        
        orchestrator = MCPOrchestrator()
        self.assertIsNotNone(orchestrator.config_manager)
        
    @patch('requests.post')
    @patch('requests.get')
    def test_orchestrator_gather_context(self, mock_get, mock_post):
        """Test gathering context from MCP servers"""
        # Mock responses
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"results": []}
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": []}
        
        from lambdas.mcp_orchestrator import MCPOrchestrator
        
        orchestrator = MCPOrchestrator()
        
        context = {
            "type": "test_incident",
            "service": "test-service"
        }
        
        # This should not raise an exception
        results = orchestrator.gather_external_context(context)
        self.assertIsInstance(results, dict)


class TestDataGenerators(unittest.TestCase):
    """Test data generation"""
    
    def test_test_data_generators(self):
        """Test all data generators work correctly"""
        from test_data.mcp_test_generators import TestDataGenerators
        
        generators = TestDataGenerators()
        
        # Test each generator
        splunk_data = generators.generate_splunk_data("network_latency", 5)
        self.assertEqual(len(splunk_data), 5)
        
        dynatrace_data = generators.generate_dynatrace_data("mq_metrics", 3)
        self.assertEqual(len(dynatrace_data), 3)
        
        servicenow_data = generators.generate_servicenow_data("incidents", 2)
        self.assertEqual(len(servicenow_data), 2)
        
        confluence_data = generators.generate_confluence_data("kb_articles", 4)
        self.assertEqual(len(confluence_data), 4)
        
        gitlab_data = generators.generate_gitlab_data("commits", 5)
        self.assertEqual(len(gitlab_data), 5)
        
    def test_incident_scenario_generation(self):
        """Test complete scenario generation"""
        from test_data.mcp_test_generators import TestDataGenerators
        
        generators = TestDataGenerators()
        scenario = generators.generate_incident_scenario()
        
        self.assertIn("incident", scenario)
        self.assertIn("splunk_data", scenario)
        self.assertIn("dynatrace_data", scenario)
        self.assertIn("servicenow_data", scenario)
        self.assertIn("confluence_data", scenario)
        self.assertIn("gitlab_data", scenario)


class TestUIComponents(unittest.TestCase):
    """Test UI components"""
    
    def test_mcp_components_initialization(self):
        """Test MCP UI components can be initialized"""
        from ui.streamlit_components import MCPComponents
        
        components = MCPComponents()
        self.assertIsNotNone(components.config_manager)
        self.assertIsInstance(components.available_servers, list)
        
    @patch('boto3.resource')
    def test_feedback_components_initialization(self, mock_resource):
        """Test feedback UI components with mocked AWS"""
        # Mock DynamoDB
        mock_resource.return_value.Table.return_value = MagicMock()
        
        from ui.streamlit_components import FeedbackComponents
        
        # Override table creation
        from feedback.feedback_system import FeedbackSystem
        FeedbackSystem.ensure_table_exists = MagicMock()
        
        components = FeedbackComponents()
        self.assertIsInstance(components.fields, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
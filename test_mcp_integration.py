"""
Comprehensive test suite for MCP integration requirements
Tests all external service integrations and human-in-the-loop feedback
"""

import unittest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import boto3
from typing import Dict, List, Any

class TestMCPIntegration(unittest.TestCase):
    """Test suite for MCP server integrations"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_incident_id = "INC-2024-001"
        self.test_timestamp = datetime.now()
        
    # Test Case 1: Splunk MCP Integration for Network Latency
    def test_splunk_network_latency_integration(self):
        """Test Splunk MCP server can retrieve network latency data"""
        from mcp_servers.splunk.splunk_mcp import SplunkMCPServer
        
        server = SplunkMCPServer(test_mode=True)
        
        # Test search for network latency
        query = "index=network sourcetype=latency | stats avg(latency) by host"
        result = server.search(query, time_range="-1h")
        
        self.assertIsInstance(result, dict)
        self.assertIn("results", result)
        self.assertTrue(len(result["results"]) > 0)
        self.assertIn("avg_latency", result["results"][0])
        self.assertIn("host", result["results"][0])
        
    # Test Case 2: Dynatrace MCP Integration for MQ Metrics
    def test_dynatrace_mq_metrics_integration(self):
        """Test Dynatrace MCP server can retrieve MQ metrics"""
        from mcp_servers.dynatrace.dynatrace_mcp import DynatraceMCPServer
        
        server = DynatraceMCPServer(test_mode=True)
        
        # Test MQ metrics retrieval
        metrics = server.get_mq_metrics(
            queue_name="OrderProcessingQueue",
            time_range="-30m"
        )
        
        self.assertIsInstance(metrics, dict)
        self.assertIn("queue_depth", metrics)
        self.assertIn("message_rate", metrics)
        self.assertIn("error_rate", metrics)
        self.assertTrue(metrics["queue_depth"] >= 0)
        
    # Test Case 3: ServiceNow MCP Integration for Incidents
    def test_servicenow_incident_integration(self):
        """Test ServiceNow MCP server can retrieve and create incidents"""
        from mcp_servers.servicenow.servicenow_mcp import ServiceNowMCPServer
        
        server = ServiceNowMCPServer(test_mode=True)
        
        # Test incident retrieval
        incidents = server.get_incidents(
            filters={"state": "active", "priority": "1"}
        )
        
        self.assertIsInstance(incidents, list)
        self.assertTrue(len(incidents) > 0)
        self.assertIn("sys_id", incidents[0])
        self.assertIn("short_description", incidents[0])
        
        # Test incident creation
        new_incident = server.create_incident({
            "short_description": "Test incident from MCP",
            "priority": "3",
            "category": "Network"
        })
        
        self.assertIn("sys_id", new_incident)
        self.assertEqual(new_incident["state"], "New")
        
    # Test Case 4: Confluence MCP Integration for KB Articles
    def test_confluence_kb_integration(self):
        """Test Confluence MCP server can search knowledge base"""
        from mcp_servers.confluence.confluence_mcp import ConfluenceMCPServer
        
        server = ConfluenceMCPServer(test_mode=True)
        
        # Test KB search
        results = server.search_content(
            query="network latency troubleshooting",
            space_key="SRE"
        )
        
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
        self.assertIn("title", results[0])
        self.assertIn("content", results[0])
        self.assertIn("url", results[0])
        
    # Test Case 5: GitLab MCP Integration for Code Analysis
    def test_gitlab_code_analysis_integration(self):
        """Test GitLab MCP server can search code and commits"""
        from mcp_servers.gitlab.gitlab_mcp import GitLabMCPServer
        
        server = GitLabMCPServer(test_mode=True)
        
        # Test code search
        code_results = server.search_code(
            query="NetworkLatencyMonitor",
            project_id="sre/monitoring"
        )
        
        self.assertIsInstance(code_results, list)
        self.assertTrue(len(code_results) > 0)
        self.assertIn("file_path", code_results[0])
        self.assertIn("content", code_results[0])
        
        # Test recent commits
        commits = server.get_recent_commits(
            project_id="sre/monitoring",
            since=datetime.now() - timedelta(days=7)
        )
        
        self.assertIsInstance(commits, list)
        self.assertTrue(len(commits) > 0)
        self.assertIn("sha", commits[0])
        self.assertIn("message", commits[0])
        
    # Test Case 6: Human-in-the-Loop Feedback System
    def test_human_feedback_system(self):
        """Test human feedback collection and storage"""
        from feedback.feedback_system import FeedbackSystem
        
        feedback_system = FeedbackSystem()
        
        # Test feedback submission
        feedback = {
            "incident_id": self.test_incident_id,
            "analysis_id": "ANAL-001",
            "rating": 4,
            "correct_root_cause": True,
            "additional_context": "The issue was actually related to DNS",
            "suggested_actions": ["Check DNS configuration", "Verify route53 records"]
        }
        
        result = feedback_system.submit_feedback(feedback)
        
        self.assertTrue(result["success"])
        self.assertIn("feedback_id", result)
        
        # Test feedback retrieval
        stored_feedback = feedback_system.get_feedback(self.test_incident_id)
        
        self.assertIsInstance(stored_feedback, list)
        self.assertTrue(len(stored_feedback) > 0)
        self.assertEqual(stored_feedback[0]["rating"], 4)
        
    # Test Case 7: Context Enhancement with Feedback
    def test_context_enhancement(self):
        """Test that feedback enhances future analysis"""
        from feedback.context_enhancer import ContextEnhancer
        
        enhancer = ContextEnhancer()
        
        # Submit feedback for a specific type of incident
        feedback = {
            "incident_type": "network_latency",
            "root_cause": "DNS misconfiguration",
            "resolution": "Updated route53 records",
            "effectiveness": 5
        }
        
        enhancer.add_feedback_to_context(feedback)
        
        # Test that similar incident gets enhanced context
        similar_incident = {
            "type": "network_latency",
            "symptoms": ["high response time", "intermittent failures"]
        }
        
        enhanced_context = enhancer.get_enhanced_context(similar_incident)
        
        self.assertIn("historical_resolutions", enhanced_context)
        self.assertIn("DNS misconfiguration", str(enhanced_context))
        
    # Test Case 8: MCP Configuration System
    def test_mcp_configuration_system(self):
        """Test extensible MCP configuration"""
        from config.mcp_config import MCPConfigManager
        
        config_manager = MCPConfigManager()
        
        # Test adding new MCP server
        new_mcp_config = {
            "name": "custom_monitoring",
            "type": "rest_api",
            "endpoint": "https://monitoring.example.com/api",
            "auth": {
                "type": "bearer",
                "token": "test_token"
            },
            "enabled": True
        }
        
        result = config_manager.add_mcp_server(new_mcp_config)
        
        self.assertTrue(result["success"])
        
        # Test retrieving configuration
        config = config_manager.get_mcp_config("custom_monitoring")
        
        self.assertEqual(config["endpoint"], "https://monitoring.example.com/api")
        self.assertTrue(config["enabled"])
        
    # Test Case 9: Lambda Integration with MCP
    def test_lambda_mcp_integration(self):
        """Test Lambda functions can call MCP servers"""
        from lambdas.mcp_orchestrator import MCPOrchestrator
        
        orchestrator = MCPOrchestrator()
        
        # Test orchestrating multiple MCP calls
        incident_context = {
            "type": "performance_degradation",
            "service": "order-processing",
            "timestamp": self.test_timestamp.isoformat()
        }
        
        mcp_results = orchestrator.gather_external_context(incident_context)
        
        self.assertIn("splunk", mcp_results)
        self.assertIn("dynatrace", mcp_results)
        self.assertIn("servicenow", mcp_results)
        self.assertIsNotNone(mcp_results["splunk"]["network_metrics"])
        self.assertIsNotNone(mcp_results["dynatrace"]["mq_metrics"])
        
    # Test Case 10: Action Group Integration
    def test_action_group_mcp_integration(self):
        """Test Bedrock action groups can invoke MCP servers"""
        from action_groups.mcp_action_group import MCPActionGroup
        
        action_group = MCPActionGroup()
        
        # Test action group calling MCP
        action_input = {
            "action": "get_network_latency",
            "parameters": {
                "time_range": "-1h",
                "host_filter": "prod-*"
            }
        }
        
        result = action_group.execute_action(action_input)
        
        self.assertIn("latency_data", result)
        self.assertIsInstance(result["latency_data"], list)
        
    # Test Case 11: End-to-End Incident Analysis with MCP
    def test_e2e_incident_analysis_with_mcp(self):
        """Test complete incident analysis flow with all MCP integrations"""
        from orchestration.incident_analyzer import IncidentAnalyzer
        
        analyzer = IncidentAnalyzer()
        
        # Create test incident
        incident = {
            "id": self.test_incident_id,
            "type": "api_latency",
            "service": "payment-service",
            "symptoms": [
                "Response time > 5s",
                "MQ backlog increasing",
                "Error rate spike"
            ],
            "start_time": self.test_timestamp.isoformat()
        }
        
        # Analyze with MCP data
        analysis = analyzer.analyze_with_mcp(incident)
        
        # Verify comprehensive analysis
        self.assertIn("root_cause", analysis)
        self.assertIn("evidence", analysis)
        self.assertIn("mcp_correlations", analysis)
        self.assertIn("splunk", analysis["mcp_correlations"])
        self.assertIn("dynatrace", analysis["mcp_correlations"])
        self.assertIn("confluence_kb", analysis["mcp_correlations"])
        self.assertIn("recommended_actions", analysis)
        self.assertTrue(len(analysis["recommended_actions"]) > 0)
        
    # Test Case 12: Streamlit UI Integration
    def test_streamlit_ui_components(self):
        """Test Streamlit UI components for MCP and feedback"""
        from ui.streamlit_components import MCPComponents, FeedbackComponents
        
        # Test MCP configuration UI
        mcp_ui = MCPComponents()
        config_form = mcp_ui.render_mcp_config_form()
        
        self.assertIsNotNone(config_form)
        self.assertIn("splunk", config_form.available_servers)
        
        # Test feedback UI
        feedback_ui = FeedbackComponents()
        feedback_form = feedback_ui.render_feedback_form(self.test_incident_id)
        
        self.assertIsNotNone(feedback_form)
        self.assertIn("rating", feedback_form.fields)
        self.assertIn("comments", feedback_form.fields)
        
    # Test Case 13: Test Data Generators
    def test_mcp_test_data_generators(self):
        """Test that each MCP has working test data generators"""
        from test_data.mcp_test_generators import TestDataGenerators
        
        generators = TestDataGenerators()
        
        # Test Splunk data generator
        splunk_data = generators.generate_splunk_data("network_latency", count=10)
        self.assertEqual(len(splunk_data), 10)
        self.assertIn("latency", splunk_data[0])
        
        # Test Dynatrace data generator
        dynatrace_data = generators.generate_dynatrace_data("mq_metrics", count=5)
        self.assertEqual(len(dynatrace_data), 5)
        self.assertIn("queue_depth", dynatrace_data[0])
        
        # Test ServiceNow data generator
        servicenow_data = generators.generate_servicenow_data("incidents", count=3)
        self.assertEqual(len(servicenow_data), 3)
        self.assertIn("sys_id", servicenow_data[0])
        
    # Test Case 14: Real API Call Verification
    def test_real_api_calls_not_mocked(self):
        """Verify MCP servers make real API calls (with test data)"""
        from mcp_servers.api_verifier import APIVerifier
        
        verifier = APIVerifier()
        
        # Verify each MCP server endpoint
        endpoints = [
            ("splunk", "http://localhost:8080/splunk/search"),
            ("dynatrace", "http://localhost:8081/dynatrace/metrics"),
            ("servicenow", "http://localhost:8082/servicenow/incidents"),
            ("confluence", "http://localhost:8083/confluence/search"),
            ("gitlab", "http://localhost:8084/gitlab/search")
        ]
        
        for service, endpoint in endpoints:
            is_real = verifier.verify_real_api_call(endpoint)
            self.assertTrue(is_real, f"{service} should make real API calls")
            
    # Test Case 15: Feedback Loop Accuracy Improvement
    def test_feedback_improves_accuracy(self):
        """Test that feedback actually improves analysis accuracy"""
        from analytics.accuracy_tracker import AccuracyTracker
        
        tracker = AccuracyTracker()
        
        # Baseline accuracy
        baseline = tracker.get_accuracy_metrics("network_latency")
        
        # Add feedback
        for i in range(10):
            tracker.add_feedback_result({
                "incident_type": "network_latency",
                "predicted_cause": "DNS issue" if i < 7 else "Route issue",
                "actual_cause": "DNS issue",
                "correct": i < 7
            })
        
        # Check improved accuracy
        improved = tracker.get_accuracy_metrics("network_latency")
        
        self.assertGreater(improved["accuracy"], baseline["accuracy"])
        self.assertGreater(improved["confidence"], baseline["confidence"])


class TestMCPAsyncIntegration(unittest.TestCase):
    """Test async MCP operations"""
    
    def test_concurrent_mcp_calls(self):
        """Test that multiple MCP servers can be called concurrently"""
        from orchestration.async_orchestrator import AsyncMCPOrchestrator
        
        async def run_test():
            orchestrator = AsyncMCPOrchestrator()
            
            # Call all MCPs concurrently
            start_time = datetime.now()
            results = await orchestrator.gather_all_mcp_data({
                "incident_id": "INC-001",
                "type": "performance"
            })
            end_time = datetime.now()
            
            # Verify all results returned
            self.assertEqual(len(results), 5)  # 5 MCP servers
            
            # Verify concurrent execution (should take < 2s, not 5s)
            self.assertLess((end_time - start_time).total_seconds(), 2.0)
            
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main(verbosity=2)
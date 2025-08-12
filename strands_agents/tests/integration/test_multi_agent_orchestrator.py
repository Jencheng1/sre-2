"""
Integration tests for MultiAgentOrchestrator
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor
import time

# Import the orchestrator class
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator

class TestMultiAgentOrchestrator(unittest.TestCase):
    """Integration tests for MultiAgentOrchestrator"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('boto3.Session'):
            self.orchestrator = MultiAgentOrchestrator(region="us-east-1", test_mode=True)
    
    def test_initialization(self):
        """Test orchestrator initialization"""
        self.assertEqual(self.orchestrator.region, "us-east-1")
        self.assertTrue(self.orchestrator.test_mode)
        self.assertIsNotNone(self.orchestrator.logger)
        self.assertIsInstance(self.orchestrator.agents, dict)
        self.assertIsInstance(self.orchestrator.active_sessions, dict)
    
    def test_get_available_agents(self):
        """Test getting available agents"""
        agents = self.orchestrator.get_available_agents()
        
        # Should have at least splunk and dynatrace agents
        expected_agents = ["splunk", "dynatrace"]
        for agent in expected_agents:
            self.assertIn(agent, agents)
    
    def test_get_agent_capabilities(self):
        """Test getting capabilities of all agents"""
        capabilities = self.orchestrator.get_agent_capabilities()
        
        self.assertIsInstance(capabilities, dict)
        
        # Check that each agent has capabilities
        for agent_name, caps in capabilities.items():
            if "error" not in caps:  # Skip agents that failed to initialize
                self.assertIn("agent_name", caps)
                self.assertIn("tools", caps)
                self.assertIn("capabilities", caps)
    
    def test_health_check_all_agents(self):
        """Test health check for all agents"""
        health_status = self.orchestrator.health_check_all_agents()
        
        self.assertIsInstance(health_status, dict)
        self.assertGreater(len(health_status), 0)
        
        # Each agent should have health status
        for agent_name, health in health_status.items():
            self.assertIn("status", health)
            self.assertIn("timestamp", health)
            self.assertIn(health["status"], ["healthy", "unhealthy", "error"])
    
    def test_execute_single_agent_valid(self):
        """Test executing query on a single valid agent"""
        result = self.orchestrator.execute_single_agent(
            "splunk", 
            "Check network latency for production servers",
            {"priority": "high"}
        )
        
        if result.get("success"):
            self.assertIn("response", result)
            self.assertIn("agent", result)
            self.assertEqual(result["agent"], "splunk")
    
    def test_execute_single_agent_invalid(self):
        """Test executing query on invalid agent"""
        result = self.orchestrator.execute_single_agent(
            "invalid_agent",
            "Test query"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("available_agents", result)
    
    def test_execute_parallel_analysis(self):
        """Test parallel execution across multiple agents"""
        queries = {
            "splunk": "Analyze network performance issues in the last hour",
            "dynatrace": "Check for application performance problems"
        }
        
        result = self.orchestrator.execute_parallel_analysis(queries)
        
        self.assertTrue(result["success"])
        self.assertIn("results", result)
        self.assertIn("execution_time", result)
        
        results = result["results"]
        self.assertIn("splunk", results)
        self.assertIn("dynatrace", results)
    
    def test_execute_parallel_analysis_with_invalid_agent(self):
        """Test parallel execution with some invalid agents"""
        queries = {
            "splunk": "Valid query",
            "invalid_agent": "Invalid query",
            "dynatrace": "Another valid query"
        }
        
        result = self.orchestrator.execute_parallel_analysis(queries)
        
        self.assertTrue(result["success"])  # Overall operation succeeds
        results = result["results"]
        
        # Valid agents should succeed, invalid should fail
        self.assertFalse(results["invalid_agent"]["success"])
        # Other agents may succeed or fail depending on agent initialization
    
    def test_comprehensive_incident_analysis(self):
        """Test comprehensive incident analysis"""
        incident_description = "High network latency causing application timeouts in production environment"
        
        result = self.orchestrator.comprehensive_incident_analysis(incident_description)
        
        # Check result structure
        required_fields = [
            "incident_id", "incident_description", "analysis_timestamp",
            "agent_results", "synthesis", "recommendations", "confidence_score"
        ]
        
        for field in required_fields:
            self.assertIn(field, result)
        
        self.assertIn(incident_description, result["incident_description"])
        self.assertIsInstance(result["confidence_score"], (int, float))
        self.assertGreaterEqual(result["confidence_score"], 0)
        self.assertLessEqual(result["confidence_score"], 100)
    
    def test_generate_incident_queries_network_issue(self):
        """Test incident query generation for network issues"""
        incident = "Network connectivity problems affecting microservices communication"
        queries = self.orchestrator._generate_incident_queries(incident)
        
        self.assertIsInstance(queries, dict)
        
        # Network issues should generate appropriate queries
        if "splunk" in queries:
            splunk_query = queries["splunk"].lower()
            self.assertTrue(any(keyword in splunk_query for keyword in ["network", "latency", "connectivity"]))
    
    def test_generate_incident_queries_performance_issue(self):
        """Test incident query generation for performance issues"""
        incident = "Application performance degradation with slow response times"
        queries = self.orchestrator._generate_incident_queries(incident)
        
        if "dynatrace" in queries:
            dynatrace_query = queries["dynatrace"].lower()
            self.assertTrue(any(keyword in dynatrace_query for keyword in ["performance", "response", "traces"]))
    
    def test_synthesize_findings_no_results(self):
        """Test synthesis when no agent results available"""
        agent_results = {}
        synthesis = self.orchestrator._synthesize_findings(agent_results, "Test incident")
        
        self.assertIn("summary", synthesis)
        self.assertIn("No successful agent responses", synthesis["summary"])
    
    def test_synthesize_findings_with_results(self):
        """Test synthesis with successful agent results"""
        agent_results = {
            "splunk": {"success": True, "response": "Network anomalies detected"},
            "dynatrace": {"success": True, "response": "Performance degradation observed"}
        }
        
        synthesis = self.orchestrator._synthesize_findings(agent_results, "Test incident")
        
        self.assertIn("summary", synthesis)
        self.assertIn("key_findings", synthesis)
        self.assertIn("correlations", synthesis)
        self.assertGreater(len(synthesis["key_findings"]), 0)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        synthesis = {
            "summary": "Multiple systems affected",
            "key_findings": ["Network issues", "Performance problems"],
            "correlations": ["System-wide impact detected"]
        }
        
        recommendations = self.orchestrator._generate_recommendations(synthesis)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check recommendation structure
        for rec in recommendations:
            required_fields = ["priority", "action", "rationale"]
            for field in required_fields:
                self.assertIn(field, rec)
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation"""
        # All agents successful
        all_success = {
            "splunk": {"success": True},
            "dynatrace": {"success": True}
        }
        score_all = self.orchestrator._calculate_confidence_score(all_success)
        self.assertEqual(score_all, 95.0)  # Capped at 95%
        
        # Half agents successful
        half_success = {
            "splunk": {"success": True},
            "dynatrace": {"success": False}
        }
        score_half = self.orchestrator._calculate_confidence_score(half_success)
        self.assertEqual(score_half, 50.0)
        
        # No agents successful
        no_success = {
            "splunk": {"success": False},
            "dynatrace": {"success": False}
        }
        score_none = self.orchestrator._calculate_confidence_score(no_success)
        self.assertEqual(score_none, 0.0)
    
    def test_create_session(self):
        """Test session creation"""
        session_id = "test-session-001"
        result = self.orchestrator.create_session(session_id)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["session_id"], session_id)
        self.assertIn("available_agents", result)
        
        # Session should be stored
        self.assertIn(session_id, self.orchestrator.active_sessions)
    
    def test_create_session_with_specific_agents(self):
        """Test session creation with specific agents"""
        session_id = "test-session-002"
        agents = ["splunk"]
        
        result = self.orchestrator.create_session(session_id, agents)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["available_agents"], ["splunk"])
    
    def test_close_session_existing(self):
        """Test closing an existing session"""
        session_id = "test-session-003"
        
        # Create session first
        self.orchestrator.create_session(session_id)
        
        # Close session
        result = self.orchestrator.close_session(session_id)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["session_id"], session_id)
        
        # Session should be removed
        self.assertNotIn(session_id, self.orchestrator.active_sessions)
    
    def test_close_session_nonexistent(self):
        """Test closing a non-existent session"""
        result = self.orchestrator.close_session("nonexistent-session")
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("active_sessions", result)
    
    def test_concurrent_operations(self):
        """Test concurrent operations on orchestrator"""
        def perform_health_check():
            return self.orchestrator.health_check_all_agents()
        
        def perform_analysis():
            return self.orchestrator.comprehensive_incident_analysis("Test concurrent incident")
        
        # Execute operations concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(perform_health_check),
                executor.submit(perform_analysis),
                executor.submit(perform_health_check)
            ]
            
            results = [future.result() for future in futures]
        
        # All operations should complete successfully
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, dict)
    
    def test_session_isolation(self):
        """Test that sessions are isolated from each other"""
        session1 = "session-1"
        session2 = "session-2"
        
        # Create two sessions
        self.orchestrator.create_session(session1, ["splunk"])
        self.orchestrator.create_session(session2, ["dynatrace"])
        
        # Check isolation
        self.assertNotEqual(
            self.orchestrator.active_sessions[session1]["agents"],
            self.orchestrator.active_sessions[session2]["agents"]
        )
        
        # Close one session, other should remain
        self.orchestrator.close_session(session1)
        self.assertNotIn(session1, self.orchestrator.active_sessions)
        self.assertIn(session2, self.orchestrator.active_sessions)

if __name__ == '__main__':
    unittest.main()
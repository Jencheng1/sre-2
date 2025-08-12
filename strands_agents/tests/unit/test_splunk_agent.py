"""
Unit tests for SplunkStrandsAgent
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Import the agent class
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.splunk_agent import SplunkStrandsAgent

class TestSplunkStrandsAgent(unittest.TestCase):
    """Test cases for SplunkStrandsAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('boto3.Session'):
            self.agent = SplunkStrandsAgent(region="us-east-1", test_mode=True)
    
    def test_initialization(self):
        """Test Splunk agent initialization"""
        self.assertEqual(self.agent.agent_name, "splunk")
        self.assertTrue(self.agent.test_mode)
        self.assertIsNotNone(self.agent.logger)
    
    def test_system_prompt(self):
        """Test system prompt content"""
        prompt = self.agent._get_system_prompt()
        
        self.assertIn("Splunk monitoring specialist", prompt)
        self.assertIn("network latency analysis", prompt)
        self.assertIn("splunk_search", prompt)
        self.assertIn("splunk_metrics", prompt)
        self.assertIn("splunk_alerts", prompt)
    
    def test_get_specific_capabilities(self):
        """Test specific capabilities"""
        capabilities = self.agent._get_specific_capabilities()
        
        expected_capabilities = [
            "Network latency monitoring",
            "SPL query execution", 
            "Log analysis and correlation",
            "Network alert management"
        ]
        
        for capability in expected_capabilities:
            self.assertIn(capability, capabilities)
    
    def test_search_tool_test_mode(self):
        """Test search tool in test mode"""
        result = self.agent._search_tool("index=network_monitoring | stats count by host", "-1h", 50)
        
        self.assertTrue(result["success"])
        self.assertIn("query", result)
        self.assertIn("results", result)
        self.assertIn("count", result)
        self.assertIn("execution_time", result)
        self.assertLessEqual(result["count"], 50)  # Respects max_results
    
    def test_search_tool_generates_realistic_data(self):
        """Test that search tool generates realistic network data"""
        result = self.agent._search_tool("network_latency", "-2h", 20)
        
        self.assertTrue(result["success"])
        results = result["results"]
        
        # Check that results contain expected fields
        if results:
            first_result = results[0]
            self.assertIn("_time", first_result)
            self.assertIn("host", first_result)
            self.assertIn("event_type", first_result)
            self.assertIn("_raw", first_result)
    
    def test_metrics_tool_latency(self):
        """Test metrics tool for latency metrics"""
        result = self.agent._metrics_tool("prod-app-01", "latency")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["host"], "prod-app-01")
        self.assertEqual(result["metric"], "latency")
        self.assertIn("value", result)
        self.assertIn("unit", result)
        self.assertIn("status", result)
        self.assertEqual(result["unit"], "ms")
    
    def test_metrics_tool_packet_loss(self):
        """Test metrics tool for packet loss metrics"""
        result = self.agent._metrics_tool("*", "packet_loss")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["metric"], "packet_loss")
        self.assertEqual(result["unit"], "percent")
        self.assertIn("threshold", result)
    
    def test_metrics_tool_throughput(self):
        """Test metrics tool for throughput metrics"""
        result = self.agent._metrics_tool("network-gateway", "throughput")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["metric"], "throughput")
        self.assertEqual(result["unit"], "Mbps")
    
    def test_alerts_tool_all_severities(self):
        """Test alerts tool with all severities"""
        result = self.agent._alerts_tool("all", "-4h")
        
        self.assertTrue(result["success"])
        self.assertIn("alerts", result)
        self.assertIn("count", result)
        self.assertEqual(result["severity_filter"], "all")
        
        # Check alert structure
        alerts = result["alerts"]
        if alerts:
            alert = alerts[0]
            required_fields = ["id", "title", "severity", "status", "host_count", "duration"]
            for field in required_fields:
                self.assertIn(field, alert)
    
    def test_alerts_tool_filtered_severity(self):
        """Test alerts tool with specific severity filter"""
        result = self.agent._alerts_tool("critical", "-2h")
        
        self.assertTrue(result["success"])
        alerts = result["alerts"]
        
        # All returned alerts should be critical severity
        for alert in alerts:
            self.assertEqual(alert["severity"], "critical")
    
    def test_generate_raw_log_entries(self):
        """Test raw log entry generation"""
        event_types = ["network_latency", "packet_loss", "connection_timeout", "bandwidth_exceeded", "dns_resolution"]
        
        for event_type in event_types:
            raw_log = self.agent._generate_raw_log_entry(event_type)
            
            self.assertIsInstance(raw_log, str)
            self.assertIn(event_type.replace("_", " ") if "_" in event_type else event_type.upper(), raw_log.upper())
            # Check timestamp format is present
            current_year = str(datetime.now().year)
            self.assertIn(current_year, raw_log)
    
    def test_generate_alert_titles_by_severity(self):
        """Test alert title generation based on severity"""
        severities = ["critical", "high", "medium", "low"]
        
        for severity in severities:
            title = self.agent._generate_alert_title(severity)
            
            self.assertIsInstance(title, str)
            self.assertGreater(len(title), 10)  # Should be descriptive
            
            # Critical and high severity should mention specific thresholds
            if severity in ["critical", "high"]:
                self.assertTrue(any(word in title.lower() for word in ["lost", "exceeding", "failures", "timeout"]))
    
    def test_generate_alert_search_query(self):
        """Test alert search query generation"""
        query = self.agent._generate_alert_search_query("critical")
        
        self.assertIsInstance(query, str)
        self.assertIn("index=", query)
        self.assertIn("stats", query)
        # Critical queries should have stricter thresholds
        self.assertTrue("1000" in query or "10" in query)  # High latency or packet loss
    
    def test_search_tool_error_handling(self):
        """Test search tool error handling"""
        with patch.object(self.agent, '_generate_search_results', side_effect=Exception("Search failed")):
            result = self.agent._search_tool("test query")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_metrics_tool_error_handling(self):
        """Test metrics tool error handling"""
        with patch.object(self.agent, '_generate_metrics_data', side_effect=Exception("Metrics failed")):
            result = self.agent._metrics_tool("test-host", "latency")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_alerts_tool_error_handling(self):
        """Test alerts tool error handling"""
        with patch.object(self.agent, '_generate_alerts_data', side_effect=Exception("Alerts failed")):
            result = self.agent._alerts_tool("high")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_tools_creation(self):
        """Test that tools are created properly"""
        tools = self.agent._create_tools()
        
        self.assertEqual(len(tools), 3)  # Should have 3 tools
        
        # Tools should be properly configured (mock verification)
        # In real implementation, would verify tool names and descriptions
        self.assertIsNotNone(tools)
    
    def test_production_mode_placeholder_methods(self):
        """Test that production methods raise NotImplementedError"""
        # These should be implemented when integrating with real Splunk
        with self.assertRaises(NotImplementedError):
            self.agent._execute_real_splunk_search("test", "-1h", 10)
        
        with self.assertRaises(NotImplementedError):
            self.agent._get_real_splunk_metrics("host", "metric")
        
        with self.assertRaises(NotImplementedError):
            self.agent._get_real_splunk_alerts("high", "-1h")
    
    def test_data_consistency_across_calls(self):
        """Test that generated data is consistent in structure"""
        # Multiple calls should return consistent structure
        result1 = self.agent._search_tool("test query 1")
        result2 = self.agent._search_tool("test query 2")
        
        # Both should have same top-level structure
        self.assertEqual(set(result1.keys()), set(result2.keys()))
        
        # Results should have consistent structure
        if result1["results"] and result2["results"]:
            result1_fields = set(result1["results"][0].keys())
            result2_fields = set(result2["results"][0].keys())
            # Core fields should be consistent
            core_fields = {"_time", "host", "event_type", "_raw"}
            self.assertTrue(core_fields.issubset(result1_fields))
            self.assertTrue(core_fields.issubset(result2_fields))

if __name__ == '__main__':
    unittest.main()
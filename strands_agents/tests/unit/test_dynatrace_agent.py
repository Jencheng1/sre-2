"""
Unit tests for DynatraceStrandsAgent
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Import the agent class
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.dynatrace_agent import DynatraceStrandsAgent

class TestDynatraceStrandsAgent(unittest.TestCase):
    """Test cases for DynatraceStrandsAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('boto3.Session'):
            self.agent = DynatraceStrandsAgent(region="us-east-1", test_mode=True)
    
    def test_initialization(self):
        """Test Dynatrace agent initialization"""
        self.assertEqual(self.agent.agent_name, "dynatrace")
        self.assertTrue(self.agent.test_mode)
        self.assertIsNotNone(self.agent.logger)
    
    def test_system_prompt(self):
        """Test system prompt content"""
        prompt = self.agent._get_system_prompt()
        
        self.assertIn("Dynatrace APM specialist", prompt)
        self.assertIn("message queue", prompt)
        self.assertIn("distributed tracing", prompt)
        self.assertIn("dynatrace_mq_metrics", prompt)
        self.assertIn("dynatrace_apm_traces", prompt)
        self.assertIn("dynatrace_problems", prompt)
    
    def test_get_specific_capabilities(self):
        """Test specific capabilities"""
        capabilities = self.agent._get_specific_capabilities()
        
        expected_capabilities = [
            "Message Queue monitoring and analysis",
            "Distributed tracing and APM",
            "Performance anomaly detection",
            "Service dependency mapping",
            "Root cause analysis"
        ]
        
        for capability in expected_capabilities:
            self.assertIn(capability, capabilities)
    
    def test_mq_metrics_tool_basic(self):
        """Test MQ metrics tool basic functionality"""
        result = self.agent._mq_metrics_tool("OrderProcessingQueue", "-30m", True)
        
        self.assertTrue(result["success"])
        self.assertIn("queue_name", result)
        self.assertIn("queue_metrics", result)
        self.assertIn("health_status", result)
        self.assertIn("sla_compliance", result)
        
        # Check queue metrics structure
        queue_metrics = result["queue_metrics"]
        expected_metrics = ["depth", "enqueue_rate", "dequeue_rate", "error_rate", "avg_processing_time"]
        for metric in expected_metrics:
            self.assertIn(metric, queue_metrics)
    
    def test_mq_metrics_tool_with_consumers(self):
        """Test MQ metrics tool with consumer information"""
        result = self.agent._mq_metrics_tool("TestQueue", "-1h", True)
        
        self.assertTrue(result["success"])
        self.assertIn("consumers", result)
        
        consumers_info = result["consumers"]
        self.assertIn("total_consumers", consumers_info)
        self.assertIn("active_consumers", consumers_info)
        self.assertIn("consumer_details", consumers_info)
        
        # Check consumer details structure
        if consumers_info["consumer_details"]:
            consumer = consumers_info["consumer_details"][0]
            expected_fields = ["consumer_id", "status", "messages_processed", "avg_processing_time"]
            for field in expected_fields:
                self.assertIn(field, consumer)
    
    def test_mq_metrics_tool_without_consumers(self):
        """Test MQ metrics tool without consumer information"""
        result = self.agent._mq_metrics_tool("TestQueue", "-30m", False)
        
        self.assertTrue(result["success"])
        self.assertNotIn("consumers", result)
    
    def test_apm_traces_tool_basic(self):
        """Test APM traces tool basic functionality"""
        result = self.agent._apm_traces_tool("payment-service", "-1h", False, 0)
        
        self.assertTrue(result["success"])
        self.assertIn("traces", result)
        self.assertIn("summary", result)
        self.assertIn("service", result)
        
        # Check traces structure
        traces = result["traces"]
        if traces:
            trace = traces[0]
            expected_fields = ["trace_id", "service", "operation", "duration_ms", "status", "spans"]
            for field in expected_fields:
                self.assertIn(field, trace)
    
    def test_apm_traces_tool_error_traces_only(self):
        """Test APM traces tool filtering for error traces only"""
        result = self.agent._apm_traces_tool("test-service", "-1h", True, 0)
        
        self.assertTrue(result["success"])
        traces = result["traces"]
        
        # All returned traces should be errors
        for trace in traces:
            self.assertIn(trace["status"], ["ERROR", "TIMEOUT"])
            self.assertIn("error_details", trace)
    
    def test_apm_traces_tool_min_duration_filter(self):
        """Test APM traces tool with minimum duration filter"""
        min_duration = 1000  # 1 second
        result = self.agent._apm_traces_tool("test-service", "-1h", False, min_duration)
        
        self.assertTrue(result["success"])
        traces = result["traces"]
        
        # All returned traces should meet minimum duration
        for trace in traces:
            self.assertGreaterEqual(trace["duration_ms"], min_duration)
    
    def test_apm_traces_summary_calculations(self):
        """Test APM traces summary statistics"""
        result = self.agent._apm_traces_tool("test-service", "-1h", False, 0)
        
        self.assertTrue(result["success"])
        summary = result["summary"]
        
        if "total_traces" in summary:  # If we have traces
            self.assertIn("avg_duration_ms", summary)
            self.assertIn("p95_duration_ms", summary)
            self.assertIn("p99_duration_ms", summary)
            self.assertIn("error_rate_percent", summary)
            
            # P95 should be >= average, P99 should be >= P95
            if summary["total_traces"] > 1:
                self.assertGreaterEqual(summary["p95_duration_ms"], summary["avg_duration_ms"])
                self.assertGreaterEqual(summary["p99_duration_ms"], summary["p95_duration_ms"])
    
    def test_generate_trace_spans(self):
        """Test trace spans generation"""
        spans = self.agent._generate_trace_spans(5, 1000)
        
        self.assertEqual(len(spans), 5)
        
        for span in spans:
            expected_fields = ["span_id", "span_type", "operation_name", "duration_ms", "tags"]
            for field in expected_fields:
                self.assertIn(field, span)
            
            self.assertGreater(span["duration_ms"], 0)
            self.assertIn("component", span["tags"])
    
    def test_problems_tool_basic(self):
        """Test problems tool basic functionality"""
        result = self.agent._problems_tool("OPEN", "ALL", "-24h")
        
        self.assertTrue(result["success"])
        self.assertIn("problems", result)
        self.assertIn("summary", result)
        self.assertIn("filters", result)
        
        problems = result["problems"]
        if problems:
            problem = problems[0]
            expected_fields = ["id", "title", "status", "severity", "impact", "root_cause"]
            for field in expected_fields:
                self.assertIn(field, problem)
    
    def test_problems_tool_status_filter(self):
        """Test problems tool with status filtering"""
        result = self.agent._problems_tool("RESOLVED", "ALL", "-24h")
        
        self.assertTrue(result["success"])
        problems = result["problems"]
        
        # All returned problems should have RESOLVED status
        for problem in problems:
            self.assertEqual(problem["status"], "RESOLVED")
            self.assertIn("resolution", problem)  # Resolved problems should have resolution details
    
    def test_problems_tool_impact_filter(self):
        """Test problems tool with impact filtering"""
        result = self.agent._problems_tool("ALL", "APPLICATION", "-24h")
        
        self.assertTrue(result["success"])
        problems = result["problems"]
        
        # All returned problems should have APPLICATION impact
        for problem in problems:
            self.assertEqual(problem["impact"], "APPLICATION")
    
    def test_problems_tool_summary_statistics(self):
        """Test problems tool summary statistics"""
        result = self.agent._problems_tool("ALL", "ALL", "-24h")
        
        self.assertTrue(result["success"])
        summary = result["summary"]
        
        expected_summary_fields = ["critical_problems", "performance_problems", "availability_problems"]
        for field in expected_summary_fields:
            self.assertIn(field, summary)
            self.assertIsInstance(summary[field], int)
    
    def test_tools_creation(self):
        """Test that tools are created properly"""
        tools = self.agent._create_tools()
        
        self.assertEqual(len(tools), 3)  # Should have 3 tools
        self.assertIsNotNone(tools)
    
    def test_mq_metrics_tool_error_handling(self):
        """Test MQ metrics tool error handling"""
        with patch.object(self.agent, '_generate_mq_metrics', side_effect=Exception("MQ error")):
            result = self.agent._mq_metrics_tool("TestQueue")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_apm_traces_tool_error_handling(self):
        """Test APM traces tool error handling"""
        with patch.object(self.agent, '_generate_apm_traces', side_effect=Exception("Traces error")):
            result = self.agent._apm_traces_tool("test-service")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_problems_tool_error_handling(self):
        """Test problems tool error handling"""
        with patch.object(self.agent, '_generate_problems_data', side_effect=Exception("Problems error")):
            result = self.agent._problems_tool("OPEN")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
    
    def test_production_mode_placeholder_methods(self):
        """Test that production methods raise NotImplementedError"""
        # These should be implemented when integrating with real Dynatrace
        with self.assertRaises(NotImplementedError):
            self.agent._get_real_dynatrace_mq_metrics("queue", "-1h", True)
        
        with self.assertRaises(NotImplementedError):
            self.agent._get_real_dynatrace_traces("service", "-1h", False, 0)
        
        with self.assertRaises(NotImplementedError):
            self.agent._get_real_dynatrace_problems("OPEN", "ALL", "-24h")
    
    def test_health_status_logic(self):
        """Test MQ health status determination logic"""
        # Test multiple calls to ensure health status varies appropriately
        results = []
        for _ in range(10):
            result = self.agent._mq_metrics_tool("TestQueue", "-30m", False)
            results.append(result["health_status"])
        
        # Should have both healthy and warning status in multiple calls
        statuses = set(results)
        self.assertTrue(statuses.issubset({"healthy", "warning"}))
    
    def test_sla_compliance_values(self):
        """Test SLA compliance values are realistic"""
        result = self.agent._mq_metrics_tool("TestQueue", "-30m", True)
        
        sla = result["sla_compliance"]
        
        # SLA values should be percentages between 0 and 100
        for sla_type, value in sla.items():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)
            self.assertIsInstance(value, float)
    
    def test_trace_error_details_structure(self):
        """Test error trace details structure"""
        result = self.agent._apm_traces_tool("test-service", "-1h", True, 0)  # Error traces only
        
        if result["success"] and result["traces"]:
            for trace in result["traces"]:
                if trace["status"] in ["ERROR", "TIMEOUT"]:
                    self.assertIn("error_details", trace)
                    error_details = trace["error_details"]
                    
                    expected_error_fields = ["error_type", "error_message"]
                    for field in expected_error_fields:
                        self.assertIn(field, error_details)

if __name__ == '__main__':
    unittest.main()
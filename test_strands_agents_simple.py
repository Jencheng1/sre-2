#!/usr/bin/env python3
"""
Simple test runner for Strands Agents
Tests the core functionality without complex import dependencies
"""

import sys
import os
import json
from datetime import datetime
import unittest
from unittest.mock import Mock, patch

# Add strands_agents to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'strands_agents'))

def test_mock_strands_framework():
    """Test the mock Strands framework"""
    print("Testing mock Strands framework...")
    
    try:
        from mock_strands import Agent, create_custom_tool
        
        # Test Agent creation
        agent = Agent(
            model="claude-4-sonnet",
            system_prompt="Test agent",
            tools=[]
        )
        
        # Test agent execution
        response = agent("Test query")
        assert "Mock response" in response
        print("✓ Mock Agent works correctly")
        
        # Test tool creation
        def test_func(param1, param2="default"):
            return {"param1": param1, "param2": param2}
        
        tool = create_custom_tool(
            name="test_tool",
            description="Test tool",
            function=test_func,
            parameters={}
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "Test tool"
        print("✓ Mock tool creation works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Mock framework test failed: {e}")
        return False

def test_base_agent():
    """Test BaseStrandsAgent functionality"""
    print("\nTesting BaseStrandsAgent...")
    
    try:
        from base.base_agent import BaseStrandsAgent, StrandsToolFactory
        
        # Create test implementation
        class TestAgent(BaseStrandsAgent):
            def _get_system_prompt(self):
                return "Test agent prompt"
            
            def _create_tools(self):
                return []
            
            def _get_specific_capabilities(self):
                return ["testing"]
        
        # Test agent creation (mocking boto3)
        with patch('boto3.Session'):
            agent = TestAgent("test_agent", test_mode=True)
            
            assert agent.agent_name == "test_agent"
            assert agent.test_mode == True
            print("✓ BaseStrandsAgent initialization works")
            
            # Test capabilities
            capabilities = agent.get_capabilities()
            assert "testing" in capabilities["capabilities"]
            print("✓ Agent capabilities work correctly")
            
            # Test health check
            health = agent.health_check()
            assert "status" in health
            print("✓ Health check functionality works")
            
        return True
        
    except Exception as e:
        print(f"✗ BaseStrandsAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_splunk_agent():
    """Test SplunkStrandsAgent functionality"""
    print("\nTesting SplunkStrandsAgent...")
    
    try:
        from agents.splunk_agent import SplunkStrandsAgent
        
        # Test agent creation
        with patch('boto3.Session'):
            agent = SplunkStrandsAgent(test_mode=True)
            
            assert agent.agent_name == "splunk"
            print("✓ SplunkStrandsAgent initialization works")
            
            # Test search tool
            result = agent._search_tool("test query", "-1h", 10)
            assert result["success"] == True
            assert "results" in result
            print("✓ Splunk search tool works")
            
            # Test metrics tool
            result = agent._metrics_tool("test-host", "latency")
            assert result["success"] == True
            assert result["metric"] == "latency"
            print("✓ Splunk metrics tool works")
            
            # Test alerts tool
            result = agent._alerts_tool("high", "-4h")
            assert result["success"] == True
            assert "alerts" in result
            print("✓ Splunk alerts tool works")
            
        return True
        
    except Exception as e:
        print(f"✗ SplunkStrandsAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dynatrace_agent():
    """Test DynatraceStrandsAgent functionality"""
    print("\nTesting DynatraceStrandsAgent...")
    
    try:
        from agents.dynatrace_agent import DynatraceStrandsAgent
        
        # Test agent creation
        with patch('boto3.Session'):
            agent = DynatraceStrandsAgent(test_mode=True)
            
            assert agent.agent_name == "dynatrace"
            print("✓ DynatraceStrandsAgent initialization works")
            
            # Test MQ metrics tool
            result = agent._mq_metrics_tool("TestQueue", "-30m", True)
            assert result["success"] == True
            assert "queue_metrics" in result
            assert "consumers" in result
            print("✓ Dynatrace MQ metrics tool works")
            
            # Test APM traces tool
            result = agent._apm_traces_tool("test-service", "-1h", False, 0)
            assert result["success"] == True
            assert "traces" in result
            print("✓ Dynatrace APM traces tool works")
            
            # Test problems tool
            result = agent._problems_tool("OPEN", "ALL", "-24h")
            assert result["success"] == True
            assert "problems" in result
            print("✓ Dynatrace problems tool works")
            
        return True
        
    except Exception as e:
        print(f"✗ DynatraceStrandsAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_agent_orchestrator():
    """Test MultiAgentOrchestrator functionality"""
    print("\nTesting MultiAgentOrchestrator...")
    
    try:
        from orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator
        
        # Test orchestrator creation
        with patch('boto3.Session'):
            orchestrator = MultiAgentOrchestrator(test_mode=True)
            
            print("✓ MultiAgentOrchestrator initialization works")
            
            # Test getting available agents
            agents = orchestrator.get_available_agents()
            assert "splunk" in agents or "dynatrace" in agents  # At least one should be available
            print(f"✓ Available agents: {agents}")
            
            # Test health check
            health = orchestrator.health_check_all_agents()
            assert isinstance(health, dict)
            print("✓ Multi-agent health check works")
            
            # Test session creation
            result = orchestrator.create_session("test-session")
            assert result["success"] == True
            print("✓ Session creation works")
            
            # Test session closing
            result = orchestrator.close_session("test-session")
            assert result["success"] == True
            print("✓ Session management works")
            
        return True
        
    except Exception as e:
        print(f"✗ MultiAgentOrchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and return results"""
    print("=" * 60)
    print("AWS STRANDS AGENTS - SIMPLE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Mock Strands Framework", test_mock_strands_framework),
        ("Base Agent", test_base_agent),
        ("Splunk Agent", test_splunk_agent),
        ("Dynatrace Agent", test_dynatrace_agent),
        ("Multi-Agent Orchestrator", test_multi_agent_orchestrator)
    ]
    
    results = []
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name:<30} {status}")
    
    print(f"\nTotal Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {len(tests) - passed}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    
    # Save test results
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(tests),
        "passed": passed,
        "failed": len(tests) - passed,
        "success_rate": passed/len(tests)*100,
        "results": [{"test": name, "passed": success} for name, success in results]
    }
    
    with open("strands_agents_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: strands_agents_test_report.json")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
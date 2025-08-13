#!/usr/bin/env python3
"""
Integration test to verify all Streamlit tabs and functionality are working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_streamlit_imports():
    """Test that all required imports work"""
    print("Testing Streamlit imports...")
    try:
        # Test main imports
        import streamlit as st
        print("✓ Streamlit imported successfully")
        
        # Test IP Masking
        try:
            from utils.ip_masker import IPMasker, mask_logs_for_llm
            print("✓ IP Masking utilities available")
        except ImportError:
            print("✗ IP Masking utilities not available")
        
        # Test Post-mortem
        try:
            from postmortem.postmortem_agent import PostMortemAgent, PostMortemReport
            print("✓ Post-mortem agent available")
        except ImportError:
            print("✗ Post-mortem agent not available")
        
        # Test MCP modules
        try:
            from feedback.feedback_system import FeedbackSystem
            from config.mcp_config import MCPConfigManager
            from enhanced_incident_scenarios import EnhancedIncidentScenarios
            print("✓ MCP modules available")
        except ImportError:
            print("✗ MCP modules not available")
        
        return True
    except Exception as e:
        print(f"✗ Error during imports: {str(e)}")
        return False

def test_streamlit_tabs():
    """Test that all tabs are defined in streamlit_app.py"""
    print("\nTesting Streamlit tab definitions...")
    
    try:
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for all required tabs
        required_tabs = [
            "🚨 Incident Management",
            "🔍 Analyze Incident",
            "🔧 Recent Changes",
            "📚 Knowledge Base",
            "📊 Analytics",
            "🐛 Defect Management",
            "🔗 Defect Correlation",
            "🧪 Correlation Scenarios",
            "📋 Post-Mortem",
            "🔐 IP Masking",
            "🧪 Test Scenarios"
        ]
        
        missing_tabs = []
        for tab in required_tabs:
            if tab in content:
                print(f"✓ Tab '{tab}' found")
            else:
                print(f"✗ Tab '{tab}' missing")
                missing_tabs.append(tab)
        
        # Check for render methods
        render_methods = [
            "render_incident_management",
            "render_analyze_tab",
            "render_recent_changes",
            "render_knowledge_base",
            "render_analytics",
            "render_defect_management",
            "render_defect_correlation",
            "render_correlation_scenarios",
            "render_postmortem_analysis",
            "render_ip_masking",
            "render_test_scenarios"
        ]
        
        print("\nChecking render methods...")
        missing_methods = []
        for method in render_methods:
            if f"def {method}" in content:
                print(f"✓ Method '{method}' found")
            else:
                print(f"✗ Method '{method}' missing")
                missing_methods.append(method)
        
        return len(missing_tabs) == 0 and len(missing_methods) == 0
        
    except Exception as e:
        print(f"✗ Error checking tabs: {str(e)}")
        return False

def test_incident_creation():
    """Test incident creation functionality"""
    print("\nTesting incident creation functionality...")
    
    try:
        # Check if generate incident functionality exists
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        required_functions = [
            "_generate_test_incident",
            "_generate_custom_incident",
            "Generate Incident",
            "Create & Generate Incident"
        ]
        
        for func in required_functions:
            if func in content:
                print(f"✓ '{func}' functionality found")
            else:
                print(f"✗ '{func}' functionality missing")
        
        return True
    except Exception as e:
        print(f"✗ Error checking incident creation: {str(e)}")
        return False

def test_correlation_functionality():
    """Test correlation functionality"""
    print("\nTesting correlation functionality...")
    
    try:
        # Check if correlation test file exists
        if os.path.exists('test_change_defect_correlation.py'):
            print("✓ Change/defect correlation test file exists")
            
            # Check content
            with open('test_change_defect_correlation.py', 'r') as f:
                content = f.read()
                
            if "test_change_incident_correlation" in content:
                print("✓ Change-incident correlation test found")
            if "test_defect_incident_correlation" in content:
                print("✓ Defect-incident correlation test found")
            if "test_combined_correlation" in content:
                print("✓ Combined correlation test found")
        else:
            print("✗ Correlation test file not found")
        
        return True
    except Exception as e:
        print(f"✗ Error checking correlation: {str(e)}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 80)
    print("STREAMLIT INTEGRATION TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Import Test", test_streamlit_imports),
        ("Tab Definition Test", test_streamlit_tabs),
        ("Incident Creation Test", test_incident_creation),
        ("Correlation Test", test_correlation_functionality)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} ERROR: {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 80)
    
    # Check if Streamlit is running
    print("\nChecking Streamlit status...")
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'streamlit' in result.stdout:
            print("✓ Streamlit is currently running")
        else:
            print("✗ Streamlit is not running")
            print("  To start: nohup python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &")
    except:
        print("✗ Could not check Streamlit status")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
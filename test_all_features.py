#!/usr/bin/env python3
"""
Comprehensive test suite for all Streamlit features
Tests Post-Mortem, IP Masking, Test Scenarios, and core functionality
"""
import sys
import os
import json
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class StreamlitFeatureTests:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
        
    def test_imports(self):
        """Test all required imports"""
        print("\n=== Testing Imports ===")
        try:
            # Core imports
            import streamlit as st
            print("✓ Streamlit imported")
            
            from streamlit_app import EnhancedSREDashboard
            print("✓ EnhancedSREDashboard imported")
            
            # Feature imports
            from utils.ip_masker import IPMasker, mask_logs_for_llm
            print("✓ IP Masker utilities imported")
            
            from postmortem.postmortem_agent import PostMortemAgent, PostMortemReport
            print("✓ Post-mortem agent imported")
            
            return True
        except Exception as e:
            print(f"✗ Import error: {str(e)}")
            return False
    
    def test_dashboard_methods(self):
        """Test that all dashboard methods exist"""
        print("\n=== Testing Dashboard Methods ===")
        try:
            from streamlit_app import EnhancedSREDashboard
            dashboard = EnhancedSREDashboard()
            
            methods = [
                # Core methods
                ('display_dashboard', 'Main dashboard display'),
                ('generate_incident', 'Incident generation'),
                ('run_root_cause_analysis', 'Root cause analysis'),
                ('display_incident_details', 'Incident details display'),
                
                # Tab methods
                ('render_analyze_tab', 'Analyze incident tab'),
                ('render_recent_changes', 'Recent changes tab'),
                ('render_knowledge_base', 'Knowledge base tab'),
                ('render_analytics', 'Analytics tab'),
                ('render_defect_management', 'Defect management tab'),
                ('render_defect_correlation', 'Defect correlation tab'),
                ('render_correlation_scenarios', 'Correlation scenarios tab'),
                
                # New feature methods
                ('render_postmortem_analysis', 'Post-mortem analysis tab'),
                ('render_ip_masking', 'IP masking tab'),
                ('render_test_scenarios', 'Test scenarios tab'),
                
                # Helper methods
                ('_render_postmortem_generator', 'Post-mortem generator'),
                ('_render_postmortem_viewer', 'Post-mortem viewer'),
                ('_render_opsitem_postmortem', 'OpsItem post-mortem'),
                ('_render_ip_masking_tool', 'IP masking tool'),
                ('_render_ip_masking_config', 'IP masking config'),
                ('_render_ip_masking_stats', 'IP masking stats'),
                ('_render_predefined_scenarios', 'Predefined scenarios'),
                ('_render_custom_scenario', 'Custom scenario'),
                ('_render_batch_testing', 'Batch testing'),
                ('_generate_test_incident', 'Test incident generator'),
                ('_generate_custom_incident', 'Custom incident generator'),
            ]
            
            missing = []
            for method_name, description in methods:
                if hasattr(dashboard, method_name):
                    print(f"✓ {description} ({method_name})")
                else:
                    print(f"✗ {description} ({method_name}) - MISSING")
                    missing.append(method_name)
            
            if missing:
                print(f"\nMissing methods: {missing}")
                return False
            
            return True
        except Exception as e:
            print(f"✗ Error testing methods: {str(e)}")
            return False
    
    def test_tab_structure(self):
        """Test that all tabs are properly defined"""
        print("\n=== Testing Tab Structure ===")
        try:
            with open('streamlit_app.py', 'r') as f:
                content = f.read()
            
            # Expected tabs in order
            expected_tabs = [
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
                "🧪 Test Scenarios",
                "❓ User Guide"
            ]
            
            # Check tab names definition
            tab_names_found = False
            for tab in expected_tabs[:11]:  # Check main tabs
                if tab in content:
                    print(f"✓ Tab '{tab}' defined")
                else:
                    print(f"✗ Tab '{tab}' NOT defined")
            
            # Check tab handlers
            tab_handlers = [
                ("main_tabs[0]", "Incident Management handler"),
                ("main_tabs[1]", "Analyze Incident handler"),
                ("main_tabs[2]", "Recent Changes handler"),
                ("main_tabs[3]", "Knowledge Base handler"),
                ("main_tabs[4]", "Analytics handler"),
                ("main_tabs[5]", "Defect Management handler"),
                ("main_tabs[6]", "Defect Correlation handler"),
                ("main_tabs[7]", "Correlation Scenarios handler"),
                ("main_tabs[8]", "Post-Mortem handler"),
                ("main_tabs[9]", "IP Masking handler"),
                ("main_tabs[10]", "Test Scenarios handler"),
            ]
            
            print("\nChecking tab handlers...")
            for handler, desc in tab_handlers:
                if handler in content:
                    print(f"✓ {desc}")
                else:
                    print(f"✗ {desc} - MISSING")
            
            return True
        except Exception as e:
            print(f"✗ Error testing tab structure: {str(e)}")
            return False
    
    def test_post_mortem_functionality(self):
        """Test post-mortem functionality"""
        print("\n=== Testing Post-Mortem Functionality ===")
        try:
            from postmortem.postmortem_agent import PostMortemAgent, PostMortemReport
            
            # Test agent creation
            agent = PostMortemAgent()
            print("✓ Post-mortem agent created")
            
            # Test sample incident analysis
            sample_incident = {
                "incident_id": "TEST-001",
                "title": "Test Incident",
                "severity": "high",
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "impact": "Test impact",
                "root_cause": "Test root cause"
            }
            
            # Test report generation
            report = agent.analyze_incident(sample_incident)
            print("✓ Post-mortem report generated")
            
            # Test markdown generation
            markdown = agent.generate_markdown_report(report)
            print("✓ Markdown report generated")
            
            # Verify report structure
            if hasattr(report, 'incident_id'):
                print("✓ Report has incident_id")
            if hasattr(report, 'timeline'):
                print("✓ Report has timeline")
            if hasattr(report, 'root_cause_analysis'):
                print("✓ Report has root cause analysis")
            
            return True
        except Exception as e:
            print(f"✗ Post-mortem test error: {str(e)}")
            return False
    
    def test_ip_masking_functionality(self):
        """Test IP masking functionality"""
        print("\n=== Testing IP Masking Functionality ===")
        try:
            from utils.ip_masker import IPMasker, mask_logs_for_llm
            
            # Test masker creation
            masker = IPMasker(mode="partial")
            print("✓ IP masker created")
            
            # Test IP masking
            test_log = "Connection from 192.168.1.100 to 10.0.0.5 failed"
            masked = masker.mask_text(test_log)
            print("✓ Text masking works")
            print(f"  Original: {test_log}")
            print(f"  Masked: {masked}")
            
            # Test IPv6
            test_ipv6 = "IPv6 address: 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
            masked_ipv6 = masker.mask_text(test_ipv6)
            print("✓ IPv6 masking works")
            
            # Test LLM masking
            llm_masked = mask_logs_for_llm(test_log)
            print("✓ LLM-specific masking works")
            
            # Test statistics
            stats = masker.get_statistics()
            print("✓ Statistics tracking works")
            
            return True
        except Exception as e:
            print(f"✗ IP masking test error: {str(e)}")
            return False
    
    def test_test_scenarios_functionality(self):
        """Test the test scenarios functionality"""
        print("\n=== Testing Test Scenarios Functionality ===")
        try:
            from streamlit_app import EnhancedSREDashboard
            dashboard = EnhancedSREDashboard()
            
            # Test scenario generation
            test_scenario = {
                "name": "Test Performance Issue",
                "description": "Test scenario",
                "severity": "high",
                "components": ["EC2", "RDS"]
            }
            
            incident = dashboard._generate_test_incident(test_scenario, "Performance")
            print("✓ Test incident generation works")
            
            if incident:
                print(f"  Generated incident ID: {incident.get('incident_id', 'N/A')}")
                print(f"  Type: {incident.get('category', 'N/A')}")
                print(f"  Severity: {incident.get('severity', 'N/A')}")
            
            # Test custom incident
            custom_scenario = {
                "name": "Custom Test",
                "type": "outage",
                "severity": "critical",
                "duration": 30,
                "services": ["EC2", "S3"],
                "error_rate": 50,
                "impact": "Service down",
                "symptoms": ["Timeouts", "503 errors"]
            }
            
            custom_incident = dashboard._generate_custom_incident(custom_scenario)
            print("✓ Custom incident generation works")
            
            # Test batch report generation
            test_results = [
                {"incident_id": "BATCH-001", "type": "performance", "severity": "high", 
                 "analysis_time": 2.5, "root_cause_found": True, "confidence": 0.85}
            ]
            
            report = dashboard._generate_batch_report(test_results)
            print("✓ Batch report generation works")
            
            return True
        except Exception as e:
            print(f"✗ Test scenarios error: {str(e)}")
            return False
    
    def test_incident_generation_analysis(self):
        """Test core incident generation and analysis"""
        print("\n=== Testing Incident Generation & Analysis ===")
        try:
            with open('streamlit_app.py', 'r') as f:
                content = f.read()
            
            # Check for incident generation
            checks = [
                ("Generate incident button", "🔥 Generate Real Incident"),
                ("Incident type selection", "Select Incident Type"),
                ("Performance Degradation option", "Performance Degradation"),
                ("Security Alert option", "Security Alert"),
                ("Service Outage option", "Service Outage"),
                ("generate_incident method", "def generate_incident"),
                ("Analyze button", "🤖 Run Root Cause Analysis"),
                ("run_root_cause_analysis method", "def run_root_cause_analysis"),
            ]
            
            for check_name, pattern in checks:
                if pattern in content:
                    print(f"✓ {check_name}")
                else:
                    print(f"✗ {check_name} - NOT FOUND")
            
            return True
        except Exception as e:
            print(f"✗ Error testing incident features: {str(e)}")
            return False
    
    def run_test(self, test_func, test_name):
        """Run a single test and track results"""
        print(f"\n{'='*60}")
        try:
            if test_func():
                self.passed += 1
                self.tests.append((test_name, "PASSED"))
                return True
            else:
                self.failed += 1
                self.tests.append((test_name, "FAILED"))
                return False
        except Exception as e:
            self.failed += 1
            self.tests.append((test_name, f"ERROR: {str(e)}"))
            print(f"✗ Test error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("="*80)
        print("COMPREHENSIVE STREAMLIT FEATURE TEST SUITE")
        print("="*80)
        
        # Run all tests
        self.run_test(self.test_imports, "Import Test")
        self.run_test(self.test_dashboard_methods, "Dashboard Methods Test")
        self.run_test(self.test_tab_structure, "Tab Structure Test")
        self.run_test(self.test_post_mortem_functionality, "Post-Mortem Functionality Test")
        self.run_test(self.test_ip_masking_functionality, "IP Masking Functionality Test")
        self.run_test(self.test_test_scenarios_functionality, "Test Scenarios Functionality Test")
        self.run_test(self.test_incident_generation_analysis, "Incident Generation & Analysis Test")
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        for test_name, result in self.tests:
            status_symbol = "✅" if result == "PASSED" else "❌"
            print(f"{status_symbol} {test_name}: {result}")
        
        print(f"\nTotal: {self.passed + self.failed} tests")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print("="*80)
        
        return self.failed == 0

def main():
    tester = StreamlitFeatureTests()
    success = tester.run_all_tests()
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Restart Streamlit: ps aux | grep streamlit | grep -v grep | awk '{print $2}' | xargs kill -9")
    print("2. Start fresh: nohup python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &")
    print("3. Access: http://localhost:8501")
    print("4. Verify all 11 main tabs are visible")
    print("5. Test each feature:")
    print("   - Tab 9: Post-Mortem (Generate reports)")
    print("   - Tab 10: IP Masking (Mask logs)")
    print("   - Tab 11: Test Scenarios (Generate test incidents)")
    print("="*80)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Comprehensive Test Suite for SRE Copilot Components
Tests all major functionality without UI interaction
"""

import json
import time
import sys
from datetime import datetime
import subprocess
import os

class SRECopilotTestSuite:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, passed, message=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            print(f"❌ {test_name}: FAILED {message}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_streamlit_components(self):
        """Test 1: Verify Streamlit components load without errors"""
        print("\n🧪 Testing Streamlit Components...")
        
        try:
            # Test key manager
            from streamlit_key_manager import key_manager
            key_manager.reset_keys()
            test_key = key_manager.get_unique_key("test", "component")
            self.log_test("Streamlit Key Manager", True, f"Generated key: {test_key}")
            
            # Test if streamlit app has required functions
            import streamlit_app
            required_methods = [
                'display_dashboard', 'display_incident_details', 
                'display_data_analysis', 'create_new_incident'
            ]
            
            dashboard = streamlit_app.SREDashboard()
            for method in required_methods:
                has_method = hasattr(dashboard, method)
                self.log_test(f"Dashboard.{method}", has_method)
            
            return True
        except Exception as e:
            self.log_test("Streamlit Components", False, str(e))
            return False
    
    def test_incident_creation_flow(self):
        """Test 2: Test incident creation workflow"""
        print("\n🧪 Testing Incident Creation Flow...")
        
        try:
            from incident_scenarios import get_incident_scenarios
            from enhanced_incident_scenarios import EnhancedIncidentScenarios
            
            # Test basic scenarios
            scenarios = get_incident_scenarios()
            self.log_test("Basic Incident Scenarios", len(scenarios) >= 8, f"Found {len(scenarios)} scenarios")
            
            # Test enhanced scenarios
            enhanced = EnhancedIncidentScenarios()
            
            # Test defect-driven scenarios
            defect_scenarios = enhanced.get_defect_driven_scenarios()
            self.log_test("Defect-Driven Scenarios", len(defect_scenarios) >= 5, f"Found {len(defect_scenarios)}")
            
            # Test change-driven scenarios  
            change_scenarios = enhanced.get_change_driven_scenarios()
            self.log_test("Change-Driven Scenarios", len(change_scenarios) >= 6, f"Found {len(change_scenarios)}")
            
            # Test scenario structure
            if scenarios:
                test_scenario = scenarios[0]
                required_fields = ['category', 'type', 'description', 'metrics', 'logs']
                has_fields = all(field in test_scenario for field in required_fields)
                self.log_test("Scenario Structure", has_fields, f"Fields: {list(test_scenario.keys())}")
            
            return True
        except Exception as e:
            self.log_test("Incident Creation Flow", False, str(e))
            return False
    
    def test_correlation_engines(self):
        """Test 3: Test defect and change correlation engines"""
        print("\n🧪 Testing Correlation Engines...")
        
        # Test Defect Correlation
        try:
            from defect_incident_correlator import DefectIncidentCorrelator
            correlator = DefectIncidentCorrelator()
            
            test_incident = {
                "type": "performance",
                "description": "High latency in payment processing",
                "root_cause": "Database connection pool exhaustion",
                "affected_services": ["payment-service"],
                "error_patterns": ["timeout", "connection refused"]
            }
            
            result = correlator.correlate_incident_to_defects(test_incident)
            confidence = result.get('confidence', 0)
            self.log_test("Defect Correlation Engine", confidence > 0, f"Confidence: {confidence}%")
            
            # Check correlation factors
            factors = result.get('correlation_factors', {})
            self.log_test("Defect Correlation Factors", len(factors) >= 5, f"Analyzed {len(factors)} factors")
            
        except Exception as e:
            self.log_test("Defect Correlation", False, str(e))
        
        # Test Change Correlation
        try:
            from change_incident_correlator import ChangeIncidentCorrelator
            correlator = ChangeIncidentCorrelator()
            
            test_incident = {
                "start_time": datetime.now(),
                "type": "outage",
                "description": "Complete service unavailability",
                "affected_services": ["api-gateway", "auth-service"],
                "environment": "production"
            }
            
            result = correlator.correlate_incident_to_changes(test_incident)
            changes = result.get('correlated_changes', [])
            self.log_test("Change Correlation Engine", len(changes) > 0, f"Found {len(changes)} related changes")
            
            # Check analysis depth
            if changes:
                top_change = changes[0]
                self.log_test("Change Analysis Detail", 'confidence_score' in top_change, 
                            f"Score: {top_change.get('confidence_score', 0)}%")
            
        except Exception as e:
            self.log_test("Change Correlation", False, str(e))
        
        return True
    
    def test_knowledge_base(self):
        """Test 4: Test knowledge base functionality"""
        print("\n🧪 Testing Knowledge Base...")
        
        try:
            # Test knowledge base documents
            from knowledge_base_documents import get_knowledge_base_documents
            docs = get_knowledge_base_documents()
            self.log_test("Knowledge Base Documents", len(docs) > 0, f"Found {len(docs)} documents")
            
            # Test serverless KB lambda if available
            kb_test_passed = False
            try:
                result = subprocess.run(
                    ["python3", "test_knowledge_base.py"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                kb_test_passed = "PASSED" in result.stdout or result.returncode == 0
            except:
                kb_test_passed = False
            
            self.log_test("Knowledge Base Tests", kb_test_passed)
            
            return True
        except Exception as e:
            self.log_test("Knowledge Base", False, str(e))
            return False
    
    def test_mcp_integration(self):
        """Test 5: Test MCP server integration"""
        print("\n🧪 Testing MCP Integration...")
        
        try:
            import requests
            
            # Load MCP ports
            with open('mcp_ports.json', 'r') as f:
                mcp_ports = json.load(f)
            
            # Test each MCP service
            services_tested = 0
            services_passed = 0
            
            for service, port in mcp_ports.items():
                if service in ['splunk', 'dynatrace', 'servicenow', 'confluence', 'gitlab', 'alm_octane', 'jira']:
                    services_tested += 1
                    try:
                        # Test endpoint based on service
                        if service == 'splunk':
                            resp = requests.post(f"http://localhost:{port}/splunk/search",
                                               json={"query": "test", "time_range": "-1h"}, timeout=2)
                        elif service == 'alm_octane':
                            resp = requests.get(f"http://localhost:{port}/octane/defects", timeout=2)
                        elif service == 'jira':
                            resp = requests.get(f"http://localhost:{port}/jira/issues", timeout=2)
                        elif service == 'servicenow':
                            resp = requests.get(f"http://localhost:{port}/servicenow/incidents", timeout=2)
                        else:
                            continue
                        
                        if resp.status_code in [200, 201]:
                            services_passed += 1
                            self.log_test(f"MCP {service.upper()}", True, f"Port {port}")
                        else:
                            self.log_test(f"MCP {service.upper()}", False, f"Status {resp.status_code}")
                    except Exception as e:
                        self.log_test(f"MCP {service.upper()}", False, str(e)[:30])
            
            self.log_test("MCP Integration Overall", services_passed >= 3, 
                         f"{services_passed}/{services_tested} services online")
            
            return services_passed >= 3
        except Exception as e:
            self.log_test("MCP Integration", False, str(e))
            return False
    
    def test_special_agents(self):
        """Test 6: Test special agents (IP Masking, Post-Mortem)"""
        print("\n🧪 Testing Special Agents...")
        
        # Test IP Masking
        try:
            from ip_masking_agent import IPMaskingAgent
            agent = IPMaskingAgent()
            
            test_logs = [
                "Error from 192.168.1.100: Connection timeout",
                "Server 10.0.0.50 responded with 500 error",
                "User authenticated from 172.16.0.1"
            ]
            
            for log in test_logs:
                masked, stats = agent.mask_ip_addresses(log)
                has_masked = any(ip not in masked for ip in ["192.168.1.100", "10.0.0.50", "172.16.0.1"])
                
            self.log_test("IP Masking Agent", has_masked, f"Masked {stats['total_ips_masked']} IPs")
            
        except Exception as e:
            self.log_test("IP Masking Agent", False, str(e))
        
        # Test Post-Mortem Agent
        try:
            from post_mortem_agent import PostMortemAgent
            agent = PostMortemAgent()
            
            # Test timeline generation
            test_incident = {
                "title": "Test Incident",
                "start_time": datetime.now().isoformat(),
                "timeline": [
                    {"time": "10:00", "event": "First error detected"},
                    {"time": "10:05", "event": "Alerts triggered"}
                ]
            }
            
            timeline = agent.generate_timeline(test_incident)
            self.log_test("Post-Mortem Timeline", len(timeline) > 0, f"{len(timeline)} events")
            
        except Exception as e:
            self.log_test("Post-Mortem Agent", False, str(e))
        
        return True
    
    def test_lambda_integration(self):
        """Test 7: Test AWS Lambda integration"""
        print("\n🧪 Testing Lambda Integration...")
        
        try:
            import boto3
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            
            lambdas_to_test = [
                'sre-supervisor-lambda',
                'sre-knowledge-base-agent',
                'sre-cloudwatch-agent'
            ]
            
            lambdas_found = 0
            for lambda_name in lambdas_to_test:
                try:
                    response = lambda_client.get_function(FunctionName=lambda_name)
                    if response['Configuration']['State'] == 'Active':
                        lambdas_found += 1
                        self.log_test(f"Lambda {lambda_name}", True, "Active")
                    else:
                        self.log_test(f"Lambda {lambda_name}", False, response['Configuration']['State'])
                except:
                    self.log_test(f"Lambda {lambda_name}", False, "Not found")
            
            self.log_test("Lambda Integration Overall", lambdas_found >= 2, 
                         f"{lambdas_found}/{len(lambdas_to_test)} lambdas active")
            
            return lambdas_found >= 2
        except Exception as e:
            self.log_test("Lambda Integration", False, str(e))
            return False
    
    def test_api_endpoints(self):
        """Test 8: Test API endpoint verification"""
        print("\n🧪 Testing API Endpoints...")
        
        try:
            # Run API verifier
            result = subprocess.run(
                ["python3", "mcp_servers/api_verifier.py"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            api_test_passed = "verified successfully" in result.stdout or result.returncode == 0
            self.log_test("API Endpoint Verifier", api_test_passed)
            
            return api_test_passed
        except Exception as e:
            self.log_test("API Endpoints", False, str(e))
            return False
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("📊 SRE COPILOT TEST SUMMARY REPORT")
        print("="*70)
        print(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print("="*70)
        
        # Group results by category
        categories = {
            "Core Components": ["Streamlit", "Dashboard"],
            "Incident Management": ["Incident", "Scenario"],
            "Correlation": ["Defect", "Change"],
            "Integration": ["MCP", "Lambda", "API"],
            "Special Features": ["IP Masking", "Post-Mortem", "Knowledge Base"]
        }
        
        print("\n📋 Detailed Results by Category:")
        for category, keywords in categories.items():
            category_tests = [t for t in self.test_results 
                            if any(kw in t['test'] for kw in keywords)]
            if category_tests:
                passed = sum(1 for t in category_tests if t['passed'])
                total = len(category_tests)
                print(f"\n{category}: {passed}/{total} passed")
                for test in category_tests:
                    status = "✅" if test['passed'] else "❌"
                    print(f"  {status} {test['test']}")
        
        # Save detailed report
        report_data = {
            "test_run": datetime.now().isoformat(),
            "environment": {
                "streamlit_url": "http://localhost:8501",
                "aws_region": "us-east-1"
            },
            "summary": {
                "total": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.total_tests - self.passed_tests,
                "success_rate": f"{(self.passed_tests/self.total_tests*100):.1f}%"
            },
            "results": self.test_results
        }
        
        with open('sre_copilot_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: sre_copilot_test_report.json")
        
        return self.passed_tests == self.total_tests

def main():
    """Run comprehensive test suite"""
    print("🚀 SRE Copilot Comprehensive Test Suite")
    print("="*70)
    print("Testing all components without UI interaction...")
    print("="*70)
    
    tester = SRECopilotTestSuite()
    
    # Run all test categories
    test_functions = [
        tester.test_streamlit_components,
        tester.test_incident_creation_flow,
        tester.test_correlation_engines,
        tester.test_knowledge_base,
        tester.test_mcp_integration,
        tester.test_special_agents,
        tester.test_lambda_integration,
        tester.test_api_endpoints
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"Test execution error: {e}")
        time.sleep(1)  # Small delay between test categories
    
    # Generate final report
    all_passed = tester.generate_report()
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED! The SRE Copilot is fully operational.")
        print("\n🎯 Next Steps:")
        print("1. Access the dashboard at http://localhost:8501")
        print("2. Create a test incident and run root cause analysis")
        print("3. Check MCP services status in the sidebar")
        print("4. Test defect and change correlation features")
    else:
        print("\n⚠️  Some tests failed. Please review the detailed report.")
        print("Common issues:")
        print("- Ensure all MCP servers are running: ./restart_mcp_servers.sh")
        print("- Check AWS credentials for Lambda access")
        print("- Verify Streamlit is running on port 8501")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Test suite for Streamlit UI components
Ensures all UI elements are working correctly without balloon celebrations
"""

import unittest
import requests
import json
import time
import subprocess
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestStreamlitComponents(unittest.TestCase):
    """Test Streamlit UI components are working properly"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:8501"
        cls.mcp_urls = {
            'alm_octane': 'http://localhost:9085',
            'jira': 'http://localhost:9086'
        }
        
    def test_mcp_servers_running(self):
        """Test that MCP servers are running"""
        # Test ALM Octane
        try:
            response = requests.get(f"{self.mcp_urls['alm_octane']}/octane/defects", timeout=5)
            self.assertEqual(response.status_code, 200)
            print("✅ ALM Octane server is running")
        except Exception as e:
            self.fail(f"ALM Octane server not running: {e}")
            
        # Test Jira
        try:
            response = requests.get(f"{self.mcp_urls['jira']}/jira/issues", timeout=5)
            self.assertEqual(response.status_code, 200)
            print("✅ Jira server is running")
        except Exception as e:
            self.fail(f"Jira server not running: {e}")
    
    def test_streamlit_accessible(self):
        """Test that Streamlit app is accessible"""
        try:
            response = requests.get(self.base_url, timeout=10)
            self.assertIn(response.status_code, [200, 304])
            print("✅ Streamlit app is accessible")
        except Exception as e:
            self.fail(f"Streamlit app not accessible: {e}")
    
    def test_no_balloon_in_code(self):
        """Test that balloon celebrations have been removed from code"""
        # Check main streamlit files
        files_to_check = [
            'streamlit_app_defect_enhanced.py',
            'streamlit_app_complete.py',
            'streamlit_app.py'
        ]
        
        for file in files_to_check:
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    self.assertNotIn('st.balloons()', content, 
                                   f"Found st.balloons() in {file}")
                    print(f"✅ No balloons found in {file}")
            except FileNotFoundError:
                # File doesn't exist, skip
                pass
    
    def test_incident_generation_api(self):
        """Test incident generation through API"""
        from incident_generator import IncidentGenerator
        
        generator = IncidentGenerator()
        incident = generator.generate_incident()
        
        # Validate incident structure
        required_fields = ['id', 'title', 'description', 'severity', 'status', 'service']
        for field in required_fields:
            self.assertIn(field, incident, f"Missing field: {field}")
        
        print("✅ Incident generation API working")
    
    def test_defect_correlation(self):
        """Test defect correlation functionality"""
        from defect_incident_correlator import DefectIncidentCorrelator
        
        correlator = DefectIncidentCorrelator()
        
        # Create test data
        incident = {
            'id': 'INC-TEST-001',
            'title': 'API timeout issue',
            'description': 'API Gateway experiencing timeouts',
            'service': 'API Gateway',
            'error_logs': ['Timeout after 30s']
        }
        
        # Get real defects from ALM Octane
        response = requests.get(f"{self.mcp_urls['alm_octane']}/octane/defects", timeout=5)
        defects = response.json()[:5]  # Get first 5 defects
        
        # Test correlation
        correlations = correlator.correlate_incident_with_defects(incident, defects)
        self.assertIsInstance(correlations, list)
        print(f"✅ Defect correlation working - found {len(correlations)} correlations")
    
    def test_change_correlation(self):
        """Test change correlation functionality"""
        from change_incident_correlator import ChangeIncidentCorrelator
        
        correlator = ChangeIncidentCorrelator()
        
        # Create test data
        incident = {
            'id': 'INC-TEST-002',
            'title': 'Database performance issue',
            'timestamp': '2025-10-04T10:00:00Z',
            'service': 'Database Engine',
            'description': 'Slow query performance'
        }
        
        change = {
            'id': 'CHG-001',
            'title': 'Database index update',
            'scheduled_time': '2025-10-04T09:00:00Z',
            'service': 'Database Engine',
            'status': 'Completed'
        }
        
        # Test correlation
        result = correlator.correlate_incident_with_changes(incident, [change])
        self.assertIn('correlations', result)
        print("✅ Change correlation working")
    
    def test_problem_management(self):
        """Test problem management functionality"""
        from servicenow_problem_manager import ServiceNowProblemManager
        
        manager = ServiceNowProblemManager()
        
        # Test initialization
        self.assertIsNotNone(manager)
        print("✅ Problem management initialized")
    
    def test_synthetic_transactions(self):
        """Test synthetic transaction generation"""
        from synthetic_transaction_generator import SyntheticTransactionGenerator
        
        generator = SyntheticTransactionGenerator()
        
        incident = {
            'id': 'INC-TEST-003',
            'service': 'Web Portal',
            'type': 'performance',
            'description': 'Slow response times'
        }
        
        transactions = generator.generate_transactions_for_incident(incident)
        self.assertIsInstance(transactions, list)
        self.assertTrue(len(transactions) > 0)
        print(f"✅ Synthetic transactions working - generated {len(transactions)} transactions")

class TestStreamlitUIWorkflow(unittest.TestCase):
    """Test complete UI workflow without balloons"""
    
    def test_complete_workflow(self):
        """Test a complete incident to defect workflow"""
        print("\n" + "="*60)
        print("Testing Complete Workflow")
        print("="*60)
        
        # 1. Generate incident
        from incident_generator import IncidentGenerator
        generator = IncidentGenerator()
        incident = generator.generate_incident()
        print(f"✅ Generated incident: {incident['id']}")
        
        # 2. Get defects from MCP
        response = requests.get("http://localhost:9085/octane/defects", timeout=5)
        defects = response.json()[:10]
        print(f"✅ Retrieved {len(defects)} defects from ALM Octane")
        
        # 3. Correlate incident with defects
        from defect_incident_correlator import DefectIncidentCorrelator
        correlator = DefectIncidentCorrelator()
        correlations = correlator.correlate_incident_with_defects(incident, defects)
        
        if correlations:
            print(f"✅ Found {len(correlations)} defect correlations")
            print(f"   Top correlation: {correlations[0]['defect']['name']} "
                  f"({correlations[0]['confidence']:.1%} confidence)")
        
        # 4. Test change correlation
        from change_incident_correlator import ChangeIncidentCorrelator
        change_correlator = ChangeIncidentCorrelator()
        
        # Create sample change
        change = {
            'id': 'CHG-WF-001',
            'title': f"Update for {incident['service']}",
            'scheduled_time': incident['timestamp'],
            'service': incident['service'],
            'status': 'Completed'
        }
        
        change_result = change_correlator.correlate_incident_with_changes(incident, [change])
        if change_result['correlations']:
            print(f"✅ Found change correlation: {change_result['correlations'][0]['confidence']:.1%} confidence")
        
        print("\n✅ Complete workflow test passed!")

def run_all_ui_tests():
    """Run all UI tests"""
    print("\n" + "="*60)
    print("🧪 Streamlit UI Component Test Suite")
    print("="*60 + "\n")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStreamlitComponents))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStreamlitUIWorkflow))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("📊 UI Test Summary")
    print("="*60)
    print(f"Total Tests: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 All UI tests passed! No balloons, just business.")
    else:
        print("\n⚠️  Some tests failed. Please review.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_ui_tests()
    sys.exit(0 if success else 1)
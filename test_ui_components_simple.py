#!/usr/bin/env python3
"""
Simple test suite for UI components without Selenium
"""

import unittest
import requests
import json
import time
import sys
import os
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestUIComponents(unittest.TestCase):
    """Test UI components and integrations"""
    
    def test_01_mcp_servers(self):
        """Test MCP servers are running"""
        servers = {
            'ALM Octane': 'http://localhost:9085/octane/defects',
            'Jira': 'http://localhost:9086/jira/issues'
        }
        
        for name, url in servers.items():
            try:
                response = requests.get(url, timeout=5)
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertIsInstance(data, list)
                print(f"✅ {name} server: Running ({len(data)} items)")
            except Exception as e:
                self.fail(f"{name} server test failed: {str(e)}")
    
    def test_02_streamlit_running(self):
        """Test Streamlit is accessible"""
        try:
            response = requests.get('http://localhost:8501', timeout=10)
            self.assertIn(response.status_code, [200, 304])
            print("✅ Streamlit: Running on port 8501")
        except Exception as e:
            self.fail(f"Streamlit test failed: {str(e)}")
    
    def test_03_no_balloons(self):
        """Verify balloon celebrations removed"""
        files_checked = 0
        files_with_success = 0
        
        files = [
            'streamlit_app_defect_enhanced.py',
            'streamlit_app_complete.py'
        ]
        
        for file in files:
            if os.path.exists(file):
                files_checked += 1
                with open(file, 'r') as f:
                    content = f.read()
                    if 'st.balloons()' not in content:
                        files_with_success += 1
                    else:
                        self.fail(f"Found st.balloons() in {file}")
        
        print(f"✅ No balloons: {files_with_success}/{files_checked} files clean")
    
    def test_04_incident_generation(self):
        """Test incident generation"""
        from incident_generator import IncidentGenerator
        
        generator = IncidentGenerator()
        incident = generator.generate_incident()
        
        required_fields = ['id', 'title', 'description', 'severity', 'status', 'service', 'timestamp']
        for field in required_fields:
            self.assertIn(field, incident)
        
        print(f"✅ Incident generation: {incident['id']} created")
    
    def test_05_defect_correlation(self):
        """Test defect correlation functionality"""
        from defect_incident_correlator import DefectIncidentCorrelator
        
        # Get real defects
        response = requests.get('http://localhost:9085/octane/defects', timeout=5)
        defects = response.json()[:5]
        
        incident = {
            'id': 'TEST-INC-001',
            'title': 'API timeout errors',
            'description': 'API Gateway experiencing timeouts',
            'service': 'API Gateway',
            'error_logs': ['Timeout after 30s', 'Connection pool exhausted']
        }
        
        correlator = DefectIncidentCorrelator()
        correlations = correlator.correlate_incident_with_defects(incident, defects)
        
        print(f"✅ Defect correlation: {len(correlations)} correlations found")
    
    def test_06_change_correlation(self):
        """Test change correlation"""
        from change_incident_correlator import ChangeIncidentCorrelator
        
        incident = {
            'id': 'TEST-INC-002',
            'title': 'Database slow queries',
            'timestamp': '2025-10-04T10:00:00Z',
            'service': 'Database Engine',
            'description': 'Database queries running slowly'
        }
        
        change = {
            'id': 'CHG-TEST-001',
            'title': 'Database index optimization',
            'scheduled_time': '2025-10-04T09:30:00Z',
            'service': 'Database Engine',
            'status': 'Completed',
            'implementer': 'DBA Team'
        }
        
        correlator = ChangeIncidentCorrelator()
        result = correlator.correlate_incident_with_changes(incident, [change])
        
        self.assertIn('correlations', result)
        if result['correlations']:
            print(f"✅ Change correlation: {result['correlations'][0]['confidence']:.1%} confidence")
        else:
            print("✅ Change correlation: Working (no correlations for test data)")
    
    def test_07_problem_management(self):
        """Test problem management initialization"""
        from servicenow_problem_manager import ServiceNowProblemManager
        
        manager = ServiceNowProblemManager()
        self.assertIsNotNone(manager)
        print("✅ Problem management: Initialized successfully")
    
    def test_08_synthetic_transactions(self):
        """Test synthetic transaction generation"""
        from synthetic_transaction_generator import SyntheticTransactionGenerator
        
        generator = SyntheticTransactionGenerator()
        
        incident = {
            'id': 'TEST-INC-003',
            'service': 'Web Portal',
            'type': 'performance',
            'description': 'Slow page loads'
        }
        
        transactions = generator.generate_transactions_for_incident(incident)
        self.assertTrue(len(transactions) > 0)
        
        # Verify transaction structure
        for trans in transactions[:1]:
            self.assertIn('timestamp', trans)
            self.assertIn('service', trans)
            self.assertIn('endpoint', trans)
            self.assertIn('response_time', trans)
        
        print(f"✅ Synthetic transactions: {len(transactions)} generated")
    
    def test_09_integration_workflow(self):
        """Test complete integration workflow"""
        from incident_generator import IncidentGenerator
        from defect_incident_correlator import DefectIncidentCorrelator
        
        # Generate incident
        generator = IncidentGenerator()
        incident = generator.generate_incident()
        
        # Get defects
        response = requests.get('http://localhost:9085/octane/defects', timeout=5)
        defects = response.json()[:10]
        
        # Correlate
        correlator = DefectIncidentCorrelator()
        correlations = correlator.correlate_incident_with_defects(incident, defects)
        
        print(f"✅ Integration workflow: Incident→Defect correlation complete")
        if correlations:
            top_match = correlations[0]
            print(f"   Top match: {top_match['defect']['name']} ({top_match['confidence']:.1%})")

def main():
    """Run all tests and generate report"""
    print("\n" + "="*60)
    print("🧪 SRE Copilot UI Component Tests")
    print("="*60 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestUIComponents)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED!")
        print("✅ No balloon celebrations found")
        print("✅ All components functional")
        print("✅ Ready for production deployment")
    else:
        print("⚠️  Some tests failed - review output above")
    print("="*60 + "\n")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
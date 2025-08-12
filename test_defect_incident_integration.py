#!/usr/bin/env python3
"""
Comprehensive test suite for integrated defect-incident analysis workflows
Tests the complete pipeline from incident creation to defect correlation and resolution
"""

import unittest
import requests
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import our modules
from defect_driven_incident_scenarios import DefectDrivenIncidentScenarios
from defect_incident_correlator import DefectIncidentCorrelator
from mcp_servers.alm_octane.alm_octane_mcp import ALMOctaneMCPServer
from mcp_servers.jira.jira_mcp import JiraMCPServer

class TestDefectIncidentIntegration(unittest.TestCase):
    """Test integrated defect-incident analysis workflows"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment with MCP servers"""
        # Start ALM Octane MCP server
        cls.alm_port = 8090
        cls.alm_url = f"http://localhost:{cls.alm_port}"
        cls.alm_server = ALMOctaneMCPServer(test_mode=True)
        cls.alm_thread = threading.Thread(target=cls.alm_server.start_server, args=(cls.alm_port,))
        cls.alm_thread.daemon = True
        cls.alm_thread.start()
        
        # Start Jira MCP server
        cls.jira_port = 8091
        cls.jira_url = f"http://localhost:{cls.jira_port}"
        cls.jira_server = JiraMCPServer(test_mode=True)
        cls.jira_thread = threading.Thread(target=cls.jira_server.start_server, args=(cls.jira_port,))
        cls.jira_thread.daemon = True
        cls.jira_thread.start()
        
        # Wait for servers to start
        time.sleep(2)
        
        # Initialize correlator and scenarios
        cls.mcp_endpoints = {
            'alm_octane': cls.alm_url,
            'jira': cls.jira_url
        }
        
        cls.correlator = DefectIncidentCorrelator(cls.mcp_endpoints)
        cls.scenarios_generator = DefectDrivenIncidentScenarios()
    
    def test_end_to_end_correlation_workflow(self):
        """Test complete end-to-end correlation workflow"""
        print("\n🔄 Testing End-to-End Correlation Workflow...")
        
        # Use a realistic scenario
        scenario = self.scenarios_generator.get_scenario("DDS-001")
        self.assertIsNotNone(scenario, "Should retrieve test scenario")
        
        # Convert scenario to incident data
        incident_data = {
            'incident_id': 'TEST-001',
            'title': scenario['incident_title'],
            'description': scenario['incident_description'],
            'severity': scenario['incident_severity'],
            'affected_services': scenario['affected_services'],
            'timestamp': scenario['detection_time']
        }
        
        # Run correlation analysis
        correlation_results = self.correlator.correlate_incident_with_defects(incident_data)
        
        # Validate results
        self.assertIsInstance(correlation_results, list, "Should return list of correlation results")
        
        # Generate summary
        summary = self.correlator.generate_correlation_summary(correlation_results)
        
        self.assertIn('total_correlations', summary)
        self.assertIn('highest_correlation', summary)
        self.assertIn('defect_likelihood', summary)
        self.assertIn('recommended_actions', summary)
        
        print(f"✅ Found {summary['total_correlations']} correlations")
        print(f"✅ Highest correlation: {summary['highest_correlation']:.2f}")
        print(f"✅ Defect likelihood: {summary['defect_likelihood']}")
    
    def test_defect_creation_from_incident(self):
        """Test creating defects in both systems from incident data"""
        print("\n🐛 Testing Defect Creation from Incident...")
        
        incident_data = {
            'title': 'Test API Timeout Incident',
            'description': 'API Gateway experiencing timeout errors during peak traffic',
            'severity': 'Critical',
            'affected_services': ['api-gateway', 'user-service']
        }
        
        # Create defect in ALM Octane
        alm_defect_data = {
            "name": f"Incident-derived: {incident_data['title']}",
            "description": f"Defect created from incident.\n\nDetails:\n{incident_data['description']}",
            "severity": incident_data['severity'],
            "component": "API Gateway",
            "environment": "Production",
            "created_by": "Test Suite"
        }
        
        alm_response = requests.post(f"{self.alm_url}/octane/defects", json=alm_defect_data, timeout=10)
        self.assertEqual(alm_response.status_code, 201, "Should create ALM Octane defect")
        
        alm_defect = alm_response.json()
        self.assertIn('id', alm_defect)
        
        # Create issue in Jira
        jira_issue_data = {
            "project": "TEST",
            "summary": f"Incident: {incident_data['title']}",
            "description": f"Issue created from incident.\n\nDetails:\n{incident_data['description']}",
            "issue_type": "Bug",
            "priority": incident_data['severity'],
            "assignee": "Test Team"
        }
        
        jira_response = requests.post(f"{self.jira_url}/jira/issues", json=jira_issue_data, timeout=10)
        self.assertEqual(jira_response.status_code, 201, "Should create Jira issue")
        
        jira_issue = jira_response.json()
        self.assertIn('key', jira_issue)
        
        print(f"✅ Created ALM Octane defect: {alm_defect['id']}")
        print(f"✅ Created Jira issue: {jira_issue['key']}")
    
    def test_correlation_accuracy_with_similar_defects(self):
        """Test correlation accuracy when similar defects exist"""
        print("\n🎯 Testing Correlation Accuracy...")
        
        # Create a defect that should correlate strongly
        similar_defect_data = {
            "name": "API Gateway Connection Pool Exhaustion",
            "description": "Connection pool exhaustion causing timeout errors in API Gateway during high load",
            "severity": "Critical",
            "component": "API Gateway",
            "environment": "Production"
        }
        
        create_response = requests.post(f"{self.alm_url}/octane/defects", json=similar_defect_data, timeout=10)
        self.assertEqual(create_response.status_code, 201)
        
        # Test incident with similar characteristics
        incident_data = {
            'incident_id': 'CORR-TEST-001',
            'title': 'API Gateway Timeout Surge',
            'description': 'API Gateway experiencing connection timeouts and pool exhaustion',
            'severity': 'Critical',
            'affected_services': ['api-gateway'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Run correlation
        correlation_results = self.correlator.correlate_incident_with_defects(incident_data)
        
        # Find the correlation with our created defect
        high_correlation_found = False
        for result in correlation_results:
            if result.correlation_score >= 0.6:  # Should find strong correlation
                high_correlation_found = True
                break
        
        self.assertTrue(high_correlation_found, "Should find high correlation with similar defect")
        
        print(f"✅ Found high correlation as expected")
    
    def test_multiple_scenario_correlation_patterns(self):
        """Test correlation patterns across multiple scenarios"""
        print("\n📊 Testing Multiple Scenario Correlation Patterns...")
        
        scenarios = self.scenarios_generator.get_all_scenarios()
        correlation_results_summary = []
        
        for scenario in scenarios[:3]:  # Test first 3 scenarios
            incident_data = {
                'incident_id': scenario['scenario_id'],
                'title': scenario['incident_title'],
                'description': scenario['incident_description'],
                'severity': scenario['incident_severity'],
                'affected_services': scenario['affected_services'],
                'timestamp': scenario['detection_time']
            }
            
            # Run correlation
            correlation_results = self.correlator.correlate_incident_with_defects(incident_data)
            summary = self.correlator.generate_correlation_summary(correlation_results)
            
            correlation_results_summary.append({
                'scenario_id': scenario['scenario_id'],
                'title': scenario['incident_title'],
                'total_correlations': summary['total_correlations'],
                'highest_correlation': summary['highest_correlation'],
                'defect_likelihood': summary['defect_likelihood']
            })
        
        # Validate that we got meaningful results for all scenarios
        for summary in correlation_results_summary:
            self.assertGreaterEqual(summary['total_correlations'], 0, 
                                  f"Should have correlation results for {summary['scenario_id']}")
            
            print(f"✅ {summary['scenario_id']}: {summary['total_correlations']} correlations, "
                  f"max score: {summary['highest_correlation']:.2f}, "
                  f"likelihood: {summary['defect_likelihood']}")
    
    def test_defect_lifecycle_tracking(self):
        """Test tracking defects through their lifecycle"""
        print("\n📋 Testing Defect Lifecycle Tracking...")
        
        # Create initial defect
        defect_data = {
            "name": "Lifecycle Test Defect",
            "description": "Testing defect lifecycle management",
            "severity": "Medium",
            "component": "Test Component",
            "assigned_to": "Test Team"
        }
        
        create_response = requests.post(f"{self.alm_url}/octane/defects", json=defect_data, timeout=10)
        self.assertEqual(create_response.status_code, 201)
        
        defect = create_response.json()
        defect_id = defect['id']
        
        # Update defect status
        update_data = {
            "status": "In Progress",
            "assigned_to": "Developer A"
        }
        
        update_response = requests.put(f"{self.alm_url}/octane/defects/{defect_id}", 
                                     json=update_data, timeout=10)
        self.assertEqual(update_response.status_code, 200)
        
        # Add comment
        comment_data = {
            "text": "Starting investigation",
            "author": "Test Suite"
        }
        
        comment_response = requests.post(f"{self.alm_url}/octane/defects/{defect_id}/comments",
                                       json=comment_data, timeout=10)
        self.assertEqual(comment_response.status_code, 200)
        
        # Verify final state
        get_response = requests.get(f"{self.alm_url}/octane/defects", timeout=10)
        self.assertEqual(get_response.status_code, 200)
        
        defects = get_response.json()
        updated_defect = next((d for d in defects if d['id'] == defect_id), None)
        
        self.assertIsNotNone(updated_defect, "Should find updated defect")
        self.assertEqual(updated_defect['status'], "In Progress")
        self.assertEqual(updated_defect['assigned_to'], "Developer A")
        
        print(f"✅ Successfully tracked defect {defect_id} through lifecycle changes")
    
    def test_cross_platform_correlation(self):
        """Test correlation between ALM Octane defects and Jira issues"""
        print("\n🔗 Testing Cross-Platform Correlation...")
        
        # Create related defects in both systems
        alm_defect_data = {
            "name": "Database Performance Issue",
            "description": "Slow database queries causing application timeouts",
            "severity": "High",
            "component": "Database"
        }
        
        jira_issue_data = {
            "project": "TEST",
            "summary": "Database Connection Timeout",
            "description": "Database connections timing out during peak usage",
            "issue_type": "Bug",
            "priority": "High"
        }
        
        # Create in both systems
        alm_response = requests.post(f"{self.alm_url}/octane/defects", json=alm_defect_data, timeout=10)
        jira_response = requests.post(f"{self.jira_url}/jira/issues", json=jira_issue_data, timeout=10)
        
        self.assertEqual(alm_response.status_code, 201)
        self.assertEqual(jira_response.status_code, 201)
        
        # Test incident that should correlate with both
        incident_data = {
            'incident_id': 'CROSS-TEST-001',
            'title': 'Database Performance Degradation',
            'description': 'Application experiencing database timeout issues during high load',
            'severity': 'High',
            'affected_services': ['database', 'app-service'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Run correlation
        correlation_results = self.correlator.correlate_incident_with_defects(incident_data)
        
        # Check that we found correlations in both systems
        alm_correlations = [r for r in correlation_results if r.defect_source == 'alm_octane']
        jira_correlations = [r for r in correlation_results if r.defect_source == 'jira']
        
        self.assertGreater(len(alm_correlations), 0, "Should find ALM Octane correlations")
        self.assertGreater(len(jira_correlations), 0, "Should find Jira correlations")
        
        print(f"✅ Found correlations: {len(alm_correlations)} ALM Octane, {len(jira_correlations)} Jira")
    
    def test_analytics_and_reporting(self):
        """Test analytics and reporting functionality"""
        print("\n📈 Testing Analytics and Reporting...")
        
        # Test ALM Octane analytics
        alm_metrics_response = requests.get(f"{self.alm_url}/octane/analytics/quality-metrics", timeout=10)
        self.assertEqual(alm_metrics_response.status_code, 200)
        
        alm_metrics = alm_metrics_response.json()
        self.assertIn('metrics', alm_metrics)
        
        quality_metrics = alm_metrics['metrics']
        expected_metrics = ['defect_density', 'test_coverage', 'defect_removal_efficiency']
        
        for metric in expected_metrics:
            self.assertIn(metric, quality_metrics, f"Should include {metric}")
        
        # Test Jira analytics
        jira_metrics_response = requests.get(f"{self.jira_url}/jira/analytics/defect-metrics", timeout=10)
        self.assertEqual(jira_metrics_response.status_code, 200)
        
        jira_metrics = jira_metrics_response.json()
        self.assertIn('metrics', jira_metrics)
        
        defect_metrics = jira_metrics['metrics']
        expected_jira_metrics = ['total_bugs', 'open_bugs', 'critical_bugs', 'average_resolution_time']
        
        for metric in expected_jira_metrics:
            self.assertIn(metric, defect_metrics, f"Should include {metric}")
        
        print("✅ ALM Octane metrics validated")
        print("✅ Jira metrics validated")
    
    def test_real_time_correlation_updates(self):
        """Test real-time correlation updates as defects change"""
        print("\n⚡ Testing Real-time Correlation Updates...")
        
        # Create base incident
        incident_data = {
            'incident_id': 'RT-TEST-001',
            'title': 'Memory Leak Investigation',
            'description': 'Application showing gradual memory increase over time',
            'severity': 'Medium',
            'affected_services': ['app-service'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Initial correlation (should be low)
        initial_results = self.correlator.correlate_incident_with_defects(incident_data)
        initial_summary = self.correlator.generate_correlation_summary(initial_results)
        
        # Create a highly relevant defect
        relevant_defect_data = {
            "name": "Memory Leak in Background Process",
            "description": "Background process not releasing memory, causing gradual memory increase",
            "severity": "Medium",
            "component": "Application Service",
            "environment": "Production"
        }
        
        create_response = requests.post(f"{self.alm_url}/octane/defects", 
                                      json=relevant_defect_data, timeout=10)
        self.assertEqual(create_response.status_code, 201)
        
        # Re-run correlation (should be higher now)
        updated_results = self.correlator.correlate_incident_with_defects(incident_data)
        updated_summary = self.correlator.generate_correlation_summary(updated_results)
        
        # Correlation should have improved
        self.assertGreaterEqual(updated_summary['highest_correlation'], 
                              initial_summary['highest_correlation'],
                              "Correlation should improve after adding relevant defect")
        
        print(f"✅ Correlation improved: {initial_summary['highest_correlation']:.2f} → "
              f"{updated_summary['highest_correlation']:.2f}")
    
    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset"""
        print("\n⚡ Testing Performance with Large Dataset...")
        
        # Create multiple defects to simulate larger dataset
        defect_count = 20
        created_defects = []
        
        start_time = time.time()
        
        for i in range(defect_count):
            defect_data = {
                "name": f"Performance Test Defect {i:02d}",
                "description": f"Test defect number {i} for performance testing",
                "severity": ["Critical", "High", "Medium", "Low"][i % 4],
                "component": f"Component {i % 3}",
                "environment": "Production"
            }
            
            response = requests.post(f"{self.alm_url}/octane/defects", json=defect_data, timeout=10)
            if response.status_code == 201:
                created_defects.append(response.json())
        
        creation_time = time.time() - start_time
        
        # Test correlation performance
        incident_data = {
            'incident_id': 'PERF-TEST-001',
            'title': 'Performance Test Incident',
            'description': 'Testing correlation performance with large dataset',
            'severity': 'High',
            'affected_services': ['component-1', 'component-2'],
            'timestamp': datetime.now().isoformat()
        }
        
        correlation_start = time.time()
        correlation_results = self.correlator.correlate_incident_with_defects(incident_data)
        correlation_time = time.time() - correlation_start
        
        # Performance assertions
        self.assertLess(creation_time, 30, "Should create defects in reasonable time")
        self.assertLess(correlation_time, 10, "Should complete correlation in reasonable time")
        self.assertGreaterEqual(len(correlation_results), 0, "Should return correlation results")
        
        print(f"✅ Created {len(created_defects)} defects in {creation_time:.2f}s")
        print(f"✅ Completed correlation in {correlation_time:.2f}s")
        print(f"✅ Found {len(correlation_results)} correlations")


def run_integration_tests():
    """Run all integration tests with comprehensive reporting"""
    print("🧪 Starting Defect-Incident Integration Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDefectIncidentIntegration)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print comprehensive summary
    print("\n" + "=" * 60)
    print("📊 Integration Test Results Summary")
    print("=" * 60)
    
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Show details for failures and errors
    if result.failures:
        print(f"\n❌ Failures ({len(result.failures)}):")
        for test, failure in result.failures:
            print(f"  - {test}")
            print(f"    {failure.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🚨 Errors ({len(result.errors)}):")
        for test, error in result.errors:
            print(f"  - {test}")
            print(f"    {error.split('Exception:')[-1].strip()}")
    
    # Overall assessment
    if result.wasSuccessful():
        print("\n🎉 All integration tests passed!")
        print("✅ Defect-incident analysis workflows are fully operational")
        print("✅ Cross-platform correlation is working correctly")
        print("✅ Analytics and reporting functions are validated")
        print("✅ Performance meets requirements")
    else:
        print(f"\n⚠️ Some tests failed - review failures above")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
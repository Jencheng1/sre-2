#!/usr/bin/env python3
"""
Comprehensive test suite for defect management system (ALM Octane & Jira MCP)
"""

import unittest
import requests
import json
import time
import threading
from datetime import datetime

# Import MCP servers for testing
from mcp_servers.alm_octane.alm_octane_mcp import ALMOctaneMCPServer
from mcp_servers.jira.jira_mcp import JiraMCPServer

class TestALMOctaneMCP(unittest.TestCase):
    """Test ALM Octane MCP server functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Start ALM Octane MCP server for testing"""
        cls.port = 8085
        cls.base_url = f"http://localhost:{cls.port}"
        cls.server = ALMOctaneMCPServer(test_mode=True)
        
        # Start server in thread
        cls.thread = threading.Thread(target=cls.server.start_server, args=(cls.port,))
        cls.thread.daemon = True
        cls.thread.start()
        time.sleep(1)  # Wait for server to start
    
    def test_get_defects(self):
        """Test retrieving defects from ALM Octane"""
        response = requests.get(f"{self.base_url}/octane/defects", timeout=5)
        self.assertEqual(response.status_code, 200)
        
        defects = response.json()
        self.assertIsInstance(defects, list)
        self.assertGreater(len(defects), 0)
        
        # Validate defect structure
        defect = defects[0]
        required_fields = ['id', 'name', 'severity', 'status', 'project']
        for field in required_fields:
            self.assertIn(field, defect)
    
    def test_create_defect(self):
        """Test creating a new defect in ALM Octane"""
        defect_data = {
            "name": "Test defect creation",
            "description": "This is a test defect created by automation",
            "severity": "High",
            "priority": "High",
            "project": "Test Project",
            "component": "API",
            "environment": "QA",
            "steps_to_reproduce": "1. Run test\n2. Observe failure",
            "expected_result": "Test should pass",
            "actual_result": "Test fails with error"
        }
        
        response = requests.post(
            f"{self.base_url}/octane/defects",
            json=defect_data,
            timeout=5
        )
        self.assertEqual(response.status_code, 201)
        
        created_defect = response.json()
        self.assertIn('id', created_defect)
        self.assertEqual(created_defect['name'], defect_data['name'])
        self.assertEqual(created_defect['severity'], defect_data['severity'])
    
    def test_update_defect(self):
        """Test updating a defect"""
        # First create a defect
        create_response = requests.post(
            f"{self.base_url}/octane/defects",
            json={"name": "Test defect for update", "severity": "Medium"},
            timeout=5
        )
        defect = create_response.json()
        defect_id = defect['id']
        
        # Update the defect
        update_data = {
            "status": "In Progress",
            "assigned_to": "Test User",
            "severity": "High"
        }
        
        response = requests.put(
            f"{self.base_url}/octane/defects/{defect_id}",
            json=update_data,
            timeout=5
        )
        self.assertEqual(response.status_code, 200)
        
        updated_defect = response.json()
        self.assertEqual(updated_defect['status'], "In Progress")
        self.assertEqual(updated_defect['severity'], "High")
    
    def test_add_defect_comment(self):
        """Test adding a comment to a defect"""
        # First create a defect
        create_response = requests.post(
            f"{self.base_url}/octane/defects",
            json={"name": "Test defect for comment"},
            timeout=5
        )
        defect = create_response.json()
        defect_id = defect['id']
        
        # Add comment
        comment_data = {
            "text": "This is a test comment",
            "author": "Test User"
        }
        
        response = requests.post(
            f"{self.base_url}/octane/defects/{defect_id}/comments",
            json=comment_data,
            timeout=5
        )
        self.assertEqual(response.status_code, 200)
        
        comment = response.json()
        self.assertIn('id', comment)
        self.assertEqual(comment['text'], comment_data['text'])
    
    def test_get_test_runs(self):
        """Test retrieving test runs"""
        response = requests.get(f"{self.base_url}/octane/test-runs", timeout=5)
        self.assertEqual(response.status_code, 200)
        
        test_runs = response.json()
        self.assertIsInstance(test_runs, list)
    
    def test_get_defect_trends(self):
        """Test defect trends analytics"""
        params = {"time_range": "-30d", "project": "all"}
        response = requests.get(f"{self.base_url}/octane/analytics/defect-trends", params=params, timeout=5)
        self.assertEqual(response.status_code, 200)
        
        trends = response.json()
        self.assertIn('trends', trends)
        self.assertIn('time_range', trends)
    
    def test_get_quality_metrics(self):
        """Test quality metrics"""
        response = requests.get(f"{self.base_url}/octane/analytics/quality-metrics", timeout=5)
        self.assertEqual(response.status_code, 200)
        
        metrics = response.json()
        self.assertIn('metrics', metrics)
        quality_metrics = metrics['metrics']
        expected_metrics = ['defect_density', 'test_coverage', 'defect_removal_efficiency']
        for metric in expected_metrics:
            self.assertIn(metric, quality_metrics)


class TestJiraMCP(unittest.TestCase):
    """Test Jira MCP server functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Start Jira MCP server for testing"""
        cls.port = 8086
        cls.base_url = f"http://localhost:{cls.port}"
        cls.server = JiraMCPServer(test_mode=True)
        
        # Start server in thread
        cls.thread = threading.Thread(target=cls.server.start_server, args=(cls.port,))
        cls.thread.daemon = True
        cls.thread.start()
        time.sleep(1)  # Wait for server to start
    
    def test_get_issues(self):
        """Test retrieving issues from Jira"""
        response = requests.get(f"{self.base_url}/jira/issues", timeout=5)
        self.assertEqual(response.status_code, 200)
        
        issues = response.json()
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)
        
        # Validate issue structure
        issue = issues[0]
        required_fields = ['key', 'summary', 'status', 'issuetype', 'project']
        for field in required_fields:
            self.assertIn(field, issue)
    
    def test_create_issue(self):
        """Test creating a new issue in Jira"""
        issue_data = {
            "project": "TEST",
            "summary": "Test issue creation",
            "description": "This is a test issue created by automation",
            "issue_type": "Bug",
            "priority": "High",
            "assignee": "Test User"
        }
        
        response = requests.post(
            f"{self.base_url}/jira/issues",
            json=issue_data,
            timeout=5
        )
        self.assertEqual(response.status_code, 201)
        
        created_issue = response.json()
        self.assertIn('key', created_issue)
        self.assertEqual(created_issue['summary'], issue_data['summary'])
        self.assertEqual(created_issue['issuetype']['name'], issue_data['issue_type'])
    
    def test_update_issue(self):
        """Test updating an issue"""
        # First create an issue
        create_response = requests.post(
            f"{self.base_url}/jira/issues",
            json={"project": "TEST", "summary": "Test issue for update", "issue_type": "Bug"},
            timeout=5
        )
        issue = create_response.json()
        issue_key = issue['key']
        
        # Update the issue
        update_data = {
            "summary": "Updated test issue",
            "priority": "Critical",
            "assignee": "New User"
        }
        
        response = requests.put(
            f"{self.base_url}/jira/issues/{issue_key}",
            json=update_data,
            timeout=5
        )
        self.assertEqual(response.status_code, 200)
        
        updated_issue = response.json()
        self.assertEqual(updated_issue['summary'], "Updated test issue")
    
    def test_transition_issue(self):
        """Test transitioning an issue"""
        # First create an issue
        create_response = requests.post(
            f"{self.base_url}/jira/issues",
            json={"project": "TEST", "summary": "Test issue for transition", "issue_type": "Bug"},
            timeout=5
        )
        issue = create_response.json()
        issue_key = issue['key']
        
        # Transition the issue
        transition_data = {
            "transition": {"name": "Done"},
            "resolution": "Fixed"
        }
        
        response = requests.post(
            f"{self.base_url}/jira/issues/{issue_key}/transitions",
            json=transition_data,
            timeout=5
        )
        self.assertEqual(response.status_code, 200)
        
        transitioned_issue = response.json()
        self.assertEqual(transitioned_issue['status']['name'], "Done")
    
    def test_add_comment(self):
        """Test adding a comment to an issue"""
        # First create an issue
        create_response = requests.post(
            f"{self.base_url}/jira/issues",
            json={"project": "TEST", "summary": "Test issue for comment", "issue_type": "Bug"},
            timeout=5
        )
        issue = create_response.json()
        issue_key = issue['key']
        
        # Add comment
        comment_data = {
            "body": "This is a test comment from automation",
            "author": "Test User"
        }
        
        response = requests.post(
            f"{self.base_url}/jira/issues/{issue_key}/comments",
            json=comment_data,
            timeout=5
        )
        self.assertEqual(response.status_code, 200)
        
        comment = response.json()
        self.assertIn('id', comment)
        self.assertEqual(comment['body'], comment_data['body'])
    
    def test_search_issues(self):
        """Test searching issues with JQL"""
        search_data = {
            "jql": "project = TEST AND status = Open",
            "maxResults": 10
        }
        
        response = requests.post(
            f"{self.base_url}/jira/search",
            json=search_data,
            timeout=5
        )
        self.assertEqual(response.status_code, 200)
        
        results = response.json()
        self.assertIn('issues', results)
        self.assertIn('jql', results)
        self.assertEqual(results['jql'], search_data['jql'])
    
    def test_get_projects(self):
        """Test retrieving Jira projects"""
        response = requests.get(f"{self.base_url}/jira/projects", timeout=5)
        self.assertEqual(response.status_code, 200)
        
        projects = response.json()
        self.assertIsInstance(projects, list)
        self.assertGreater(len(projects), 0)
    
    def test_get_defect_metrics(self):
        """Test defect metrics analytics"""
        params = {"project": "all", "time_range": "-30d"}
        response = requests.get(f"{self.base_url}/jira/analytics/defect-metrics", params=params, timeout=5)
        self.assertEqual(response.status_code, 200)
        
        metrics = response.json()
        self.assertIn('metrics', metrics)
        defect_metrics = metrics['metrics']
        expected_metrics = ['total_bugs', 'open_bugs', 'resolved_bugs', 'average_resolution_time']
        for metric in expected_metrics:
            self.assertIn(metric, defect_metrics)
    
    def test_get_burndown_data(self):
        """Test sprint burndown analytics"""
        response = requests.get(f"{self.base_url}/jira/analytics/burndown?sprint_id=1", timeout=5)
        self.assertEqual(response.status_code, 200)
        
        burndown = response.json()
        self.assertIn('burndown', burndown)
        self.assertIn('sprint_id', burndown)


class TestDefectManagementIntegration(unittest.TestCase):
    """Integration tests for defect management system"""
    
    @classmethod
    def setUpClass(cls):
        """Start both servers for integration testing"""
        # Start ALM Octane server
        cls.octane_port = 8087
        cls.octane_url = f"http://localhost:{cls.octane_port}"
        cls.octane_server = ALMOctaneMCPServer(test_mode=True)
        cls.octane_thread = threading.Thread(target=cls.octane_server.start_server, args=(cls.octane_port,))
        cls.octane_thread.daemon = True
        cls.octane_thread.start()
        
        # Start Jira server
        cls.jira_port = 8088
        cls.jira_url = f"http://localhost:{cls.jira_port}"
        cls.jira_server = JiraMCPServer(test_mode=True)
        cls.jira_thread = threading.Thread(target=cls.jira_server.start_server, args=(cls.jira_port,))
        cls.jira_thread.daemon = True
        cls.jira_thread.start()
        
        time.sleep(2)  # Wait for servers to start
    
    def test_cross_platform_defect_tracking(self):
        """Test creating similar defects in both systems"""
        defect_info = {
            "summary": "Critical API timeout issue",
            "description": "API calls are timing out after 30 seconds",
            "severity": "High",
            "environment": "Production"
        }
        
        # Create defect in ALM Octane
        octane_defect = {
            "name": defect_info["summary"],
            "description": defect_info["description"],
            "severity": defect_info["severity"],
            "environment": defect_info["environment"]
        }
        octane_response = requests.post(f"{self.octane_url}/octane/defects", json=octane_defect, timeout=5)
        self.assertEqual(octane_response.status_code, 201)
        octane_result = octane_response.json()
        
        # Create issue in Jira
        jira_issue = {
            "project": "PROD",
            "summary": defect_info["summary"],
            "description": defect_info["description"],
            "issue_type": "Bug",
            "priority": defect_info["severity"]
        }
        jira_response = requests.post(f"{self.jira_url}/jira/issues", json=jira_issue, timeout=5)
        self.assertEqual(jira_response.status_code, 201)
        jira_result = jira_response.json()
        
        # Verify both were created successfully
        self.assertIn('id', octane_result)
        self.assertIn('key', jira_result)
        self.assertEqual(octane_result['name'], defect_info["summary"])
        self.assertEqual(jira_result['summary'], defect_info["summary"])
    
    def test_defect_lifecycle_management(self):
        """Test complete defect lifecycle in both systems"""
        # Create defects
        octane_response = requests.post(
            f"{self.octane_url}/octane/defects",
            json={"name": "Lifecycle test defect", "severity": "Medium"},
            timeout=5
        )
        octane_defect = octane_response.json()
        
        jira_response = requests.post(
            f"{self.jira_url}/jira/issues",
            json={"project": "TEST", "summary": "Lifecycle test issue", "issue_type": "Bug"},
            timeout=5
        )
        jira_issue = jira_response.json()
        
        # Update defects (assign and add comments)
        octane_update = requests.put(
            f"{self.octane_url}/octane/defects/{octane_defect['id']}",
            json={"status": "In Progress", "assigned_to": "Developer"},
            timeout=5
        )
        self.assertEqual(octane_update.status_code, 200)
        
        jira_update = requests.put(
            f"{self.jira_url}/jira/issues/{jira_issue['key']}",
            json={"assignee": "Developer"},
            timeout=5
        )
        self.assertEqual(jira_update.status_code, 200)
        
        # Add comments
        octane_comment = requests.post(
            f"{self.octane_url}/octane/defects/{octane_defect['id']}/comments",
            json={"text": "Working on fix", "author": "Developer"},
            timeout=5
        )
        self.assertEqual(octane_comment.status_code, 200)
        
        jira_comment = requests.post(
            f"{self.jira_url}/jira/issues/{jira_issue['key']}/comments",
            json={"body": "Working on fix", "author": "Developer"},
            timeout=5
        )
        self.assertEqual(jira_comment.status_code, 200)
        
        # Close/resolve defects
        octane_close = requests.put(
            f"{self.octane_url}/octane/defects/{octane_defect['id']}",
            json={"status": "Fixed"},
            timeout=5
        )
        self.assertEqual(octane_close.status_code, 200)
        
        jira_close = requests.post(
            f"{self.jira_url}/jira/issues/{jira_issue['key']}/transitions",
            json={"transition": {"name": "Done"}, "resolution": "Fixed"},
            timeout=5
        )
        self.assertEqual(jira_close.status_code, 200)
    
    def test_analytics_comparison(self):
        """Test analytics from both systems"""
        # Get ALM Octane metrics
        octane_metrics = requests.get(f"{self.octane_url}/octane/analytics/quality-metrics", timeout=5)
        self.assertEqual(octane_metrics.status_code, 200)
        octane_data = octane_metrics.json()
        
        # Get Jira metrics
        jira_metrics = requests.get(f"{self.jira_url}/jira/analytics/defect-metrics", timeout=5)
        self.assertEqual(jira_metrics.status_code, 200)
        jira_data = jira_metrics.json()
        
        # Validate both provide analytics
        self.assertIn('metrics', octane_data)
        self.assertIn('metrics', jira_data)
        
        # Verify key metrics are present
        octane_metrics = octane_data['metrics']
        jira_metrics = jira_data['metrics']
        
        self.assertIn('defect_density', octane_metrics)
        self.assertIn('test_coverage', octane_metrics)
        self.assertIn('total_bugs', jira_metrics)
        self.assertIn('average_resolution_time', jira_metrics)


def run_defect_management_tests():
    """Run all defect management tests"""
    print("🧪 Running Defect Management Test Suite")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add ALM Octane tests
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestALMOctaneMCP))
    
    # Add Jira tests
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestJiraMCP))
    
    # Add integration tests
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDefectManagementIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, error in result.errors:
            print(f"  - {test}: {error.split('Exception:')[-1].strip()}")
    
    if not result.failures and not result.errors:
        print("🎉 All tests passed!")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_defect_management_tests()
    exit(0 if success else 1)
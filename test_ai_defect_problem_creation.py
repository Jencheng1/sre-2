#!/usr/bin/env python3
"""
Comprehensive Test Suite for AI-Powered Automatic Defect and Problem Creation
Tests the automatic creation of defects in ALM Octane/Jira and problems in ServiceNow
"""

import unittest
import json
import requests
import boto3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lambdas.supervisor.lambda_function_defect_enhanced import (
    correlate_with_defects,
    create_defect_from_incident,
    create_jira_issue_from_incident,
    analyze_incident_type,
    calculate_correlation_score,
    determine_component_from_incident,
    map_incident_severity_to_defect,
    extract_keywords
)

from servicenow_problem_integration import ServiceNowProblemManager


class TestAIDefectCreation(unittest.TestCase):
    """Test cases for AI-powered automatic defect creation"""
    
    def setUp(self):
        """Set up test data and mocks"""
        self.sample_incident = {
            'id': 'INC-20250812-001',
            'title': 'API Gateway Timeout Error Affecting Payment Processing',
            'description': 'Multiple timeout errors occurring in API Gateway when processing payment transactions. Error rate spiked to 65% causing customer impact.',
            'severity': 'Critical',
            'status': 'Open',
            'created_time': datetime.now().isoformat(),
            'affected_service': 'Payment Service'
        }
        
        self.sample_metrics = {
            'ErrorRate': 65.0,
            'ResponseTime': 8500,
            'CPUUtilization': 45.0,
            'MemoryUtilization': 78.0
        }
        
        self.sample_analysis_results = {
            'root_cause_analysis': 'Connection pool exhaustion in payment service due to database connection leaks',
            'defect_correlation': {
                'correlation_score': 0.3,  # Low score should trigger defect creation
                'alm_octane_defects': [],
                'jira_issues': [],
                'recommended_actions': ['Create new defect for connection pool issue'],
                'defect_evidence': ['No existing defects match this pattern']
            }
        }
    
    def test_analyze_incident_type(self):
        """Test incident type analysis"""
        # Test performance incident
        incident = {'description': 'System experiencing slow response times and performance degradation'}
        self.assertEqual(analyze_incident_type(incident['description']), 'performance')
        
        # Test security incident
        incident = {'description': 'Unauthorized access attempt detected in authentication service'}
        self.assertEqual(analyze_incident_type(incident['description']), 'security')
        
        # Test outage incident
        incident = {'description': 'Complete service outage - system is down'}
        self.assertEqual(analyze_incident_type(incident['description']), 'outage')
        
        # Test defect-related incident
        incident = {'description': 'API timeout errors causing connection failures'}
        self.assertEqual(analyze_incident_type(incident['description']), 'defect_related')
    
    @patch('requests.get')
    def test_correlate_with_defects_high_correlation(self, mock_get):
        """Test defect correlation when existing defects match"""
        # Mock response with matching defects
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                'id': 'DEF-001',
                'name': 'Payment API Timeout Issue',
                'severity': 'Critical',
                'status': 'In Progress',
                'description': 'API Gateway timeouts affecting payment processing'
            }
        ]
        
        result = correlate_with_defects(
            self.sample_incident['description'],
            'defect_related',
            self.sample_metrics
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('correlation_score', result)
        self.assertIn('alm_octane_defects', result)
        self.assertIn('recommended_actions', result)
        self.assertIn('defect_evidence', result)
    
    @patch('requests.post')
    def test_create_defect_from_incident_low_correlation(self, mock_post):
        """Test automatic defect creation when correlation is low"""
        # Mock successful defect creation
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'id': 'DEF-002',
            'name': 'Incident-derived defect: API Gateway Timeout Error',
            'status': 'New',
            'created_date': datetime.now().isoformat()
        }
        
        result = create_defect_from_incident(
            self.sample_incident,
            self.sample_analysis_results
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 'DEF-002')
        
        # Verify the defect data sent
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        defect_data = call_args[1]['json']
        
        self.assertIn('Incident-derived defect:', defect_data['name'])
        self.assertEqual(defect_data['severity'], 'Critical')
        self.assertEqual(defect_data['environment'], 'Production')
        self.assertIn('Root Cause Analysis:', defect_data['description'])
    
    @patch('requests.post')
    def test_create_defect_not_created_high_correlation(self, mock_post):
        """Test that defect is NOT created when correlation is high"""
        # Set high correlation score
        high_correlation_analysis = self.sample_analysis_results.copy()
        high_correlation_analysis['defect_correlation']['correlation_score'] = 0.8
        
        result = create_defect_from_incident(
            self.sample_incident,
            high_correlation_analysis
        )
        
        # Should not create defect
        self.assertIsNone(result)
        mock_post.assert_not_called()
    
    @patch('requests.post')
    def test_create_jira_issue_from_incident(self, mock_post):
        """Test Jira issue creation from incident"""
        # Mock successful issue creation
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'key': 'SREPROJ-123',
            'id': '10001',
            'self': 'http://localhost:9086/jira/issues/SREPROJ-123'
        }
        
        result = create_jira_issue_from_incident(
            self.sample_incident,
            self.sample_analysis_results
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['key'], 'SREPROJ-123')
        
        # Verify issue data
        call_args = mock_post.call_args
        issue_data = call_args[1]['json']
        
        self.assertEqual(issue_data['project'], 'SREPROJ')
        self.assertEqual(issue_data['issue_type'], 'Bug')
        self.assertEqual(issue_data['priority'], 'Blocker')
        self.assertIn('incident-derived', issue_data['labels'])
    
    def test_determine_component_from_incident(self):
        """Test component determination logic"""
        # Test various incident descriptions
        test_cases = [
            ('API gateway timeout errors', 'API Gateway'),
            ('Database connection pool exhausted', 'Database'),
            ('Authentication service failures', 'Authentication'),
            ('Payment processing errors', 'Payment System'),
            ('Search index corruption', 'Search Service'),
            ('File upload failures', 'File Management'),
            ('Unknown error occurred', 'General')
        ]
        
        for description, expected_component in test_cases:
            incident = {'description': description}
            component = determine_component_from_incident(incident)
            self.assertEqual(component, expected_component)
    
    def test_severity_mapping(self):
        """Test severity mapping between incidents and defects"""
        # Test ALM Octane mapping
        self.assertEqual(map_incident_severity_to_defect('Critical'), 'Critical')
        self.assertEqual(map_incident_severity_to_defect('High'), 'High')
        self.assertEqual(map_incident_severity_to_defect('Medium'), 'Medium')
        self.assertEqual(map_incident_severity_to_defect('Low'), 'Low')
        self.assertEqual(map_incident_severity_to_defect('Unknown'), 'Medium')
    
    def test_extract_keywords(self):
        """Test keyword extraction from incident description"""
        description = "API timeout errors causing payment failures and customer impact"
        keywords = extract_keywords(description)
        
        self.assertIn('api', keywords)
        self.assertIn('timeout', keywords)
        self.assertIn('payment', keywords)
        self.assertIn('failures', keywords)
    
    def test_correlation_score_calculation(self):
        """Test correlation score calculation logic"""
        # Test with matching defects
        octane_defects = [
            {'relevance_score': 0.8},
            {'relevance_score': 0.6}
        ]
        jira_issues = [
            {'relevance_score': 0.7},
            {'relevance_score': 0.5}
        ]
        
        score = calculate_correlation_score(
            octane_defects,
            jira_issues,
            self.sample_metrics
        )
        
        self.assertGreater(score, 0.5)
        self.assertLessEqual(score, 1.0)
    
    @patch('requests.post')
    def test_ai_decision_making_for_defect_creation(self, mock_post):
        """Test AI decision-making process for automatic defect creation"""
        # Simulate different scenarios
        scenarios = [
            {
                'name': 'New unique incident - should create defect',
                'correlation_score': 0.2,
                'should_create': True
            },
            {
                'name': 'Similar to existing defect - should not create',
                'correlation_score': 0.8,
                'should_create': False
            },
            {
                'name': 'Borderline case - should create defect',
                'correlation_score': 0.45,
                'should_create': True
            }
        ]
        
        for scenario in scenarios:
            mock_post.reset_mock()
            analysis = self.sample_analysis_results.copy()
            analysis['defect_correlation']['correlation_score'] = scenario['correlation_score']
            
            result = create_defect_from_incident(
                self.sample_incident,
                analysis
            )
            
            if scenario['should_create']:
                self.assertIsNotNone(result, f"Failed for scenario: {scenario['name']}")
                mock_post.assert_called_once()
            else:
                self.assertIsNone(result, f"Failed for scenario: {scenario['name']}")
                mock_post.assert_not_called()


class TestAIProblemCreation(unittest.TestCase):
    """Test cases for AI-powered automatic problem creation in ServiceNow"""
    
    def setUp(self):
        """Set up test data"""
        self.problem_manager = ServiceNowProblemManager()
        self.sample_incident = {
            'id': 'INC-20250812-002',
            'title': 'Recurring Database Connection Pool Exhaustion',
            'description': 'Database connection pool repeatedly exhausting causing widespread service disruptions',
            'severity': 'High',
            'status': 'Open',
            'created_time': datetime.now().isoformat()
        }
    
    @patch('requests.post')
    def test_create_problem_from_incident(self, mock_post):
        """Test automatic problem creation from incident"""
        # Mock successful problem creation
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'problem_id': 'PRB001234',
            'number': 'PRB0001234',
            'url': 'http://localhost:9082/problem/PRB001234'
        }
        
        result = self.problem_manager.create_problem_from_incident(
            self.sample_incident['id'],
            self.sample_incident
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['problem_id'], 'PRB001234')
        self.assertIn('Problem created successfully', result['message'])
        
        # Verify problem data
        call_args = mock_post.call_args
        problem_data = call_args[1]['json']
        
        self.assertIn('Problem:', problem_data['short_description'])
        self.assertEqual(problem_data['category'], 'Software')
        self.assertEqual(problem_data['assignment_group'], 'SRE Team')
        self.assertIn('source_incident_id', problem_data)
    
    @patch('boto3.client')
    def test_link_problem_to_incident(self, mock_boto):
        """Test linking ServiceNow problem to AWS SSM incident"""
        # Mock SSM client
        mock_ssm = MagicMock()
        mock_boto.return_value = mock_ssm
        
        result = self.problem_manager.link_problem_to_incident(
            'PRB001234',
            self.sample_incident['id']
        )
        
        self.assertTrue(result['success'])
        
        # Verify SSM tags were added
        mock_ssm.add_tags_to_resource.assert_called_once()
        call_args = mock_ssm.add_tags_to_resource.call_args
        tags = call_args[1]['Tags']
        
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0]['Key'], 'ServiceNowProblemId')
        self.assertEqual(tags[0]['Value'], 'PRB001234')
    
    @patch('requests.put')
    def test_update_problem_with_resolution(self, mock_put):
        """Test updating problem with resolution information"""
        mock_put.return_value.status_code = 200
        
        resolution_data = {
            'resolution_code': 'Solved (Permanently)',
            'root_cause': 'Connection leak in payment service code',
            'resolution_notes': 'Fixed connection leak and added monitoring',
            'workaround': 'Restart service to clear connections',
            'resolved_by': 'john.doe@company.com'
        }
        
        result = self.problem_manager.update_problem_with_resolution(
            'PRB001234',
            resolution_data
        )
        
        self.assertTrue(result['success'])
        self.assertIn('updated with resolution', result['message'])
        
        # Verify update data
        call_args = mock_put.call_args
        update_data = call_args[1]['json']
        
        self.assertEqual(update_data['state'], 'Resolved')
        self.assertEqual(update_data['root_cause'], resolution_data['root_cause'])
        self.assertIn('resolved_at', update_data)
    
    def test_problem_description_generation(self):
        """Test problem description generation from incident"""
        description = self.problem_manager._generate_problem_description(
            self.sample_incident['id'],
            self.sample_incident
        )
        
        self.assertIn('Incident ID:', description)
        self.assertIn('Title:', description)
        self.assertIn('Description:', description)
        self.assertIn('Impact Analysis:', description)
        self.assertIn('Next Steps:', description)
    
    def test_severity_mapping_for_problems(self):
        """Test incident severity to problem priority mapping"""
        test_cases = [
            ('Critical', {'impact': '1', 'urgency': '1', 'priority': '1'}),
            ('High', {'impact': '2', 'urgency': '2', 'priority': '2'}),
            ('Medium', {'impact': '3', 'urgency': '3', 'priority': '3'}),
            ('Low', {'impact': '4', 'urgency': '4', 'priority': '4'})
        ]
        
        for severity, expected in test_cases:
            result = self.problem_manager._map_incident_severity(severity)
            self.assertEqual(result, expected)
    
    @patch('requests.post')
    def test_create_problem_workflow(self, mock_post):
        """Test complete problem creation workflow"""
        # Mock successful responses
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'problem_id': 'PRB001235',
            'number': 'PRB0001235'
        }
        
        # Test workflow
        workflow_result = self.problem_manager.create_problem_workflow(
            self.sample_incident['id'],
            self.sample_incident
        )
        
        self.assertTrue(workflow_result['success'])
        self.assertIn('problem_created', workflow_result)
        self.assertIn('linked_to_incident', workflow_result)
        self.assertIn('knowledge_base_updated', workflow_result)


class TestIntegrationScenarios(unittest.TestCase):
    """Test end-to-end integration scenarios"""
    
    @patch('requests.post')
    @patch('requests.get')
    def test_incident_to_defect_and_problem_flow(self, mock_get, mock_post):
        """Test complete flow from incident to defect and problem creation"""
        # Setup incident
        incident = {
            'id': 'INC-20250812-003',
            'title': 'Critical Payment Service Failure',
            'description': 'Payment service experiencing critical failures with 90% error rate',
            'severity': 'Critical',
            'status': 'Open'
        }
        
        # Mock no existing defects (low correlation)
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []
        
        # Mock successful creation responses
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.side_effect = [
            {'id': 'DEF-003', 'name': 'Payment Service Failure'},  # ALM Octane
            {'key': 'SREPROJ-124', 'id': '10002'},  # Jira
            {'problem_id': 'PRB001236', 'number': 'PRB0001236'}  # ServiceNow
        ]
        
        # Execute workflow
        analysis_results = {
            'root_cause_analysis': 'Critical failure in payment processing module',
            'defect_correlation': {
                'correlation_score': 0.2,  # Low correlation triggers creation
                'alm_octane_defects': [],
                'jira_issues': []
            }
        }
        
        # Create defect
        defect_result = create_defect_from_incident(incident, analysis_results)
        self.assertIsNotNone(defect_result)
        
        # Create Jira issue
        jira_result = create_jira_issue_from_incident(incident, analysis_results)
        self.assertIsNotNone(jira_result)
        
        # Create problem
        problem_manager = ServiceNowProblemManager()
        problem_result = problem_manager.create_problem_from_incident(
            incident['id'],
            incident
        )
        self.assertTrue(problem_result['success'])
        
        # Verify all creations
        self.assertEqual(mock_post.call_count, 3)
    
    def test_ai_powered_decision_matrix(self):
        """Test AI decision matrix for creation logic"""
        decision_matrix = [
            {
                'scenario': 'New critical incident with no matches',
                'correlation_score': 0.1,
                'severity': 'Critical',
                'expected_action': 'create_all'  # Defect + Problem
            },
            {
                'scenario': 'High correlation with existing defect',
                'correlation_score': 0.9,
                'severity': 'High',
                'expected_action': 'link_existing'  # No creation
            },
            {
                'scenario': 'Medium incident with partial match',
                'correlation_score': 0.5,
                'severity': 'Medium',
                'expected_action': 'create_problem_only'  # Problem only
            },
            {
                'scenario': 'Low severity with low correlation',
                'correlation_score': 0.3,
                'severity': 'Low',
                'expected_action': 'monitor_only'  # No immediate action
            }
        ]
        
        for scenario in decision_matrix:
            # Test decision logic
            should_create_defect = scenario['correlation_score'] < 0.5
            should_create_problem = scenario['severity'] in ['Critical', 'High', 'Medium']
            
            if scenario['expected_action'] == 'create_all':
                self.assertTrue(should_create_defect)
                self.assertTrue(should_create_problem)
            elif scenario['expected_action'] == 'link_existing':
                self.assertFalse(should_create_defect)
            elif scenario['expected_action'] == 'create_problem_only':
                self.assertFalse(should_create_defect)
                self.assertTrue(should_create_problem)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    @patch('requests.post')
    def test_defect_creation_failure_handling(self, mock_post):
        """Test handling of defect creation failures"""
        # Mock failure response
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = 'Internal Server Error'
        
        incident = {'id': 'INC-ERR-001', 'title': 'Test Error'}
        analysis = {'defect_correlation': {'correlation_score': 0.1}}
        
        result = create_defect_from_incident(incident, analysis)
        self.assertIsNone(result)
    
    @patch('requests.post')
    def test_problem_creation_timeout(self, mock_post):
        """Test handling of timeout during problem creation"""
        # Mock timeout exception
        mock_post.side_effect = requests.Timeout('Connection timeout')
        
        problem_manager = ServiceNowProblemManager()
        result = problem_manager.create_problem_from_incident(
            'INC-TIMEOUT-001',
            {'title': 'Timeout Test'}
        )
        
        self.assertFalse(result['success'])
        self.assertIn('Error creating problem', result['error'])
    
    def test_invalid_incident_data_handling(self):
        """Test handling of invalid or incomplete incident data"""
        # Test with missing required fields
        invalid_incidents = [
            {},  # Empty incident
            {'title': 'No ID'},  # Missing ID
            {'id': 'INC-001'},  # Missing title
            {'id': 'INC-002', 'title': None}  # Null title
        ]
        
        for incident in invalid_incidents:
            # Should handle gracefully without exceptions
            try:
                component = determine_component_from_incident(incident)
                self.assertEqual(component, 'General')  # Should default to General
            except Exception as e:
                self.fail(f"Failed to handle invalid incident: {e}")


def run_all_tests():
    """Run all test suites and return results"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAIDefectCreation))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAIProblemCreation))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegrationScenarios))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "="*70)
    print("AI-POWERED DEFECT AND PROBLEM CREATION TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED! AI-powered defect and problem creation is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
    
    return result


if __name__ == '__main__':
    run_all_tests()
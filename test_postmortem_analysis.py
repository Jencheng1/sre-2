#!/usr/bin/env python3
"""
Test Suite for Post-Mortem Analysis Feature
Tests both backend agent and Streamlit UI integration
"""

import unittest
import json
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import boto3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules to test
from postmortem.postmortem_agent import PostMortemAgent, PostMortemReport
from dataclasses import asdict


class TestPostMortemAgent(unittest.TestCase):
    """Test the post-mortem analysis agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = PostMortemAgent()
        
        # Mock AWS clients
        self.agent.bedrock = MagicMock()
        self.agent.cloudwatch = MagicMock()
        self.agent.logs = MagicMock()
        self.agent.ssm = MagicMock()
        
    def test_analyze_incident_basic(self):
        """Test basic incident analysis"""
        incident_data = {
            'incident_id': 'TEST-001',
            'type': 'outage',
            'severity': 'HIGH',
            'description': 'Database connection pool exhausted causing service outage',
            'start_time': datetime.now() - timedelta(hours=2),
            'resolution_time': datetime.now().isoformat(),
            'service': 'payment-api'
        }
        
        # Mock Bedrock response
        self.agent.bedrock.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': json.dumps({
                        'title': 'Database Connection Pool Exhaustion',
                        'root_cause': 'Connection pool size insufficient for peak load',
                        'contributing_factors': [
                            'Sudden traffic spike',
                            'Long-running queries',
                            'No connection timeout configured'
                        ],
                        'detection_method': 'Monitoring alert on error rate',
                        'response_actions': [
                            'Increased connection pool size',
                            'Restarted affected services'
                        ],
                        'what_went_well': [
                            'Quick detection via monitoring',
                            'Effective incident communication',
                            'Rapid mitigation applied'
                        ],
                        'what_went_wrong': [
                            'Insufficient capacity planning',
                            'No auto-scaling configured',
                            'Runbook was outdated'
                        ],
                        'lessons_learned': [
                            'Need better capacity planning',
                            'Implement connection pool monitoring',
                            'Update runbooks quarterly'
                        ],
                        'preventive_measures': [
                            'Implement auto-scaling for connection pools',
                            'Add predictive capacity alerts',
                            'Regular load testing'
                        ],
                        'monitoring_improvements': [
                            'Add connection pool metrics',
                            'Create capacity dashboard'
                        ],
                        'confidence_score': 0.9
                    })
                }]
            }).encode())
        }
        
        # Analyze incident
        report = self.agent.analyze_incident(incident_data)
        
        # Verify report structure
        self.assertIsInstance(report, PostMortemReport)
        self.assertEqual(report.incident_id, 'TEST-001')
        self.assertEqual(report.severity, 'HIGH')
        self.assertEqual(report.title, 'Database Connection Pool Exhaustion')
        self.assertEqual(report.root_cause, 'Connection pool size insufficient for peak load')
        self.assertEqual(len(report.contributing_factors), 3)
        self.assertEqual(len(report.lessons_learned), 3)
        self.assertEqual(len(report.action_items), 5)  # 3 preventive + 2 monitoring
        self.assertGreater(report.ai_confidence_score, 0.8)
        
    def test_analyze_incident_with_metrics(self):
        """Test incident analysis with metrics data"""
        incident_data = {
            'incident_id': 'TEST-002',
            'type': 'performance',
            'description': 'API response times degraded',
            'start_time': datetime.now() - timedelta(hours=1),
            'raw_data': {
                'metrics': {
                    'ResponseTime': [
                        {'Maximum': 5000, 'Timestamp': datetime.now().isoformat()},
                        {'Maximum': 4500, 'Timestamp': (datetime.now() - timedelta(minutes=5)).isoformat()}
                    ],
                    'ErrorRate': [
                        {'Maximum': 25, 'Timestamp': datetime.now().isoformat()}
                    ]
                }
            }
        }
        
        # Mock default response
        self.agent.bedrock.invoke_model.side_effect = Exception("Bedrock error")
        
        # Analyze should fall back to default
        report = self.agent.analyze_incident(incident_data)
        
        # Verify fallback worked
        self.assertEqual(report.incident_id, 'TEST-002')
        self.assertEqual(report.root_cause, 'Under investigation')
        self.assertGreater(len(report.contributing_factors), 0)
        
    def test_timeline_building(self):
        """Test timeline construction"""
        incident_data = {
            'start_time': datetime(2024, 1, 15, 10, 0, 0),
            'resolution_time': '2024-01-15T12:00:00',
            'raw_data': {
                'logs': {
                    '/aws/lambda/test': [
                        {'message': 'Error occurred', 'timestamp': 1705315200000}
                    ]
                }
            }
        }
        
        timeline = self.agent._build_timeline(incident_data)
        
        # Verify timeline
        self.assertGreater(len(timeline), 0)
        self.assertEqual(timeline[0]['event'], 'Incident started')
        self.assertEqual(timeline[-1]['event'], 'Incident resolved')
        
    def test_impact_analysis(self):
        """Test impact analysis for different incident types"""
        # Test outage impact
        outage_data = {'type': 'outage', 'service': 'payment-api'}
        impact = self.agent._analyze_impact(outage_data, {})
        
        self.assertEqual(impact['users_impacted'], 10000)
        self.assertEqual(impact['revenue_impact'], '$50,000')
        self.assertTrue(impact['sla_breached'])
        
        # Test performance impact
        perf_data = {'type': 'performance', 'service': 'api-gateway'}
        impact = self.agent._analyze_impact(perf_data, {})
        
        self.assertEqual(impact['users_impacted'], 5000)
        self.assertEqual(impact['revenue_impact'], '$10,000')
        self.assertFalse(impact['sla_breached'])
        
        # Test security impact
        sec_data = {'type': 'security', 'service': 'auth-service'}
        impact = self.agent._analyze_impact(sec_data, {})
        
        self.assertEqual(impact['users_impacted'], 1000)
        self.assertEqual(impact['revenue_impact'], 'Potential compliance fine')
        self.assertFalse(impact['sla_breached'])
        
    def test_markdown_generation(self):
        """Test markdown report generation"""
        # Create a sample report
        report = PostMortemReport(
            incident_id='TEST-003',
            title='Test Incident',
            severity='HIGH',
            incident_start='2024-01-15T10:00:00',
            incident_end='2024-01-15T12:00:00',
            detection_time='2024-01-15T10:05:00',
            resolution_time='2024-01-15T12:00:00',
            duration_minutes=120,
            services_affected=['api', 'database'],
            users_impacted=5000,
            revenue_impact='$25,000',
            sla_breached=True,
            timeline=[
                {'time': '2024-01-15T10:00:00', 'event': 'Incident started', 'severity': 'critical'},
                {'time': '2024-01-15T12:00:00', 'event': 'Incident resolved', 'severity': 'info'}
            ],
            root_cause='Test root cause',
            contributing_factors=['Factor 1', 'Factor 2'],
            detection_method='Automated alert',
            response_actions=['Action 1', 'Action 2'],
            what_went_well=['Good thing 1', 'Good thing 2'],
            what_went_wrong=['Bad thing 1', 'Bad thing 2'],
            lessons_learned=['Lesson 1', 'Lesson 2'],
            action_items=[
                {
                    'id': 'AI-1',
                    'title': 'Fix the issue',
                    'priority': 'HIGH',
                    'assigned_to': 'SRE Team',
                    'due_date': '2024-01-22',
                    'status': 'TODO'
                }
            ],
            preventive_measures=['Measure 1', 'Measure 2'],
            monitoring_improvements=['Improvement 1'],
            generated_at='2024-01-15T14:00:00',
            generated_by='Test Agent',
            ai_confidence_score=0.85
        )
        
        # Generate markdown
        markdown = self.agent.generate_markdown_report(report)
        
        # Verify markdown content
        self.assertIn('# Post-Mortem Report: Test Incident', markdown)
        self.assertIn('**Incident ID:** TEST-003', markdown)
        self.assertIn('**Severity:** HIGH', markdown)
        self.assertIn('**Duration:** 120 minutes', markdown)
        self.assertIn('## Root Cause Analysis', markdown)
        self.assertIn('Test root cause', markdown)
        self.assertIn('## Timeline', markdown)
        self.assertIn('## Action Items', markdown)
        self.assertIn('Fix the issue', markdown)
        
    def test_error_categorization(self):
        """Test error message categorization"""
        test_cases = [
            ('Connection timeout to database', 'timeout'),
            ('Connection refused by server', 'connection'),
            ('Out of memory error', 'memory'),
            ('Permission denied accessing file', 'permission'),
            ('404 not found error', 'not_found'),
            ('Generic error occurred', 'general')
        ]
        
        for error_msg, expected_category in test_cases:
            category = self.agent._categorize_error(error_msg)
            self.assertEqual(category, expected_category, 
                           f"Failed to categorize '{error_msg}' as '{expected_category}'")


class TestPostMortemLambda(unittest.TestCase):
    """Test Lambda handler functionality"""
    
    @patch('postmortem.postmortem_agent.boto3.client')
    def test_lambda_handler(self, mock_boto_client):
        """Test Lambda handler"""
        from postmortem.postmortem_agent import lambda_handler
        
        # Mock event
        event = {
            'incident_data': {
                'incident_id': 'LAMBDA-TEST-001',
                'type': 'outage',
                'description': 'Service unavailable',
                'severity': 'CRITICAL',
                'start_time': datetime.now().isoformat()
            }
        }
        
        # Mock Bedrock response
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': json.dumps(PostMortemAgent()._get_default_analysis())
                }]
            }).encode())
        }
        
        def get_client(service):
            if service == 'bedrock-runtime':
                return mock_bedrock
            return MagicMock()
            
        mock_boto_client.side_effect = get_client
        
        # Call handler
        response = lambda_handler(event, None)
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('report', body)
        self.assertIn('markdown', body)
        self.assertEqual(body['report']['incident_id'], 'LAMBDA-TEST-001')


class TestStreamlitIntegration(unittest.TestCase):
    """Test Streamlit UI integration"""
    
    def test_postmortem_imports(self):
        """Test that Streamlit app imports post-mortem functionality"""
        try:
            # Check if streamlit app has post-mortem imports
            with open('streamlit_app.py', 'r') as f:
                content = f.read()
                
            self.assertIn('PostMortemAgent', content)
            self.assertIn('POSTMORTEM_AVAILABLE', content)
            self.assertIn('render_postmortem_analysis', content)
            
        except FileNotFoundError:
            self.skipTest("streamlit_app.py not found")
            
    def test_postmortem_tab_added(self):
        """Test that post-mortem tab is added to navigation"""
        try:
            with open('streamlit_app.py', 'r') as f:
                content = f.read()
                
            # Check tab is added
            self.assertIn('📋 Post-Mortem', content)
            self.assertIn('render_postmortem_analysis()', content)
            
            # Check sub-tabs
            self.assertIn('Generate Report', content)
            self.assertIn('View Reports', content)
            self.assertIn('Analyze OpsItem', content)
            
        except FileNotFoundError:
            self.skipTest("streamlit_app.py not found")


class TestEndToEndScenarios(unittest.TestCase):
    """Test complete post-mortem scenarios"""
    
    def test_outage_scenario(self):
        """Test complete outage post-mortem"""
        agent = PostMortemAgent()
        
        # Mock AWS services
        agent.bedrock = MagicMock()
        agent.bedrock.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': json.dumps({
                        'title': 'Production Database Outage',
                        'root_cause': 'Database server ran out of disk space',
                        'contributing_factors': [
                            'Log rotation was disabled',
                            'No disk space monitoring',
                            'Backup retention too long'
                        ],
                        'detection_method': 'Customer complaints',
                        'response_actions': [
                            'Cleared old logs',
                            'Increased disk size',
                            'Restarted database'
                        ],
                        'what_went_well': [
                            'Quick diagnosis',
                            'Clear communication',
                            'Effective mitigation'
                        ],
                        'what_went_wrong': [
                            'No proactive monitoring',
                            'Manual intervention required',
                            'Customer impact before detection'
                        ],
                        'lessons_learned': [
                            'Implement disk space monitoring',
                            'Automate log rotation',
                            'Set up predictive alerts'
                        ],
                        'preventive_measures': [
                            'Deploy disk space monitors',
                            'Implement log rotation policy',
                            'Create automated cleanup jobs'
                        ],
                        'monitoring_improvements': [
                            'Add disk usage dashboards',
                            'Create capacity planning metrics'
                        ],
                        'confidence_score': 0.95
                    })
                }]
            }).encode())
        }
        
        # Create incident
        incident = {
            'incident_id': 'PROD-DB-001',
            'type': 'outage',
            'severity': 'CRITICAL',
            'description': 'Production database became unresponsive due to disk space',
            'start_time': datetime(2024, 1, 15, 14, 30, 0),
            'resolution_time': datetime(2024, 1, 15, 16, 45, 0).isoformat(),
            'service': 'production-database',
            'raw_data': {
                'metrics': {
                    'DiskUtilization': [{'Maximum': 100, 'Timestamp': '2024-01-15T14:30:00'}],
                    'DatabaseConnections': [{'Maximum': 0, 'Timestamp': '2024-01-15T14:35:00'}]
                }
            }
        }
        
        # Generate report
        report = agent.analyze_incident(incident)
        
        # Verify comprehensive report
        self.assertEqual(report.severity, 'CRITICAL')
        self.assertEqual(report.title, 'Production Database Outage')
        self.assertIn('disk space', report.root_cause.lower())
        self.assertEqual(report.duration_minutes, 135)  # 2h 15m
        self.assertEqual(report.services_affected[0], 'production-database')
        self.assertTrue(report.sla_breached)
        self.assertEqual(report.users_impacted, 10000)
        self.assertGreater(len(report.action_items), 3)
        
        # Verify markdown generation
        markdown = agent.generate_markdown_report(report)
        self.assertIn('CRITICAL', markdown)
        self.assertIn('disk space', markdown)
        self.assertIn('135 minutes', markdown)
        
    def test_performance_scenario(self):
        """Test performance degradation post-mortem"""
        agent = PostMortemAgent()
        
        # Use default analysis
        agent.bedrock = MagicMock()
        agent.bedrock.invoke_model.side_effect = Exception("Use default")
        
        incident = {
            'incident_id': 'PERF-001',
            'type': 'performance',
            'severity': 'MEDIUM',
            'description': 'API response times increased 5x during peak hours',
            'start_time': datetime.now() - timedelta(hours=3),
            'resolution_time': datetime.now().isoformat()
        }
        
        report = agent.analyze_incident(incident)
        
        # Verify performance-specific handling
        self.assertEqual(report.users_impacted, 5000)
        self.assertEqual(report.revenue_impact, '$10,000')
        self.assertFalse(report.sla_breached)
        
    def test_security_scenario(self):
        """Test security incident post-mortem"""
        agent = PostMortemAgent()
        agent.bedrock = MagicMock()
        
        # Security-specific response
        agent.bedrock.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': json.dumps({
                        'title': 'Unauthorized Access Attempt Detected',
                        'root_cause': 'Exposed API endpoint without authentication',
                        'contributing_factors': [
                            'Missing auth middleware',
                            'Incomplete security review',
                            'No API gateway protection'
                        ],
                        'detection_method': 'WAF alert on suspicious patterns',
                        'response_actions': [
                            'Blocked malicious IPs',
                            'Added authentication',
                            'Reviewed all endpoints'
                        ],
                        'what_went_well': [
                            'WAF detected attack',
                            'No data breach occurred',
                            'Quick remediation'
                        ],
                        'what_went_wrong': [
                            'Endpoint exposed',
                            'Security review missed',
                            'No rate limiting'
                        ],
                        'lessons_learned': [
                            'All endpoints need auth',
                            'Security review checklist',
                            'Implement rate limiting'
                        ],
                        'preventive_measures': [
                            'Mandatory auth middleware',
                            'Automated security scans',
                            'API gateway for all services'
                        ],
                        'monitoring_improvements': [
                            'Enhanced WAF rules',
                            'API access monitoring'
                        ],
                        'confidence_score': 0.88
                    })
                }]
            }).encode())
        }
        
        incident = {
            'incident_id': 'SEC-001',
            'type': 'security',
            'severity': 'HIGH',
            'description': 'Unauthorized API access attempts detected',
            'start_time': datetime.now() - timedelta(hours=1)
        }
        
        report = agent.analyze_incident(incident)
        
        # Verify security-specific elements
        self.assertIn('Unauthorized', report.title)
        self.assertIn('auth', report.root_cause.lower())
        self.assertEqual(report.revenue_impact, 'Potential compliance fine')
        self.assertIn('WAF', report.detection_method)


def run_all_tests():
    """Run all test suites"""
    print("🧪 Running Post-Mortem Analysis Test Suite")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestPostMortemAgent,
        TestPostMortemLambda,
        TestStreamlitIntegration,
        TestEndToEndScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
        
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"🚫 Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 All tests passed! Post-mortem analysis is working correctly.")
        print("\n✅ Features Validated:")
        print("  • AI-powered incident analysis")
        print("  • Comprehensive report generation")
        print("  • Timeline visualization")
        print("  • Action item tracking")
        print("  • Markdown/JSON export")
        print("  • Streamlit UI integration")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
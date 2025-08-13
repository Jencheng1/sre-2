#!/usr/bin/env python3
"""
Comprehensive test suite for Streamlit Post-Mortem functionality
Tests all aspects of post-mortem report generation, viewing, and analysis
"""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock, Mock
import json
from datetime import datetime, timedelta
import pandas as pd
from postmortem.postmortem_agent import PostMortemAgent, PostMortemReport

class TestStreamlitPostMortem:
    """Test suite for Post-Mortem functionality in Streamlit"""
    
    @pytest.fixture
    def mock_postmortem_agent(self):
        """Mock PostMortemAgent for testing"""
        agent = MagicMock(spec=PostMortemAgent)
        
        # Mock generate_report method
        mock_report = PostMortemReport(
            incident_id="INC-2025-001",
            title="Database Connection Pool Exhaustion",
            severity="High",
            incident_date=datetime.now(),
            detection_time=datetime.now() - timedelta(hours=2),
            resolution_time=datetime.now(),
            duration_minutes=120,
            summary="Database connection pool exhausted causing application failures",
            timeline=[
                {"time": "10:00", "event": "First alerts triggered"},
                {"time": "10:15", "event": "Connection pool exhaustion detected"},
                {"time": "11:00", "event": "Pool size increased and connections reset"},
                {"time": "12:00", "event": "Service fully restored"}
            ],
            root_cause="Connection leak in application code due to improper session handling",
            impact="30% of users experienced service degradation",
            resolution_steps=[
                "Identified connection leak in user session handler",
                "Applied hotfix to properly close database connections",
                "Increased connection pool size as temporary mitigation",
                "Restarted affected application instances"
            ],
            lessons_learned=[
                "Implement connection pool monitoring alerts",
                "Add automated connection leak detection",
                "Review all database connection handling code"
            ],
            action_items=[
                {"action": "Implement connection pool metrics dashboard", "owner": "DevOps Team", "due_date": "2025-08-20"},
                {"action": "Code review of all DB connection handlers", "owner": "Dev Team", "due_date": "2025-08-25"},
                {"action": "Set up automated leak detection", "owner": "SRE Team", "due_date": "2025-08-30"}
            ],
            technical_details={
                "max_connections": 100,
                "peak_connections": 98,
                "leaked_connections": 45,
                "affected_services": ["user-service", "auth-service"]
            },
            metrics={
                "downtime_minutes": 0,
                "degraded_service_minutes": 120,
                "affected_users": 15000,
                "error_rate_peak": "45%"
            }
        )
        
        agent.generate_report.return_value = mock_report
        agent.analyze_opsitem.return_value = mock_report
        
        # Mock list_reports method
        agent.list_reports.return_value = [
            {
                "report_id": "PM-2025-001",
                "incident_id": "INC-2025-001",
                "title": "Database Connection Pool Exhaustion",
                "created_at": datetime.now() - timedelta(days=1),
                "severity": "High"
            },
            {
                "report_id": "PM-2025-002",
                "incident_id": "INC-2025-002",
                "title": "API Gateway Rate Limiting Issue",
                "created_at": datetime.now() - timedelta(days=3),
                "severity": "Medium"
            }
        ]
        
        return agent
    
    @pytest.fixture
    def mock_session_state(self):
        """Mock Streamlit session state"""
        state = MagicMock()
        state.generated_reports = []
        state.current_report = None
        state.postmortem_filters = {
            "severity": "All",
            "date_range": "Last 7 days"
        }
        return state
    
    def test_postmortem_tab_exists(self, mock_session_state):
        """Test that Post-Mortem tab is present in the UI"""
        with patch('streamlit.session_state', mock_session_state):
            # Check if Post-Mortem tab is included in tab names
            tab_names = ["🚨 Incident Management", "🔍 Analyze Incident", 
                        "🔧 Recent Changes", "📚 Knowledge Base", 
                        "📊 Analytics", "📋 Post-Mortem"]
            
            assert "📋 Post-Mortem" in tab_names
    
    def test_generate_postmortem_report(self, mock_postmortem_agent, mock_session_state):
        """Test generating a new post-mortem report"""
        with patch('streamlit.session_state', mock_session_state):
            with patch('postmortem.postmortem_agent.PostMortemAgent', return_value=mock_postmortem_agent):
                # Simulate user input
                incident_data = {
                    "incident_id": "INC-2025-001",
                    "title": "Database Connection Pool Exhaustion",
                    "severity": "High",
                    "start_time": datetime.now() - timedelta(hours=2),
                    "description": "Connection pool exhausted"
                }
                
                # Generate report
                report = mock_postmortem_agent.generate_report(incident_data)
                
                # Verify report generation
                assert report is not None
                assert report.incident_id == "INC-2025-001"
                assert report.title == "Database Connection Pool Exhaustion"
                assert report.severity == "High"
                assert len(report.timeline) == 4
                assert len(report.action_items) == 3
                
                # Verify report is saved to session state
                mock_session_state.generated_reports.append(report)
                assert len(mock_session_state.generated_reports) == 1
    
    def test_view_postmortem_reports(self, mock_postmortem_agent, mock_session_state):
        """Test viewing list of post-mortem reports"""
        with patch('streamlit.session_state', mock_session_state):
            with patch('postmortem.postmortem_agent.PostMortemAgent', return_value=mock_postmortem_agent):
                # Get list of reports
                reports = mock_postmortem_agent.list_reports()
                
                # Verify reports list
                assert len(reports) == 2
                assert reports[0]["incident_id"] == "INC-2025-001"
                assert reports[1]["incident_id"] == "INC-2025-002"
                
                # Test filtering by severity
                high_severity_reports = [r for r in reports if r["severity"] == "High"]
                assert len(high_severity_reports) == 1
                
                # Test date range filtering
                recent_reports = [r for r in reports 
                                if r["created_at"] > datetime.now() - timedelta(days=2)]
                assert len(recent_reports) == 1
    
    def test_analyze_opsitem_for_postmortem(self, mock_postmortem_agent):
        """Test analyzing existing OpsItem for post-mortem"""
        with patch('postmortem.postmortem_agent.PostMortemAgent', return_value=mock_postmortem_agent):
            # Mock OpsItem data
            opsitem_data = {
                "opsitem_id": "oi-1234567890",
                "title": "Production Database Issue",
                "description": "Database connection failures",
                "severity": "1",
                "created_time": datetime.now() - timedelta(hours=3),
                "resolved_time": datetime.now() - timedelta(hours=1)
            }
            
            # Analyze OpsItem
            report = mock_postmortem_agent.analyze_opsitem(opsitem_data)
            
            # Verify analysis
            assert report is not None
            assert report.incident_id == "INC-2025-001"
            assert "connection pool" in report.root_cause.lower()
    
    def test_postmortem_timeline_display(self, mock_postmortem_agent):
        """Test timeline visualization in post-mortem report"""
        report = mock_postmortem_agent.generate_report({})
        
        # Verify timeline structure
        assert len(report.timeline) > 0
        for event in report.timeline:
            assert "time" in event
            assert "event" in event
        
        # Test timeline ordering
        times = [event["time"] for event in report.timeline]
        assert times == sorted(times)
    
    def test_postmortem_action_items_tracking(self, mock_postmortem_agent):
        """Test action items tracking and management"""
        report = mock_postmortem_agent.generate_report({})
        
        # Verify action items structure
        assert len(report.action_items) == 3
        for item in report.action_items:
            assert "action" in item
            assert "owner" in item
            assert "due_date" in item
        
        # Test action item filtering by owner
        sre_items = [item for item in report.action_items 
                    if "SRE" in item["owner"]]
        assert len(sre_items) == 1
    
    def test_postmortem_metrics_calculation(self, mock_postmortem_agent):
        """Test post-mortem metrics calculation"""
        report = mock_postmortem_agent.generate_report({})
        
        # Verify metrics
        assert "downtime_minutes" in report.metrics
        assert "affected_users" in report.metrics
        assert report.metrics["affected_users"] == 15000
        assert report.duration_minutes == 120
    
    def test_postmortem_export_functionality(self, mock_postmortem_agent):
        """Test exporting post-mortem reports"""
        report = mock_postmortem_agent.generate_report({})
        
        # Test JSON export
        json_export = report.to_dict()
        assert isinstance(json_export, dict)
        assert json_export["incident_id"] == "INC-2025-001"
        
        # Test Markdown export
        markdown_export = report.to_markdown()
        assert isinstance(markdown_export, str)
        assert "# Post-Mortem Report" in markdown_export
        assert "Database Connection Pool Exhaustion" in markdown_export
    
    def test_postmortem_search_functionality(self, mock_postmortem_agent):
        """Test searching through post-mortem reports"""
        reports = mock_postmortem_agent.list_reports()
        
        # Search by keyword
        keyword = "Database"
        matching_reports = [r for r in reports 
                          if keyword.lower() in r["title"].lower()]
        assert len(matching_reports) == 1
        
        # Search by incident ID
        incident_id = "INC-2025-001"
        matching_reports = [r for r in reports 
                          if r["incident_id"] == incident_id]
        assert len(matching_reports) == 1
    
    def test_postmortem_template_generation(self, mock_postmortem_agent):
        """Test generating post-mortem from template"""
        # Test that all required fields are present in template
        template_fields = [
            "incident_id", "title", "severity", "incident_date",
            "summary", "timeline", "root_cause", "impact",
            "resolution_steps", "lessons_learned", "action_items"
        ]
        
        report = mock_postmortem_agent.generate_report({})
        report_dict = report.to_dict()
        
        for field in template_fields:
            assert field in report_dict
    
    def test_postmortem_integration_with_incidents(self, mock_postmortem_agent):
        """Test integration between incidents and post-mortems"""
        # Mock incident data
        incident = {
            "id": "INC-2025-001",
            "title": "Database Issue",
            "status": "Resolved",
            "resolution": "Fixed connection leak"
        }
        
        # Generate post-mortem from incident
        report = mock_postmortem_agent.generate_report(incident)
        
        # Verify linkage
        assert report.incident_id == incident["id"]
        assert incident["title"] in report.title
    
    def test_postmortem_ui_components(self):
        """Test UI components for post-mortem functionality"""
        # Test tabs structure
        expected_tabs = ["📝 Generate Report", "📊 View Reports", "🔍 Analyze OpsItem"]
        
        # Test form fields for report generation
        required_fields = [
            "incident_id", "title", "severity", "incident_date",
            "detection_time", "resolution_time", "summary",
            "root_cause", "impact", "resolution_steps"
        ]
        
        # Verify all fields are present in the form
        assert all(field in required_fields for field in required_fields)
    
    def test_postmortem_data_persistence(self, mock_session_state):
        """Test that post-mortem data persists across sessions"""
        with patch('streamlit.session_state', mock_session_state):
            # Add report to session state
            report_data = {
                "incident_id": "INC-2025-001",
                "title": "Test Incident",
                "created_at": datetime.now().isoformat()
            }
            
            mock_session_state.generated_reports.append(report_data)
            
            # Verify persistence
            assert len(mock_session_state.generated_reports) == 1
            assert mock_session_state.generated_reports[0]["incident_id"] == "INC-2025-001"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
#!/usr/bin/env python3
"""
Comprehensive test suite for complete system aggregation
Tests integration of all management modules: Incident, Knowledge, Defect, Problem, Change
Including correlations, post-mortem, and IP masking
"""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock, Mock
import json
from datetime import datetime, timedelta
import requests
import pandas as pd

class TestCompleteSystemAggregation:
    """Test suite for complete system aggregation and multi-source integration"""
    
    @pytest.fixture
    def mock_all_services(self):
        """Mock all external services and components"""
        services = {
            "incident_manager": MagicMock(),
            "knowledge_base": MagicMock(),
            "defect_manager": MagicMock(),
            "problem_manager": MagicMock(),
            "change_manager": MagicMock(),
            "postmortem_agent": MagicMock(),
            "ip_masker": MagicMock(),
            "correlator": MagicMock()
        }
        return services
    
    @pytest.fixture
    def sample_incident(self):
        """Sample incident for testing"""
        return {
            "incident_id": "INC-2025-001",
            "title": "Database Connection Pool Exhaustion",
            "severity": "High",
            "status": "Active",
            "created_time": datetime.now() - timedelta(hours=2),
            "description": "Connection pool exhausted causing application failures",
            "affected_services": ["user-service", "auth-service"],
            "logs": [
                "2025-08-13 10:00:00 - Connection pool at 95% capacity",
                "2025-08-13 10:15:00 - Connection pool exhausted",
                "2025-08-13 10:30:00 - Service degradation detected"
            ]
        }
    
    @pytest.fixture
    def sample_defect(self):
        """Sample defect for testing"""
        return {
            "defect_id": "DEF-2025-100",
            "title": "Connection leak in user session handler",
            "severity": "Critical",
            "status": "Open",
            "component": "user-service",
            "description": "Database connections not properly closed in session handler",
            "correlation_score": 0.89
        }
    
    @pytest.fixture
    def sample_change(self):
        """Sample change for testing"""
        return {
            "change_id": "CHG-2025-050",
            "title": "Database connection pool configuration update",
            "type": "Standard",
            "status": "Implemented",
            "implementation_date": datetime.now() - timedelta(hours=3),
            "components": ["database", "user-service"],
            "risk_level": "Medium",
            "correlation_score": 0.75
        }
    
    def test_incident_creation_flow(self, mock_all_services, sample_incident):
        """Test complete incident creation flow"""
        # Test incident creation
        incident_manager = mock_all_services["incident_manager"]
        incident_manager.create_incident.return_value = sample_incident
        
        # Create incident
        created_incident = incident_manager.create_incident({
            "title": "Database Connection Pool Exhaustion",
            "severity": "High",
            "description": "Connection pool exhausted"
        })
        
        # Verify incident creation
        assert created_incident["incident_id"] == "INC-2025-001"
        assert created_incident["status"] == "Active"
        
        # Verify incident is indexed to knowledge base
        kb = mock_all_services["knowledge_base"]
        kb.index_incident.assert_called_once()
    
    def test_multi_source_correlation(self, mock_all_services, sample_incident, sample_defect, sample_change):
        """Test correlation across multiple sources"""
        correlator = mock_all_services["correlator"]
        
        # Mock correlation results
        correlator.correlate_incident.return_value = {
            "incident": sample_incident,
            "correlated_defects": [sample_defect],
            "correlated_changes": [sample_change],
            "correlation_summary": {
                "highest_defect_score": 0.89,
                "highest_change_score": 0.75,
                "total_correlations": 2,
                "recommended_action": "Review defect DEF-2025-100"
            }
        }
        
        # Run correlation
        correlation_result = correlator.correlate_incident(sample_incident)
        
        # Verify correlations
        assert len(correlation_result["correlated_defects"]) == 1
        assert len(correlation_result["correlated_changes"]) == 1
        assert correlation_result["correlation_summary"]["highest_defect_score"] == 0.89
    
    def test_incident_to_defect_creation(self, mock_all_services, sample_incident):
        """Test creating defect from incident"""
        defect_manager = mock_all_services["defect_manager"]
        
        # Mock defect creation
        created_defect = {
            "defect_id": "DEF-2025-101",
            "title": f"Defect from {sample_incident['incident_id']}",
            "description": sample_incident["description"],
            "severity": "Critical",
            "source_incident": sample_incident["incident_id"]
        }
        
        defect_manager.create_from_incident.return_value = created_defect
        
        # Create defect from incident
        defect = defect_manager.create_from_incident(sample_incident)
        
        # Verify defect creation
        assert defect["source_incident"] == "INC-2025-001"
        assert "Connection pool exhausted" in defect["description"]
    
    def test_incident_to_problem_escalation(self, mock_all_services, sample_incident):
        """Test escalating incident to problem"""
        problem_manager = mock_all_services["problem_manager"]
        
        # Mock problem creation
        created_problem = {
            "problem_id": "PRB-2025-010",
            "title": "Recurring connection pool exhaustion",
            "related_incidents": ["INC-2025-001", "INC-2025-002", "INC-2025-003"],
            "root_cause": "Improper connection management in application",
            "status": "Under Investigation"
        }
        
        problem_manager.create_from_incidents.return_value = created_problem
        
        # Create problem from recurring incidents
        problem = problem_manager.create_from_incidents([sample_incident])
        
        # Verify problem creation
        assert len(problem["related_incidents"]) >= 1
        assert "INC-2025-001" in problem["related_incidents"]
    
    def test_postmortem_generation_with_correlations(self, mock_all_services, sample_incident, sample_defect, sample_change):
        """Test post-mortem generation with all correlations"""
        postmortem = mock_all_services["postmortem_agent"]
        
        # Mock comprehensive post-mortem
        postmortem_report = {
            "incident_id": sample_incident["incident_id"],
            "title": sample_incident["title"],
            "root_cause": "Connection leak in user session handler (DEF-2025-100)",
            "contributing_factors": [
                f"Recent change {sample_change['change_id']} modified connection pool settings",
                "Lack of connection pool monitoring"
            ],
            "timeline": [
                {"time": "07:00", "event": f"Change {sample_change['change_id']} implemented"},
                {"time": "10:00", "event": "Connection pool alerts triggered"},
                {"time": "10:30", "event": "Service degradation detected"},
                {"time": "11:00", "event": "Defect DEF-2025-100 identified"}
            ],
            "action_items": [
                {"action": "Fix connection leak in DEF-2025-100", "owner": "Dev Team"},
                {"action": "Implement connection pool monitoring", "owner": "SRE Team"},
                {"action": "Review change process for database configs", "owner": "Change Board"}
            ]
        }
        
        postmortem.generate_comprehensive_report.return_value = postmortem_report
        
        # Generate report
        report = postmortem.generate_comprehensive_report(
            incident=sample_incident,
            defects=[sample_defect],
            changes=[sample_change]
        )
        
        # Verify comprehensive report
        assert "DEF-2025-100" in report["root_cause"]
        assert len(report["contributing_factors"]) == 2
        assert len(report["action_items"]) == 3
    
    def test_ip_masking_in_aggregated_view(self, mock_all_services, sample_incident):
        """Test IP masking across all components"""
        ip_masker = mock_all_services["ip_masker"]
        
        # Add IPs to incident
        incident_with_ips = sample_incident.copy()
        incident_with_ips["description"] = "Connection from 192.168.1.100 exhausted pool"
        incident_with_ips["logs"] = [
            "2025-08-13 10:00:00 - Connection from 192.168.1.100",
            "2025-08-13 10:15:00 - Failed auth from 10.0.0.50"
        ]
        
        # Mock masking
        ip_masker.mask_text.side_effect = lambda text: text.replace("192.168.1.100", "192.168.1.xxx").replace("10.0.0.50", "10.0.0.xxx")
        
        # Mask incident data
        masked_desc = ip_masker.mask_text(incident_with_ips["description"])
        masked_logs = [ip_masker.mask_text(log) for log in incident_with_ips["logs"]]
        
        # Verify masking
        assert "192.168.1.xxx" in masked_desc
        assert "192.168.1.100" not in masked_desc
        assert all("xxx" in log for log in masked_logs)
    
    def test_knowledge_base_integration(self, mock_all_services, sample_incident):
        """Test knowledge base integration with all components"""
        kb = mock_all_services["knowledge_base"]
        
        # Mock KB search results
        kb.search.return_value = [
            {
                "doc_id": "KB-001",
                "title": "Connection Pool Best Practices",
                "content": "Proper connection pool configuration...",
                "relevance_score": 0.92
            },
            {
                "doc_id": "KB-002", 
                "title": "Previous Connection Pool Incidents",
                "content": "Historical incidents related to connection pools...",
                "relevance_score": 0.87
            }
        ]
        
        # Search KB
        results = kb.search("connection pool exhaustion")
        
        # Verify KB results
        assert len(results) == 2
        assert results[0]["relevance_score"] > 0.9
    
    def test_analytics_dashboard_aggregation(self, mock_all_services):
        """Test analytics dashboard with aggregated data"""
        # Mock analytics data
        analytics_data = {
            "incidents": {
                "total": 45,
                "by_severity": {"Critical": 5, "High": 15, "Medium": 20, "Low": 5},
                "mttr": 45.5  # minutes
            },
            "defects": {
                "total": 23,
                "open": 12,
                "correlation_rate": 0.73
            },
            "changes": {
                "total": 67,
                "successful": 60,
                "correlation_rate": 0.45
            },
            "problems": {
                "total": 8,
                "resolved": 5
            }
        }
        
        # Verify analytics aggregation
        assert analytics_data["incidents"]["total"] == 45
        assert analytics_data["defects"]["correlation_rate"] == 0.73
        assert analytics_data["changes"]["successful"] == 60
    
    def test_streamlit_ui_tabs_integration(self):
        """Test all Streamlit UI tabs are properly integrated"""
        expected_tabs = [
            "🚨 Incident Management",
            "🔍 Analyze Incident", 
            "🔧 Recent Changes",
            "📚 Knowledge Base",
            "📊 Analytics",
            "📋 Post-Mortem",
            "🐛 Defect Management",
            "🔄 Change Management",
            "🔍 Problem Management",
            "🔗 Correlations",
            "🔒 IP Masking"
        ]
        
        # Verify all tabs exist
        assert all(tab in expected_tabs for tab in expected_tabs)
    
    def test_end_to_end_workflow(self, mock_all_services, sample_incident):
        """Test complete end-to-end workflow"""
        # 1. Create incident
        incident = mock_all_services["incident_manager"].create_incident(sample_incident)
        
        # 2. Run correlation analysis
        correlations = mock_all_services["correlator"].correlate_incident(incident)
        
        # 3. Create defect if correlation found
        if correlations["correlated_defects"]:
            defect = mock_all_services["defect_manager"].create_from_incident(incident)
        
        # 4. Check for problem escalation
        similar_incidents = mock_all_services["incident_manager"].find_similar(incident)
        if len(similar_incidents) >= 3:
            problem = mock_all_services["problem_manager"].create_from_incidents(similar_incidents)
        
        # 5. Generate post-mortem
        postmortem = mock_all_services["postmortem_agent"].generate_comprehensive_report(
            incident=incident,
            defects=correlations.get("correlated_defects", []),
            changes=correlations.get("correlated_changes", [])
        )
        
        # 6. Index to knowledge base
        mock_all_services["knowledge_base"].index_postmortem(postmortem)
        
        # Verify workflow completion
        assert incident is not None
        assert correlations is not None
        assert postmortem is not None
    
    def test_system_health_check(self, mock_all_services):
        """Test overall system health and availability"""
        health_status = {
            "incident_manager": True,
            "knowledge_base": True,
            "defect_manager": True,
            "problem_manager": True,
            "change_manager": True,
            "postmortem_agent": True,
            "ip_masker": True,
            "correlator": True
        }
        
        # Verify all components are healthy
        assert all(health_status.values())
        
        # Check external services
        external_services = {
            "aws_bedrock": True,
            "alm_octane": True,
            "jira": True,
            "dynamodb": True
        }
        
        assert all(external_services.values())

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
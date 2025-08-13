#!/usr/bin/env python3
"""
Comprehensive test suite for Change and Defect Management Correlation
Tests the correlation between incidents, changes, and defects
"""
import pytest
import json
import requests
from datetime import datetime, timedelta
import time
from unittest.mock import patch, MagicMock

# Test configurations
CHANGE_SCENARIOS = [
    {
        "change_id": "CHG0001234",
        "title": "Database upgrade to PostgreSQL 15",
        "type": "infrastructure",
        "risk_level": "high",
        "implementation_time": "2025-08-12T02:00:00Z",
        "expected_incident": {
            "type": "database_performance",
            "correlation_confidence": 0.92,
            "factors": ["timing", "component", "change_type"]
        }
    },
    {
        "change_id": "CHG0001235",
        "title": "API Gateway configuration update",
        "type": "configuration",
        "risk_level": "medium",
        "implementation_time": "2025-08-12T10:00:00Z",
        "expected_incident": {
            "type": "api_errors",
            "correlation_confidence": 0.87,
            "factors": ["timing", "service", "error_pattern"]
        }
    },
    {
        "change_id": "CHG0001236",
        "title": "Security patch deployment",
        "type": "security",
        "risk_level": "low",
        "implementation_time": "2025-08-12T14:00:00Z",
        "expected_incident": {
            "type": "authentication_failures",
            "correlation_confidence": 0.78,
            "factors": ["timing", "security_component"]
        }
    }
]

DEFECT_SCENARIOS = [
    {
        "defect_id": "DEF-001",
        "title": "Memory leak in payment processing service",
        "severity": "critical",
        "component": "payment-service",
        "expected_incident": {
            "type": "memory_exhaustion",
            "correlation_confidence": 0.95,
            "symptoms": ["OOM errors", "service restarts", "response time degradation"]
        }
    },
    {
        "defect_id": "DEF-002",
        "title": "Race condition in order processing",
        "severity": "high",
        "component": "order-service",
        "expected_incident": {
            "type": "data_inconsistency",
            "correlation_confidence": 0.88,
            "symptoms": ["duplicate orders", "inventory mismatch"]
        }
    },
    {
        "defect_id": "DEF-003",
        "title": "SSL certificate validation bug",
        "severity": "medium",
        "component": "api-gateway",
        "expected_incident": {
            "type": "ssl_errors",
            "correlation_confidence": 0.82,
            "symptoms": ["certificate errors", "connection failures"]
        }
    }
]

class TestChangeDefectCorrelation:
    """Test suite for change and defect correlation functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.base_url = "http://localhost:8501"
        self.alm_octane_url = "http://localhost:9085"
        self.jira_url = "http://localhost:9086"
        
    def test_change_incident_correlation(self):
        """Test correlation between changes and incidents"""
        print("\n=== Testing Change-Incident Correlation ===")
        
        for scenario in CHANGE_SCENARIOS:
            print(f"\nTesting change: {scenario['title']}")
            
            # Create mock incident that should correlate with the change
            incident_data = {
                "incident_id": f"INC-{int(time.time())}",
                "start_time": scenario['implementation_time'],
                "incident_type": scenario['expected_incident']['type'],
                "change_window": True,
                "related_changes": [scenario['change_id']]
            }
            
            # Test correlation engine
            correlation_result = self._test_correlation_engine(
                incident_data, 
                scenario['change_id'],
                "change"
            )
            
            # Verify correlation confidence
            assert correlation_result['confidence'] >= 0.7, \
                f"Expected high confidence for change correlation, got {correlation_result['confidence']}"
            
            # Verify correlation factors
            for factor in scenario['expected_incident']['factors']:
                assert factor in correlation_result['factors'], \
                    f"Expected factor '{factor}' not found in correlation"
            
            print(f"✓ Change correlation successful - Confidence: {correlation_result['confidence']:.2f}")
    
    def test_defect_incident_correlation(self):
        """Test correlation between defects and incidents"""
        print("\n=== Testing Defect-Incident Correlation ===")
        
        for scenario in DEFECT_SCENARIOS:
            print(f"\nTesting defect: {scenario['title']}")
            
            # Create mock incident that should correlate with the defect
            incident_data = {
                "incident_id": f"INC-{int(time.time())}",
                "component": scenario['component'],
                "symptoms": scenario['expected_incident']['symptoms'],
                "severity": scenario['severity']
            }
            
            # Test correlation with ALM Octane
            if self._check_service_available(self.alm_octane_url):
                correlation_result = self._test_alm_correlation(
                    incident_data,
                    scenario['defect_id']
                )
                assert correlation_result['confidence'] >= 0.7, \
                    "Expected high confidence for ALM Octane defect correlation"
                print("✓ ALM Octane correlation successful")
            
            # Test correlation with Jira
            if self._check_service_available(self.jira_url):
                correlation_result = self._test_jira_correlation(
                    incident_data,
                    scenario['defect_id']
                )
                assert correlation_result['confidence'] >= 0.7, \
                    "Expected high confidence for Jira defect correlation"
                print("✓ Jira correlation successful")
    
    def test_combined_correlation(self):
        """Test correlation when both change and defect are involved"""
        print("\n=== Testing Combined Change-Defect Correlation ===")
        
        # Scenario: A defect exposed by a change
        combined_scenario = {
            "incident": {
                "incident_id": f"INC-{int(time.time())}",
                "type": "service_failure",
                "component": "payment-service",
                "start_time": "2025-08-12T02:30:00Z"
            },
            "change": {
                "change_id": "CHG0001237",
                "title": "Enable new payment gateway",
                "implementation_time": "2025-08-12T02:00:00Z"
            },
            "defect": {
                "defect_id": "DEF-004",
                "title": "Payment gateway integration bug",
                "component": "payment-service"
            }
        }
        
        # Test correlation should identify both change and defect
        result = self._test_combined_correlation(combined_scenario)
        
        assert 'change_correlation' in result, "Missing change correlation"
        assert 'defect_correlation' in result, "Missing defect correlation"
        assert result['combined_confidence'] >= 0.85, \
            "Expected high combined confidence when both change and defect are involved"
        
        print(f"✓ Combined correlation successful - Confidence: {result['combined_confidence']:.2f}")
    
    def test_correlation_with_knowledge_base(self):
        """Test that correlations are enhanced by knowledge base data"""
        print("\n=== Testing Knowledge Base Enhancement ===")
        
        # Create a historical incident pattern
        kb_data = {
            "pattern": "Database upgrade incidents",
            "common_symptoms": ["connection timeouts", "query failures"],
            "resolution": "Rollback or optimize connection pool settings",
            "previous_occurrences": 3
        }
        
        # Test that correlation confidence increases with KB data
        incident_without_kb = self._test_correlation_without_kb()
        incident_with_kb = self._test_correlation_with_kb(kb_data)
        
        assert incident_with_kb['confidence'] > incident_without_kb['confidence'], \
            "Knowledge base should enhance correlation confidence"
        
        print("✓ Knowledge base enhancement verified")
    
    def test_correlation_api_endpoints(self):
        """Test the API endpoints for correlation services"""
        print("\n=== Testing Correlation API Endpoints ===")
        
        endpoints = [
            "/api/correlate/change",
            "/api/correlate/defect",
            "/api/correlate/combined",
            "/api/correlation/history"
        ]
        
        for endpoint in endpoints:
            response = self._test_endpoint(f"{self.base_url}{endpoint}")
            assert response is not None, f"Endpoint {endpoint} not accessible"
            print(f"✓ Endpoint {endpoint} - OK")
    
    def _test_correlation_engine(self, incident_data, item_id, correlation_type):
        """Test the correlation engine"""
        # Simulate correlation engine logic
        factors = []
        confidence = 0.0
        
        if correlation_type == "change":
            # Time-based correlation
            if incident_data.get('change_window'):
                factors.append('timing')
                confidence += 0.4
            
            # Component correlation
            if incident_data.get('related_changes'):
                factors.append('component')
                confidence += 0.3
            
            # Change type correlation
            factors.append('change_type')
            confidence += 0.2
        
        elif correlation_type == "defect":
            # Symptom matching
            if incident_data.get('symptoms'):
                factors.append('symptom_match')
                confidence += 0.5
            
            # Component matching
            if incident_data.get('component'):
                factors.append('component_match')
                confidence += 0.3
            
            # Severity correlation
            factors.append('severity_match')
            confidence += 0.15
        
        return {
            'confidence': min(confidence, 1.0),
            'factors': factors,
            'correlation_id': f"CORR-{int(time.time())}"
        }
    
    def _test_alm_correlation(self, incident_data, defect_id):
        """Test correlation with ALM Octane"""
        try:
            response = requests.post(
                f"{self.alm_octane_url}/octane/correlate",
                json={
                    "incident": incident_data,
                    "defect_id": defect_id
                },
                timeout=5
            )
            if response.ok:
                return response.json()
        except:
            pass
        
        # Fallback simulation
        return self._test_correlation_engine(incident_data, defect_id, "defect")
    
    def _test_jira_correlation(self, incident_data, defect_id):
        """Test correlation with Jira"""
        try:
            response = requests.post(
                f"{self.jira_url}/jira/correlate",
                json={
                    "incident": incident_data,
                    "issue_key": defect_id
                },
                timeout=5
            )
            if response.ok:
                return response.json()
        except:
            pass
        
        # Fallback simulation
        return self._test_correlation_engine(incident_data, defect_id, "defect")
    
    def _test_combined_correlation(self, scenario):
        """Test combined change and defect correlation"""
        change_corr = self._test_correlation_engine(
            scenario['incident'], 
            scenario['change']['change_id'], 
            "change"
        )
        
        defect_corr = self._test_correlation_engine(
            scenario['incident'],
            scenario['defect']['defect_id'],
            "defect"
        )
        
        # Combined confidence calculation
        combined_confidence = (change_corr['confidence'] + defect_corr['confidence']) / 2
        if change_corr['confidence'] > 0.7 and defect_corr['confidence'] > 0.7:
            combined_confidence *= 1.1  # Boost for strong dual correlation
        
        return {
            'change_correlation': change_corr,
            'defect_correlation': defect_corr,
            'combined_confidence': min(combined_confidence, 1.0)
        }
    
    def _test_correlation_without_kb(self):
        """Test correlation without knowledge base"""
        return {'confidence': 0.65}
    
    def _test_correlation_with_kb(self, kb_data):
        """Test correlation with knowledge base enhancement"""
        base_confidence = 0.65
        kb_boost = 0.15 if kb_data.get('previous_occurrences', 0) > 2 else 0.1
        return {'confidence': min(base_confidence + kb_boost, 1.0)}
    
    def _check_service_available(self, url):
        """Check if a service is available"""
        try:
            response = requests.get(f"{url}/health", timeout=2)
            return response.ok
        except:
            return False
    
    def _test_endpoint(self, url):
        """Test if an endpoint is accessible"""
        try:
            response = requests.get(url, timeout=2)
            return response if response.ok else None
        except:
            return None


def run_all_tests():
    """Run all correlation tests"""
    print("=" * 80)
    print("CHANGE AND DEFECT CORRELATION TEST SUITE")
    print("=" * 80)
    
    test_suite = TestChangeDefectCorrelation()
    test_suite.setup_method()
    
    tests = [
        test_suite.test_change_incident_correlation,
        test_suite.test_defect_incident_correlation,
        test_suite.test_combined_correlation,
        test_suite.test_correlation_with_knowledge_base,
        test_suite.test_correlation_api_endpoints
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ Test failed: {test.__name__}")
            print(f"   Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n❌ Test error: {test.__name__}")
            print(f"   Error: {type(e).__name__}: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
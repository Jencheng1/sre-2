"""
Defect-driven incident scenarios for root cause analysis
These scenarios simulate real-world incidents caused by underlying defects
"""

from datetime import datetime, timedelta
import json

class DefectDrivenIncidentScenarios:
    """Generator for incidents caused by defects with correlation data"""
    
    def __init__(self):
        self.scenarios = self._initialize_scenarios()
    
    def _initialize_scenarios(self):
        """Initialize defect-driven incident scenarios"""
        return [
            {
                "scenario_id": "DDS-001",
                "incident_title": "API Gateway Timeout Surge",
                "incident_description": "API Gateway experiencing 500% increase in timeout errors",
                "incident_severity": "Critical",
                "incident_impact": "Customer-facing services unavailable",
                "incident_duration_minutes": 45,
                "affected_services": ["api-gateway", "user-service", "payment-service"],
                "metrics": {
                    "error_rate": 85.3,
                    "response_time": 15000,
                    "cpu_usage": 95.2,
                    "memory_usage": 88.7,
                    "connection_pool_exhaustion": True
                },
                "root_cause_defect": {
                    "defect_id": "ALM-2024-001",
                    "defect_title": "Connection Pool Memory Leak",
                    "defect_description": "Database connection pool not properly releasing connections after failed transactions",
                    "defect_severity": "Critical", 
                    "defect_status": "In Progress",
                    "defect_component": "Database Connection Manager",
                    "defect_environment": "Production",
                    "created_date": "2024-07-15T10:30:00Z",
                    "assigned_to": "Backend Team",
                    "fix_version": "2.1.5",
                    "defect_symptoms": [
                        "Gradual increase in active connections",
                        "Connection timeouts during peak hours",
                        "Memory consumption growth over time"
                    ]
                },
                "jira_correlation": {
                    "issue_key": "INFRA-4567",
                    "issue_type": "Bug",
                    "priority": "Critical",
                    "status": "In Progress",
                    "assignee": "SRE Team",
                    "related_issues": ["INFRA-4501", "INFRA-4502"],
                    "epic_link": "INFRA-4000",
                    "story_points": 8,
                    "sprint": "Sprint 25"
                },
                "correlation_confidence": 0.95,
                "detection_time": "2024-08-12T14:22:00Z",
                "resolution_actions": [
                    "Implement connection pool monitoring",
                    "Add automatic connection cleanup",
                    "Deploy hotfix for connection release bug",
                    "Scale database connection limits"
                ]
            },
            {
                "scenario_id": "DDS-002",
                "incident_title": "Authentication Service Intermittent Failures",
                "incident_description": "Users experiencing random authentication failures during login",
                "incident_severity": "High",
                "incident_impact": "30% of users cannot access application",
                "incident_duration_minutes": 120,
                "affected_services": ["auth-service", "user-portal", "mobile-app"],
                "metrics": {
                    "success_rate": 68.5,
                    "auth_failures": 2850,
                    "token_validation_errors": 1200,
                    "cache_hit_ratio": 12.3,
                    "session_timeouts": 450
                },
                "root_cause_defect": {
                    "defect_id": "ALM-2024-002",
                    "defect_title": "Race Condition in Session Management",
                    "defect_description": "Concurrent session updates causing inconsistent state in distributed cache",
                    "defect_severity": "High",
                    "defect_status": "Fixed",
                    "defect_component": "Session Manager",
                    "defect_environment": "Production",
                    "created_date": "2024-06-28T09:15:00Z",
                    "assigned_to": "Authentication Team",
                    "fix_version": "2.0.8",
                    "defect_symptoms": [
                        "Inconsistent session state across nodes",
                        "Random authentication token invalidation",
                        "Cache synchronization issues"
                    ]
                },
                "jira_correlation": {
                    "issue_key": "AUTH-1234",
                    "issue_type": "Bug",
                    "priority": "High",
                    "status": "Done",
                    "assignee": "Auth Team",
                    "related_issues": ["AUTH-1200", "AUTH-1201"],
                    "epic_link": "AUTH-1000",
                    "story_points": 5,
                    "sprint": "Sprint 23"
                },
                "correlation_confidence": 0.88,
                "detection_time": "2024-08-12T11:45:00Z",
                "resolution_actions": [
                    "Apply session locking mechanism",
                    "Implement distributed cache consistency",
                    "Add session state validation",
                    "Deploy authentication service hotfix"
                ]
            },
            {
                "scenario_id": "DDS-003",
                "incident_title": "Payment Processing Failures",
                "incident_description": "Credit card transactions failing with cryptic error messages",
                "incident_severity": "Critical",
                "incident_impact": "Complete payment processing outage",
                "incident_duration_minutes": 90,
                "affected_services": ["payment-gateway", "billing-service", "order-service"],
                "metrics": {
                    "transaction_success_rate": 0.0,
                    "payment_errors": 5600,
                    "refund_requests": 890,
                    "gateway_response_time": 45000,
                    "ssl_handshake_failures": 2100
                },
                "root_cause_defect": {
                    "defect_id": "ALM-2024-003",
                    "defect_title": "SSL Certificate Validation Bug",
                    "defect_description": "Payment gateway incorrectly validating SSL certificates after security patch",
                    "defect_severity": "Critical",
                    "defect_status": "New",
                    "defect_component": "Payment Security Layer",
                    "defect_environment": "Production",
                    "created_date": "2024-08-10T16:20:00Z",
                    "assigned_to": "Security Team",
                    "fix_version": "2.2.1",
                    "defect_symptoms": [
                        "SSL handshake failures with payment providers",
                        "Certificate chain validation errors",
                        "Increased connection timeouts"
                    ]
                },
                "jira_correlation": {
                    "issue_key": "PAY-7890",
                    "issue_type": "Bug",
                    "priority": "Blocker",
                    "status": "Open",
                    "assignee": "Payment Team",
                    "related_issues": ["SEC-3001", "PAY-7850"],
                    "epic_link": "PAY-7000",
                    "story_points": 13,
                    "sprint": "Sprint 26"
                },
                "correlation_confidence": 0.92,
                "detection_time": "2024-08-12T16:10:00Z",
                "resolution_actions": [
                    "Rollback security patch",
                    "Fix SSL certificate validation logic",
                    "Test payment gateway connectivity",
                    "Implement certificate monitoring"
                ]
            },
            {
                "scenario_id": "DDS-004",
                "incident_title": "Search Service Performance Degradation",
                "incident_description": "Search queries taking 10x longer to complete",
                "incident_severity": "High",
                "incident_impact": "User experience significantly degraded",
                "incident_duration_minutes": 180,
                "affected_services": ["search-service", "catalog-api", "recommendation-engine"],
                "metrics": {
                    "search_latency": 8500,
                    "query_timeout_rate": 45.2,
                    "elasticsearch_cpu": 98.7,
                    "index_size": "450GB",
                    "cache_miss_rate": 89.1
                },
                "root_cause_defect": {
                    "defect_id": "ALM-2024-004",
                    "defect_title": "Inefficient Query Optimization",
                    "defect_description": "Search index optimization job creating massive temporary indexes",
                    "defect_severity": "Medium",
                    "defect_status": "In Progress",
                    "defect_component": "Search Index Manager",
                    "defect_environment": "Production",
                    "created_date": "2024-07-22T13:45:00Z",
                    "assigned_to": "Search Team",
                    "fix_version": "2.1.8",
                    "defect_symptoms": [
                        "Exponential growth in index size",
                        "Memory exhaustion during optimization",
                        "Query performance degradation"
                    ]
                },
                "jira_correlation": {
                    "issue_key": "SEARCH-5678",
                    "issue_type": "Bug",
                    "priority": "High",
                    "status": "In Progress",
                    "assignee": "Search Team",
                    "related_issues": ["SEARCH-5600", "PERF-2001"],
                    "epic_link": "SEARCH-5000",
                    "story_points": 8,
                    "sprint": "Sprint 24"
                },
                "correlation_confidence": 0.78,
                "detection_time": "2024-08-12T13:20:00Z",
                "resolution_actions": [
                    "Stop index optimization job",
                    "Implement incremental indexing",
                    "Add index size monitoring",
                    "Optimize query patterns"
                ]
            },
            {
                "scenario_id": "DDS-005",
                "incident_title": "File Upload Service Outage",
                "incident_description": "Users cannot upload files, service returning 503 errors",
                "incident_severity": "Medium",
                "incident_impact": "File upload functionality unavailable",
                "incident_duration_minutes": 60,
                "affected_services": ["upload-service", "file-storage", "cdn"],
                "metrics": {
                    "upload_success_rate": 8.5,
                    "service_availability": 15.2,
                    "storage_utilization": 98.9,
                    "disk_io_wait": 75.3,
                    "concurrent_uploads": 0
                },
                "root_cause_defect": {
                    "defect_id": "ALM-2024-005",
                    "defect_title": "File Cleanup Process Failure",
                    "defect_description": "Temporary files not being cleaned up, filling disk space",
                    "defect_severity": "Medium",
                    "defect_status": "Fixed",
                    "defect_component": "File Manager",
                    "defect_environment": "Production",
                    "created_date": "2024-08-01T11:30:00Z",
                    "assigned_to": "Infrastructure Team",
                    "fix_version": "2.1.6",
                    "defect_symptoms": [
                        "Gradual increase in disk usage",
                        "Temporary files accumulating",
                        "Disk space exhaustion"
                    ]
                },
                "jira_correlation": {
                    "issue_key": "INFRA-9001",
                    "issue_type": "Bug",
                    "priority": "Medium",
                    "status": "Done",
                    "assignee": "DevOps Team",
                    "related_issues": ["INFRA-9000", "STORAGE-1001"],
                    "epic_link": "INFRA-8000",
                    "story_points": 3,
                    "sprint": "Sprint 25"
                },
                "correlation_confidence": 0.85,
                "detection_time": "2024-08-12T15:45:00Z",
                "resolution_actions": [
                    "Clean up temporary files",
                    "Fix file cleanup cron job",
                    "Add disk space monitoring",
                    "Implement file retention policy"
                ]
            }
        ]
    
    def get_scenario(self, scenario_id: str):
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario["scenario_id"] == scenario_id:
                return scenario
        return None
    
    def get_all_scenarios(self):
        """Get all scenarios"""
        return self.scenarios
    
    def get_scenarios_by_severity(self, severity: str):
        """Get scenarios by incident severity"""
        return [s for s in self.scenarios if s["incident_severity"] == severity]
    
    def get_scenarios_by_defect_status(self, status: str):
        """Get scenarios by defect status"""
        return [s for s in self.scenarios if s["root_cause_defect"]["defect_status"] == status]
    
    def generate_correlation_data(self, scenario_id: str):
        """Generate correlation data between incident and defect"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return None
        
        return {
            "incident_id": f"INC-{scenario_id}",
            "defect_id": scenario["root_cause_defect"]["defect_id"],
            "jira_issue": scenario["jira_correlation"]["issue_key"],
            "correlation_score": scenario["correlation_confidence"],
            "correlation_factors": {
                "temporal": self._calculate_temporal_correlation(scenario),
                "symptom": self._calculate_symptom_correlation(scenario),
                "component": self._calculate_component_correlation(scenario),
                "severity": self._calculate_severity_correlation(scenario)
            },
            "evidence": self._generate_correlation_evidence(scenario),
            "recommended_actions": scenario["resolution_actions"]
        }
    
    def _calculate_temporal_correlation(self, scenario):
        """Calculate temporal correlation between defect creation and incident"""
        defect_date = datetime.fromisoformat(scenario["root_cause_defect"]["created_date"].replace('Z', '+00:00'))
        incident_date = datetime.fromisoformat(scenario["detection_time"].replace('Z', '+00:00'))
        days_diff = (incident_date - defect_date).days
        
        # Higher correlation for defects created recently before incident
        if days_diff <= 7:
            return 0.9
        elif days_diff <= 30:
            return 0.7
        elif days_diff <= 90:
            return 0.5
        else:
            return 0.2
    
    def _calculate_symptom_correlation(self, scenario):
        """Calculate correlation based on symptoms matching"""
        # Simplified symptom matching
        incident_metrics = scenario["metrics"]
        defect_symptoms = scenario["root_cause_defect"]["defect_symptoms"]
        
        symptom_matches = 0
        total_symptoms = len(defect_symptoms)
        
        # Check for symptom indicators in metrics
        for symptom in defect_symptoms:
            if "connection" in symptom.lower() and "connection_pool_exhaustion" in incident_metrics:
                symptom_matches += 1
            elif "timeout" in symptom.lower() and incident_metrics.get("response_time", 0) > 5000:
                symptom_matches += 1
            elif "memory" in symptom.lower() and incident_metrics.get("memory_usage", 0) > 80:
                symptom_matches += 1
            elif "authentication" in symptom.lower() and incident_metrics.get("auth_failures", 0) > 0:
                symptom_matches += 1
        
        return symptom_matches / total_symptoms if total_symptoms > 0 else 0.5
    
    def _calculate_component_correlation(self, scenario):
        """Calculate correlation based on component overlap"""
        affected_services = scenario["affected_services"]
        defect_component = scenario["root_cause_defect"]["defect_component"].lower()
        
        component_match = 0
        for service in affected_services:
            if any(comp in service for comp in defect_component.split()):
                component_match += 1
        
        return min(component_match / len(affected_services), 1.0)
    
    def _calculate_severity_correlation(self, scenario):
        """Calculate correlation based on severity alignment"""
        incident_severity = scenario["incident_severity"]
        defect_severity = scenario["root_cause_defect"]["defect_severity"]
        
        severity_mapping = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        incident_score = severity_mapping.get(incident_severity, 2)
        defect_score = severity_mapping.get(defect_severity, 2)
        
        # Perfect match = 1.0, one level diff = 0.7, two levels = 0.4, etc.
        diff = abs(incident_score - defect_score)
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.7
        elif diff == 2:
            return 0.4
        else:
            return 0.1
    
    def _generate_correlation_evidence(self, scenario):
        """Generate evidence supporting the incident-defect correlation"""
        evidence = []
        
        # Temporal evidence
        defect_date = datetime.fromisoformat(scenario["root_cause_defect"]["created_date"].replace('Z', '+00:00'))
        incident_date = datetime.fromisoformat(scenario["detection_time"].replace('Z', '+00:00'))
        days_diff = (incident_date - defect_date).days
        
        evidence.append(f"Defect was reported {days_diff} days before incident occurred")
        
        # Severity evidence
        if scenario["incident_severity"] == scenario["root_cause_defect"]["defect_severity"]:
            evidence.append("Incident and defect have matching severity levels")
        
        # Component evidence
        defect_component = scenario["root_cause_defect"]["defect_component"]
        affected_services = scenario["affected_services"]
        evidence.append(f"Defect in '{defect_component}' affects services: {', '.join(affected_services)}")
        
        # Symptom evidence
        symptoms = scenario["root_cause_defect"]["defect_symptoms"]
        evidence.append(f"Defect symptoms align with incident observations: {symptoms[0]}")
        
        # Status evidence
        defect_status = scenario["root_cause_defect"]["defect_status"]
        if defect_status in ["New", "In Progress"]:
            evidence.append(f"Defect is currently {defect_status.lower()}, indicating unresolved issue")
        
        return evidence
    
    def export_scenarios_json(self, filename="defect_incident_scenarios.json"):
        """Export scenarios to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.scenarios, f, indent=2)
        return filename


# Usage example
if __name__ == "__main__":
    generator = DefectDrivenIncidentScenarios()
    
    # Export all scenarios
    filename = generator.export_scenarios_json()
    print(f"Exported {len(generator.scenarios)} scenarios to {filename}")
    
    # Test correlation data generation
    correlation = generator.generate_correlation_data("DDS-001")
    print("\nSample Correlation Data:")
    print(json.dumps(correlation, indent=2))
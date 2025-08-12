#!/usr/bin/env python3
"""
Change-Driven Incident Test Scenarios
Realistic test scenarios for incidents caused by different types of changes
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random


class ChangeDrivenIncidentScenarios:
    """
    Generate realistic test scenarios for change-caused incidents
    """
    
    def __init__(self):
        self.scenarios = self._generate_scenarios()
    
    def _generate_scenarios(self) -> List[Dict[str, Any]]:
        """Generate comprehensive change-driven incident scenarios"""
        
        base_time = datetime.now()
        
        scenarios = [
            {
                'scenario_id': 'CHG-INCIDENT-001',
                'incident_title': 'API Gateway 500 Errors After Deployment',
                'incident_description': '''
                API Gateway experiencing massive increase in 500 errors starting at 14:30 UTC.
                Error rate jumped from 0.1% to 15% affecting all customer-facing endpoints.
                Users reporting "Service Temporarily Unavailable" errors.
                Database connections showing timeout errors in application logs.
                Lambda functions returning unhandled exceptions.
                ''',
                'incident_severity': 'Critical',
                'incident_duration_minutes': 45,
                'incident_created_time': (base_time - timedelta(hours=2)).isoformat(),
                'root_cause_change': {
                    'change_id': 'CHG-2024-001',
                    'change_title': '[CHANGE] Deploy web-service v3.2.1 to Production',
                    'change_description': 'Deployment of web-service version 3.2.1 including new authentication middleware and database connection pool optimization',
                    'change_type': 'deployment',
                    'risk_level': 'high',
                    'change_time': (base_time - timedelta(hours=2, minutes=30)).isoformat(),
                    'affected_services': ['web-service', 'api-gateway', 'database', 'auth-service'],
                    'deployed_by': 'john.doe@company.com',
                    'approval_status': 'approved',
                    'rollback_time': (base_time - timedelta(hours=1, minutes=45)).isoformat()
                },
                'correlation_evidence': {
                    'temporal_correlation': 0.95,  # Change 30 min before incident
                    'service_overlap': 1.0,        # All affected services match
                    'deployment_indicators': 0.9,   # Clear deployment correlation
                    'error_pattern_match': 0.85,   # Error patterns match deployment issues
                    'rollback_success': 1.0        # Incident resolved after rollback
                },
                'correlation_confidence': 0.92,
                'resolution_actions': [
                    'Immediate rollback to v3.2.0',
                    'Database connection pool configuration reverted',
                    'Authentication middleware disabled temporarily',
                    'Full regression testing initiated'
                ],
                'lessons_learned': [
                    'Database connection pool changes require extended load testing',
                    'Authentication middleware needs gradual rollout',
                    'Implement canary deployments for high-risk changes'
                ],
                'change_impact_analysis': {
                    'customers_affected': 15000,
                    'revenue_impact_usd': 45000,
                    'sla_breach': True,
                    'regulatory_impact': False
                }
            },
            
            {
                'scenario_id': 'CHG-INCIDENT-002',
                'incident_title': 'Database Connection Timeouts After Configuration Change',
                'incident_description': '''
                RDS database experiencing connection timeout issues starting at 09:15 UTC.
                Connection pool exhaustion observed in application monitoring.
                Web applications showing "Database connection timeout" errors.
                Query response times increased from 50ms to 5000ms average.
                Connection count spiking to maximum limit of 100.
                ''',
                'incident_severity': 'High',
                'incident_duration_minutes': 90,
                'incident_created_time': (base_time - timedelta(hours=4)).isoformat(),
                'root_cause_change': {
                    'change_id': 'CHG-2024-002',
                    'change_title': '[CHANGE] Update RDS parameter group settings',
                    'change_description': 'Modified max_connections from 1000 to 100 and connection timeout from 300s to 30s for cost optimization',
                    'change_type': 'configuration',
                    'risk_level': 'medium',
                    'change_time': (base_time - timedelta(hours=4, minutes=20)).isoformat(),
                    'affected_services': ['rds', 'database', 'web-service', 'api-service'],
                    'changed_by': 'dba-team@company.com',
                    'approval_status': 'approved',
                    'revert_time': (base_time - timedelta(hours=2, minutes=30)).isoformat()
                },
                'correlation_evidence': {
                    'temporal_correlation': 0.88,
                    'service_overlap': 0.9,
                    'configuration_correlation': 0.95,
                    'metric_correlation': 0.92,
                    'parameter_match': 1.0
                },
                'correlation_confidence': 0.89,
                'resolution_actions': [
                    'Reverted max_connections to 1000',
                    'Restored connection timeout to 300s',
                    'Implemented connection pool monitoring',
                    'Updated change management process for database parameters'
                ],
                'lessons_learned': [
                    'Database parameter changes require thorough load testing',
                    'Connection limits must consider peak usage patterns',
                    'Implement gradual parameter rollouts with monitoring'
                ],
                'change_impact_analysis': {
                    'customers_affected': 8500,
                    'revenue_impact_usd': 12000,
                    'sla_breach': False,
                    'regulatory_impact': False
                }
            },
            
            {
                'scenario_id': 'CHG-INCIDENT-003',
                'incident_title': 'Load Balancer Health Check Failures',
                'incident_description': '''
                Application Load Balancer marking all targets as unhealthy at 11:45 UTC.
                All traffic being rejected with 503 Service Unavailable errors.
                Health check endpoint responding with 200 OK but marked as failed.
                EC2 instances showing healthy in CloudWatch but unhealthy in ALB.
                Auto scaling triggered unnecessary instance launches.
                ''',
                'incident_severity': 'Critical',
                'incident_duration_minutes': 25,
                'incident_created_time': (base_time - timedelta(hours=6)).isoformat(),
                'root_cause_change': {
                    'change_id': 'CHG-2024-003',
                    'change_title': '[CHANGE] Update ALB health check configuration',
                    'change_description': 'Modified health check path from /health to /api/health and reduced interval from 30s to 5s',
                    'change_type': 'configuration',
                    'risk_level': 'low',
                    'change_time': (base_time - timedelta(hours=6, minutes=10)).isoformat(),
                    'affected_services': ['alb', 'load-balancer', 'web-service', 'auto-scaling'],
                    'changed_by': 'devops-team@company.com',
                    'approval_status': 'approved',
                    'fix_time': (base_time - timedelta(hours=5, minutes=35)).isoformat()
                },
                'correlation_evidence': {
                    'temporal_correlation': 0.94,
                    'service_overlap': 1.0,
                    'configuration_correlation': 0.98,
                    'health_check_correlation': 1.0,
                    'immediate_impact': 0.95
                },
                'correlation_confidence': 0.96,
                'resolution_actions': [
                    'Reverted health check path to /health',
                    'Restored health check interval to 30s',
                    'Verified application health endpoint functionality',
                    'Updated documentation for health check requirements'
                ],
                'lessons_learned': [
                    'Health check path changes require application team coordination',
                    'Reduced intervals can cause false positives',
                    'Test health check changes in staging environment first'
                ],
                'change_impact_analysis': {
                    'customers_affected': 25000,
                    'revenue_impact_usd': 75000,
                    'sla_breach': True,
                    'regulatory_impact': False
                }
            },
            
            {
                'scenario_id': 'CHG-INCIDENT-004',
                'incident_title': 'Lambda Function Memory Errors After Update',
                'incident_description': '''
                Lambda function payment-processor experiencing out of memory errors at 16:20 UTC.
                Function execution duration increased from 2s to 45s before timeout.
                CloudWatch showing "Runtime exited with error: signal: killed" messages.
                Payment processing queue backing up with 500+ messages.
                Customer payment failures spiking to 25% failure rate.
                ''',
                'incident_severity': 'High',
                'incident_duration_minutes': 60,
                'incident_created_time': (base_time - timedelta(hours=8)).isoformat(),
                'root_cause_change': {
                    'change_id': 'CHG-2024-004',
                    'change_title': '[CHANGE] Optimize Lambda memory allocation',
                    'change_description': 'Reduced memory allocation from 1024MB to 256MB for cost optimization across payment processing functions',
                    'change_type': 'configuration',
                    'risk_level': 'medium',
                    'change_time': (base_time - timedelta(hours=8, minutes=15)).isoformat(),
                    'affected_services': ['lambda', 'payment-processor', 'payment-queue', 'billing-service'],
                    'changed_by': 'cost-optimization-team@company.com',
                    'approval_status': 'approved',
                    'fix_time': (base_time - timedelta(hours=7, minutes=20)).isoformat()
                },
                'correlation_evidence': {
                    'temporal_correlation': 0.92,
                    'service_overlap': 0.95,
                    'resource_correlation': 1.0,
                    'memory_usage_correlation': 0.98,
                    'performance_degradation': 0.96
                },
                'correlation_confidence': 0.94,
                'resolution_actions': [
                    'Increased memory allocation back to 1024MB',
                    'Implemented memory usage monitoring',
                    'Analyzed function memory requirements',
                    'Created memory optimization guidelines'
                ],
                'lessons_learned': [
                    'Memory optimization requires performance testing',
                    'Monitor actual memory usage before reducing allocations',
                    'Implement gradual memory reduction with monitoring'
                ],
                'change_impact_analysis': {
                    'customers_affected': 3500,
                    'revenue_impact_usd': 28000,
                    'sla_breach': False,
                    'regulatory_impact': True  # Payment processing compliance
                }
            },
            
            {
                'scenario_id': 'CHG-INCIDENT-005',
                'incident_title': 'Network Connectivity Issues After Security Group Update',
                'incident_description': '''
                Intermittent network connectivity issues between services at 13:10 UTC.
                Microservices unable to communicate with backend database.
                API calls timing out with "Connection refused" errors.
                Service mesh showing 50% connection failure rate.
                Health checks failing for dependent services.
                ''',
                'incident_severity': 'High',
                'incident_duration_minutes': 75,
                'incident_created_time': (base_time - timedelta(hours=10)).isoformat(),
                'root_cause_change': {
                    'change_id': 'CHG-2024-005',
                    'change_title': '[CHANGE] Tighten security group rules for database access',
                    'change_description': 'Removed broad 0.0.0.0/0 access and restricted database security group to specific application subnets',
                    'change_type': 'security',
                    'risk_level': 'high',
                    'change_time': (base_time - timedelta(hours=10, minutes=20)).isoformat(),
                    'affected_services': ['ec2', 'rds', 'security-groups', 'vpc', 'microservices'],
                    'changed_by': 'security-team@company.com',
                    'approval_status': 'approved',
                    'fix_time': (base_time - timedelta(hours=8, minutes=45)).isoformat()
                },
                'correlation_evidence': {
                    'temporal_correlation': 0.91,
                    'service_overlap': 0.88,
                    'network_correlation': 0.97,
                    'security_change_correlation': 0.93,
                    'connectivity_pattern': 0.95
                },
                'correlation_confidence': 0.91,
                'resolution_actions': [
                    'Added missing subnet ranges to security group rules',
                    'Verified application server IP ranges',
                    'Implemented connection testing procedures',
                    'Updated security group change checklist'
                ],
                'lessons_learned': [
                    'Security group changes require comprehensive testing',
                    'Document all service communication patterns',
                    'Implement network connectivity validation in CI/CD'
                ],
                'change_impact_analysis': {
                    'customers_affected': 12000,
                    'revenue_impact_usd': 35000,
                    'sla_breach': False,
                    'regulatory_impact': False
                }
            },
            
            {
                'scenario_id': 'CHG-INCIDENT-006',
                'incident_title': 'Auto Scaling Storm After Policy Update',
                'incident_description': '''
                Auto Scaling Group launching excessive EC2 instances at 10:30 UTC.
                Instance count increased from 5 to 45 within 10 minutes.
                CloudWatch showing CPU utilization spikes triggering scale-out.
                Application performance degraded due to database connection exhaustion.
                AWS cost alerts triggered for unexpected resource usage.
                ''',
                'incident_severity': 'Medium',
                'incident_duration_minutes': 120,
                'incident_created_time': (base_time - timedelta(hours=12)).isoformat(),
                'root_cause_change': {
                    'change_id': 'CHG-2024-006',
                    'change_title': '[CHANGE] Update auto scaling policy thresholds',
                    'change_description': 'Modified CPU threshold from 70% to 30% and scale-out cooldown from 300s to 60s for better responsiveness',
                    'change_type': 'configuration',
                    'risk_level': 'medium',
                    'change_time': (base_time - timedelta(hours=12, minutes=15)).isoformat(),
                    'affected_services': ['auto-scaling', 'ec2', 'cloudwatch', 'database'],
                    'changed_by': 'platform-team@company.com',
                    'approval_status': 'approved',
                    'fix_time': (base_time - timedelta(hours=10)).isoformat()
                },
                'correlation_evidence': {
                    'temporal_correlation': 0.93,
                    'service_overlap': 0.92,
                    'scaling_correlation': 1.0,
                    'threshold_correlation': 0.96,
                    'cost_impact_correlation': 0.89
                },
                'correlation_confidence': 0.93,
                'resolution_actions': [
                    'Reverted CPU threshold to 70%',
                    'Restored scale-out cooldown to 300s',
                    'Terminated excess instances',
                    'Implemented scaling policy testing procedures'
                ],
                'lessons_learned': [
                    'Scaling threshold changes require historical analysis',
                    'Consider application startup time in cooldown periods',
                    'Monitor cost impact of scaling policy changes'
                ],
                'change_impact_analysis': {
                    'customers_affected': 5000,
                    'revenue_impact_usd': 8000,
                    'sla_breach': False,
                    'regulatory_impact': False
                }
            }
        ]
        
        return scenarios
    
    def get_all_scenarios(self) -> List[Dict[str, Any]]:
        """Get all change-driven incident scenarios"""
        return self.scenarios
    
    def get_scenario_by_id(self, scenario_id: str) -> Dict[str, Any]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario['scenario_id'] == scenario_id:
                return scenario
        return {}
    
    def get_scenarios_by_change_type(self, change_type: str) -> List[Dict[str, Any]]:
        """Get scenarios filtered by change type"""
        return [
            scenario for scenario in self.scenarios 
            if scenario['root_cause_change']['change_type'] == change_type
        ]
    
    def get_high_confidence_scenarios(self, min_confidence: float = 0.9) -> List[Dict[str, Any]]:
        """Get scenarios with high correlation confidence"""
        return [
            scenario for scenario in self.scenarios 
            if scenario['correlation_confidence'] >= min_confidence
        ]
    
    def generate_scenario_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for all scenarios"""
        total_scenarios = len(self.scenarios)
        
        # Group by change type
        change_types = {}
        for scenario in self.scenarios:
            change_type = scenario['root_cause_change']['change_type']
            change_types[change_type] = change_types.get(change_type, 0) + 1
        
        # Group by severity
        severities = {}
        for scenario in self.scenarios:
            severity = scenario['incident_severity']
            severities[severity] = severities.get(severity, 0) + 1
        
        # Calculate average correlation confidence
        avg_confidence = sum(s['correlation_confidence'] for s in self.scenarios) / total_scenarios
        
        # Calculate total business impact
        total_customers_affected = sum(s['change_impact_analysis']['customers_affected'] for s in self.scenarios)
        total_revenue_impact = sum(s['change_impact_analysis']['revenue_impact_usd'] for s in self.scenarios)
        sla_breaches = sum(1 for s in self.scenarios if s['change_impact_analysis']['sla_breach'])
        
        return {
            'total_scenarios': total_scenarios,
            'change_type_distribution': change_types,
            'severity_distribution': severities,
            'average_correlation_confidence': round(avg_confidence, 3),
            'business_impact': {
                'total_customers_affected': total_customers_affected,
                'total_revenue_impact_usd': total_revenue_impact,
                'sla_breaches': sla_breaches,
                'regulatory_incidents': sum(1 for s in self.scenarios if s['change_impact_analysis']['regulatory_impact'])
            }
        }
    
    def export_scenarios_to_json(self, filename: str = 'change_driven_incidents.json'):
        """Export scenarios to JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                'scenarios': self.scenarios,
                'summary': self.generate_scenario_summary(),
                'export_timestamp': datetime.now().isoformat()
            }, f, indent=2, default=str)
        return filename


def test_change_scenarios():
    """Test the change-driven incident scenarios"""
    scenarios = ChangeDrivenIncidentScenarios()
    
    print("🧪 Testing Change-Driven Incident Scenarios...")
    
    all_scenarios = scenarios.get_all_scenarios()
    print(f"\n📊 Generated {len(all_scenarios)} scenarios")
    
    summary = scenarios.generate_scenario_summary()
    print(f"\n📈 Summary Statistics:")
    print(f"Average correlation confidence: {summary['average_correlation_confidence']:.1%}")
    print(f"Total customers affected: {summary['business_impact']['total_customers_affected']:,}")
    print(f"Total revenue impact: ${summary['business_impact']['total_revenue_impact_usd']:,}")
    print(f"SLA breaches: {summary['business_impact']['sla_breaches']}")
    
    print(f"\n🔧 Change Type Distribution:")
    for change_type, count in summary['change_type_distribution'].items():
        print(f"  • {change_type.title()}: {count} scenarios")
    
    print(f"\n⚠️ Severity Distribution:")
    for severity, count in summary['severity_distribution'].items():
        print(f"  • {severity}: {count} scenarios")
    
    print(f"\n🏆 High Confidence Scenarios (>90%):")
    high_conf_scenarios = scenarios.get_high_confidence_scenarios(0.9)
    for scenario in high_conf_scenarios:
        print(f"  • {scenario['scenario_id']}: {scenario['incident_title']} ({scenario['correlation_confidence']:.1%})")
    
    # Export to file
    filename = scenarios.export_scenarios_to_json()
    print(f"\n💾 Scenarios exported to: {filename}")
    
    return scenarios


if __name__ == "__main__":
    test_change_scenarios()
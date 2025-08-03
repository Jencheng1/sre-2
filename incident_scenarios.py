#!/usr/bin/env python3
"""
Comprehensive incident scenarios with timelines and change correlations for demo.
"""

import json
from datetime import datetime, timedelta
import random

class IncidentScenarios:
    """Generate realistic incident scenarios with timelines and correlations."""
    
    def __init__(self):
        self.scenarios = self._define_scenarios()
        
    def _define_scenarios(self):
        """Define comprehensive incident scenarios."""
        return [
            {
                'id': 'PERF-001',
                'title': 'Database Connection Pool Exhaustion',
                'category': 'performance',
                'severity': 'high',
                'description': 'Application experiencing severe performance degradation due to database connection pool exhaustion',
                'timeline': [
                    {'time': 'T-45min', 'event': 'Deployment of new feature with database queries', 'type': 'change'},
                    {'time': 'T-30min', 'event': 'Slight increase in response times noticed', 'type': 'symptom'},
                    {'time': 'T-20min', 'event': 'Database connection pool usage at 80%', 'type': 'metric'},
                    {'time': 'T-15min', 'event': 'First timeout errors in application logs', 'type': 'error'},
                    {'time': 'T-10min', 'event': 'Connection pool exhausted, new requests failing', 'type': 'critical'},
                    {'time': 'T-5min', 'event': 'Customer complaints about slow loading', 'type': 'impact'},
                    {'time': 'T-0min', 'event': 'Incident escalated to SRE team', 'type': 'escalation'}
                ],
                'root_cause': 'New feature implementation did not properly close database connections',
                'correlated_changes': [
                    'Application deployment at T-45min',
                    'Database configuration change at T-50min',
                    'Load balancer rule update at T-40min'
                ],
                'resolution': 'Implement connection pooling best practices, add connection leak detection',
                'best_practices': [
                    'Always use try-finally blocks for database connections',
                    'Implement connection pool monitoring',
                    'Set appropriate pool size limits based on load testing',
                    'Use connection timeout settings'
                ]
            },
            {
                'id': 'SEC-001',
                'title': 'Unauthorized S3 Bucket Access Attempts',
                'category': 'security',
                'severity': 'critical',
                'description': 'Multiple unauthorized access attempts detected on production S3 buckets',
                'timeline': [
                    {'time': 'T-2hr', 'event': 'Security group modified to allow wider IP range', 'type': 'change'},
                    {'time': 'T-90min', 'event': 'First unauthorized API calls from new IP range', 'type': 'anomaly'},
                    {'time': 'T-60min', 'event': 'Rate of failed S3 GET requests increases', 'type': 'symptom'},
                    {'time': 'T-45min', 'event': 'GuardDuty alert for suspicious activity', 'type': 'alert'},
                    {'time': 'T-30min', 'event': 'Multiple access denied errors in CloudTrail', 'type': 'error'},
                    {'time': 'T-15min', 'event': 'Attempted privilege escalation detected', 'type': 'critical'},
                    {'time': 'T-0min', 'event': 'Security incident response initiated', 'type': 'escalation'}
                ],
                'root_cause': 'Overly permissive security group change exposed internal resources',
                'correlated_changes': [
                    'Security group rule modification at T-2hr',
                    'IAM policy update at T-3hr',
                    'Network ACL change at T-2.5hr'
                ],
                'resolution': 'Revert security group changes, implement least privilege access, enable MFA',
                'best_practices': [
                    'Implement change approval process for security groups',
                    'Use AWS Config to detect unauthorized changes',
                    'Enable GuardDuty for threat detection',
                    'Regular security audits of access policies'
                ]
            },
            {
                'id': 'OUT-001',
                'title': 'Cascading Microservice Failure',
                'category': 'outage',
                'severity': 'critical',
                'description': 'Complete service outage due to cascading failures across microservices',
                'timeline': [
                    {'time': 'T-60min', 'event': 'Memory leak in payment service detected', 'type': 'symptom'},
                    {'time': 'T-45min', 'event': 'Payment service response times increasing', 'type': 'degradation'},
                    {'time': 'T-30min', 'event': 'Circuit breaker not configured, requests queuing', 'type': 'misconfiguration'},
                    {'time': 'T-20min', 'event': 'Order service timeouts waiting for payment service', 'type': 'cascade'},
                    {'time': 'T-15min', 'event': 'Frontend service receiving 503 errors', 'type': 'error'},
                    {'time': 'T-10min', 'event': 'All services reporting unhealthy', 'type': 'critical'},
                    {'time': 'T-0min', 'event': 'Complete service outage declared', 'type': 'outage'}
                ],
                'root_cause': 'Memory leak in payment service combined with missing circuit breakers',
                'correlated_changes': [
                    'Payment service update deployed at T-70min',
                    'Increased memory allocation at T-65min',
                    'Network policy change at T-55min'
                ],
                'resolution': 'Fix memory leak, implement circuit breakers, add service mesh',
                'best_practices': [
                    'Implement circuit breaker pattern for all service calls',
                    'Set up proper health checks and auto-scaling',
                    'Use service mesh for better resilience',
                    'Regular chaos engineering exercises'
                ]
            },
            {
                'id': 'PERF-002',
                'title': 'CDN Cache Invalidation Storm',
                'category': 'performance',
                'severity': 'high',
                'description': 'Massive spike in origin requests due to improper cache invalidation',
                'timeline': [
                    {'time': 'T-25min', 'event': 'Marketing team updates product images', 'type': 'change'},
                    {'time': 'T-20min', 'event': 'Bulk cache invalidation triggered', 'type': 'action'},
                    {'time': 'T-15min', 'event': 'Origin server load increases 10x', 'type': 'symptom'},
                    {'time': 'T-10min', 'event': 'Response times degraded globally', 'type': 'impact'},
                    {'time': 'T-5min', 'event': 'Origin servers CPU at 95%', 'type': 'critical'},
                    {'time': 'T-0min', 'event': 'Emergency scaling initiated', 'type': 'response'}
                ],
                'root_cause': 'Wildcard cache invalidation instead of targeted invalidation',
                'correlated_changes': [
                    'Content update process changed at T-30min',
                    'CDN configuration modified at T-40min',
                    'New invalidation script deployed at T-35min'
                ],
                'resolution': 'Implement targeted cache invalidation, add rate limiting',
                'best_practices': [
                    'Use targeted cache invalidation paths',
                    'Implement cache invalidation rate limiting',
                    'Pre-warm cache after invalidation',
                    'Monitor origin server capacity'
                ]
            },
            {
                'id': 'SEC-002',
                'title': 'Exposed API Keys in Public Repository',
                'category': 'security',
                'severity': 'critical',
                'description': 'Production API keys discovered in public GitHub repository',
                'timeline': [
                    {'time': 'T-4hr', 'event': 'Developer commits code with embedded API keys', 'type': 'mistake'},
                    {'time': 'T-3hr', 'event': 'Code pushed to public repository', 'type': 'exposure'},
                    {'time': 'T-2hr', 'event': 'Automated bot scrapes repository', 'type': 'detection'},
                    {'time': 'T-90min', 'event': 'First unauthorized API usage detected', 'type': 'exploit'},
                    {'time': 'T-60min', 'event': 'Unusual API traffic patterns observed', 'type': 'anomaly'},
                    {'time': 'T-30min', 'event': 'Rate limiting triggered on APIs', 'type': 'protection'},
                    {'time': 'T-0min', 'event': 'Security team notified of breach', 'type': 'escalation'}
                ],
                'root_cause': 'Lack of pre-commit hooks and secret scanning in CI/CD pipeline',
                'correlated_changes': [
                    'New developer onboarded at T-5hr',
                    'Repository visibility changed at T-6hr',
                    'CI/CD pipeline updated at T-7hr'
                ],
                'resolution': 'Rotate all API keys, implement secret scanning, educate developers',
                'best_practices': [
                    'Use AWS Secrets Manager for API keys',
                    'Implement pre-commit hooks for secret detection',
                    'Regular secret scanning in repositories',
                    'Developer training on secure coding'
                ]
            },
            {
                'id': 'OUT-002',
                'title': 'DNS Resolution Failure',
                'category': 'outage',
                'severity': 'critical',
                'description': 'Complete service unavailability due to DNS configuration error',
                'timeline': [
                    {'time': 'T-35min', 'event': 'DNS record TTL reduced for migration', 'type': 'change'},
                    {'time': 'T-30min', 'event': 'DNS records updated with typo in IP address', 'type': 'mistake'},
                    {'time': 'T-25min', 'event': 'Old DNS entries start expiring', 'type': 'propagation'},
                    {'time': 'T-20min', 'event': 'First reports of site unreachable', 'type': 'impact'},
                    {'time': 'T-15min', 'event': '50% of users unable to resolve domain', 'type': 'degradation'},
                    {'time': 'T-10min', 'event': 'Complete DNS resolution failure', 'type': 'outage'},
                    {'time': 'T-0min', 'event': 'Emergency DNS rollback initiated', 'type': 'response'}
                ],
                'root_cause': 'Manual DNS update with typographical error and no validation',
                'correlated_changes': [
                    'DNS migration project started at T-1hr',
                    'Route53 hosted zone modified at T-30min',
                    'Load balancer IP changed at T-45min'
                ],
                'resolution': 'Fix DNS records, implement DNS validation, use infrastructure as code',
                'best_practices': [
                    'Use Infrastructure as Code for DNS management',
                    'Implement DNS record validation',
                    'Gradual DNS migration with monitoring',
                    'Maintain DNS fallback procedures'
                ]
            },
            {
                'id': 'PERF-003',
                'title': 'Lambda Cold Start Storm',
                'category': 'performance',
                'severity': 'medium',
                'description': 'Significant latency spikes due to Lambda cold starts after idle period',
                'timeline': [
                    {'time': 'T-2hr', 'event': 'Traffic drops during maintenance window', 'type': 'context'},
                    {'time': 'T-90min', 'event': 'Lambda functions scale down to zero', 'type': 'scaling'},
                    {'time': 'T-30min', 'event': 'Maintenance completed, traffic resumes', 'type': 'change'},
                    {'time': 'T-25min', 'event': 'First requests experience 5s latency', 'type': 'symptom'},
                    {'time': 'T-20min', 'event': 'Multiple concurrent cold starts', 'type': 'impact'},
                    {'time': 'T-15min', 'event': 'API Gateway timeouts reported', 'type': 'error'},
                    {'time': 'T-0min', 'event': 'Performance degradation alert triggered', 'type': 'alert'}
                ],
                'root_cause': 'Lambda provisioned concurrency not configured for critical functions',
                'correlated_changes': [
                    'Lambda memory configuration reduced at T-3hr',
                    'Reserved concurrency removed at T-4hr',
                    'New Lambda runtime version at T-5hr'
                ],
                'resolution': 'Configure provisioned concurrency, implement warming strategy',
                'best_practices': [
                    'Use provisioned concurrency for critical paths',
                    'Implement Lambda warming for predictable traffic',
                    'Monitor cold start metrics',
                    'Optimize Lambda package size'
                ]
            },
            {
                'id': 'DATA-001',
                'title': 'RDS Replication Lag Crisis',
                'category': 'data',
                'severity': 'high',
                'description': 'Critical data inconsistency due to RDS read replica lag',
                'timeline': [
                    {'time': 'T-90min', 'event': 'Large batch job starts on primary RDS', 'type': 'workload'},
                    {'time': 'T-75min', 'event': 'Replication lag begins increasing', 'type': 'symptom'},
                    {'time': 'T-60min', 'event': 'Read replica lag exceeds 5 minutes', 'type': 'degradation'},
                    {'time': 'T-45min', 'event': 'Applications reading stale data', 'type': 'impact'},
                    {'time': 'T-30min', 'event': 'Data inconsistency reports from users', 'type': 'complaint'},
                    {'time': 'T-15min', 'event': 'Replication lag exceeds 15 minutes', 'type': 'critical'},
                    {'time': 'T-0min', 'event': 'Data integrity incident declared', 'type': 'escalation'}
                ],
                'root_cause': 'Unoptimized batch queries overwhelming replication stream',
                'correlated_changes': [
                    'New batch processing job deployed at T-2hr',
                    'RDS parameter group modified at T-3hr',
                    'Read replica instance class downgraded at T-24hr'
                ],
                'resolution': 'Optimize batch queries, upgrade read replica, implement read preference routing',
                'best_practices': [
                    'Monitor replication lag continuously',
                    'Size read replicas appropriately',
                    'Implement read preference routing',
                    'Batch job optimization and scheduling'
                ]
            }
        ]
        
    def get_scenario(self, scenario_id):
        """Get a specific scenario by ID."""
        for scenario in self.scenarios:
            if scenario['id'] == scenario_id:
                return scenario
        return None
        
    def get_scenarios_by_category(self, category):
        """Get all scenarios for a specific category."""
        return [s for s in self.scenarios if s['category'] == category]
        
    def generate_timeline_events(self, scenario, current_time=None):
        """Generate timeline events with actual timestamps."""
        if not current_time:
            current_time = datetime.now()
            
        timeline_with_timestamps = []
        for event in scenario['timeline']:
            # Parse relative time
            time_str = event['time']
            if time_str.startswith('T-'):
                # Extract minutes
                minutes = int(time_str.split('min')[0].replace('T-', '').replace('hr', ''))
                if 'hr' in time_str:
                    minutes *= 60
                timestamp = current_time - timedelta(minutes=minutes)
            else:
                timestamp = current_time
                
            timeline_with_timestamps.append({
                'timestamp': timestamp.isoformat(),
                'relative_time': event['time'],
                'event': event['event'],
                'type': event['type']
            })
            
        return timeline_with_timestamps
        
    def format_scenario_for_kb(self, scenario):
        """Format scenario for knowledge base ingestion."""
        return {
            'document_id': scenario['id'],
            'title': scenario['title'],
            'content': f"""
Incident: {scenario['title']}
Category: {scenario['category']}
Severity: {scenario['severity']}

Description: {scenario['description']}

Timeline:
{self._format_timeline(scenario['timeline'])}

Root Cause: {scenario['root_cause']}

Correlated Changes:
{self._format_list(scenario['correlated_changes'])}

Resolution: {scenario['resolution']}

Best Practices:
{self._format_list(scenario['best_practices'])}
""",
            'metadata': {
                'category': scenario['category'],
                'severity': scenario['severity'],
                'incident_id': scenario['id'],
                'tags': [scenario['category'], scenario['severity'], 'incident', 'root_cause']
            }
        }
        
    def _format_timeline(self, timeline):
        """Format timeline for display."""
        return '\n'.join([f"  {e['time']}: {e['event']} ({e['type']})" for e in timeline])
        
    def _format_list(self, items):
        """Format list items for display."""
        return '\n'.join([f"  - {item}" for item in items])


# Test the scenarios
if __name__ == "__main__":
    scenarios = IncidentScenarios()
    
    print("Available Incident Scenarios:")
    print("=" * 50)
    
    for scenario in scenarios.scenarios:
        print(f"\nID: {scenario['id']}")
        print(f"Title: {scenario['title']}")
        print(f"Category: {scenario['category']}")
        print(f"Severity: {scenario['severity']}")
        print(f"Root Cause: {scenario['root_cause']}")
        print("-" * 30)
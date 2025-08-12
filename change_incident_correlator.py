#!/usr/bin/env python3
"""
Change-Incident Correlation Engine
Advanced multi-factor analysis system for correlating incidents with changes (deployments, configs, infrastructure)
"""

import boto3
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import re
import hashlib


class ChangeIncidentCorrelator:
    """
    Advanced correlation engine to identify incidents caused by changes
    """
    
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
        self.cloudtrail_client = boto3.client('cloudtrail', region_name='us-east-1')
        
        # Change correlation factors and weights
        self.correlation_factors = {
            'temporal_proximity': 0.25,      # Time between change and incident
            'service_overlap': 0.20,         # Service/component overlap
            'change_severity': 0.15,         # Change risk level
            'change_type_match': 0.15,       # Type of change vs incident pattern
            'deployment_correlation': 0.10,   # Deployment-related indicators
            'configuration_impact': 0.10,    # Configuration change impact
            'rollback_evidence': 0.05        # Evidence of rollbacks after incident
        }
    
    def analyze_change_incident_correlation(self, incident_id: str, incident_description: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of incident correlation with recent changes
        """
        print(f"🔍 Analyzing change correlation for incident {incident_id}")
        
        # Extract incident timing and metadata
        incident_time = self._extract_incident_timestamp(incident_id)
        incident_services = self._extract_affected_services(incident_description)
        
        # Get recent changes from multiple sources
        recent_changes = self._get_recent_changes(incident_time)
        
        # Calculate correlation for each change
        correlations = []
        for change in recent_changes:
            correlation = self._calculate_change_correlation(
                incident_id, incident_description, incident_time, incident_services, change
            )
            if correlation['correlation_score'] > 0.3:  # Only include significant correlations
                correlations.append(correlation)
        
        # Sort by correlation score
        correlations.sort(key=lambda x: x['correlation_score'], reverse=True)
        
        # Generate analysis summary
        analysis = self._generate_change_analysis(correlations, incident_description)
        
        return {
            'incident_id': incident_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_changes_analyzed': len(recent_changes),
            'significant_correlations': len(correlations),
            'top_correlation_score': correlations[0]['correlation_score'] if correlations else 0,
            'correlations': correlations[:10],  # Top 10 correlations
            'analysis': analysis,
            'change_categories': self._categorize_changes(correlations),
            'recommendations': self._generate_change_recommendations(correlations)
        }
    
    def _extract_incident_timestamp(self, incident_id: str) -> datetime:
        """Extract incident timestamp from OpsItem"""
        try:
            response = self.ssm_client.get_ops_item(OpsItemId=incident_id)
            created_time = response['OpsItem'].get('CreatedTime')
            if created_time:
                return created_time
        except Exception as e:
            print(f"Warning: Could not get incident timestamp: {e}")
        
        # Fallback to current time minus 2 hours
        return datetime.now() - timedelta(hours=2)
    
    def _extract_affected_services(self, description: str) -> List[str]:
        """Extract affected services from incident description"""
        services = []
        
        # Common AWS services patterns
        aws_services = [
            'EC2', 'RDS', 'S3', 'Lambda', 'ELB', 'ALB', 'NLB', 'CloudFront',
            'API Gateway', 'DynamoDB', 'SQS', 'SNS', 'ECS', 'EKS', 'Route53'
        ]
        
        description_upper = description.upper()
        for service in aws_services:
            if service in description_upper:
                services.append(service.lower())
        
        # Extract service names from common patterns
        patterns = [
            r'(\w+)-service',
            r'(\w+)-api',
            r'(\w+)-app',
            r'service[:\s]+(\w+)',
            r'application[:\s]+(\w+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            services.extend([match.lower() for match in matches])
        
        return list(set(services))
    
    def _get_recent_changes(self, incident_time: datetime) -> List[Dict[str, Any]]:
        """Get recent changes from multiple sources"""
        changes = []
        
        # Time window: 24 hours before incident
        start_time = incident_time - timedelta(hours=24)
        end_time = incident_time + timedelta(minutes=30)  # Include changes slightly after incident
        
        # Get deployment changes from OpsItems with [CHANGE] prefix
        try:
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Title',
                        'Values': ['[CHANGE]'],
                        'Operator': 'Contains'
                    },
                    {
                        'Key': 'CreatedTime',
                        'Values': [start_time.isoformat()],
                        'Operator': 'GreaterThan'
                    }
                ],
                MaxResults=50
            )
            
            for item in response.get('OpsItemSummaries', []):
                changes.append({
                    'id': item.get('OpsItemId'),
                    'title': item.get('Title', ''),
                    'description': item.get('Description', ''),
                    'created_time': item.get('CreatedTime'),
                    'status': item.get('Status'),
                    'source': 'OpsItem',
                    'change_type': self._classify_change_type(item.get('Title', ''))
                })
        except Exception as e:
            print(f"Warning: Could not fetch OpsItem changes: {e}")
        
        # Get CloudTrail events for infrastructure changes
        changes.extend(self._get_cloudtrail_changes(start_time, end_time))
        
        # Generate synthetic changes for demo
        changes.extend(self._generate_demo_changes(start_time, incident_time))
        
        return changes
    
    def _get_cloudtrail_changes(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get infrastructure changes from CloudTrail"""
        changes = []
        
        try:
            # Look for significant infrastructure events
            high_impact_events = [
                'CreateStack', 'UpdateStack', 'DeleteStack',
                'PutScalingPolicy', 'CreateAutoScalingGroup', 'UpdateAutoScalingGroup',
                'CreateFunction', 'UpdateFunctionCode', 'UpdateFunctionConfiguration',
                'CreateDBInstance', 'ModifyDBInstance', 'RebootDBInstance'
            ]
            
            response = self.cloudtrail_client.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'EventName',
                        'AttributeValue': 'UpdateStack'  # Example - in real implementation, iterate through events
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                MaxItems=20
            )
            
            for event in response.get('Events', []):
                changes.append({
                    'id': f"ct-{event.get('EventId', 'unknown')}",
                    'title': f"CloudTrail: {event.get('EventName')}",
                    'description': f"User: {event.get('Username', 'Unknown')} performed {event.get('EventName')}",
                    'created_time': event.get('EventTime'),
                    'status': 'Completed',
                    'source': 'CloudTrail',
                    'change_type': 'infrastructure',
                    'user': event.get('Username', 'Unknown'),
                    'resource': event.get('ResourceName', 'Unknown')
                })
                
        except Exception as e:
            print(f"Warning: Could not fetch CloudTrail changes: {e}")
        
        return changes
    
    def _generate_demo_changes(self, start_time: datetime, incident_time: datetime) -> List[Dict[str, Any]]:
        """Generate realistic demo changes for testing"""
        demo_changes = []
        
        # Define realistic change scenarios
        change_scenarios = [
            {
                'title': '[CHANGE] Deploy web-service v2.1.4 to Production',
                'description': 'Deployment of web-service version 2.1.4 including database schema updates and new authentication module',
                'change_type': 'deployment',
                'risk_level': 'high',
                'services': ['web-service', 'database', 'auth-service'],
                'time_offset_minutes': -45
            },
            {
                'title': '[CHANGE] Update ELB health check configuration',
                'description': 'Modified health check interval from 30s to 10s and unhealthy threshold from 3 to 2',
                'change_type': 'configuration',
                'risk_level': 'medium',
                'services': ['elb', 'load-balancer'],
                'time_offset_minutes': -120
            },
            {
                'title': '[CHANGE] Scale up EC2 instances for peak traffic',
                'description': 'Increased desired capacity from 5 to 15 instances in auto-scaling group',
                'change_type': 'infrastructure',
                'risk_level': 'low',
                'services': ['ec2', 'auto-scaling'],
                'time_offset_minutes': -30
            },
            {
                'title': '[CHANGE] Deploy database migration scripts',
                'description': 'Applied schema changes for user profile enhancement feature',
                'change_type': 'database',
                'risk_level': 'high',
                'services': ['rds', 'database', 'user-service'],
                'time_offset_minutes': -90
            },
            {
                'title': '[CHANGE] Update Lambda function memory allocation',
                'description': 'Increased memory from 512MB to 1024MB for payment-processor function',
                'change_type': 'configuration',
                'risk_level': 'low',
                'services': ['lambda', 'payment-processor'],
                'time_offset_minutes': -15
            }
        ]
        
        for i, scenario in enumerate(change_scenarios):
            change_time = incident_time + timedelta(minutes=scenario['time_offset_minutes'])
            demo_changes.append({
                'id': f'demo-change-{i+1:03d}',
                'title': scenario['title'],
                'description': scenario['description'],
                'created_time': change_time,
                'status': 'Completed',
                'source': 'Demo',
                'change_type': scenario['change_type'],
                'risk_level': scenario['risk_level'],
                'affected_services': scenario['services']
            })
        
        return demo_changes
    
    def _classify_change_type(self, title: str) -> str:
        """Classify change type from title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['deploy', 'deployment', 'release']):
            return 'deployment'
        elif any(word in title_lower for word in ['config', 'configuration', 'setting']):
            return 'configuration'
        elif any(word in title_lower for word in ['database', 'schema', 'migration']):
            return 'database'
        elif any(word in title_lower for word in ['infrastructure', 'network', 'security']):
            return 'infrastructure'
        else:
            return 'other'
    
    def _calculate_change_correlation(self, incident_id: str, incident_description: str, 
                                    incident_time: datetime, incident_services: List[str], 
                                    change: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate correlation score between incident and change"""
        
        factors = {}
        
        # 1. Temporal Proximity (25% weight)
        time_diff = abs((incident_time - change['created_time']).total_seconds() / 60)  # minutes
        if time_diff <= 15:
            temporal_score = 1.0
        elif time_diff <= 60:
            temporal_score = 0.8
        elif time_diff <= 180:
            temporal_score = 0.5
        elif time_diff <= 480:
            temporal_score = 0.2
        else:
            temporal_score = 0.1
        factors['temporal_proximity'] = temporal_score
        
        # 2. Service Overlap (20% weight)
        change_services = change.get('affected_services', [])
        if not change_services:
            # Extract services from change description
            change_services = self._extract_affected_services(change.get('description', ''))
        
        common_services = set(incident_services) & set(change_services)
        if common_services:
            service_score = min(len(common_services) / max(len(incident_services), 1), 1.0)
        else:
            service_score = 0.0
        factors['service_overlap'] = service_score
        
        # 3. Change Severity (15% weight)
        risk_level = change.get('risk_level', 'medium')
        severity_scores = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
        factors['change_severity'] = severity_scores.get(risk_level, 0.5)
        
        # 4. Change Type Match (15% weight)
        change_type = change.get('change_type', 'other')
        incident_keywords = incident_description.lower()
        
        type_relevance = {
            'deployment': 0.9 if any(word in incident_keywords for word in ['deploy', 'release', 'version']) else 0.3,
            'configuration': 0.8 if any(word in incident_keywords for word in ['config', 'setting', 'parameter']) else 0.2,
            'database': 1.0 if any(word in incident_keywords for word in ['database', 'sql', 'query', 'connection']) else 0.1,
            'infrastructure': 0.7 if any(word in incident_keywords for word in ['network', 'server', 'infrastructure']) else 0.2
        }
        factors['change_type_match'] = type_relevance.get(change_type, 0.2)
        
        # 5. Deployment Correlation (10% weight)
        deployment_score = 0.8 if change_type == 'deployment' and time_diff <= 120 else 0.2
        factors['deployment_correlation'] = deployment_score
        
        # 6. Configuration Impact (10% weight)
        config_score = 0.7 if change_type == 'configuration' and 'config' in incident_keywords else 0.1
        factors['configuration_impact'] = config_score
        
        # 7. Rollback Evidence (5% weight)
        rollback_score = 0.9 if any(word in incident_keywords for word in ['rollback', 'revert', 'undo']) else 0.1
        factors['rollback_evidence'] = rollback_score
        
        # Calculate weighted correlation score
        correlation_score = sum(
            factors[factor] * self.correlation_factors[factor] 
            for factor in factors
        )
        
        return {
            'change_id': change['id'],
            'change_title': change['title'],
            'change_description': change.get('description', ''),
            'change_time': change['created_time'].isoformat() if isinstance(change['created_time'], datetime) else str(change['created_time']),
            'change_type': change.get('change_type', 'unknown'),
            'risk_level': change.get('risk_level', 'medium'),
            'correlation_score': round(correlation_score, 3),
            'correlation_factors': factors,
            'time_difference_minutes': int(time_diff),
            'common_services': list(common_services) if 'common_services' in locals() else [],
            'confidence_level': self._determine_confidence_level(correlation_score)
        }
    
    def _determine_confidence_level(self, score: float) -> str:
        """Determine confidence level based on correlation score"""
        if score >= 0.8:
            return 'Very High'
        elif score >= 0.6:
            return 'High'
        elif score >= 0.4:
            return 'Medium'
        elif score >= 0.2:
            return 'Low'
        else:
            return 'Very Low'
    
    def _categorize_changes(self, correlations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize changes by type"""
        categories = {}
        for correlation in correlations:
            change_type = correlation.get('change_type', 'unknown')
            categories[change_type] = categories.get(change_type, 0) + 1
        return categories
    
    def _generate_change_analysis(self, correlations: List[Dict[str, Any]], incident_description: str) -> str:
        """Generate AI-powered analysis of change-incident correlation"""
        if not correlations:
            return "No significant change correlations found. This incident may be caused by external factors, gradual degradation, or changes not tracked in the system."
        
        top_correlation = correlations[0]
        analysis_parts = []
        
        # Primary finding
        analysis_parts.append(f"**Primary Change Correlation ({top_correlation['confidence_level']} confidence):**")
        analysis_parts.append(f"Change '{top_correlation['change_title']}' shows {top_correlation['correlation_score']:.1%} correlation with this incident.")
        
        # Temporal analysis
        time_diff = top_correlation['time_difference_minutes']
        if time_diff <= 30:
            analysis_parts.append(f"⚠️ **Critical Timeline**: Change occurred only {time_diff} minutes before incident - strong temporal correlation.")
        elif time_diff <= 120:
            analysis_parts.append(f"🕐 **Moderate Timeline**: Change occurred {time_diff} minutes before incident - possible correlation.")
        
        # Service overlap analysis
        common_services = top_correlation.get('common_services', [])
        if common_services:
            analysis_parts.append(f"🎯 **Service Overlap**: Both change and incident affected: {', '.join(common_services)}")
        
        # Change type analysis
        change_type = top_correlation.get('change_type', 'unknown')
        if change_type == 'deployment':
            analysis_parts.append("🚀 **Deployment Risk**: Deployment changes have high incident correlation potential.")
        elif change_type == 'database':
            analysis_parts.append("🗄️ **Database Risk**: Database changes can cause cascading application issues.")
        elif change_type == 'configuration':
            analysis_parts.append("⚙️ **Configuration Risk**: Configuration changes may have unexpected side effects.")
        
        # Multiple correlations
        if len(correlations) > 1:
            high_correlations = [c for c in correlations if c['correlation_score'] >= 0.6]
            if len(high_correlations) > 1:
                analysis_parts.append(f"📊 **Multiple Correlations**: {len(high_correlations)} changes show high correlation - potential cascade effect.")
        
        # Recommendations
        analysis_parts.append("\n**Recommended Actions:**")
        if top_correlation['correlation_score'] >= 0.7:
            analysis_parts.append("• Immediately investigate the correlated change for root cause")
            analysis_parts.append("• Consider rollback if change was recent and high-impact")
            analysis_parts.append("• Review change approval and testing processes")
        else:
            analysis_parts.append("• Review all correlated changes as potential contributing factors")
            analysis_parts.append("• Analyze change interaction effects")
        
        return "\n".join(analysis_parts)
    
    def _generate_change_recommendations(self, correlations: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on correlations"""
        if not correlations:
            return [
                "Investigate external factors or gradual system degradation",
                "Review monitoring for early warning signs",
                "Check for untracked changes or manual interventions"
            ]
        
        recommendations = []
        top_correlation = correlations[0]
        
        if top_correlation['correlation_score'] >= 0.8:
            recommendations.extend([
                f"🚨 HIGH PRIORITY: Investigate change '{top_correlation['change_title']}' as primary root cause",
                "Consider immediate rollback if change was deployed recently",
                "Implement enhanced testing for similar changes"
            ])
        elif top_correlation['correlation_score'] >= 0.6:
            recommendations.extend([
                f"🔍 INVESTIGATE: Review change '{top_correlation['change_title']}' for potential impact",
                "Analyze change interaction with other system components",
                "Review change deployment process for improvements"
            ])
        
        # Type-specific recommendations
        change_type = top_correlation.get('change_type')
        if change_type == 'deployment':
            recommendations.append("📋 Review deployment checklist and rollback procedures")
        elif change_type == 'database':
            recommendations.append("🗄️ Verify database performance and connection pools")
        elif change_type == 'configuration':
            recommendations.append("⚙️ Audit configuration changes and dependencies")
        
        # Multiple changes
        if len(correlations) > 2:
            recommendations.append("📊 Analyze cumulative impact of multiple recent changes")
        
        return recommendations


def test_change_correlation():
    """Test the change-incident correlation system"""
    correlator = ChangeIncidentCorrelator()
    
    # Test with a sample incident
    sample_incident_id = "oi-test-change-001"
    sample_description = """
    Performance degradation observed in web-service starting at 14:30.
    Response times increased from 200ms to 2000ms average.
    Database connections showing timeout errors.
    Users reporting slow page loads and login failures.
    """
    
    print("🧪 Testing Change-Incident Correlation Engine...")
    result = correlator.analyze_change_incident_correlation(sample_incident_id, sample_description)
    
    print(f"\n📊 Analysis Results:")
    print(f"Total changes analyzed: {result['total_changes_analyzed']}")
    print(f"Significant correlations: {result['significant_correlations']}")
    print(f"Top correlation score: {result['top_correlation_score']:.1%}")
    
    print(f"\n🔍 Analysis:")
    print(result['analysis'])
    
    if result['correlations']:
        print(f"\n🏆 Top Correlations:")
        for i, correlation in enumerate(result['correlations'][:3]):
            print(f"{i+1}. {correlation['change_title']} ({correlation['correlation_score']:.1%})")
            print(f"   Time difference: {correlation['time_difference_minutes']} minutes")
            print(f"   Confidence: {correlation['confidence_level']}")
    
    return result


if __name__ == "__main__":
    test_change_correlation()
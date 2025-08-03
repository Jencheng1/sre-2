"""
Human-in-the-Loop Feedback System for SRE Copilot
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError

class FeedbackSystem:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'sre-copilot-feedback'
        self.table = None
        self.ensure_table_exists()
        
    def ensure_table_exists(self):
        """Create DynamoDB table if it doesn't exist"""
        try:
            self.table = self.dynamodb.Table(self.table_name)
            self.table.load()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self.create_feedback_table()
            else:
                raise
    
    def create_feedback_table(self):
        """Create the feedback DynamoDB table"""
        self.table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'feedback_id', 'KeyType': 'HASH'},
                {'AttributeName': 'incident_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'feedback_id', 'AttributeType': 'S'},
                {'AttributeName': 'incident_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'incident-timestamp-index',
                    'KeySchema': [
                        {'AttributeName': 'incident_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        self.table.wait_until_exists()
    
    def submit_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit feedback for an incident analysis"""
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'feedback_id': feedback_id,
            'incident_id': feedback_data['incident_id'],
            'analysis_id': feedback_data.get('analysis_id', ''),
            'timestamp': timestamp,
            'rating': feedback_data.get('rating', 0),
            'correct_root_cause': feedback_data.get('correct_root_cause', False),
            'additional_context': feedback_data.get('additional_context', ''),
            'suggested_actions': feedback_data.get('suggested_actions', []),
            'user_corrections': feedback_data.get('user_corrections', {}),
            'effectiveness': feedback_data.get('effectiveness', 0),
            'time_to_resolution': feedback_data.get('time_to_resolution', 0),
            'false_positives': feedback_data.get('false_positives', []),
            'missed_correlations': feedback_data.get('missed_correlations', [])
        }
        
        try:
            self.table.put_item(Item=item)
            
            # Also add to knowledge base for future reference
            self._add_to_knowledge_base(item)
            
            return {
                'success': True,
                'feedback_id': feedback_id,
                'message': 'Feedback submitted successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_feedback(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for a specific incident"""
        try:
            response = self.table.query(
                IndexName='incident-timestamp-index',
                KeyConditionExpression='incident_id = :iid',
                ExpressionAttributeValues={
                    ':iid': incident_id
                },
                ScanIndexForward=False  # Most recent first
            )
            
            return response.get('Items', [])
        except Exception as e:
            print(f"Error retrieving feedback: {e}")
            return []
    
    def get_feedback_stats(self, time_range: str = '7d') -> Dict[str, Any]:
        """Get feedback statistics"""
        # In a real implementation, this would query and aggregate data
        # For now, return sample stats
        return {
            'total_feedback': 150,
            'average_rating': 4.2,
            'accuracy_rate': 0.85,
            'most_common_issues': [
                'False positive alerts',
                'Missing correlation with deployments',
                'Incomplete root cause analysis'
            ],
            'improvement_trend': '+12%',
            'feedback_by_type': {
                'network_latency': 45,
                'service_outage': 38,
                'performance_degradation': 67
            }
        }
    
    def get_recent_feedback(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent feedback entries"""
        try:
            # Mock recent feedback for testing
            recent = []
            for i in range(min(limit, 5)):
                recent.append({
                    'feedback_id': f'FEEDBACK-{i}',
                    'incident_id': f'INC-{i}',
                    'rating': 4 + (i % 2),
                    'timestamp': datetime.now().isoformat(),
                    'additional_context': f'Test feedback {i}'
                })
            return recent
        except Exception as e:
            print(f"Error getting recent feedback: {e}")
            return []
    
    def get_feedback_by_type(self, incident_type: str) -> List[Dict[str, Any]]:
        """Get feedback by incident type"""
        try:
            # Mock feedback by type for testing
            if incident_type == 'performance':
                return [
                    {'incident_id': 'PERF-001', 'rating': 4, 'incident_type': 'performance'},
                    {'incident_id': 'PERF-002', 'rating': 5, 'incident_type': 'performance'}
                ]
            elif incident_type == 'security':
                return [
                    {'incident_id': 'SEC-001', 'rating': 5, 'incident_type': 'security'},
                    {'incident_id': 'SEC-002', 'rating': 4, 'incident_type': 'security'}
                ]
            else:
                return []
        except Exception as e:
            print(f"Error getting feedback by type: {e}")
            return []
    
    def _add_to_knowledge_base(self, feedback: Dict[str, Any]):
        """Add validated feedback to knowledge base"""
        if feedback.get('rating', 0) >= 4 and feedback.get('correct_root_cause', False):
            # This is good feedback that should enhance future analysis
            kb_entry = {
                'incident_type': feedback.get('incident_type', 'unknown'),
                'root_cause': feedback.get('actual_root_cause', ''),
                'resolution': feedback.get('resolution_steps', []),
                'additional_context': feedback.get('additional_context', ''),
                'effectiveness_rating': feedback.get('effectiveness', 0)
            }
            
            # In real implementation, this would add to the knowledge base
            # using the existing KB Lambda function
            pass


class FeedbackAnalyzer:
    """Analyze feedback to improve future predictions"""
    
    def __init__(self):
        self.feedback_system = FeedbackSystem()
    
    def analyze_patterns(self, incident_type: str) -> Dict[str, Any]:
        """Analyze feedback patterns for a specific incident type"""
        # This would aggregate feedback to find patterns
        return {
            'common_misidentifications': [
                {
                    'predicted': 'Network congestion',
                    'actual': 'DNS misconfiguration',
                    'frequency': 12
                },
                {
                    'predicted': 'Database slowdown',
                    'actual': 'Connection pool exhaustion',
                    'frequency': 8
                }
            ],
            'accuracy_by_component': {
                'network': 0.82,
                'database': 0.78,
                'application': 0.91,
                'infrastructure': 0.85
            },
            'improvement_suggestions': [
                'Include DNS checks in network latency analysis',
                'Correlate with recent deployment events',
                'Check connection pool metrics for database issues'
            ]
        }
    
    def get_enhanced_context(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Get enhanced context based on historical feedback"""
        similar_incidents = self._find_similar_incidents(incident)
        
        return {
            'historical_resolutions': self._get_successful_resolutions(similar_incidents),
            'common_pitfalls': self._get_common_mistakes(similar_incidents),
            'recommended_checks': self._get_recommended_checks(incident['type']),
            'confidence_adjustment': self._calculate_confidence_adjustment(incident)
        }
    
    def _find_similar_incidents(self, incident: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar historical incidents"""
        # Implementation would search for similar patterns
        return []
    
    def _get_successful_resolutions(self, incidents: List[Dict[str, Any]]) -> List[str]:
        """Extract successful resolution strategies"""
        return [
            "Check DNS configuration and Route53 health checks",
            "Verify security group rules haven't changed",
            "Analyze recent deployments for configuration changes"
        ]
    
    def _get_common_mistakes(self, incidents: List[Dict[str, Any]]) -> List[str]:
        """Identify common misdiagnoses"""
        return [
            "Assuming network congestion without checking DNS",
            "Missing correlation with deployment events",
            "Not checking upstream service dependencies"
        ]
    
    def _get_recommended_checks(self, incident_type: str) -> List[str]:
        """Get recommended checks based on incident type"""
        checks_map = {
            'network_latency': [
                'DNS resolution time',
                'Route53 health checks',
                'Security group rules',
                'Network ACLs'
            ],
            'performance_degradation': [
                'Recent deployments',
                'Database connection pools',
                'Cache hit rates',
                'Resource utilization'
            ],
            'service_outage': [
                'Health check endpoints',
                'Load balancer status',
                'Auto-scaling group health',
                'Dependency services'
            ]
        }
        
        return checks_map.get(incident_type, [])
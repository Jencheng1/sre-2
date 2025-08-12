#!/usr/bin/env python3
"""
AI-Powered Problem Management Module
Automatically creates and manages problems from incidents using AI analysis
"""

import json
import requests
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AIProblemManager:
    """
    AI-powered problem management with automatic creation from incidents
    """
    
    def __init__(self):
        self.servicenow_url = "http://localhost:9082"
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        
        # Problem creation thresholds
        self.thresholds = {
            'recurrence_count': 3,  # Create problem after 3 similar incidents
            'impact_score': 0.7,    # Create problem if impact > 70%
            'ai_confidence': 0.8    # Create problem if AI confidence > 80%
        }
    
    def analyze_incident_for_problem(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze incident to determine if a problem should be created
        """
        analysis = {
            'should_create_problem': False,
            'confidence_score': 0.0,
            'reasoning': [],
            'problem_type': None,
            'related_incidents': [],
            'impact_analysis': {},
            'ai_recommendation': None
        }
        
        # Check for recurring incidents
        recurrence_analysis = self._analyze_recurrence(incident_data)
        analysis['related_incidents'] = recurrence_analysis['related_incidents']
        
        if recurrence_analysis['count'] >= self.thresholds['recurrence_count']:
            analysis['should_create_problem'] = True
            analysis['reasoning'].append(
                f"Recurring issue detected: {recurrence_analysis['count']} similar incidents"
            )
            analysis['problem_type'] = 'recurring'
        
        # Analyze business impact
        impact_analysis = self._analyze_business_impact(incident_data)
        analysis['impact_analysis'] = impact_analysis
        
        if impact_analysis['score'] >= self.thresholds['impact_score']:
            analysis['should_create_problem'] = True
            analysis['reasoning'].append(
                f"High business impact: {impact_analysis['score']:.0%}"
            )
            if not analysis['problem_type']:
                analysis['problem_type'] = 'high_impact'
        
        # Get AI recommendation
        ai_analysis = self._get_ai_recommendation(incident_data, recurrence_analysis, impact_analysis)
        analysis['ai_recommendation'] = ai_analysis['recommendation']
        analysis['confidence_score'] = ai_analysis['confidence']
        
        if ai_analysis['confidence'] >= self.thresholds['ai_confidence']:
            analysis['should_create_problem'] = True
            analysis['reasoning'].append(
                f"AI recommends problem creation with {ai_analysis['confidence']:.0%} confidence"
            )
            if not analysis['problem_type']:
                analysis['problem_type'] = 'ai_recommended'
        
        return analysis
    
    def create_problem_automatically(self, incident_data: Dict[str, Any], 
                                   analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically create a problem based on incident and analysis
        """
        try:
            # Generate problem details using AI
            problem_details = self._generate_problem_details(incident_data, analysis)
            
            # Create problem in ServiceNow
            response = requests.post(
                f"{self.servicenow_url}/servicenow/problems",
                json=problem_details,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                problem_data = response.json()
                
                # Link to incident
                self._link_problem_to_incident(
                    problem_data['problem_id'],
                    incident_data['id']
                )
                
                # Link to related incidents
                for related_id in analysis['related_incidents']:
                    self._link_problem_to_incident(
                        problem_data['problem_id'],
                        related_id
                    )
                
                return {
                    'success': True,
                    'problem_id': problem_data['problem_id'],
                    'problem_number': problem_data.get('number'),
                    'message': 'Problem created automatically by AI',
                    'details': problem_details
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to create problem: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error creating problem: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_recurrence(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze if this is a recurring incident
        """
        try:
            # Search for similar incidents in the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'CreatedTime',
                        'Values': [start_date.isoformat()],
                        'Operator': 'GreaterThan'
                    }
                ],
                MaxResults=50
            )
            
            similar_incidents = []
            incident_keywords = self._extract_keywords(incident_data.get('description', ''))
            
            for item in response.get('OpsItemSummaries', []):
                if item['OpsItemId'] != incident_data.get('id'):
                    item_keywords = self._extract_keywords(
                        item.get('Description', '') + ' ' + item.get('Title', '')
                    )
                    
                    # Calculate similarity
                    common_keywords = set(incident_keywords) & set(item_keywords)
                    if len(common_keywords) >= 3:  # At least 3 common keywords
                        similar_incidents.append(item['OpsItemId'])
            
            return {
                'count': len(similar_incidents) + 1,  # Include current incident
                'related_incidents': similar_incidents[:5]  # Top 5 related
            }
            
        except Exception as e:
            logger.error(f"Recurrence analysis error: {str(e)}")
            return {'count': 1, 'related_incidents': []}
    
    def _analyze_business_impact(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the business impact of the incident
        """
        impact_score = 0.0
        impact_factors = []
        
        # Severity impact
        severity = incident_data.get('severity', 'Medium')
        severity_scores = {
            'Critical': 0.4,
            'High': 0.3,
            'Medium': 0.2,
            'Low': 0.1
        }
        impact_score += severity_scores.get(severity, 0.2)
        if severity in ['Critical', 'High']:
            impact_factors.append(f"{severity} severity incident")
        
        # Service criticality
        description = incident_data.get('description', '').lower()
        critical_services = ['payment', 'authentication', 'api gateway', 'database']
        
        for service in critical_services:
            if service in description:
                impact_score += 0.2
                impact_factors.append(f"Affects critical service: {service}")
                break
        
        # Customer impact keywords
        customer_impact_keywords = ['customer', 'user', 'client', 'downtime', 'outage']
        for keyword in customer_impact_keywords:
            if keyword in description:
                impact_score += 0.1
                impact_factors.append("Direct customer impact")
                break
        
        # Time-based impact (business hours)
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            impact_score += 0.1
            impact_factors.append("Occurred during business hours")
        
        return {
            'score': min(impact_score, 1.0),
            'factors': impact_factors,
            'category': 'high' if impact_score >= 0.7 else 'medium' if impact_score >= 0.4 else 'low'
        }
    
    def _get_ai_recommendation(self, incident_data: Dict[str, Any],
                              recurrence: Dict[str, Any],
                              impact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get AI recommendation for problem creation
        """
        try:
            # Prepare context for AI
            prompt = f"""
            Analyze the following incident and determine if a problem record should be created:
            
            Incident Details:
            - Title: {incident_data.get('title', 'Unknown')}
            - Description: {incident_data.get('description', 'No description')}
            - Severity: {incident_data.get('severity', 'Medium')}
            - Recurrence: {recurrence['count']} similar incidents found
            - Business Impact Score: {impact['score']:.0%}
            - Impact Factors: {', '.join(impact['factors'])}
            
            Based on ITIL best practices, should a problem record be created?
            Provide your recommendation with confidence score (0-1) and reasoning.
            
            Response format:
            {{
                "create_problem": true/false,
                "confidence": 0.0-1.0,
                "reasoning": "explanation",
                "problem_category": "category",
                "recommended_priority": "priority"
            }}
            """
            
            # Call Claude via Bedrock
            response = self.bedrock_client.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_response = json.loads(response_body['content'][0]['text'])
            
            return {
                'recommendation': ai_response,
                'confidence': ai_response.get('confidence', 0.5),
                'should_create': ai_response.get('create_problem', False)
            }
            
        except Exception as e:
            logger.error(f"AI recommendation error: {str(e)}")
            # Fallback recommendation
            return {
                'recommendation': {
                    'create_problem': recurrence['count'] >= 3 or impact['score'] >= 0.7,
                    'confidence': 0.6,
                    'reasoning': 'Based on recurrence and impact analysis',
                    'problem_category': 'Technical',
                    'recommended_priority': '2 - High' if impact['score'] >= 0.7 else '3 - Moderate'
                },
                'confidence': 0.6,
                'should_create': recurrence['count'] >= 3 or impact['score'] >= 0.7
            }
    
    def _generate_problem_details(self, incident_data: Dict[str, Any],
                                analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate problem details using AI
        """
        ai_rec = analysis['ai_recommendation']
        
        # Build problem statement
        problem_statement = f"""
        Problem identified from incident analysis:
        
        **Incident**: {incident_data.get('title', 'Unknown')}
        **Pattern**: {analysis['problem_type'].replace('_', ' ').title()}
        **Recurrence**: {len(analysis['related_incidents']) + 1} related incidents
        **Business Impact**: {analysis['impact_analysis']['category'].upper()}
        
        **Description**:
        {incident_data.get('description', 'No description available')}
        
        **AI Analysis**:
        {ai_rec.get('reasoning', 'Automated problem detection')}
        
        **Impact Factors**:
        {chr(10).join('- ' + factor for factor in analysis['impact_analysis']['factors'])}
        """
        
        return {
            'short_description': f"Problem: {incident_data.get('title', 'Recurring Issue')}",
            'description': problem_statement,
            'problem_statement': problem_statement,
            'category': ai_rec.get('problem_category', 'Software'),
            'subcategory': 'Application',
            'priority': ai_rec.get('recommended_priority', '3 - Moderate'),
            'assignment_group': 'SRE Team',
            'assigned_to': 'sre-team@company.com',
            'state': 'New',
            'known_error': False,
            'root_cause_analysis': 'In Progress',
            'workaround': '',
            'source_incident_id': incident_data.get('id'),
            'related_incidents': json.dumps(analysis['related_incidents']),
            'ai_confidence_score': analysis['confidence_score'],
            'auto_created': True,
            'created_by': 'AI Problem Manager',
            'created_on': datetime.now().isoformat()
        }
    
    def _link_problem_to_incident(self, problem_id: str, incident_id: str):
        """
        Link problem to incident in SSM
        """
        try:
            self.ssm_client.add_tags_to_resource(
                ResourceType='OpsItem',
                ResourceId=incident_id,
                Tags=[
                    {
                        'Key': 'ServiceNowProblemId',
                        'Value': problem_id
                    },
                    {
                        'Key': 'ProblemCreatedBy',
                        'Value': 'AI-Automatic'
                    },
                    {
                        'Key': 'ProblemCreatedAt',
                        'Value': datetime.now().isoformat()
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Error linking problem to incident: {str(e)}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for similarity comparison
        """
        import re
        
        # Convert to lowercase and extract words
        words = re.findall(r'\w+', text.lower())
        
        # Remove common words
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        # Extract meaningful keywords
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        
        return keywords[:20]  # Return top 20 keywords
    
    def get_problem_status(self, problem_id: str) -> Dict[str, Any]:
        """
        Get current status of a problem
        """
        try:
            response = requests.get(
                f"{self.servicenow_url}/servicenow/problems/{problem_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'Problem not found: {problem_id}'}
                
        except Exception as e:
            logger.error(f"Error getting problem status: {str(e)}")
            return {'error': str(e)}
    
    def update_problem_resolution(self, problem_id: str, resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update problem with resolution information
        """
        try:
            update_data = {
                'state': 'Resolved',
                'resolution_code': resolution_data.get('resolution_code', 'Solved (Permanently)'),
                'root_cause': resolution_data.get('root_cause', ''),
                'resolution_notes': resolution_data.get('resolution_notes', ''),
                'workaround': resolution_data.get('workaround', ''),
                'resolved_by': resolution_data.get('resolved_by', 'SRE Team'),
                'resolved_at': datetime.now().isoformat()
            }
            
            response = requests.put(
                f"{self.servicenow_url}/servicenow/problems/{problem_id}",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'Problem {problem_id} resolved',
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to update problem: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error updating problem: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
"""
ServiceNow Problem Management Integration
Handles problem creation, correlation, and management
"""

import json
import requests
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProblemPriority(Enum):
    CRITICAL = "1"
    HIGH = "2"
    MEDIUM = "3"
    LOW = "4"


class ProblemState(Enum):
    NEW = "100"
    OPEN = "200"
    PENDING = "300"
    RESOLVED = "400"
    CLOSED = "500"


@dataclass
class Problem:
    """ServiceNow Problem Record"""
    short_description: str
    description: str
    priority: ProblemPriority
    state: ProblemState
    category: str
    assigned_to: Optional[str] = None
    assignment_group: Optional[str] = None
    impact: str = "3"
    urgency: str = "3"
    correlation_id: Optional[str] = None
    related_incidents: List[str] = None
    root_cause: Optional[str] = None
    workaround: Optional[str] = None
    
    def __post_init__(self):
        if self.related_incidents is None:
            self.related_incidents = []


class ServiceNowProblemManager:
    """Manages ServiceNow Problem Integration"""
    
    def __init__(self, instance_url: str = None, username: str = None, password: str = None):
        self.instance_url = instance_url or "https://dev12345.service-now.com"
        self.username = username or "admin"
        self.password = password or "admin123"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
    def create_problem_from_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a problem record from an incident using AI analysis"""
        
        # Use AI to analyze incident and generate problem details
        problem_details = self._analyze_incident_for_problem(incident_data)
        
        # Create problem record
        problem = Problem(
            short_description=problem_details['short_description'],
            description=problem_details['description'],
            priority=ProblemPriority(problem_details['priority']),
            state=ProblemState.NEW,
            category=problem_details['category'],
            impact=problem_details.get('impact', '3'),
            urgency=problem_details.get('urgency', '3'),
            related_incidents=[incident_data.get('id', '')],
            root_cause=problem_details.get('root_cause'),
            workaround=problem_details.get('workaround')
        )
        
        # Create in ServiceNow (mock for demo)
        problem_id = self._create_problem_in_servicenow(problem)
        
        return {
            'problem_id': problem_id,
            'problem': problem.__dict__,
            'ai_analysis': problem_details
        }
    
    def _analyze_incident_for_problem(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to analyze incident and suggest problem details"""
        
        prompt = f"""
        Analyze the following incident and suggest a problem record:
        
        Incident Title: {incident_data.get('title', 'Unknown')}
        Incident Description: {incident_data.get('description', 'No description')}
        Service: {incident_data.get('service', 'Unknown')}
        Impact: {incident_data.get('impact', 'Unknown')}
        
        Based on this incident, provide:
        1. A short description for the problem (max 100 chars)
        2. A detailed description of the underlying problem
        3. Priority (1-Critical, 2-High, 3-Medium, 4-Low)
        4. Category (Application, Infrastructure, Network, Database, Security)
        5. Potential root cause
        6. Suggested workaround
        7. Impact assessment (1-5, where 1 is highest)
        8. Urgency assessment (1-5, where 1 is highest)
        
        Return the response as a JSON object.
        """
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_response = json.loads(response_body['content'][0]['text'])
            
            return {
                'short_description': ai_response.get('short_description', 'Problem from incident'),
                'description': ai_response.get('description', incident_data.get('description', '')),
                'priority': str(ai_response.get('priority', '3')),
                'category': ai_response.get('category', 'Application'),
                'root_cause': ai_response.get('root_cause', 'Under investigation'),
                'workaround': ai_response.get('workaround', 'None available'),
                'impact': str(ai_response.get('impact', '3')),
                'urgency': str(ai_response.get('urgency', '3'))
            }
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {
                'short_description': f"Problem: {incident_data.get('title', 'Unknown incident')}",
                'description': incident_data.get('description', 'Problem created from incident'),
                'priority': '3',
                'category': 'Application',
                'root_cause': 'Under investigation',
                'workaround': 'None available',
                'impact': '3',
                'urgency': '3'
            }
    
    def _create_problem_in_servicenow(self, problem: Problem) -> str:
        """Create problem record in ServiceNow (mock implementation)"""
        
        # In real implementation, this would make REST API call to ServiceNow
        # For demo, we'll generate a mock problem ID
        problem_id = f"PRB{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Created ServiceNow problem: {problem_id}")
        
        # Store problem locally for demo
        problem_data = {
            'id': problem_id,
            'created': datetime.now().isoformat(),
            **problem.__dict__
        }
        
        # Save to local file for persistence
        problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
        try:
            with open(problems_file, 'r') as f:
                problems = json.load(f)
        except:
            problems = []
        
        problems.append(problem_data)
        
        with open(problems_file, 'w') as f:
            json.dump(problems, f, indent=2, default=str)
        
        return problem_id
    
    def correlate_incident_to_problem(self, incident_id: str, problem_id: str) -> Dict[str, Any]:
        """Correlate an incident to an existing problem"""
        
        # Load problems
        problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
        try:
            with open(problems_file, 'r') as f:
                problems = json.load(f)
        except:
            problems = []
        
        # Find problem and add incident
        for problem in problems:
            if problem['id'] == problem_id:
                if 'related_incidents' not in problem:
                    problem['related_incidents'] = []
                if incident_id not in problem['related_incidents']:
                    problem['related_incidents'].append(incident_id)
                
                # Save updated problems
                with open(problems_file, 'w') as f:
                    json.dump(problems, f, indent=2, default=str)
                
                return {
                    'success': True,
                    'problem_id': problem_id,
                    'incident_id': incident_id,
                    'related_incidents': problem['related_incidents']
                }
        
        return {
            'success': False,
            'error': f'Problem {problem_id} not found'
        }
    
    def get_problems_for_correlation(self, incident_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of problems that might correlate with the incident"""
        
        # Load all problems
        problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
        try:
            with open(problems_file, 'r') as f:
                all_problems = json.load(f)
        except:
            all_problems = []
        
        # Use AI to find correlating problems
        correlations = self._find_problem_correlations(incident_data, all_problems)
        
        return correlations
    
    def _find_problem_correlations(self, incident_data: Dict[str, Any], problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use AI to find problems that might correlate with the incident"""
        
        if not problems:
            return []
        
        prompt = f"""
        Find problems that might correlate with this incident:
        
        Incident: {incident_data.get('title', 'Unknown')}
        Description: {incident_data.get('description', 'No description')}
        Service: {incident_data.get('service', 'Unknown')}
        
        Available problems:
        {json.dumps([{'id': p['id'], 'short_description': p.get('short_description', ''), 'category': p.get('category', '')} for p in problems[:10]], indent=2)}
        
        Return a JSON array of problem IDs with correlation confidence (0-100).
        """
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 500,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            correlations = json.loads(response_body['content'][0]['text'])
            
            # Enhance with full problem data
            result = []
            for corr in correlations:
                for problem in problems:
                    if problem['id'] == corr['id']:
                        result.append({
                            **problem,
                            'correlation_confidence': corr.get('confidence', 0)
                        })
                        break
            
            return sorted(result, key=lambda x: x.get('correlation_confidence', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            # Return all problems with low confidence as fallback
            return [{**p, 'correlation_confidence': 10} for p in problems[:5]]
    
    def get_all_problems(self) -> List[Dict[str, Any]]:
        """Get all problems"""
        problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
        try:
            with open(problems_file, 'r') as f:
                return json.load(f)
        except:
            return []
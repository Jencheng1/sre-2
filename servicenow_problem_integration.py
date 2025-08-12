#!/usr/bin/env python3
"""
ServiceNow Problem Management Integration
Create problems in ServiceNow from incidents for tracking resolution
"""

import requests
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class ServiceNowProblemManager:
    """
    ServiceNow integration for creating and managing problems from incidents
    """
    
    def __init__(self, servicenow_port: int = 9082):
        self.servicenow_url = f"http://localhost:{servicenow_port}"
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        
    def create_problem_from_incident(self, incident_id: str, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a ServiceNow problem from an AWS SSM incident
        """
        try:
            # Extract incident details
            incident_title = incident_data.get('title', 'Unknown Incident')
            incident_description = incident_data.get('description', 'No description available')
            incident_status = incident_data.get('status', 'Open')
            incident_severity = self._map_incident_severity(incident_data.get('severity', 'Medium'))
            
            # Create problem payload
            problem_data = {
                'short_description': f"Problem: {incident_title}",
                'description': self._generate_problem_description(incident_id, incident_data),
                'state': self._map_incident_status_to_problem_state(incident_status),
                'impact': incident_severity['impact'],
                'urgency': incident_severity['urgency'],
                'priority': incident_severity['priority'],
                'category': 'Software',
                'subcategory': 'Application',
                'assignment_group': 'SRE Team',
                'assigned_to': 'sre-team@company.com',
                'source_incident_id': incident_id,
                'problem_statement': self._generate_problem_statement(incident_data),
                'workaround': '',
                'known_error': False,
                'root_cause_analysis': 'In Progress',
                'resolution_notes': '',
                'created_by': 'SRE-Copilot',
                'opened_at': datetime.now().isoformat()
            }
            
            # Send to ServiceNow MCP server
            response = requests.post(
                f"{self.servicenow_url}/servicenow/problems",
                json=problem_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                problem_result = response.json()
                return {
                    'success': True,
                    'problem_id': problem_result.get('problem_id', f'PRB{datetime.now().strftime("%Y%m%d%H%M%S")}'),
                    'problem_number': problem_result.get('number', f'PRB0001{len(incident_id)}'),
                    'status': 'created',
                    'message': f'Problem created successfully for incident {incident_id}',
                    'servicenow_url': problem_result.get('url', f'{self.servicenow_url}/problem/{problem_result.get("problem_id", "unknown")}')
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to create problem: HTTP {response.status_code}',
                    'response': response.text[:500]
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error creating problem: {str(e)}'
            }
    
    def update_problem_with_resolution(self, problem_id: str, resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update ServiceNow problem with resolution information
        """
        try:
            update_data = {
                'problem_id': problem_id,
                'state': 'Resolved',
                'resolution_code': resolution_data.get('resolution_code', 'Solved (Permanently)'),
                'resolution_notes': resolution_data.get('resolution_notes', ''),
                'root_cause': resolution_data.get('root_cause', ''),
                'workaround': resolution_data.get('workaround', ''),
                'resolved_by': resolution_data.get('resolved_by', 'SRE-Copilot'),
                'resolved_at': datetime.now().isoformat(),
                'close_notes': resolution_data.get('close_notes', 'Problem resolved through SRE Copilot analysis')
            }
            
            response = requests.put(
                f"{self.servicenow_url}/servicenow/problems/{problem_id}",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'Problem {problem_id} updated with resolution',
                    'status': 'updated'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to update problem: HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error updating problem: {str(e)}'
            }
    
    def link_problem_to_incident(self, problem_id: str, incident_id: str) -> Dict[str, Any]:
        """
        Create a link between ServiceNow problem and AWS SSM incident
        """
        try:
            # Update the incident with problem reference
            self.ssm_client.add_tags_to_resource(
                ResourceType='OpsItem',
                ResourceId=incident_id,
                Tags=[
                    {
                        'Key': 'ServiceNowProblemId',
                        'Value': problem_id
                    },
                    {
                        'Key': 'ProblemTrackingEnabled',
                        'Value': 'true'
                    }
                ]
            )
            
            return {
                'success': True,
                'message': f'Linked problem {problem_id} to incident {incident_id}',
                'incident_id': incident_id,
                'problem_id': problem_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error linking problem to incident: {str(e)}'
            }
    
    def get_problems_by_incident(self, incident_id: str) -> Dict[str, Any]:
        """
        Get all problems associated with an incident
        """
        try:
            response = requests.get(
                f"{self.servicenow_url}/servicenow/problems/by-incident/{incident_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'problems': response.json(),
                    'count': len(response.json())
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to retrieve problems: HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error retrieving problems: {str(e)}'
            }
    
    def _generate_problem_description(self, incident_id: str, incident_data: Dict[str, Any]) -> str:
        """Generate comprehensive problem description"""
        description_parts = [
            f"**Source Incident:** {incident_id}",
            f"**Incident Title:** {incident_data.get('title', 'N/A')}",
            f"**Incident Status:** {incident_data.get('status', 'N/A')}",
            f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "**Problem Statement:**",
            incident_data.get('description', 'No description available'),
            "",
            "**Impact Analysis:**",
            "- Service disruption affecting end users",
            "- Potential revenue impact if not resolved",
            "- SLA compliance risk",
            "",
            "**Next Steps:**",
            "1. Root cause analysis in progress",
            "2. Correlation with recent changes and defects",
            "3. Resolution tracking through SRE Copilot",
            "",
            "**Auto-generated by SRE Copilot Problem Management Integration**"
        ]
        
        return "\n".join(description_parts)
    
    def _generate_problem_statement(self, incident_data: Dict[str, Any]) -> str:
        """Generate concise problem statement"""
        title = incident_data.get('title', 'System Issue')
        return f"Root cause analysis required for: {title}"
    
    def _map_incident_severity(self, severity: str) -> Dict[str, str]:
        """Map incident severity to ServiceNow impact/urgency/priority"""
        severity_mapping = {
            'Critical': {'impact': '1 - High', 'urgency': '1 - High', 'priority': '1 - Critical'},
            'High': {'impact': '2 - Medium', 'urgency': '2 - Medium', 'priority': '2 - High'},
            'Medium': {'impact': '3 - Low', 'urgency': '3 - Low', 'priority': '3 - Moderate'},
            'Low': {'impact': '3 - Low', 'urgency': '3 - Low', 'priority': '4 - Low'}
        }
        return severity_mapping.get(severity, severity_mapping['Medium'])
    
    def _map_incident_status_to_problem_state(self, status: str) -> str:
        """Map incident status to ServiceNow problem state"""
        status_mapping = {
            'Open': 'New',
            'InProgress': 'In Progress', 
            'Resolved': 'Resolved',
            'Closed': 'Closed'
        }
        return status_mapping.get(status, 'New')
    
    def create_problem_workflow(self, incident_id: str) -> Dict[str, Any]:
        """
        Complete workflow to create problem from incident
        """
        try:
            # Get incident details from AWS SSM
            incident_response = self.ssm_client.get_ops_item(OpsItemId=incident_id)
            incident_data = {
                'title': incident_response['OpsItem'].get('Title', ''),
                'description': incident_response['OpsItem'].get('Description', ''),
                'status': incident_response['OpsItem'].get('Status', 'Open'),
                'severity': incident_response['OpsItem'].get('Severity', 'Medium'),
                'source': incident_response['OpsItem'].get('Source', 'AWS'),
                'created_time': incident_response['OpsItem'].get('CreatedTime')
            }
            
            # Create problem in ServiceNow
            problem_result = self.create_problem_from_incident(incident_id, incident_data)
            
            if problem_result['success']:
                # Link problem to incident
                link_result = self.link_problem_to_incident(
                    problem_result['problem_id'], 
                    incident_id
                )
                
                return {
                    'success': True,
                    'workflow_status': 'completed',
                    'incident_id': incident_id,
                    'problem_id': problem_result['problem_id'],
                    'problem_number': problem_result['problem_number'],
                    'servicenow_url': problem_result['servicenow_url'],
                    'link_status': link_result['success'],
                    'message': f'Problem tracking enabled for incident {incident_id}'
                }
            else:
                return problem_result
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in problem workflow: {str(e)}'
            }


def test_servicenow_integration():
    """Test ServiceNow problem management integration"""
    print("🧪 Testing ServiceNow Problem Management Integration...")
    
    problem_manager = ServiceNowProblemManager()
    
    # Test with sample incident data
    sample_incident_id = "oi-123456789012"
    sample_incident_data = {
        'title': 'API Gateway Timeout Issues',
        'description': 'API Gateway experiencing increased timeout errors affecting customer transactions',
        'status': 'Open',
        'severity': 'High',
        'source': 'CloudWatch',
        'created_time': datetime.now()
    }
    
    print(f"\n1. Creating problem from incident {sample_incident_id}...")
    result = problem_manager.create_problem_from_incident(sample_incident_id, sample_incident_data)
    
    if result['success']:
        print(f"✅ Problem created: {result['problem_id']}")
        print(f"   Problem Number: {result['problem_number']}")
        print(f"   ServiceNow URL: {result['servicenow_url']}")
        
        # Test problem update
        print(f"\n2. Testing problem resolution update...")
        resolution_data = {
            'resolution_code': 'Solved (Permanently)',
            'resolution_notes': 'Root cause identified as database connection pool exhaustion. Increased pool size and implemented monitoring.',
            'root_cause': 'Database connection pool configuration insufficient for peak load',
            'workaround': 'Temporary increase in timeout values',
            'resolved_by': 'SRE Team'
        }
        
        update_result = problem_manager.update_problem_with_resolution(result['problem_id'], resolution_data)
        if update_result['success']:
            print(f"✅ Problem updated with resolution")
        else:
            print(f"❌ Failed to update problem: {update_result['error']}")
    else:
        print(f"❌ Failed to create problem: {result['error']}")
    
    print(f"\n3. Testing problem retrieval...")
    problems = problem_manager.get_problems_by_incident(sample_incident_id)
    if problems['success']:
        print(f"✅ Retrieved {problems['count']} problems for incident")
    else:
        print(f"❌ Failed to retrieve problems: {problems['error']}")
    
    return result


if __name__ == "__main__":
    test_servicenow_integration()
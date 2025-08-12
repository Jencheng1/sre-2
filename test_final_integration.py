#!/usr/bin/env python3
"""
Final Complete Integration Test
Tests all enhanced functionality: defect creation, change correlation, and ServiceNow problem management
"""

import requests
import boto3
import json
from datetime import datetime
import sys
import os

# Add path for modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from change_incident_correlator import ChangeIncidentCorrelator
    from servicenow_problem_integration import ServiceNowProblemManager
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")


def test_complete_workflow():
    """Test complete workflow: Incident -> Defect + Change Analysis + Problem Management"""
    
    print("🧪 Complete Integration Test - Enhanced SRE Copilot")
    print("=" * 70)
    
    # Test data
    test_incident_id = "oi-114b7755dee1"  # Using real incident ID from system
    test_incident_description = """
    API Gateway experiencing 500 errors starting at 14:30 UTC.
    Error rate jumped from 0.1% to 15% affecting all customer-facing endpoints.
    Users reporting 'Service Temporarily Unavailable' errors.
    Recent deployment of web-service v3.2.1 completed 30 minutes ago.
    Database connections showing timeout errors in application logs.
    """
    
    results = {
        'incident_retrieval': False,
        'defect_creation_alm': False,
        'defect_creation_jira': False,
        'change_correlation': False,
        'problem_management': False
    }
    
    # Step 1: Test incident retrieval
    print("\n🔍 Step 1: Testing incident retrieval...")
    try:
        ssm_client = boto3.client('ssm', region_name='us-east-1')
        response = ssm_client.describe_ops_items(
            OpsItemFilters=[
                {
                    'Key': 'Status',
                    'Values': ['Open', 'InProgress', 'Resolved'],
                    'Operator': 'Equal'
                }
            ],
            MaxResults=5
        )
        
        incidents = response.get('OpsItemSummaries', [])
        if incidents:
            print(f"✅ Retrieved {len(incidents)} incidents")
            print(f"   Sample: {incidents[0]['OpsItemId']} - {incidents[0]['Title']}")
            results['incident_retrieval'] = True
        else:
            print("❌ No incidents found")
            
    except Exception as e:
        print(f"❌ Error retrieving incidents: {str(e)}")
    
    # Step 2: Test defect creation in ALM Octane
    print("\n🐛 Step 2: Testing ALM Octane defect creation...")
    try:
        defect_data = {
            "name": f"Defect from incident {test_incident_id}",
            "description": f"Root cause analysis required for incident: {test_incident_description}",
            "severity": "High",
            "component": "API Gateway",
            "environment": "Production",
            "assigned_to": "sre-team@company.com",
            "source_incident_id": test_incident_id
        }
        
        response = requests.post(
            "http://localhost:9085/octane/defects",
            json=defect_data,
            timeout=10
        )
        
        if response.status_code == 201:
            created_defect = response.json()
            print(f"✅ Created ALM Octane defect: {created_defect.get('id')}")
            results['defect_creation_alm'] = True
        else:
            print(f"❌ Failed to create ALM Octane defect: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error creating ALM Octane defect: {str(e)}")
    
    # Step 3: Test defect creation in Jira
    print("\n🎫 Step 3: Testing Jira issue creation...")
    try:
        issue_data = {
            "project": "SREPROJ",
            "summary": f"Issue from incident {test_incident_id}",
            "description": f"Investigation required for incident: {test_incident_description}",
            "issue_type": "Bug",
            "priority": "High",
            "assignee": "sre-team@company.com"
        }
        
        response = requests.post(
            "http://localhost:9086/jira/issues",
            json=issue_data,
            timeout=10
        )
        
        if response.status_code == 201:
            created_issue = response.json()
            print(f"✅ Created Jira issue: {created_issue.get('key')}")
            results['defect_creation_jira'] = True
        else:
            print(f"❌ Failed to create Jira issue: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error creating Jira issue: {str(e)}")
    
    # Step 4: Test change correlation
    print("\n🔄 Step 4: Testing change-incident correlation...")
    try:
        correlator = ChangeIncidentCorrelator()
        correlation_result = correlator.analyze_change_incident_correlation(
            test_incident_id, test_incident_description
        )
        
        if correlation_result.get('total_changes_analyzed', 0) > 0:
            print(f"✅ Change correlation analysis completed")
            print(f"   Changes analyzed: {correlation_result['total_changes_analyzed']}")
            print(f"   Significant correlations: {correlation_result['significant_correlations']}")
            print(f"   Top correlation: {correlation_result['top_correlation_score']:.1%}")
            results['change_correlation'] = True
        else:
            print("❌ No changes analyzed")
            
    except Exception as e:
        print(f"❌ Error in change correlation: {str(e)}")
    
    # Step 5: Test ServiceNow problem management
    print("\n🎫 Step 5: Testing ServiceNow problem management...")
    try:
        problem_manager = ServiceNowProblemManager()
        
        incident_data = {
            'title': 'API Gateway Performance Degradation',
            'description': test_incident_description,
            'status': 'Open',
            'severity': 'High'
        }
        
        problem_result = problem_manager.create_problem_from_incident(test_incident_id, incident_data)
        
        if problem_result['success']:
            print(f"✅ Created ServiceNow problem: {problem_result['problem_id']}")
            print(f"   Problem number: {problem_result['problem_number']}")
            
            # Test problem linking
            link_result = problem_manager.link_problem_to_incident(
                problem_result['problem_id'], test_incident_id
            )
            
            if link_result['success']:
                print(f"✅ Linked problem to incident")
                results['problem_management'] = True
            else:
                print(f"❌ Failed to link problem: {link_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Failed to create problem: {problem_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in problem management: {str(e)}")
    
    # Final Results
    print("\n" + "=" * 70)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 70)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n🏆 Overall Score: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Complete integration working!")
    elif passed_tests >= 3:
        print("✅ Core functionality working - Minor issues detected")
    else:
        print("❌ Major integration issues detected")
    
    return {
        'passed_tests': passed_tests,
        'total_tests': total_tests,
        'success_rate': passed_tests/total_tests,
        'results': results
    }


if __name__ == "__main__":
    test_complete_workflow()
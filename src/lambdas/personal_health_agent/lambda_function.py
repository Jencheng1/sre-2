import json
import os
import boto3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
health = boto3.client('health')
organizations = boto3.client('organizations')
bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for AWS Personal Health agent.
    Processes health events and returns analysis results.
    """
    try:
        # Extract parameters from the event
        action = event.get('action', 'get_maintenance_events')
        max_results = event.get('max_results', 100)
        start_time = event.get('start_time')
        end_time = event.get('end_time')
        
        if action == 'get_maintenance_events':
            return get_maintenance_events(max_results, start_time, end_time)
        elif action == 'get_service_issues':
            return get_service_issues(max_results, start_time, end_time)
        elif action == 'get_account_notifications':
            return get_account_notifications(max_results, start_time, end_time)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unsupported action: {action}'})
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_maintenance_events(max_results, start_time=None, end_time=None):
    """Get AWS maintenance events."""
    try:
        # Set default time range if not provided
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(days=7)).isoformat()
        if not end_time:
            end_time = (datetime.utcnow() + timedelta(days=7)).isoformat()

        # Get events from AWS Health API
        response = health.describe_events(
            filter={
                'eventTypeCodes': ['AWS_MAINTENANCE'],
                'startTimes': [
                    {
                        'from': start_time,
                        'to': end_time
                    }
                ]
            },
            maxResults=max_results
        )

        maintenance_events = []
        for event in response.get('events', []):
            maintenance_events.append({
                'event_arn': event.get('arn'),
                'service': event.get('service'),
                'event_type_code': event.get('eventTypeCode'),
                'event_type_category': event.get('eventTypeCategory'),
                'start_time': event.get('startTime'),
                'end_time': event.get('endTime'),
                'last_updated_time': event.get('lastUpdatedTime'),
                'status_code': event.get('statusCode'),
                'region': event.get('region'),
                'severity': determine_maintenance_severity(event)
            })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'maintenance_events': maintenance_events,
                'analysis': analyze_with_bedrock(maintenance_events)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_maintenance_events: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_service_issues(max_results, start_time=None, end_time=None):
    """Get AWS service issues."""
    try:
        # Set default time range if not provided
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        if not end_time:
            end_time = datetime.utcnow().isoformat()

        # Get events from AWS Health API
        response = health.describe_events(
            filter={
                'eventTypeCodes': ['AWS_ISSUE'],
                'startTimes': [
                    {
                        'from': start_time,
                        'to': end_time
                    }
                ]
            },
            maxResults=max_results
        )

        service_issues = []
        for event in response.get('events', []):
            service_issues.append({
                'event_arn': event.get('arn'),
                'service': event.get('service'),
                'event_type_code': event.get('eventTypeCode'),
                'event_type_category': event.get('eventTypeCategory'),
                'start_time': event.get('startTime'),
                'end_time': event.get('endTime'),
                'last_updated_time': event.get('lastUpdatedTime'),
                'status_code': event.get('statusCode'),
                'region': event.get('region'),
                'severity': determine_service_issue_severity(event)
            })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'service_issues': service_issues,
                'analysis': analyze_with_bedrock(service_issues)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_service_issues: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_account_notifications(max_results, start_time=None, end_time=None):
    """Get AWS account notifications."""
    try:
        # Set default time range if not provided
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_time:
            end_time = datetime.utcnow().isoformat()

        # Get events from AWS Health API
        response = health.describe_events(
            filter={
                'eventTypeCodes': ['AWS_ACCOUNT_NOTIFICATION'],
                'startTimes': [
                    {
                        'from': start_time,
                        'to': end_time
                    }
                ]
            },
            maxResults=max_results
        )

        account_notifications = []
        for event in response.get('events', []):
            account_notifications.append({
                'event_arn': event.get('arn'),
                'service': event.get('service'),
                'event_type_code': event.get('eventTypeCode'),
                'event_type_category': event.get('eventTypeCategory'),
                'start_time': event.get('startTime'),
                'end_time': event.get('endTime'),
                'last_updated_time': event.get('lastUpdatedTime'),
                'status_code': event.get('statusCode'),
                'region': event.get('region'),
                'severity': determine_account_notification_severity(event)
            })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'account_notifications': account_notifications,
                'analysis': analyze_with_bedrock(account_notifications)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_account_notifications: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def analyze_with_bedrock(events):
    """Analyze events using Bedrock."""
    try:
        # Prepare the prompt for Bedrock
        prompt = {
            "prompt": f"""Analyze the following AWS Health events:
            {json.dumps(events, indent=2)}
            
            Please provide:
            1. A summary of the events
            2. Impact assessment
            3. Recommended actions
            4. Preventive measures
            """,
            "max_tokens": 1000,
            "temperature": 0.7
        }

        # Call Bedrock
        response = bedrock.invoke_model(
            modelId='anthropic.claude-v2',
            body=json.dumps(prompt)
        )

        # Parse and return the analysis
        analysis = json.loads(response['body'].read())
        return analysis

    except Exception as e:
        logger.error(f"Error in analyze_with_bedrock: {str(e)}")
        return {"error": str(e)}

def determine_maintenance_severity(event):
    """Determine the severity of a maintenance event."""
    event_type_code = event.get('eventTypeCode', '').lower()
    
    # High severity maintenance events
    high_severity_events = [
        'ec2-maintenance',
        'rds-maintenance',
        'eks-maintenance',
        'elasticache-maintenance'
    ]
    
    # Medium severity maintenance events
    medium_severity_events = [
        's3-maintenance',
        'dynamodb-maintenance',
        'lambda-maintenance',
        'apigateway-maintenance'
    ]
    
    for event_type in high_severity_events:
        if event_type in event_type_code:
            return 'high'
    
    for event_type in medium_severity_events:
        if event_type in event_type_code:
            return 'medium'
    
    return 'low'

def determine_service_issue_severity(event):
    """Determine the severity of a service issue."""
    event_type_code = event.get('eventTypeCode', '').lower()
    
    # High severity service issues
    high_severity_events = [
        'ec2-issue',
        'rds-issue',
        'eks-issue',
        'elasticache-issue',
        'vpc-issue'
    ]
    
    # Medium severity service issues
    medium_severity_events = [
        's3-issue',
        'dynamodb-issue',
        'lambda-issue',
        'apigateway-issue',
        'cloudfront-issue'
    ]
    
    for event_type in high_severity_events:
        if event_type in event_type_code:
            return 'high'
    
    for event_type in medium_severity_events:
        if event_type in event_type_code:
            return 'medium'
    
    return 'low'

def determine_account_notification_severity(event):
    """Determine the severity of an account notification."""
    event_type_code = event.get('eventTypeCode', '').lower()
    
    # High severity account notifications
    high_severity_events = [
        'security-notification',
        'compliance-notification',
        'billing-notification'
    ]
    
    # Medium severity account notifications
    medium_severity_events = [
        'service-notification',
        'feature-notification',
        'deprecation-notification'
    ]
    
    for event_type in high_severity_events:
        if event_type in event_type_code:
            return 'high'
    
    for event_type in medium_severity_events:
        if event_type in event_type_code:
            return 'medium'
    
    return 'low'

def get_organization_id() -> str:
    """Get the AWS organization ID."""
    try:
        response = organizations.describe_organization()
        return response.get('Organization', {}).get('Id', '')
    except Exception as e:
        print(f"Error getting organization ID: {e}")
        return '' 
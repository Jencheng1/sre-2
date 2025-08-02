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
cloudtrail = boto3.client('cloudtrail')
bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for CloudTrail agent.
    Processes CloudTrail events and returns analysis results.
    """
    try:
        # Extract parameters from the event
        action = event.get('action', 'get_api_errors')
        max_results = event.get('max_results', 100)
        start_time = event.get('start_time')
        end_time = event.get('end_time')

        if action == 'get_api_errors':
            return get_api_errors(max_results, start_time, end_time)
        elif action == 'get_security_events':
            return get_security_events(max_results, start_time, end_time)
        elif action == 'get_compliance_events':
            return get_compliance_events(max_results, start_time, end_time)
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

def get_api_errors(max_results, start_time=None, end_time=None):
    """Get API errors from CloudTrail logs."""
    try:
        # Set default time range if not provided
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        if not end_time:
            end_time = datetime.utcnow().isoformat()

        # Get CloudTrail events
        response = cloudtrail.lookup_events(
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=max_results,
            LookupAttributes=[
                {
                    'AttributeKey': 'EventType',
                    'AttributeValue': 'AwsApiCall'
                }
            ]
        )

        errors = []
        for event in response.get('Events', []):
            # Check if the event represents an error
            if event.get('ErrorCode') or 'error' in event.get('EventName', '').lower():
                errors.append({
                    'event_id': event.get('EventId'),
                    'event_name': event.get('EventName'),
                    'event_time': event.get('EventTime'),
                    'username': event.get('Username'),
                    'resource_name': event.get('Resources', [{}])[0].get('ResourceName'),
                    'resource_type': event.get('Resources', [{}])[0].get('ResourceType'),
                    'error_code': event.get('ErrorCode'),
                    'error_message': event.get('ErrorMessage'),
                    'severity': determine_error_severity(event)
                })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'api_errors': errors,
                'analysis': analyze_with_bedrock(errors)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_api_errors: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_security_events(max_results, start_time=None, end_time=None):
    """Get security-related events from CloudTrail logs."""
    try:
        # Set default time range if not provided
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        if not end_time:
            end_time = datetime.utcnow().isoformat()

        # Get CloudTrail events
        response = cloudtrail.lookup_events(
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=max_results,
            LookupAttributes=[
                {
                    'AttributeKey': 'EventType',
                    'AttributeValue': 'AwsApiCall'
                },
                {
                    'AttributeKey': 'ResourceType',
                    'AttributeValue': 'AWS::IAM::*'
                }
            ]
        )

        security_events = []
        for event in response.get('Events', []):
            # Check if the event is security-related
            if is_security_event(event):
                security_events.append({
                    'event_id': event.get('EventId'),
                    'event_name': event.get('EventName'),
                    'event_time': event.get('EventTime'),
                    'username': event.get('Username'),
                    'resource_name': event.get('Resources', [{}])[0].get('ResourceName'),
                    'resource_type': event.get('Resources', [{}])[0].get('ResourceType'),
                    'source_ip': event.get('SourceIPAddress'),
                    'user_agent': event.get('UserAgent'),
                    'severity': determine_security_severity(event)
                })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'security_events': security_events,
                'analysis': analyze_with_bedrock(security_events)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_security_events: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_compliance_events(max_results, start_time=None, end_time=None):
    """Get compliance-related events from CloudTrail logs."""
    try:
        # Set default time range if not provided
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        if not end_time:
            end_time = datetime.utcnow().isoformat()

        # Get CloudTrail events
        response = cloudtrail.lookup_events(
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=max_results,
            LookupAttributes=[
                {
                    'AttributeKey': 'EventType',
                    'AttributeValue': 'AwsApiCall'
                }
            ]
        )

        compliance_events = []
        for event in response.get('Events', []):
            # Check if the event is compliance-related
            if is_compliance_event(event):
                compliance_events.append({
                    'event_id': event.get('EventId'),
                    'event_name': event.get('EventName'),
                    'event_time': event.get('EventTime'),
                    'username': event.get('Username'),
                    'resource_name': event.get('Resources', [{}])[0].get('ResourceName'),
                    'resource_type': event.get('Resources', [{}])[0].get('ResourceType'),
                    'service': event.get('EventSource'),
                    'severity': determine_compliance_severity(event)
                })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'compliance_events': compliance_events,
                'analysis': analyze_with_bedrock(compliance_events)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_compliance_events: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def analyze_with_bedrock(events):
    """Analyze events using Bedrock."""
    try:
        # Prepare the prompt for Bedrock
        prompt = {
            "prompt": f"""Analyze the following CloudTrail events:
            {json.dumps(events, indent=2)}
            
            Please provide:
            1. A summary of the events
            2. Security implications
            3. Compliance concerns
            4. Recommended actions
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

def is_security_event(event):
    """Determine if an event is security-related."""
    security_events = [
        'CreateUser',
        'DeleteUser',
        'CreateRole',
        'DeleteRole',
        'CreatePolicy',
        'DeletePolicy',
        'AttachUserPolicy',
        'DetachUserPolicy',
        'AttachRolePolicy',
        'DetachRolePolicy',
        'CreateAccessKey',
        'DeleteAccessKey',
        'CreateLoginProfile',
        'DeleteLoginProfile',
        'UpdateLoginProfile',
        'CreateGroup',
        'DeleteGroup',
        'AddUserToGroup',
        'RemoveUserFromGroup'
    ]
    
    return event.get('EventName', '') in security_events

def is_compliance_event(event):
    """Determine if an event is compliance-related."""
    compliance_events = [
        'CreateBucket',
        'DeleteBucket',
        'PutBucketPolicy',
        'PutBucketEncryption',
        'PutBucketVersioning',
        'PutBucketLogging',
        'PutBucketAcl',
        'PutObject',
        'DeleteObject',
        'PutObjectAcl',
        'CreateTrail',
        'DeleteTrail',
        'UpdateTrail',
        'StartLogging',
        'StopLogging'
    ]
    
    return event.get('EventName', '') in compliance_events

def determine_error_severity(event):
    """Determine the severity of an API error."""
    error_code = event.get('ErrorCode', '').lower()
    
    # High severity errors
    high_severity_codes = [
        'accessdenied',
        'unauthorized',
        'forbidden',
        'invalidtoken',
        'expiredtoken',
        'invalidcredentials'
    ]
    
    # Medium severity errors
    medium_severity_codes = [
        'throttling',
        'ratelimitexceeded',
        'serviceunavailable',
        'internalerror'
    ]
    
    for code in high_severity_codes:
        if code in error_code:
            return 'high'
    
    for code in medium_severity_codes:
        if code in error_code:
            return 'medium'
    
    return 'low'

def determine_security_severity(event):
    """Determine the severity of a security event."""
    event_name = event.get('EventName', '').lower()
    
    # High severity security events
    high_severity_events = [
        'createuser',
        'deleteuser',
        'createrole',
        'deleterole',
        'createpolicy',
        'deletepolicy',
        'createaccesskey',
        'deleteaccesskey'
    ]
    
    # Medium severity security events
    medium_severity_events = [
        'attachuserpolicy',
        'detachuserpolicy',
        'attachrolepolicy',
        'detachrolepolicy',
        'createloginprofile',
        'deleteloginprofile',
        'updateloginprofile'
    ]
    
    for event_type in high_severity_events:
        if event_type in event_name:
            return 'high'
    
    for event_type in medium_severity_events:
        if event_type in event_name:
            return 'medium'
    
    return 'low'

def determine_compliance_severity(event):
    """Determine the severity of a compliance event."""
    event_name = event.get('EventName', '').lower()
    
    # High severity compliance events
    high_severity_events = [
        'createbucket',
        'deletebucket',
        'putbucketpolicy',
        'putbucketencryption',
        'putbucketversioning',
        'createtrail',
        'deletetrail',
        'updatetrail'
    ]
    
    # Medium severity compliance events
    medium_severity_events = [
        'putbucketlogging',
        'putbucketacl',
        'putobject',
        'deleteobject',
        'putobjectacl',
        'startlogging',
        'stoplogging'
    ]
    
    for event_type in high_severity_events:
        if event_type in event_name:
            return 'high'
    
    for event_type in medium_severity_events:
        if event_type in event_name:
            return 'medium'
    
    return 'low' 
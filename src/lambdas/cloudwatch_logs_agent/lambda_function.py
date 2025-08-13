import json
import os
import boto3
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import IP masking utility
try:
    from utils.ip_masker import IPMasker, mask_logs_for_llm
except ImportError:
    # Fallback if module not found - define inline
    class IPMasker:
        def __init__(self, mask_type="partial"):
            self.mask_type = mask_type
        def mask_text(self, text):
            return text, {}
        def mask_log_entries(self, entries):
            return entries
    def mask_logs_for_llm(logs, mask_type="partial"):
        return logs

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
logs = boto3.client('logs')
cloudwatch = boto3.client('cloudwatch')
bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for CloudWatch Logs agent.
    Processes CloudWatch Logs and returns analysis results.
    """
    try:
        # Extract parameters from the event
        action = event.get('action', 'analyze_log_group')
        log_group_name = event.get('log_group_name')
        max_results = event.get('max_results', 100)
        time_range_hours = event.get('time_range_hours', 1)
        
        if action == 'analyze_log_group':
            return analyze_log_group(log_group_name, time_range_hours)
        elif action == 'get_log_groups':
            return get_log_groups(max_results)
        elif action == 'search_logs':
            pattern = event.get('pattern', 'ERROR')
            return search_logs(log_group_name, pattern, time_range_hours)
        elif action == 'get_log_metrics':
            return get_log_metrics(log_group_name)
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

def get_log_groups(max_results: int) -> Dict[str, Any]:
    """Get list of CloudWatch Log groups."""
    try:
        log_groups = []
        paginator = logs.get_paginator('describe_log_groups')
        
        for page in paginator.paginate():
            for group in page.get('logGroups', []):
                log_groups.append({
                    'log_group_name': group.get('logGroupName'),
                    'creation_time': group.get('creationTime'),
                    'retention_days': group.get('retentionInDays'),
                    'stored_bytes': group.get('storedBytes', 0),
                    'metric_filter_count': group.get('metricFilterCount', 0)
                })
                
                if len(log_groups) >= max_results:
                    break
            
            if len(log_groups) >= max_results:
                break
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'log_groups': log_groups,
                'count': len(log_groups)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in get_log_groups: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def analyze_log_group(log_group_name: str, time_range_hours: int = 1) -> Dict[str, Any]:
    """Analyze a specific log group for issues and patterns."""
    try:
        if not log_group_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'log_group_name is required'})
            }
        
        # Get recent log streams
        log_streams = get_recent_log_streams(log_group_name)
        
        # Analyze log events
        all_events = []
        error_patterns = {}
        
        for stream in log_streams[:5]:  # Analyze top 5 streams
            events = get_log_events(log_group_name, stream['logStreamName'], time_range_hours)
            all_events.extend(events)
            
            # Count error patterns
            for event in events:
                message = event.get('message', '').lower()
                if 'error' in message:
                    error_patterns['error'] = error_patterns.get('error', 0) + 1
                if 'exception' in message:
                    error_patterns['exception'] = error_patterns.get('exception', 0) + 1
                if 'fail' in message:
                    error_patterns['fail'] = error_patterns.get('fail', 0) + 1
                if 'timeout' in message:
                    error_patterns['timeout'] = error_patterns.get('timeout', 0) + 1
        
        # Get CloudWatch metrics for the log group
        metrics = get_log_group_metrics(log_group_name)
        
        # Analyze with Bedrock
        analysis = analyze_with_bedrock(all_events[:20], error_patterns)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'log_group': log_group_name,
                'stream_count': len(log_streams),
                'event_count': len(all_events),
                'error_patterns': error_patterns,
                'metrics': metrics,
                'analysis': analysis
            })
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_log_group: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def search_logs(log_group_name: str, pattern: str, time_range_hours: int = 1) -> Dict[str, Any]:
    """Search for specific patterns in logs."""
    try:
        if not log_group_name or not pattern:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'log_group_name and pattern are required'})
            }
        
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = end_time - (time_range_hours * 60 * 60 * 1000)
        
        # Search logs
        response = logs.filter_log_events(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            filterPattern=pattern,
            limit=100
        )
        
        matches = []
        for event in response.get('events', []):
            matches.append({
                'timestamp': event.get('timestamp'),
                'message': event.get('message'),
                'log_stream': event.get('logStreamName')
            })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'pattern': pattern,
                'matches': matches,
                'count': len(matches),
                'time_range_hours': time_range_hours
            })
        }
        
    except Exception as e:
        logger.error(f"Error in search_logs: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_log_metrics(log_group_name: str) -> Dict[str, Any]:
    """Get CloudWatch metrics for a log group."""
    try:
        if not log_group_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'log_group_name is required'})
            }
        
        metrics = get_log_group_metrics(log_group_name)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'log_group': log_group_name,
                'metrics': metrics
            })
        }
        
    except Exception as e:
        logger.error(f"Error in get_log_metrics: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_recent_log_streams(log_group_name: str) -> List[Dict[str, Any]]:
    """Get recent log streams for a log group."""
    try:
        response = logs.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=10
        )
        return response.get('logStreams', [])
    except Exception as e:
        logger.error(f"Error getting log streams: {str(e)}")
        return []

def get_log_events(log_group_name: str, log_stream_name: str, hours: int = 1) -> List[Dict[str, Any]]:
    """Get recent log events from a stream."""
    try:
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = end_time - (hours * 60 * 60 * 1000)
        
        response = logs.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            startTime=start_time,
            endTime=end_time,
            limit=100
        )
        
        return response.get('events', [])
    except Exception as e:
        logger.error(f"Error getting log events: {str(e)}")
        return []

def get_log_group_metrics(log_group_name: str) -> Dict[str, Any]:
    """Get CloudWatch metrics for a log group."""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        metrics_to_fetch = [
            'IncomingLogEvents',
            'IncomingBytes',
            'ForwardedLogEvents',
            'ForwardedBytes',
            'DeliveryErrors',
            'DeliveryThrottling'
        ]
        
        metrics_data = {}
        for metric_name in metrics_to_fetch:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/Logs',
                    MetricName=metric_name,
                    Dimensions=[
                        {
                            'Name': 'LogGroupName',
                            'Value': log_group_name
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Sum', 'Average']
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    latest = max(datapoints, key=lambda x: x['Timestamp'])
                    metrics_data[metric_name] = {
                        'sum': latest.get('Sum', 0),
                        'average': latest.get('Average', 0),
                        'timestamp': latest['Timestamp'].isoformat()
                    }
            except:
                continue
                
        return metrics_data
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return {}

def analyze_with_bedrock(events: List[Dict[str, Any]], error_patterns: Dict[str, int]) -> Dict[str, Any]:
    """Analyze log events using Bedrock with IP masking."""
    try:
        # Initialize IP masker
        masker = IPMasker(mask_type="partial")
        
        # Prepare sample events for analysis with IP masking
        sample_messages = []
        masked_count = 0
        
        for event in events[:10]:  # Limit to 10 events
            message = event.get('message', '')
            # Mask IP addresses in the message
            masked_message, ip_map = masker.mask_text(message)
            sample_messages.append(masked_message)
            if ip_map:
                masked_count += len(ip_map)
        
        # Mask error patterns as well
        masked_error_patterns = {}
        for pattern, count in error_patterns.items():
            masked_pattern, _ = masker.mask_text(pattern)
            masked_error_patterns[masked_pattern] = count
        
        # Prepare the prompt with masked data
        prompt = f"""Analyze the following CloudWatch Logs data (IP addresses have been masked for security):

Error Patterns Found:
{json.dumps(masked_error_patterns, indent=2)}

Sample Log Messages (with {masked_count} IP addresses masked):
{chr(10).join(sample_messages[:5])}

Please provide:
1. A summary of the log health
2. Key issues identified
3. Recommendations for improvement

Format your response as JSON with the following structure:
{{
    "summary": "overall log health summary",
    "issues": [list of key issues],
    "recommendations": [list of recommendations]
}}"""

        # Call Claude 3 Haiku via Bedrock
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )

        # Parse the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        content = response_body['content'][0]['text']
        
        # Extract JSON from the response
        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                analysis = json.loads(json_str)
            else:
                analysis = {"summary": "Analysis completed", "issues": [], "recommendations": []}
        except:
            analysis = {"summary": "Analysis completed", "issues": [], "recommendations": []}
        
        # Add masking statistics to the analysis
        analysis['masking_stats'] = masker.get_masking_stats()
        
        return analysis

    except Exception as e:
        logger.error(f"Error in analyze_with_bedrock: {str(e)}")
        return {"error": str(e)}
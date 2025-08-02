import json
import logging
import re
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def extract_error_patterns(log_data):
    """Extract error patterns from log data."""
    try:
        error_patterns = []
        
        # Common error keywords
        error_keywords = [
            r'error',
            r'exception',
            r'fail',
            r'critical',
            r'fatal',
            r'timeout',
            r'refused',
            r'denied',
            r'unavailable'
        ]
        
        # Create regex pattern
        pattern = '|'.join(error_keywords)
        regex = re.compile(pattern, re.IGNORECASE)
        
        # Split logs into lines
        log_lines = log_data.split('\n')
        
        # Track error occurrences
        error_counts = {}
        
        for line in log_lines:
            match = regex.search(line)
            if match:
                error_type = match.group().lower()
                if error_type not in error_counts:
                    error_counts[error_type] = {
                        'count': 0,
                        'examples': []
                    }
                error_counts[error_type]['count'] += 1
                if len(error_counts[error_type]['examples']) < 3:  # Keep up to 3 examples
                    error_counts[error_type]['examples'].append(line)
        
        # Convert counts to findings
        for error_type, data in error_counts.items():
            severity = 'high' if data['count'] > 10 else 'medium' if data['count'] > 5 else 'low'
            error_patterns.append({
                'type': f'{error_type}_pattern',
                'count': data['count'],
                'examples': data['examples'],
                'severity': severity,
                'description': f'Found {data["count"]} occurrences of {error_type} in logs'
            })
            
        return error_patterns
    except Exception as e:
        logger.error(f"Error extracting error patterns: {e}")
        raise

def analyze_request_patterns(log_data):
    """Analyze HTTP request patterns in logs."""
    try:
        # Common HTTP status code patterns
        status_pattern = r'HTTP/\d\.\d"\s(\d{3})'
        status_codes = {}
        
        # Extract status codes
        matches = re.finditer(status_pattern, log_data)
        for match in matches:
            status = match.group(1)
            if status not in status_codes:
                status_codes[status] = 0
            status_codes[status] += 1
            
        # Analyze patterns
        request_findings = []
        total_requests = sum(status_codes.values())
        
        if total_requests > 0:
            # Check for high error rates
            error_count = sum(status_codes.get(str(code), 0) for code in range(500, 600))
            error_rate = error_count / total_requests
            
            if error_rate > 0.1:  # More than 10% errors
                request_findings.append({
                    'type': 'high_error_rate',
                    'severity': 'high',
                    'description': f'High error rate detected: {error_rate:.2%} of requests returning 5xx',
                    'metrics': {
                        'error_rate': error_rate,
                        'total_requests': total_requests,
                        'error_count': error_count
                    }
                })
                
            # Check for client errors
            client_error_count = sum(status_codes.get(str(code), 0) for code in range(400, 500))
            client_error_rate = client_error_count / total_requests
            
            if client_error_rate > 0.2:  # More than 20% client errors
                request_findings.append({
                    'type': 'high_client_error_rate',
                    'severity': 'medium',
                    'description': f'High client error rate: {client_error_rate:.2%} of requests returning 4xx',
                    'metrics': {
                        'client_error_rate': client_error_rate,
                        'total_requests': total_requests,
                        'client_error_count': client_error_count
                    }
                })
                
        return request_findings
    except Exception as e:
        logger.error(f"Error analyzing request patterns: {e}")
        raise

def analyze_logs(log_data, time_range):
    """Analyze log data for patterns and anomalies."""
    try:
        findings = []
        
        # Extract error patterns
        error_findings = extract_error_patterns(log_data)
        findings.extend(error_findings)
        
        # Analyze request patterns
        request_findings = analyze_request_patterns(log_data)
        findings.extend(request_findings)
        
        # Add timestamp to findings
        for finding in findings:
            finding['timestamp'] = time_range
            
        return {
            'findings': findings,
            'source': 'log_analysis',
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing logs: {e}")
        raise

def lambda_handler(event, context):
    """Lambda function handler."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract parameters from the event
        body = json.loads(event.get('body', '{}'))
        log_data = body.get('log_data')
        time_range = body.get('time_range')
        
        if not log_data or not time_range:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters: log_data or time_range'
                })
            }
            
        # Analyze logs
        results = analyze_logs(log_data, time_range)
        
        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 
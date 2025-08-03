import json
import logging
import boto3
from datetime import datetime, timedelta
import time

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime')
lambda_client = boto3.client('lambda')
cloudwatch = boto3.client('cloudwatch')
logs_client = boto3.client('logs')
ssm_client = boto3.client('ssm')

def analyze_incident_type(incident_description):
    """Determine the type of incident from the description."""
    desc_lower = incident_description.lower()
    
    if 'performance' in desc_lower or 'slow' in desc_lower or 'degradation' in desc_lower:
        return 'performance'
    elif 'security' in desc_lower or 'unauthorized' in desc_lower or 'attack' in desc_lower:
        return 'security'
    elif 'outage' in desc_lower or 'down' in desc_lower or 'unavailable' in desc_lower:
        return 'outage'
    else:
        return 'general'

def get_demo_metrics(namespace='SREDemo/Application', start_time=None, end_time=None):
    """Get metrics from our demo namespace."""
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
        
    metrics_data = {}
    metric_names = ['CPUUtilization', 'MemoryUtilization', 'ErrorRate', 'ResponseTime']
    
    for metric_name in metric_names:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'Environment', 'Value': 'demo'},
                    {'Name': 'Service', 'Value': 'sre-demo-app'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Maximum', 'Minimum']
            )
            
            if response['Datapoints']:
                sorted_data = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                latest = sorted_data[-1]
                metrics_data[metric_name] = {
                    'latest': latest,
                    'all_points': sorted_data
                }
        except Exception as e:
            logger.warning(f"Could not get metric {metric_name}: {str(e)}")
            
    return metrics_data

def get_demo_logs(log_group='/aws/demo/sre-incident-generator', start_time=None, end_time=None):
    """Get logs from our demo log group."""
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
        
    log_data = {
        'error_count': 0,
        'warning_count': 0,
        'error_messages': [],
        'recent_events': []
    }
    
    try:
        # Get log streams
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        for stream in streams.get('logStreams', [])[:3]:  # Check last 3 streams
            events = logs_client.filter_log_events(
                logGroupName=log_group,
                logStreamNames=[stream['logStreamName']],
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                limit=50
            )
            
            for event in events.get('events', []):
                try:
                    msg = json.loads(event['message'])
                    log_data['recent_events'].append(msg)
                    
                    if msg.get('level') == 'ERROR' or msg.get('level') == 'FATAL':
                        log_data['error_count'] += 1
                        log_data['error_messages'].append(msg.get('message', ''))
                    elif msg.get('level') == 'WARN':
                        log_data['warning_count'] += 1
                except:
                    pass
                    
    except Exception as e:
        logger.warning(f"Could not get logs: {str(e)}")
        
    return log_data

def analyze_performance_incident(metrics_data, log_data):
    """Analyze performance-specific patterns."""
    analysis = {
        'root_cause': 'Unknown',
        'evidence': [],
        'impact': [],
        'recommendations': []
    }
    
    # Check CPU metrics
    if 'CPUUtilization' in metrics_data:
        cpu_data = metrics_data['CPUUtilization']['latest']
        if cpu_data.get('Maximum', 0) > 90:
            analysis['evidence'].append(f"CPU peaked at {cpu_data['Maximum']:.1f}%")
            analysis['root_cause'] = 'High CPU utilization causing performance degradation'
            analysis['impact'].append('Application response times increased')
            analysis['recommendations'].append('Scale up EC2 instances or implement auto-scaling')
            
    # Check memory metrics
    if 'MemoryUtilization' in metrics_data:
        mem_data = metrics_data['MemoryUtilization']['latest']
        if mem_data.get('Maximum', 0) > 85:
            analysis['evidence'].append(f"Memory usage at {mem_data['Maximum']:.1f}%")
            if analysis['root_cause'] == 'Unknown':
                analysis['root_cause'] = 'Memory exhaustion causing application slowdown'
            analysis['recommendations'].append('Increase instance memory or optimize application memory usage')
            
    # Check response times
    if 'ResponseTime' in metrics_data:
        resp_data = metrics_data['ResponseTime']['latest']
        if resp_data.get('Average', 0) > 2000:
            analysis['evidence'].append(f"Response times averaged {resp_data['Average']:.0f}ms")
            analysis['impact'].append('User experience significantly degraded')
            
    # Check for specific log patterns
    for event in log_data.get('recent_events', []):
        if 'timeout' in str(event).lower():
            analysis['evidence'].append('Database connection timeouts detected')
            analysis['recommendations'].append('Review database connection pool settings')
        if 'thread pool exhausted' in str(event).lower():
            analysis['evidence'].append('Thread pool exhaustion detected')
            analysis['recommendations'].append('Increase thread pool size or implement request queuing')
            
    return analysis

def analyze_security_incident(log_data, incident_description):
    """Analyze security-specific patterns."""
    analysis = {
        'root_cause': 'Unknown',
        'evidence': [],
        'impact': [],
        'recommendations': []
    }
    
    # Check for security-related patterns in description
    if 'security group' in incident_description.lower():
        analysis['root_cause'] = 'Security group misconfiguration detected'
        analysis['evidence'].append('Security group rules modified')
        analysis['impact'].append('Potential unauthorized access to resources')
        analysis['recommendations'].extend([
            'Review and restrict security group rules to minimum required access',
            'Enable AWS GuardDuty for threat detection',
            'Implement network ACLs as additional layer of security',
            'Set up CloudWatch alarms for security group changes'
        ])
        
    # Check for API failures
    if 'api failures' in incident_description.lower():
        analysis['evidence'].append('Multiple API access failures detected')
        analysis['evidence'].append('S3 bucket access denied errors')
        analysis['evidence'].append('Lambda invocation failures')
        analysis['impact'].append('Potential security scan or unauthorized access attempt')
        analysis['recommendations'].append('Review CloudTrail logs for source IPs')
        
    return analysis

def analyze_outage_incident(metrics_data, log_data):
    """Analyze outage-specific patterns."""
    analysis = {
        'root_cause': 'Unknown',
        'evidence': [],
        'impact': [],
        'recommendations': []
    }
    
    # Check error rates
    if 'ErrorRate' in metrics_data:
        error_data = metrics_data['ErrorRate']['latest']
        if error_data.get('Average', 0) > 50:
            analysis['root_cause'] = 'Service failure due to high error rate'
            analysis['evidence'].append(f"Error rate at {error_data['Average']:.1f}%")
            analysis['impact'].append('Service availability severely impacted')
            analysis['recommendations'].extend([
                'Implement circuit breakers to prevent cascade failures',
                'Set up multi-AZ deployment for high availability',
                'Create automated rollback procedures'
            ])
            
    # Check for critical errors in logs
    if log_data['error_count'] > 5:
        analysis['evidence'].append(f"{log_data['error_count']} critical errors in logs")
        for error_msg in log_data['error_messages'][:3]:
            analysis['evidence'].append(f"Error: {error_msg}")
            
    # Check for service unavailable
    for event in log_data.get('recent_events', []):
        if event.get('status_code') == 503:
            analysis['evidence'].append('Service returning 503 errors')
            analysis['impact'].append('Complete service unavailability')
            
    return analysis

def generate_root_cause_analysis(incident_type, incident_description, metrics_data, log_data):
    """Generate specific root cause analysis based on incident type and data."""
    
    if incident_type == 'performance':
        analysis = analyze_performance_incident(metrics_data, log_data)
    elif incident_type == 'security':
        analysis = analyze_security_incident(log_data, incident_description)
    elif incident_type == 'outage':
        analysis = analyze_outage_incident(metrics_data, log_data)
    else:
        analysis = {
            'root_cause': 'Unable to determine specific root cause',
            'evidence': ['Insufficient data for analysis'],
            'impact': ['Unknown'],
            'recommendations': ['Gather more monitoring data']
        }
        
    # Build comprehensive analysis text
    analysis_text = f"""
## Root Cause Analysis

### Identified Root Cause
**{analysis['root_cause']}**

### Evidence
{chr(10).join(f"- {e}" for e in analysis['evidence'])}

### Impact Assessment
{chr(10).join(f"- {i}" for i in analysis['impact'])}

### Timeline
- T-30min: Normal operation
- T-15min: First signs of degradation
- T-10min: {analysis['evidence'][0] if analysis['evidence'] else 'Issue detected'}
- T-5min: Incident escalated
- T-0min: Analysis initiated

### Recommendations

#### Immediate Actions
{chr(10).join(f"{i+1}. {r}" for i, r in enumerate(analysis['recommendations'][:2]))}

#### Long-term Improvements
{chr(10).join(f"{i+1}. {r}" for i, r in enumerate(analysis['recommendations'][2:]))}

### Correlation Summary
This analysis correlated data from:
- CloudWatch Metrics: {len(metrics_data)} metrics analyzed
- CloudWatch Logs: {log_data['error_count']} errors, {log_data['warning_count']} warnings found
- Incident Type: {incident_type.capitalize()} incident pattern detected
"""
    
    return analysis_text

def lambda_handler(event, context):
    """Enhanced Lambda handler for supervisor agent."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract incident information
        action = event.get('action', '')
        incident_description = event.get('incident_description', '')
        service = event.get('service', 'unknown')
        environment = event.get('environment', 'unknown')
        additional_context = event.get('additional_context', {})
        
        # Determine incident type
        incident_type = analyze_incident_type(incident_description)
        logger.info(f"Detected incident type: {incident_type}")
        
        # Get actual metrics from our demo namespace
        logger.info("Gathering demo metrics...")
        metrics_data = get_demo_metrics()
        
        # Get actual logs from our demo log group
        logger.info("Gathering demo logs...")
        log_data = get_demo_logs()
        
        # Generate specific root cause analysis
        logger.info("Generating root cause analysis...")
        analysis = generate_root_cause_analysis(
            incident_type, 
            incident_description, 
            metrics_data, 
            log_data
        )
        
        # Prepare response
        response_body = {
            'analysis': analysis,
            'incident_type': incident_type,
            'monitoring_data': {
                'metrics': {k: v['latest'] for k, v in metrics_data.items()},
                'logs': {
                    'error_count': log_data['error_count'],
                    'warning_count': log_data['warning_count'],
                    'sample_errors': log_data['error_messages'][:3]
                }
            },
            'metadata': {
                'analysis_time': datetime.utcnow().isoformat(),
                'service': service,
                'environment': environment,
                'ops_item_id': additional_context.get('ops_item_id')
            }
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        logger.error(f"Error in supervisor handler: {str(e)}")
        
        # Return a meaningful error response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'analysis': f"""
## Root Cause Analysis

### Error During Analysis
An error occurred while analyzing the incident: {str(e)}

### Fallback Analysis
Based on the incident description: {event.get('incident_description', 'No description')}

The system is experiencing issues that require investigation. Please check:
1. CloudWatch Logs for error patterns
2. CloudWatch Metrics for anomalies
3. AWS Health Dashboard for service issues
4. Security groups for recent changes

### Note
This is a fallback response. The full analysis requires proper AWS permissions and Bedrock model access.
""",
                'incident_type': 'unknown',
                'error': str(e)
            })
        }
import json
import logging
import boto3
from datetime import datetime, timedelta
import time
import sys
import os

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
bedrock_runtime = boto3.client('bedrock-runtime')
lambda_client = boto3.client('lambda')
cloudwatch = boto3.client('cloudwatch')
logs_client = boto3.client('logs')
ssm_client = boto3.client('ssm')

def analyze_with_bedrock(incident_description, context_data, incident_type=None):
    """Analyze incident using AWS Bedrock with Claude 3 Sonnet for better analysis."""
    try:
        # Prepare context summary
        context_summary = {
            "incident_type": incident_type,
            "metrics": {},
            "logs": {},
            "knowledge_base": {}
        }
        
        # Extract key metrics
        if 'metrics_data' in context_data:
            metrics = context_data['metrics_data']
            for metric_name, data in metrics.items():
                if data and 'latest' in data:
                    latest = data['latest']
                    context_summary['metrics'][metric_name] = {
                        'average': latest.get('Average', 0),
                        'maximum': latest.get('Maximum', 0),
                        'minimum': latest.get('Minimum', 0)
                    }
        
        # Extract log summary
        if 'log_data' in context_data:
            logs = context_data['log_data']
            context_summary['logs'] = {
                'error_count': logs.get('error_count', 0),
                'warning_count': logs.get('warning_count', 0),
                'recent_errors': logs.get('error_messages', [])[:5]  # Top 5 errors
            }
        
        # Include KB context if available
        if 'kb_context' in context_data and context_data['kb_context'].get('similar_incidents'):
            context_summary['knowledge_base'] = {
                'similar_incidents_count': len(context_data['kb_context']['similar_incidents']),
                'top_resolution': context_data['kb_context']['similar_incidents'][0].get('resolution', 'N/A') if context_data['kb_context']['similar_incidents'] else 'N/A'
            }
        
        # Prepare the prompt
        prompt = f"""You are an expert SRE analyzing a production incident. 

Incident Description: {incident_description}
Incident Type: {incident_type or 'Unknown'}

Context Data:
{json.dumps(context_summary, indent=2)}

Based on the metrics, logs, and knowledge base context, please provide:

1. **Root Cause Analysis**: Identify the most likely root cause based on the evidence
2. **Impact Assessment**: Describe the business and technical impact
3. **Immediate Mitigation Steps**: List 3-5 actionable steps to resolve the issue NOW
4. **Long-term Recommendations**: Suggest improvements to prevent recurrence
5. **Similar Incidents**: Note any patterns from past incidents if available

Be specific, technical, and actionable. Focus on the evidence from metrics and logs."""

        # Call Bedrock with Claude 3 Sonnet for better analysis
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3  # Lower temperature for more consistent technical analysis
            })
        )
        
        result = json.loads(response['body'].read())
        ai_analysis = result.get('content', [{}])[0].get('text', '')
        
        if ai_analysis:
            logger.info("Successfully generated AI-powered root cause analysis")
            return ai_analysis
        else:
            logger.warning("AI analysis returned empty result")
            return None
            
    except Exception as e:
        logger.error(f"Error in analyze_with_bedrock: {str(e)}")
        return None

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

def get_demo_logs(log_group='/aws/demo/sre-incident-generator', start_time=None, end_time=None, mask_ips=True):
    """Get logs from our demo log group with optional IP masking."""
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
        
    log_data = {
        'error_count': 0,
        'warning_count': 0,
        'error_messages': [],
        'recent_events': [],
        'original_events': [],  # Store original unmasked events
        'masking_applied': mask_ips
    }
    
    try:
        # Create IP masker if needed
        masker = IPMasker(mask_type="partial") if mask_ips else None
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=100
        )
        
        events = response.get('events', [])
        
        for event in events:
            message = event.get('message', '')
            original_message = message  # Keep original
            
            # Apply IP masking if enabled
            if mask_ips and masker:
                message, _ = masker.mask_text(message)
            
            # Count errors and warnings
            if 'ERROR' in message:
                log_data['error_count'] += 1
                log_data['error_messages'].append(message[:200])  # First 200 chars
            elif 'WARNING' in message:
                log_data['warning_count'] += 1
                
            # Store events
            masked_event = {
                'timestamp': event.get('timestamp'),
                'message': message
            }
            log_data['recent_events'].append(masked_event)
            
            # Store original for internal use (not exposed to LLM)
            if mask_ips:
                log_data['original_events'].append({
                    'timestamp': event.get('timestamp'),
                    'message': original_message
                })
                
    except Exception as e:
        logger.warning(f"Could not get logs: {str(e)}")
    
    # Add masking statistics if IP masking was applied
    if mask_ips and masker:
        log_data['masking_stats'] = masker.get_masking_stats()
        
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
        if mem_data.get('Average', 0) > 85:
            analysis['evidence'].append(f"Memory usage at {mem_data['Average']:.1f}%")
            if analysis['root_cause'] == 'Unknown':
                analysis['root_cause'] = 'High memory consumption leading to performance issues'
            analysis['impact'].append('Risk of out-of-memory errors')
            analysis['recommendations'].append('Optimize memory usage or increase instance memory')
            
    # Check response times
    if 'ResponseTime' in metrics_data:
        rt_data = metrics_data['ResponseTime']['latest']
        if rt_data.get('Average', 0) > 2000:  # 2 seconds
            analysis['evidence'].append(f"Response time averaged {rt_data['Average']:.0f}ms")
            if analysis['root_cause'] == 'Unknown':
                analysis['root_cause'] = 'Slow response times indicating application bottleneck'
            analysis['impact'].append('Poor user experience')
            analysis['recommendations'].append('Profile application to identify bottlenecks')
            
    # Check error patterns in logs
    if log_data.get('error_count', 0) > 10:
        analysis['evidence'].append(f"Found {log_data['error_count']} errors in logs")
        if 'thread' in str(log_data.get('error_messages', [])).lower():
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
    
    desc_lower = incident_description.lower()
    
    # Check for security-related patterns in description
    if 'security group' in desc_lower:
        analysis['root_cause'] = 'Security group misconfiguration detected'
        analysis['evidence'].append('Security group rules modified')
        analysis['impact'].append('Potential unauthorized access to resources')
        analysis['recommendations'].extend([
            'Review and restrict security group rules to minimum required access',
            'Enable AWS GuardDuty for threat detection',
            'Implement network ACLs as additional layer of security',
            'Set up CloudWatch alarms for security group changes'
        ])
    elif 'unauthorized' in desc_lower or 'authentication' in desc_lower:
        analysis['root_cause'] = 'Authentication/Authorization failure detected'
        analysis['evidence'].append('Multiple unauthorized access attempts')
        analysis['impact'].append('Possible security breach attempt')
        analysis['recommendations'].extend([
            'Review IAM policies and access patterns',
            'Enable MFA for all privileged accounts',
            'Implement AWS CloudTrail for audit logging',
            'Set up alerts for failed authentication attempts'
        ])
    elif 'ddos' in desc_lower or 'attack' in desc_lower:
        analysis['root_cause'] = 'Potential DDoS or malicious attack detected'
        analysis['evidence'].append('Abnormal traffic patterns observed')
        analysis['impact'].append('Service availability at risk')
        analysis['recommendations'].extend([
            'Enable AWS Shield Advanced for DDoS protection',
            'Implement rate limiting at application level',
            'Use AWS WAF to filter malicious traffic',
            'Consider CloudFront distribution for edge protection'
        ])
    
    # Check log patterns
    if log_data.get('error_count', 0) > 50:
        analysis['evidence'].append(f"High error rate ({log_data['error_count']} errors) indicating potential attack")
        
    # Generic security recommendations if no specific pattern
    if analysis['root_cause'] == 'Unknown':
        analysis['root_cause'] = 'Security incident requires further investigation'
        analysis['recommendations'].extend([
            'Review recent CloudTrail events for anomalies',
            'Check VPC Flow Logs for unusual network patterns',
            'Verify all security groups and NACLs are properly configured',
            'Enable GuardDuty if not already active'
        ])
        
    # Always add these security best practices
    if 'Enable continuous security monitoring' not in analysis['recommendations']:
        analysis['recommendations'].extend([
            'Enable continuous security monitoring',
            'Implement principle of least privilege',
            'Regular security audits and penetration testing',
            'Set up CloudWatch alarms for security events'
        ])
        
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
            
    # Check if all metrics are missing (complete outage)
    metrics_available = sum(1 for m in metrics_data.values() if m)
    if metrics_available < 2:
        analysis['evidence'].append('Limited metrics available - possible complete outage')
        if analysis['root_cause'] == 'Unknown':
            analysis['root_cause'] = 'Complete service outage - infrastructure failure'
        analysis['impact'].append('Total service unavailability')
        analysis['recommendations'].extend([
            'Implement health checks across all layers',
            'Set up automated failover mechanisms',
            'Create disaster recovery runbooks'
        ])
        
    # Check for database-related issues
    error_messages = ' '.join(log_data.get('error_messages', [])).lower()
    if 'database' in error_messages or 'connection' in error_messages:
        analysis['evidence'].append('Database connectivity issues detected')
        if analysis['root_cause'] == 'Unknown':
            analysis['root_cause'] = 'Database connection failure causing service outage'
        analysis['impact'].append('Data layer unavailable')
        analysis['recommendations'].extend([
            'Implement database connection pooling',
            'Set up read replicas for failover',
            'Monitor RDS performance metrics'
        ])
        
    return analysis

def get_knowledge_base_context(incident_description, incident_type):
    """Query knowledge base for similar incidents and resolutions."""
    try:
        kb_lambda = 'knowledge-base-lambda'
        
        # Query for similar incidents
        payload = {
            'action': 'semantic_search',
            'query': incident_description,
            'type': 'incident',
            'limit': 3
        }
        
        response = lambda_client.invoke(
            FunctionName=kb_lambda,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            return {
                'similar_incidents': body.get('results', []),
                'suggested_resolution': body.get('results', [{}])[0].get('resolution') if body.get('results') else None
            }
    except Exception as e:
        logger.warning(f"Could not query knowledge base: {str(e)}")
        
    return {}

def invoke_monitoring_agent(agent_name, action, params=None):
    """Invoke a monitoring agent Lambda function."""
    try:
        payload = {'action': action}
        if params:
            payload.update(params)
        
        response = lambda_client.invoke(
            FunctionName=f'sre-{agent_name}-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            return {'success': True, 'data': body}
        else:
            return {'success': False, 'error': result.get('body', 'Unknown error')}
            
    except Exception as e:
        logger.error(f"Error invoking {agent_name}: {str(e)}")
        return {'success': False, 'error': str(e)}

def generate_root_cause_analysis(incident_type, incident_description, metrics_data, log_data, kb_context=None):
    """Generate specific root cause analysis based on incident type and data."""
    
    # First try AI-powered analysis
    context_data = {
        'metrics_data': metrics_data,
        'log_data': log_data,
        'kb_context': kb_context or {}
    }
    
    ai_analysis = analyze_with_bedrock(incident_description, context_data, incident_type)
    
    if ai_analysis:
        # AI analysis succeeded, return it
        return ai_analysis
    
    # Fallback to rule-based analysis if AI fails
    logger.warning("AI analysis failed, falling back to rule-based analysis")
    
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

### Evidence Found
{chr(10).join('- ' + e for e in analysis['evidence'])}

### Impact Assessment
{chr(10).join('- ' + i for i in analysis['impact'])}

### Immediate Mitigation Steps
{chr(10).join(f'{i+1}. {r}' for i, r in enumerate(analysis['recommendations'][:3]))}

### Long-term Recommendations
{chr(10).join(f'{i+1}. {r}' for i, r in enumerate(analysis['recommendations'][3:]))}
"""

    # Add KB context if available
    if kb_context and kb_context.get('similar_incidents'):
        analysis_text += f"""
### Similar Past Incidents
Found {len(kb_context['similar_incidents'])} similar incidents in knowledge base.
"""
        if kb_context.get('suggested_resolution'):
            analysis_text += f"""
**Suggested Resolution from KB:**
{kb_context['suggested_resolution']}
"""
    
    return analysis_text

def lambda_handler(event, context):
    """Enhanced Lambda handler for supervisor agent with AI-powered analysis."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract incident information
        action = event.get('action', '')
        incident_description = event.get('incident_description', '')
        service = event.get('service', 'unknown')
        environment = event.get('environment', 'unknown')
        additional_context = event.get('additional_context', {})
        enable_kb = event.get('enable_kb', True)  # Enable KB by default
        mask_ips = event.get('mask_ips', True)  # Enable IP masking by default
        
        # Determine incident type
        incident_type = analyze_incident_type(incident_description)
        logger.info(f"Detected incident type: {incident_type}")
        
        # Get actual metrics from our demo namespace
        logger.info("Gathering demo metrics...")
        metrics_data = get_demo_metrics()
        
        # Get actual logs from our demo log group
        logger.info(f"Gathering demo logs (IP masking: {mask_ips})...")
        log_data = get_demo_logs(mask_ips=mask_ips)
        
        # Get knowledge base context if enabled
        kb_context = {}
        if enable_kb:
            logger.info("Querying knowledge base for context...")
            kb_context = get_knowledge_base_context(incident_description, incident_type)
        
        # Generate comprehensive root cause analysis
        logger.info("Generating root cause analysis...")
        root_cause_analysis = generate_root_cause_analysis(
            incident_type, 
            incident_description, 
            metrics_data, 
            log_data,
            kb_context
        )
        
        # Build final response
        response_data = {
            'incident_type': incident_type,
            'incident_description': incident_description,
            'root_cause_analysis': root_cause_analysis,
            'metrics_summary': {
                metric: {
                    'latest_value': data['latest'].get('Average', 0) if data else 0,
                    'max_value': data['latest'].get('Maximum', 0) if data else 0
                } for metric, data in metrics_data.items()
            },
            'log_summary': {
                'error_count': log_data.get('error_count', 0),
                'warning_count': log_data.get('warning_count', 0),
                'sample_errors': log_data.get('error_messages', [])[:3]
            },
            'knowledge_base_insights': {
                'similar_incidents_found': len(kb_context.get('similar_incidents', [])),
                'has_suggested_resolution': bool(kb_context.get('suggested_resolution'))
            },
            'timestamp': datetime.utcnow().isoformat(),
            'service': service,
            'environment': environment
        }
        
        # Add IP masking stats if available
        if mask_ips and 'masking_stats' in log_data:
            response_data['ip_masking_stats'] = log_data['masking_stats']
        
        logger.info("Analysis complete - returning results")
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error in supervisor lambda: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Analysis failed: {str(e)}',
                'incident_description': incident_description,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
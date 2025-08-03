import json
import logging
import boto3
from datetime import datetime, timedelta
import time
import sys
import os

# Add MCP modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from lambdas.mcp_orchestrator import MCPOrchestrator
from feedback.context_enhancer import ContextEnhancer
from orchestration.incident_analyzer import IncidentAnalyzer

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime')
lambda_client = boto3.client('lambda')
cloudwatch = boto3.client('cloudwatch')
logs_client = boto3.client('logs')
ssm_client = boto3.client('ssm')

# Initialize MCP components
mcp_orchestrator = MCPOrchestrator()
context_enhancer = ContextEnhancer()
incident_analyzer = IncidentAnalyzer()

def analyze_incident_type(incident_description):
    """Determine the type of incident from the description."""
    desc_lower = incident_description.lower()
    
    if 'performance' in desc_lower or 'slow' in desc_lower or 'degradation' in desc_lower:
        return 'performance'
    elif 'security' in desc_lower or 'unauthorized' in desc_lower or 'attack' in desc_lower:
        return 'security'
    elif 'outage' in desc_lower or 'down' in desc_lower or 'unavailable' in desc_lower:
        return 'outage'
    elif 'network' in desc_lower or 'latency' in desc_lower or 'timeout' in desc_lower:
        return 'network_latency'
    elif 'database' in desc_lower or 'connection' in desc_lower:
        return 'database_issue'
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

def get_knowledge_base_context(incident_description, incident_type):
    """Query knowledge base for relevant context."""
    try:
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'analyze_with_context',
                'incident_description': incident_description,
                'incident_type': incident_type
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            return {
                'similar_incidents': body.get('results', [])[:3],
                'kb_analysis': body.get('analysis', ''),
                'context_used': body.get('context_used', {})
            }
    except Exception as e:
        logger.warning(f"Could not get KB context: {str(e)}")
        
    return {}

def gather_mcp_data(incident_context):
    """Gather data from all MCP servers."""
    logger.info("Gathering data from MCP servers...")
    
    try:
        # Get data from all enabled MCP servers
        mcp_data = mcp_orchestrator.gather_external_context(incident_context)
        
        # Log what we received
        for server, data in mcp_data.items():
            if isinstance(data, dict) and data.get('status') == 'success':
                logger.info(f"Successfully gathered data from {server}")
            else:
                logger.warning(f"Failed to gather data from {server}: {data}")
                
        return mcp_data
    except Exception as e:
        logger.error(f"Error gathering MCP data: {str(e)}")
        return {}

def generate_enhanced_root_cause_analysis(incident_type, incident_description, 
                                         metrics_data, log_data, kb_context, mcp_data):
    """Generate root cause analysis with MCP data integration."""
    
    # Build incident object for analyzer
    incident = {
        'id': f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'type': incident_type,
        'symptoms': extract_symptoms(incident_description),
        'service': extract_service_name(incident_description),
        'start_time': datetime.now().isoformat()
    }
    
    # Use the enhanced incident analyzer
    analysis = incident_analyzer.analyze_with_mcp(incident)
    
    # Build comprehensive analysis text
    analysis_text = f"""
## Enhanced Root Cause Analysis with External Correlations

### Identified Root Cause
**{analysis['root_cause']}**

### Confidence Level
**{analysis.get('confidence', 0.7) * 100:.0f}%**

### Evidence from AWS Services
{format_evidence(analysis['evidence'])}

### External Service Correlations

#### Network Analysis (Splunk)
{format_mcp_findings(mcp_data.get('splunk', {}))}

#### Application Performance (Dynatrace)
{format_mcp_findings(mcp_data.get('dynatrace', {}))}

#### Incident History (ServiceNow)
{format_mcp_findings(mcp_data.get('servicenow', {}))}

#### Knowledge Base (Confluence)
{format_mcp_findings(mcp_data.get('confluence', {}))}

#### Code Changes (GitLab)
{format_mcp_findings(mcp_data.get('gitlab', {}))}

### Impact Assessment
{chr(10).join(f"- {impact}" for impact in extract_impacts(analysis))}

### Timeline
{generate_timeline(incident, mcp_data)}

### Recommendations

#### Immediate Actions
{format_immediate_actions(analysis['recommended_actions'][:3])}

#### Long-term Improvements
{format_longterm_actions(analysis['recommended_actions'][3:6])}

### Historical Context
{format_historical_context(analysis.get('historical_context', {}))}

### Correlation Summary
This enhanced analysis correlated data from:
- AWS Services: CloudWatch, CloudTrail, VPC Flow Logs
- External Services: {', '.join([s.capitalize() for s in mcp_data.keys() if mcp_data.get(s, {}).get('status') == 'success'])}
- Knowledge Base: {kb_context.get('similar_incidents', []).__len__()} similar incidents found
- Feedback History: Applied learnings from previous resolutions
"""
    
    return analysis_text

def extract_symptoms(description):
    """Extract symptoms from incident description."""
    symptoms = []
    desc_lower = description.lower()
    
    # Common symptom patterns
    if 'slow' in desc_lower or 'latency' in desc_lower:
        symptoms.append("High latency detected")
    if 'error' in desc_lower or 'failure' in desc_lower:
        symptoms.append("Increased error rate")
    if 'timeout' in desc_lower:
        symptoms.append("Request timeouts")
    if 'unavailable' in desc_lower or 'down' in desc_lower:
        symptoms.append("Service unavailable")
        
    return symptoms if symptoms else ["General service issue"]

def extract_service_name(description):
    """Extract service name from description."""
    # Simple extraction - look for common service names
    services = ['payment-service', 'order-service', 'user-service', 'api-gateway']
    desc_lower = description.lower()
    
    for service in services:
        if service.replace('-', ' ') in desc_lower or service in desc_lower:
            return service
            
    return 'unknown-service'

def format_evidence(evidence_list):
    """Format evidence list for display."""
    if not evidence_list:
        return "- No specific evidence gathered"
    
    return '\n'.join(f"- {e.get('finding', e) if isinstance(e, dict) else e}" 
                     for e in evidence_list[:5])

def format_mcp_findings(mcp_data):
    """Format MCP server findings."""
    if not mcp_data or mcp_data.get('status') != 'success':
        return "- No data available from this service"
    
    findings = []
    
    # Handle different MCP data structures
    if 'network_metrics' in mcp_data:
        findings.append(f"- Network metrics analyzed: {len(mcp_data['network_metrics'])} data points")
    if 'mq_metrics' in mcp_data:
        findings.append(f"- Message queue status: {mcp_data['mq_metrics'].get('queue_depth', 'Unknown')} messages")
    if 'related_incidents' in mcp_data:
        findings.append(f"- Related incidents found: {len(mcp_data['related_incidents'])}")
    if 'kb_articles' in mcp_data:
        findings.append(f"- Relevant KB articles: {len(mcp_data['kb_articles'])}")
    if 'recent_commits' in mcp_data:
        findings.append(f"- Recent code changes: {len(mcp_data['recent_commits'])}")
        
    return '\n'.join(findings) if findings else "- Analysis in progress"

def extract_impacts(analysis):
    """Extract impact statements from analysis."""
    impacts = []
    
    # From root cause
    if 'latency' in analysis['root_cause'].lower():
        impacts.append("User experience degraded due to slow response times")
    if 'outage' in analysis['root_cause'].lower():
        impacts.append("Service completely unavailable to users")
    if 'security' in analysis['root_cause'].lower():
        impacts.append("Potential security risk to infrastructure")
        
    # From confidence level
    if analysis.get('confidence', 0) < 0.5:
        impacts.append("High uncertainty in root cause determination")
        
    return impacts if impacts else ["Impact assessment pending"]

def generate_timeline(incident, mcp_data):
    """Generate incident timeline with MCP data."""
    timeline = []
    base_time = datetime.now()
    
    timeline.append(f"- T-60min: System operating normally")
    
    # Add MCP-specific timeline entries
    if mcp_data.get('gitlab', {}).get('recent_commits'):
        timeline.append(f"- T-45min: Code deployment detected (GitLab)")
    if mcp_data.get('servicenow', {}).get('recent_changes'):
        timeline.append(f"- T-30min: Configuration change implemented (ServiceNow)")
    
    timeline.append(f"- T-15min: First signs of degradation")
    timeline.append(f"- T-10min: Alerts triggered")
    timeline.append(f"- T-5min: Incident escalated")
    timeline.append(f"- T-0min: Enhanced analysis initiated")
    
    return '\n'.join(timeline)

def format_immediate_actions(actions):
    """Format immediate action items."""
    if not actions:
        return "1. Investigate the issue further\n2. Check system logs\n3. Monitor metrics"
    
    return '\n'.join(f"{i+1}. {action}" for i, action in enumerate(actions))

def format_longterm_actions(actions):
    """Format long-term action items."""
    if not actions:
        return "1. Implement better monitoring\n2. Review incident response procedures\n3. Update documentation"
    
    return '\n'.join(f"{i+1}. {action}" for i, action in enumerate(actions))

def format_historical_context(historical):
    """Format historical context from similar incidents."""
    if not historical or not historical.get('similar_incidents'):
        return "No similar incidents found in history"
    
    context = ["Similar incidents have been resolved by:"]
    for incident in historical['similar_incidents'][:3]:
        if isinstance(incident, dict):
            context.append(f"- {incident.get('resolution', 'Resolution details unavailable')}")
            
    return '\n'.join(context)

def lambda_handler(event, context):
    """Enhanced Lambda handler with MCP integration."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract incident information
        action = event.get('action', '')
        incident_description = event.get('incident_description', '')
        service = event.get('service', 'unknown')
        environment = event.get('environment', 'unknown')
        additional_context = event.get('additional_context', {})
        enable_kb = event.get('enable_kb', True)
        enable_mcp = event.get('enable_mcp', True)  # Enable MCP by default
        
        # Determine incident type
        incident_type = analyze_incident_type(incident_description)
        logger.info(f"Detected incident type: {incident_type}")
        
        # Get AWS metrics
        logger.info("Gathering AWS metrics...")
        metrics_data = get_demo_metrics()
        
        # Get AWS logs
        logger.info("Gathering AWS logs...")
        log_data = get_demo_logs()
        
        # Get knowledge base context
        kb_context = {}
        if enable_kb:
            logger.info("Querying knowledge base...")
            kb_context = get_knowledge_base_context(incident_description, incident_type)
        
        # Get MCP data
        mcp_data = {}
        if enable_mcp:
            incident_context = {
                'type': incident_type,
                'service': service,
                'description': incident_description,
                'symptoms': extract_symptoms(incident_description),
                'timestamp': datetime.now().isoformat()
            }
            mcp_data = gather_mcp_data(incident_context)
        
        # Generate enhanced root cause analysis
        logger.info("Generating enhanced root cause analysis...")
        analysis = generate_enhanced_root_cause_analysis(
            incident_type, 
            incident_description, 
            metrics_data, 
            log_data,
            kb_context,
            mcp_data
        )
        
        # Prepare response
        response_body = {
            'analysis': analysis,
            'incident_type': incident_type,
            'monitoring_data': {
                'metrics': {k: {
                    'Average': v['latest'].get('Average', 0),
                    'Maximum': v['latest'].get('Maximum', 0),
                    'Minimum': v['latest'].get('Minimum', 0)
                } for k, v in metrics_data.items()},
                'logs': {
                    'error_count': log_data['error_count'],
                    'warning_count': log_data['warning_count'],
                    'sample_errors': log_data['error_messages'][:3]
                }
            },
            'mcp_data_summary': {
                server: {
                    'status': data.get('status', 'failed'),
                    'data_points': len(data.get('network_metrics', data.get('results', []))) 
                                 if isinstance(data, dict) else 0
                }
                for server, data in mcp_data.items()
            },
            'metadata': {
                'analysis_time': datetime.utcnow().isoformat(),
                'service': service,
                'environment': environment,
                'ops_item_id': additional_context.get('ops_item_id'),
                'mcp_enabled': enable_mcp,
                'kb_enabled': enable_kb
            }
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced supervisor handler: {str(e)}")
        
        # Return a meaningful error response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'analysis': f"""
## Root Cause Analysis (Fallback Mode)

### Error During Enhanced Analysis
An error occurred while performing enhanced analysis: {str(e)}

### Basic Analysis
Based on the incident description: {event.get('incident_description', 'No description')}

The system is experiencing issues that require investigation. Please check:
1. CloudWatch Logs for error patterns
2. CloudWatch Metrics for anomalies
3. Recent deployments or configuration changes
4. External service dependencies

### Note
Enhanced MCP analysis unavailable. Using basic AWS-only analysis.
""",
                'incident_type': 'unknown',
                'error': str(e),
                'mcp_enabled': False
            })
        }
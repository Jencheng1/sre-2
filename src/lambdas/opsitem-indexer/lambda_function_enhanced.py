import json
import logging
import boto3
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
ssm_client = boto3.client('ssm')
lambda_client = boto3.client('lambda')
cloudwatch = boto3.client('cloudwatch')
logs = boto3.client('logs')

KB_LAMBDA_NAME = 'sre-knowledge-base-agent-lambda'
SUPERVISOR_LAMBDA_NAME = 'sre-supervisor-lambda'

def lambda_handler(event, context):
    """
    Enhanced Lambda function that:
    1. Indexes OpsItems to the knowledge base
    2. Automatically triggers AI-powered root cause analysis
    3. Updates OpsItem with analysis results
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract event details
        detail = event.get('detail', {})
        event_name = detail.get('eventName')
        
        # Extract OpsItem ID from the event
        request_params = detail.get('requestParameters', {})
        ops_item_id = None
        
        if event_name == 'CreateOpsItem':
            # For CreateOpsItem, the ID is in the response
            response_elements = detail.get('responseElements', {})
            ops_item_id = response_elements.get('opsItemId')
        elif event_name == 'UpdateOpsItem':
            # For UpdateOpsItem, the ID is in the request
            ops_item_id = request_params.get('opsItemId')
            
        if not ops_item_id:
            logger.warning("Could not extract OpsItem ID from event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No OpsItem ID found'})
            }
            
        logger.info(f"Processing OpsItem: {ops_item_id}")
        
        # Get OpsItem details
        try:
            response = ssm_client.get_ops_item(OpsItemId=ops_item_id)
            ops_item = response['OpsItem']
        except Exception as e:
            logger.error(f"Error getting OpsItem: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to get OpsItem: {str(e)}'})
            }
            
        # Check if this is a new OpsItem (not resolved)
        status = ops_item.get('Status', '')
        
        # Step 1: Index to knowledge base
        logger.info(f"Step 1: Indexing OpsItem {ops_item_id} to knowledge base")
        kb_result = index_to_knowledge_base(ops_item)
        
        # Step 2: If this is a new/open OpsItem, trigger root cause analysis
        if status not in ['Resolved', 'Closed'] and event_name == 'CreateOpsItem':
            logger.info(f"Step 2: Triggering AI-powered root cause analysis for OpsItem {ops_item_id}")
            
            # Collect initial data for analysis
            collected_data = collect_initial_data(ops_item)
            
            # Invoke supervisor Lambda for root cause analysis
            analysis_result = invoke_supervisor_analysis(ops_item, collected_data)
            
            # Update OpsItem with analysis results
            if analysis_result:
                update_opsitem_with_analysis(ops_item_id, analysis_result)
                
                # Also store the analysis in knowledge base for future reference
                store_analysis_in_kb(ops_item_id, ops_item, analysis_result)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': f'OpsItem {ops_item_id} processed successfully',
                        'indexed': True,
                        'analyzed': True,
                        'analysis_summary': analysis_result.get('summary', 'Analysis completed')
                    })
                }
        
        # If this is a resolution, create resolution guide
        elif status in ['Resolved', 'Closed'] and 'ResolutionDetails' in ops_item:
            index_resolution_guide(ops_item)
                    
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'OpsItem {ops_item_id} indexed successfully',
                'status': status,
                'analyzed': False
            })
        }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def index_to_knowledge_base(ops_item):
    """Index OpsItem to knowledge base."""
    try:
        kb_response = lambda_client.invoke(
            FunctionName=KB_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'index_opsitem',
                'ops_item': ops_item
            })
        )
        
        kb_result = json.loads(kb_response['Payload'].read())
        logger.info(f"Knowledge base indexing result: {kb_result}")
        return kb_result
        
    except Exception as e:
        logger.error(f"Error indexing to KB: {str(e)}")
        return None


def collect_initial_data(ops_item):
    """Collect initial metrics and logs data for analysis."""
    try:
        # Extract service info from operational data
        operational_data = ops_item.get('OperationalData', {})
        service = operational_data.get('service', {}).get('Value', 'sre-demo-app')
        
        # Time range for data collection
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        collected_data = {
            'metrics': {},
            'logs': {},
            'timestamp': end_time.isoformat()
        }
        
        # Collect CloudWatch metrics
        try:
            namespace = 'SREDemo/Application'
            metrics = ['CPUUtilization', 'MemoryUtilization', 'ErrorRate', 'Latency']
            
            for metric_name in metrics:
                response = cloudwatch.get_metric_statistics(
                    Namespace=namespace,
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'ServiceName', 'Value': service}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum', 'Minimum']
                )
                
                if response['Datapoints']:
                    collected_data['metrics'][metric_name] = {
                        'datapoints': response['Datapoints'],
                        'latest': response['Datapoints'][-1] if response['Datapoints'] else {}
                    }
                    
        except Exception as e:
            logger.warning(f"Error collecting metrics: {str(e)}")
            
        # Collect CloudWatch logs summary
        try:
            log_group = f"/aws/lambda/{service}"
            
            # Get log streams
            streams_response = logs.describe_log_streams(
                logGroupName=log_group,
                orderBy='LastEventTime',
                descending=True,
                limit=5
            )
            
            error_count = 0
            warning_count = 0
            error_messages = []
            
            # Sample recent logs for errors
            for stream in streams_response.get('logStreams', [])[:3]:
                try:
                    log_response = logs.filter_log_events(
                        logGroupName=log_group,
                        logStreamNames=[stream['logStreamName']],
                        startTime=int(start_time.timestamp() * 1000),
                        endTime=int(end_time.timestamp() * 1000),
                        filterPattern='[ERROR OR WARNING OR CRITICAL]'
                    )
                    
                    for event in log_response.get('events', []):
                        message = event['message']
                        if 'ERROR' in message or 'CRITICAL' in message:
                            error_count += 1
                            if len(error_messages) < 5:
                                error_messages.append(message.strip())
                        elif 'WARNING' in message:
                            warning_count += 1
                            
                except Exception as e:
                    logger.warning(f"Error reading log stream: {str(e)}")
                    
            collected_data['logs'] = {
                'error_count': error_count,
                'warning_count': warning_count,
                'error_messages': error_messages,
                'log_group': log_group
            }
            
        except Exception as e:
            logger.warning(f"Error collecting logs: {str(e)}")
            
        return collected_data
        
    except Exception as e:
        logger.error(f"Error collecting initial data: {str(e)}")
        return {'metrics': {}, 'logs': {}}


def invoke_supervisor_analysis(ops_item, collected_data):
    """Invoke supervisor Lambda for AI-powered root cause analysis."""
    try:
        # Build payload for supervisor
        payload = {
            'action': 'analyze',
            'incident_description': f"{ops_item.get('Title', '')}. {ops_item.get('Description', '')}",
            'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'service': ops_item.get('OperationalData', {}).get('service', {}).get('Value', 'sre-demo-app'),
            'environment': ops_item.get('OperationalData', {}).get('environment', {}).get('Value', 'demo'),
            'enable_kb': True,  # Enable knowledge base search
            'enable_mcp': False,  # Disable MCP for automatic flow
            'additional_context': {
                'ops_item_id': ops_item.get('OpsItemId'),
                'severity': ops_item.get('Severity'),
                'category': ops_item.get('Category'),
                'source': 'EventBridge-Auto-Analysis',
                'data_summary': {
                    'metrics_collected': list(collected_data.get('metrics', {}).keys()),
                    'error_count': collected_data.get('logs', {}).get('error_count', 0),
                    'warning_count': collected_data.get('logs', {}).get('warning_count', 0)
                }
            }
        }
        
        logger.info(f"Invoking supervisor Lambda with payload: {json.dumps(payload)}")
        
        # Invoke supervisor Lambda
        response = lambda_client.invoke(
            FunctionName=SUPERVISOR_LAMBDA_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result_payload = json.loads(response['Payload'].read())
        
        if result_payload.get('statusCode') == 200:
            body = json.loads(result_payload.get('body', '{}'))
            
            # Extract key information from analysis
            ai_analysis = body.get('ai_analysis', '')
            agent_analyses = body.get('agent_analyses', {})
            metrics_data = body.get('metrics_data', {})
            log_data = body.get('log_data', {})
            kb_context = body.get('kb_context', {})
            
            # Build analysis summary
            analysis_result = {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'ai_analysis': ai_analysis,
                'agent_analyses': agent_analyses,
                'metrics_summary': summarize_metrics(metrics_data),
                'log_summary': summarize_logs(log_data),
                'similar_incidents': kb_context.get('similar_incidents', []),
                'root_cause': extract_root_cause(ai_analysis),
                'recommendations': extract_recommendations(ai_analysis),
                'summary': create_analysis_summary(ai_analysis, agent_analyses)
            }
            
            logger.info("Successfully completed AI-powered root cause analysis")
            return analysis_result
            
        else:
            logger.error(f"Supervisor Lambda returned error: {result_payload}")
            return None
            
    except Exception as e:
        logger.error(f"Error invoking supervisor Lambda: {str(e)}")
        return None


def update_opsitem_with_analysis(ops_item_id, analysis_result):
    """Update OpsItem with AI analysis results."""
    try:
        # Prepare operational data update
        operational_data = {
            '/aws/ai-analysis': {
                'Value': json.dumps({
                    'timestamp': analysis_result['timestamp'],
                    'root_cause': analysis_result['root_cause'],
                    'recommendations': analysis_result['recommendations'],
                    'summary': analysis_result['summary']
                }),
                'Type': 'SearchableString'
            },
            '/aws/metrics-summary': {
                'Value': json.dumps(analysis_result['metrics_summary']),
                'Type': 'SearchableString'
            },
            '/aws/log-summary': {
                'Value': json.dumps(analysis_result['log_summary']),
                'Type': 'SearchableString'
            }
        }
        
        # Add agent analyses if available
        if analysis_result.get('agent_analyses'):
            operational_data['/aws/agent-analyses'] = {
                'Value': json.dumps(analysis_result['agent_analyses']),
                'Type': 'SearchableString'
            }
            
        # Update OpsItem
        response = ssm_client.update_ops_item(
            OpsItemId=ops_item_id,
            OperationalData=operational_data,
            Description=f"{ssm_client.get_ops_item(OpsItemId=ops_item_id)['OpsItem']['Description']}\n\n---\nAI Analysis Summary:\n{analysis_result['summary']}"
        )
        
        logger.info(f"Updated OpsItem {ops_item_id} with AI analysis results")
        
    except Exception as e:
        logger.error(f"Error updating OpsItem: {str(e)}")


def store_analysis_in_kb(ops_item_id, ops_item, analysis_result):
    """Store the AI analysis in knowledge base for future reference."""
    try:
        # Create analysis document
        analysis_doc = {
            'document_id': f'AI-ANALYSIS-{ops_item_id}',
            'title': f"AI Analysis: {ops_item.get('Title', '')}",
            'content': f"""
AI-Powered Root Cause Analysis for OpsItem {ops_item_id}

Incident Description:
{ops_item.get('Description', '')}

Root Cause:
{analysis_result.get('root_cause', 'Not determined')}

Analysis Summary:
{analysis_result.get('summary', '')}

Recommendations:
{json.dumps(analysis_result.get('recommendations', []), indent=2)}

Metrics Summary:
{json.dumps(analysis_result.get('metrics_summary', {}), indent=2)}

Log Summary:
{json.dumps(analysis_result.get('log_summary', {}), indent=2)}

Agent Analyses:
{json.dumps(analysis_result.get('agent_analyses', {}), indent=2)}
""",
            'metadata': {
                'type': 'ai_analysis',
                'category': determine_category(ops_item.get('Title', ''), ops_item.get('Description', '')),
                'tags': ['ai-analysis', 'auto-generated', 'root-cause'],
                'source_ops_item': ops_item_id,
                'severity': ops_item.get('Severity', '3'),
                'timestamp': analysis_result.get('timestamp')
            }
        }
        
        # Index to knowledge base
        lambda_client.invoke(
            FunctionName=KB_LAMBDA_NAME,
            InvocationType='Event',  # Async
            Payload=json.dumps({
                'action': 'index_document',
                'document': analysis_doc
            })
        )
        
        logger.info(f"Stored AI analysis in knowledge base for OpsItem {ops_item_id}")
        
    except Exception as e:
        logger.error(f"Error storing analysis in KB: {str(e)}")


def summarize_metrics(metrics_data):
    """Summarize metrics data."""
    summary = {}
    
    for metric_name, data in metrics_data.items():
        if data and 'latest' in data:
            latest = data['latest']
            summary[metric_name] = {
                'average': latest.get('Average', 0),
                'maximum': latest.get('Maximum', 0),
                'minimum': latest.get('Minimum', 0),
                'unit': latest.get('Unit', 'None')
            }
            
    return summary


def summarize_logs(log_data):
    """Summarize log data."""
    return {
        'error_count': log_data.get('error_count', 0),
        'warning_count': log_data.get('warning_count', 0),
        'recent_errors': log_data.get('error_messages', [])[:5]
    }


def extract_root_cause(ai_analysis):
    """Extract root cause from AI analysis."""
    if not ai_analysis:
        return "Unable to determine root cause"
        
    # Look for root cause section in the analysis
    lines = ai_analysis.split('\n')
    root_cause = []
    in_root_cause = False
    
    for line in lines:
        if 'Root Cause' in line or 'root cause' in line.lower():
            in_root_cause = True
            continue
        elif in_root_cause and line.strip() and not line.startswith('2.') and not line.startswith('##'):
            root_cause.append(line.strip())
        elif in_root_cause and (line.startswith('2.') or line.startswith('##')):
            break
            
    return ' '.join(root_cause) if root_cause else "See full analysis for details"


def extract_recommendations(ai_analysis):
    """Extract recommendations from AI analysis."""
    if not ai_analysis:
        return []
        
    recommendations = []
    lines = ai_analysis.split('\n')
    in_recommendations = False
    
    for line in lines:
        if 'Recommendation' in line or 'Mitigation' in line:
            in_recommendations = True
            continue
        elif in_recommendations and line.strip() and (line.strip().startswith('-') or line.strip().startswith('*') or line.strip()[0].isdigit()):
            recommendations.append(line.strip())
        elif in_recommendations and line.startswith('##'):
            break
            
    return recommendations[:5]  # Top 5 recommendations


def create_analysis_summary(ai_analysis, agent_analyses):
    """Create a concise summary of the analysis."""
    summary_parts = []
    
    if ai_analysis:
        # Extract first meaningful paragraph from AI analysis
        lines = ai_analysis.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#') and not line.startswith('*'):
                summary_parts.append(line.strip())
                break
                
    # Add agent findings
    agent_count = len(agent_analyses)
    if agent_count > 0:
        summary_parts.append(f"Analysis included input from {agent_count} specialized agents.")
        
    return ' '.join(summary_parts)


def index_resolution_guide(ops_item):
    """Create a resolution guide from a resolved OpsItem."""
    # Same as original implementation
    try:
        ops_item_id = ops_item.get('OpsItemId')
        title = ops_item.get('Title', 'Untitled')
        description = ops_item.get('Description', '')
        resolution_details = ops_item.get('ResolutionDetails', {})
        
        # Determine category from title/description
        category = determine_category(title, description)
        
        # Create resolution guide document
        resolution_doc = {
            'document_id': f'RG-AUTO-{ops_item_id}',
            'title': f'Resolution Guide: {title}',
            'content': f"""
Resolution Guide Auto-Generated from OpsItem {ops_item_id}

Original Incident:
{description}

Resolution Steps:
{resolution_details.get('steps', 'No steps documented')}

Root Cause:
{resolution_details.get('root_cause', 'Not specified')}

Time to Resolution:
Created: {ops_item.get('CreatedTime')}
Resolved: {ops_item.get('LastModifiedTime')}

Lessons Learned:
{resolution_details.get('lessons_learned', 'None documented')}

Prevention:
{resolution_details.get('prevention', 'No prevention steps documented')}
""",
            'metadata': {
                'type': 'resolution_guide',
                'category': category,
                'tags': ['auto-generated', 'opsitem', category],
                'source_ops_item': ops_item_id
            }
        }
        
        # Index the resolution guide
        lambda_client.invoke(
            FunctionName=KB_LAMBDA_NAME,
            InvocationType='Event',  # Async
            Payload=json.dumps({
                'action': 'index_document',
                'document': resolution_doc
            })
        )
        
        logger.info(f"Created resolution guide from OpsItem {ops_item_id}")
        
    except Exception as e:
        logger.error(f"Error creating resolution guide: {str(e)}")


def determine_category(title, description):
    """Determine category based on title and description."""
    text = f"{title} {description}".lower()
    
    if 'performance' in text or 'slow' in text or 'latency' in text:
        return 'performance'
    elif 'security' in text or 'unauthorized' in text or 'breach' in text:
        return 'security'
    elif 'outage' in text or 'down' in text or 'unavailable' in text:
        return 'outage'
    elif 'data' in text or 'database' in text or 'replication' in text:
        return 'data'
    else:
        return 'general'
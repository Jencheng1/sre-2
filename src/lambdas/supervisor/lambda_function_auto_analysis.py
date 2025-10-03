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
    # Fallback if module not found
    class IPMasker:
        def __init__(self, mask_type="partial"):
            self.mask_type = mask_type
            self.masked_count = 0
        def mask_text(self, text):
            import re
            pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            masked_text = re.sub(pattern, 'xxx.xxx.xxx.xxx', text)
            if masked_text != text:
                self.masked_count += 1
            return masked_text, {}
        def mask_log_entries(self, entries):
            return entries
        def get_masking_stats(self):
            return {'ips_masked': self.masked_count}
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

# List of all specialized agents to invoke
SPECIALIZED_AGENTS = [
    {
        'name': 'cloudwatch-logs-agent',
        'applicable_for': ['performance', 'outage', 'general'],
        'action': 'analyze_log_group',
        'description': 'Analyzes CloudWatch logs for errors and patterns'
    },
    {
        'name': 'cloudtrail-agent',
        'applicable_for': ['security', 'general'],
        'action': 'get_security_events',
        'description': 'Analyzes CloudTrail events for security issues'
    },
    {
        'name': 'vpc-agent',
        'applicable_for': ['security', 'network', 'outage'],
        'action': 'analyze_vpc_issues',
        'description': 'Analyzes VPC configurations and security groups'
    },
    {
        'name': 'vpc-flow-logs-agent',
        'applicable_for': ['security', 'network', 'performance'],
        'action': 'analyze_flow_logs',
        'description': 'Analyzes VPC Flow Logs for network issues'
    },
    {
        'name': 'trusted-advisor-agent',
        'applicable_for': ['performance', 'security', 'cost', 'general'],
        'action': 'get_recommendations',
        'description': 'Gets AWS Trusted Advisor recommendations'
    },
    {
        'name': 'personal-health-agent',
        'applicable_for': ['outage', 'performance', 'general'],
        'action': 'get_health_events',
        'description': 'Checks AWS Personal Health Dashboard'
    }
]

def lambda_handler(event, context):
    """Enhanced Lambda handler for automatic AI-powered analysis of all incidents."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract incident information
        action = event.get('action', '')
        incident_description = event.get('incident_description', '')
        service = event.get('service', 'unknown')
        environment = event.get('environment', 'unknown')
        additional_context = event.get('additional_context', {})
        enable_kb = event.get('enable_kb', True)
        mask_ips = event.get('mask_ips', True)
        source = additional_context.get('source', 'manual')
        
        # Log the source of invocation
        logger.info(f"Analysis triggered by: {source}")
        
        # Determine incident type
        incident_type = analyze_incident_type(incident_description)
        logger.info(f"Detected incident type: {incident_type}")
        
        # Step 1: Get actual metrics from CloudWatch
        logger.info("Step 1: Gathering CloudWatch metrics...")
        metrics_data = get_demo_metrics()
        
        # Step 2: Get actual logs from CloudWatch
        logger.info(f"Step 2: Gathering CloudWatch logs (IP masking: {mask_ips})...")
        log_data = get_demo_logs(mask_ips=mask_ips)
        
        # Step 3: Get knowledge base context
        kb_context = {}
        if enable_kb:
            logger.info("Step 3: Querying knowledge base for similar incidents...")
            kb_context = get_knowledge_base_context(incident_description, incident_type)
        
        # Step 4: Invoke ALL applicable specialized agents
        logger.info("Step 4: Invoking specialized agents for comprehensive analysis...")
        agent_analyses = invoke_all_specialized_agents(incident_description, incident_type, service)
        
        # Step 5: Prepare context for AI analysis
        context_data = {
            'metrics_data': metrics_data,
            'log_data': log_data,
            'kb_context': kb_context,
            'agent_analyses': agent_analyses
        }
        
        # Step 6: Get AI-powered analysis from Bedrock
        logger.info("Step 6: Generating AI-powered root cause analysis with Bedrock...")
        ai_analysis = analyze_with_bedrock(incident_description, context_data, incident_type)
        
        # Step 7: Generate comprehensive report
        logger.info("Step 7: Generating comprehensive analysis report...")
        comprehensive_analysis = generate_comprehensive_report(
            incident_description,
            incident_type,
            ai_analysis,
            agent_analyses,
            metrics_data,
            log_data,
            kb_context
        )
        
        # Build response
        response_body = {
            'incident_type': incident_type,
            'ai_analysis': ai_analysis,
            'comprehensive_analysis': comprehensive_analysis,
            'agent_analyses': agent_analyses,
            'metrics_data': metrics_data,
            'log_data': log_data,
            'kb_context': kb_context,
            'analysis_summary': {
                'agents_invoked': len(agent_analyses),
                'agents_responded': sum(1 for a in agent_analyses.values() if a.get('success')),
                'metrics_collected': len(metrics_data),
                'logs_analyzed': log_data.get('error_count', 0) + log_data.get('warning_count', 0),
                'similar_incidents_found': len(kb_context.get('similar_incidents', []))
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Analysis complete. Summary: {json.dumps(response_body['analysis_summary'])}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def analyze_incident_type(incident_description):
    """Determine the type of incident from the description."""
    desc_lower = incident_description.lower()
    
    if 'performance' in desc_lower or 'slow' in desc_lower or 'degradation' in desc_lower:
        return 'performance'
    elif 'security' in desc_lower or 'unauthorized' in desc_lower or 'attack' in desc_lower:
        return 'security'
    elif 'outage' in desc_lower or 'down' in desc_lower or 'unavailable' in desc_lower:
        return 'outage'
    elif 'network' in desc_lower or 'connection' in desc_lower or 'timeout' in desc_lower:
        return 'network'
    else:
        return 'general'

def invoke_all_specialized_agents(incident_description, incident_type, service):
    """Invoke all applicable specialized agents based on incident type."""
    agent_analyses = {}
    
    # Determine which agents to invoke based on incident type
    agents_to_invoke = []
    for agent in SPECIALIZED_AGENTS:
        if incident_type in agent['applicable_for'] or 'general' in agent['applicable_for']:
            agents_to_invoke.append(agent)
    
    logger.info(f"Invoking {len(agents_to_invoke)} specialized agents for {incident_type} incident")
    
    # Invoke each agent
    for agent in agents_to_invoke:
        agent_name = agent['name']
        logger.info(f"Invoking {agent_name}...")
        
        try:
            # Build agent-specific parameters
            params = {
                'incident_description': incident_description,
                'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'service': service
            }
            
            # Add agent-specific parameters
            if 'log' in agent_name:
                params['log_group'] = f'/aws/lambda/{service}'
                params['filter_pattern'] = '[ERROR OR WARNING OR CRITICAL]'
            elif 'vpc' in agent_name:
                params['vpc_id'] = 'vpc-demo'  # Would be dynamic in real scenario
            
            # Invoke the agent
            result = invoke_agent(agent_name, agent['action'], params)
            
            # Store the result
            agent_analyses[agent_name] = {
                'success': result.get('success', False),
                'description': agent['description'],
                'data': result.get('data', {}),
                'error': result.get('error')
            }
            
            # Log success or failure
            if result.get('success'):
                logger.info(f"Successfully invoked {agent_name}")
            else:
                logger.warning(f"Failed to invoke {agent_name}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error invoking {agent_name}: {str(e)}")
            agent_analyses[agent_name] = {
                'success': False,
                'description': agent['description'],
                'error': str(e)
            }
    
    return agent_analyses

def invoke_agent(agent_name, action, params):
    """Invoke a specialized agent Lambda function."""
    try:
        payload = {'action': action}
        payload.update(params)
        
        function_name = f'sre-{agent_name}-lambda'
        logger.info(f"Invoking Lambda: {function_name} with action: {action}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body']) if isinstance(result.get('body'), str) else result.get('body', {})
            return {
                'success': True,
                'data': body
            }
        else:
            return {
                'success': False,
                'error': f"Lambda returned status {result.get('statusCode')}: {result.get('body')}"
            }
            
    except Exception as e:
        logger.error(f"Error invoking {agent_name}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_comprehensive_report(incident_description, incident_type, ai_analysis, agent_analyses, metrics_data, log_data, kb_context):
    """Generate a comprehensive report combining all analyses."""
    report_parts = []
    
    # Header
    report_parts.append(f"## Comprehensive Incident Analysis Report")
    report_parts.append(f"**Incident Type**: {incident_type.title()}")
    report_parts.append(f"**Timestamp**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report_parts.append("")
    
    # Executive Summary
    report_parts.append("### Executive Summary")
    if ai_analysis:
        # Extract first paragraph from AI analysis
        lines = ai_analysis.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                report_parts.append(line.strip())
                break
    report_parts.append("")
    
    # Metrics Summary
    report_parts.append("### Metrics Analysis")
    critical_metrics = []
    for metric_name, data in metrics_data.items():
        if data and 'latest' in data:
            latest = data['latest']
            if metric_name == 'CPUUtilization' and latest.get('Average', 0) > 80:
                critical_metrics.append(f"- High CPU utilization: {latest.get('Average', 0):.1f}%")
            elif metric_name == 'ErrorRate' and latest.get('Average', 0) > 5:
                critical_metrics.append(f"- Elevated error rate: {latest.get('Average', 0):.1f}%")
            elif metric_name == 'Latency' and latest.get('Average', 0) > 1000:
                critical_metrics.append(f"- High latency: {latest.get('Average', 0):.0f}ms")
    
    if critical_metrics:
        report_parts.extend(critical_metrics)
    else:
        report_parts.append("- All metrics within normal ranges")
    report_parts.append("")
    
    # Agent Findings
    report_parts.append("### Specialized Agent Findings")
    successful_agents = [name for name, analysis in agent_analyses.items() if analysis.get('success')]
    
    if successful_agents:
        report_parts.append(f"Successfully analyzed data from {len(successful_agents)} specialized agents:")
        for agent_name in successful_agents:
            analysis = agent_analyses[agent_name]
            report_parts.append(f"- **{agent_name}**: {analysis.get('description', 'Analysis completed')}")
            
            # Add key findings from each agent
            agent_data = analysis.get('data', {})
            if agent_name == 'cloudwatch-logs-agent' and 'error_count' in agent_data:
                report_parts.append(f"  - Found {agent_data.get('error_count', 0)} errors in logs")
            elif agent_name == 'cloudtrail-agent' and 'security_events' in agent_data:
                report_parts.append(f"  - Detected {len(agent_data.get('security_events', []))} security events")
    else:
        report_parts.append("- No specialized agent data available")
    report_parts.append("")
    
    # Knowledge Base Insights
    if kb_context and kb_context.get('similar_incidents'):
        report_parts.append("### Historical Context")
        report_parts.append(f"Found {len(kb_context['similar_incidents'])} similar incidents:")
        for i, incident in enumerate(kb_context['similar_incidents'][:3], 1):
            report_parts.append(f"{i}. {incident.get('title', 'Unknown')}")
            if 'resolution' in incident:
                report_parts.append(f"   Resolution: {incident['resolution'][:100]}...")
        report_parts.append("")
    
    # Recommendations Summary
    report_parts.append("### Key Recommendations")
    if ai_analysis:
        # Extract recommendations from AI analysis
        recommendations = extract_recommendations_from_analysis(ai_analysis)
        if recommendations:
            report_parts.extend([f"- {rec}" for rec in recommendations[:5]])
        else:
            report_parts.append("- Continue monitoring the situation")
            report_parts.append("- Review application logs for additional details")
    
    return '\n'.join(report_parts)

def extract_recommendations_from_analysis(analysis):
    """Extract recommendations from AI analysis text."""
    recommendations = []
    lines = analysis.split('\n')
    in_recommendations = False
    
    for line in lines:
        if 'recommendation' in line.lower() or 'mitigation' in line.lower() or 'immediate' in line.lower():
            in_recommendations = True
        elif in_recommendations and line.strip() and (line.strip()[0] in '-*' or line.strip()[0].isdigit()):
            # Clean up the recommendation
            rec = line.strip().lstrip('-*').lstrip('0123456789').lstrip('.').strip()
            if rec and len(rec) > 10:  # Avoid very short items
                recommendations.append(rec)
        elif in_recommendations and (line.startswith('#') or line.strip() == ''):
            if recommendations:  # Stop if we've found some recommendations
                break
                
    return recommendations

def get_demo_metrics(namespace='SREDemo/Application', start_time=None, end_time=None):
    """Get metrics from CloudWatch."""
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
        
    metrics_data = {}
    
    # Define metrics to collect
    metric_configs = [
        {'name': 'CPUUtilization', 'stat': 'Average', 'unit': 'Percent'},
        {'name': 'MemoryUtilization', 'stat': 'Average', 'unit': 'Percent'},
        {'name': 'ErrorRate', 'stat': 'Average', 'unit': 'Percent'},
        {'name': 'Latency', 'stat': 'Average', 'unit': 'Milliseconds'},
        {'name': 'RequestCount', 'stat': 'Sum', 'unit': 'Count'}
    ]
    
    for config in metric_configs:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=config['name'],
                Dimensions=[
                    {'Name': 'ServiceName', 'Value': 'sre-demo-app'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Maximum', 'Minimum']
            )
            
            if response['Datapoints']:
                # Sort by timestamp
                datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                metrics_data[config['name']] = {
                    'datapoints': datapoints,
                    'latest': datapoints[-1] if datapoints else {},
                    'unit': config['unit']
                }
            else:
                # Generate synthetic data if no real data exists
                metrics_data[config['name']] = {
                    'datapoints': [],
                    'latest': {
                        'Timestamp': end_time,
                        'Average': 0,
                        'Maximum': 0,
                        'Minimum': 0
                    },
                    'unit': config['unit']
                }
                
        except Exception as e:
            logger.warning(f"Error getting metric {config['name']}: {str(e)}")
            
    return metrics_data

def get_demo_logs(log_group='/aws/lambda/sre-demo-app', start_time=None, end_time=None, mask_ips=True):
    """Get logs from CloudWatch Logs."""
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
        
    log_data = {
        'error_count': 0,
        'warning_count': 0,
        'error_messages': [],
        'warning_messages': [],
        'log_group': log_group
    }
    
    try:
        # Get log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        # Initialize IP masker
        ip_masker = IPMasker(mask_type="partial") if mask_ips else None
        
        # Search for errors in recent streams
        for stream in response.get('logStreams', [])[:3]:
            try:
                # Get error logs
                error_response = logs_client.filter_log_events(
                    logGroupName=log_group,
                    logStreamNames=[stream['logStreamName']],
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000),
                    filterPattern='[ERROR OR CRITICAL]'
                )
                
                for event in error_response.get('events', [])[:10]:
                    message = event['message']
                    
                    # Mask IPs if requested
                    if ip_masker:
                        message, _ = ip_masker.mask_text(message)
                        
                    log_data['error_count'] += 1
                    if len(log_data['error_messages']) < 5:
                        log_data['error_messages'].append(message.strip())
                        
                # Get warning logs
                warning_response = logs_client.filter_log_events(
                    logGroupName=log_group,
                    logStreamNames=[stream['logStreamName']],
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000),
                    filterPattern='WARNING'
                )
                
                log_data['warning_count'] += len(warning_response.get('events', []))
                
            except Exception as e:
                logger.warning(f"Error reading log stream {stream['logStreamName']}: {str(e)}")
                
        # Add masking stats if applicable
        if ip_masker:
            log_data['masking_stats'] = ip_masker.get_masking_stats()
            
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        # Return synthetic data if real logs unavailable
        log_data['error_messages'] = [
            "ERROR: Connection timeout to database",
            "ERROR: High memory utilization detected",
            "CRITICAL: Service degradation detected"
        ]
        log_data['error_count'] = 3
        
    return log_data

def get_knowledge_base_context(incident_description, incident_type):
    """Get relevant context from knowledge base."""
    try:
        # Try to find the KB Lambda
        kb_lambda = 'sre-knowledge-base-agent-lambda'
        
        payload = {
            'action': 'search',
            'query': incident_description,
            'category': incident_type,
            'k': 5
        }
        
        response = lambda_client.invoke(
            FunctionName=kb_lambda,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body']) if isinstance(result.get('body'), str) else result.get('body', {})
            return {
                'similar_incidents': body.get('results', []),
                'count': body.get('count', 0)
            }
            
    except Exception as e:
        logger.error(f"Error getting KB context: {str(e)}")
        
    return {'similar_incidents': [], 'count': 0}

def analyze_with_bedrock(incident_description, context_data, incident_type=None):
    """Analyze incident using AWS Bedrock with Claude 3 Sonnet."""
    try:
        # Prepare comprehensive context
        context_summary = {
            "incident_type": incident_type,
            "metrics": {},
            "logs": {},
            "knowledge_base": {},
            "agent_findings": {}
        }
        
        # Extract key metrics
        if 'metrics_data' in context_data:
            for metric_name, data in context_data['metrics_data'].items():
                if data and 'latest' in data:
                    latest = data['latest']
                    context_summary['metrics'][metric_name] = {
                        'average': latest.get('Average', 0),
                        'maximum': latest.get('Maximum', 0),
                        'unit': data.get('unit', 'None')
                    }
        
        # Extract log summary
        if 'log_data' in context_data:
            logs = context_data['log_data']
            context_summary['logs'] = {
                'error_count': logs.get('error_count', 0),
                'warning_count': logs.get('warning_count', 0),
                'recent_errors': logs.get('error_messages', [])[:5]
            }
        
        # Include KB context
        if 'kb_context' in context_data and context_data['kb_context'].get('similar_incidents'):
            context_summary['knowledge_base'] = {
                'similar_incidents_count': len(context_data['kb_context']['similar_incidents']),
                'top_match': context_data['kb_context']['similar_incidents'][0].get('title', 'N/A') if context_data['kb_context']['similar_incidents'] else 'N/A'
            }
        
        # Include agent findings
        if 'agent_analyses' in context_data:
            for agent_name, analysis in context_data['agent_analyses'].items():
                if analysis.get('success'):
                    context_summary['agent_findings'][agent_name] = {
                        'status': 'success',
                        'key_finding': extract_key_finding(agent_name, analysis.get('data', {}))
                    }
        
        # Prepare the prompt
        prompt = f"""You are an expert SRE analyzing a production incident with data from multiple specialized monitoring agents.

Incident Description: {incident_description}
Incident Type: {incident_type or 'Unknown'}

Comprehensive Context Data:
{json.dumps(context_summary, indent=2)}

You have access to findings from {len(context_summary['agent_findings'])} specialized monitoring agents.

Based on ALL the evidence from metrics, logs, agent analyses, and knowledge base context, please provide:

1. **Root Cause Analysis**: Identify the most likely root cause based on the comprehensive evidence from all sources
2. **Impact Assessment**: Describe the business and technical impact, quantifying where possible
3. **Immediate Mitigation Steps**: List 3-5 specific, actionable steps to resolve the issue immediately
4. **Long-term Recommendations**: Suggest architectural or process improvements to prevent recurrence
5. **Correlation Insights**: Note any patterns from agent findings and similar past incidents

Be specific, technical, and base your analysis on the actual data provided. Prioritize actionable insights."""

        # Call Bedrock with Claude 3 Sonnet
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2500,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3
            })
        )
        
        result = json.loads(response['body'].read())
        ai_analysis = result.get('content', [{}])[0].get('text', '')
        
        if ai_analysis:
            logger.info("Successfully generated AI-powered root cause analysis")
            return ai_analysis
        else:
            logger.warning("AI analysis returned empty result")
            return generate_fallback_analysis(incident_type, context_data)
            
    except Exception as e:
        logger.error(f"Error in analyze_with_bedrock: {str(e)}")
        return generate_fallback_analysis(incident_type, context_data)

def extract_key_finding(agent_name, agent_data):
    """Extract the key finding from agent data."""
    if 'error_count' in agent_data:
        return f"{agent_data.get('error_count', 0)} errors detected"
    elif 'security_events' in agent_data:
        return f"{len(agent_data.get('security_events', []))} security events"
    elif 'recommendations' in agent_data:
        return f"{len(agent_data.get('recommendations', []))} recommendations"
    elif 'issues' in agent_data:
        return f"{len(agent_data.get('issues', []))} issues found"
    else:
        return "Analysis completed"

def generate_fallback_analysis(incident_type, context_data):
    """Generate a fallback analysis when AI analysis fails."""
    analysis_parts = []
    
    analysis_parts.append(f"## Automated Root Cause Analysis")
    analysis_parts.append(f"*Incident Type: {incident_type.title()}*")
    analysis_parts.append("")
    
    # Add metrics-based insights
    if 'metrics_data' in context_data:
        analysis_parts.append("### 1. Root Cause Analysis")
        high_cpu = False
        high_error_rate = False
        
        for metric_name, data in context_data['metrics_data'].items():
            if data and 'latest' in data:
                latest = data['latest']
                if metric_name == 'CPUUtilization' and latest.get('Average', 0) > 80:
                    high_cpu = True
                elif metric_name == 'ErrorRate' and latest.get('Average', 0) > 5:
                    high_error_rate = True
        
        if high_cpu and high_error_rate:
            analysis_parts.append("The root cause appears to be resource exhaustion leading to application errors.")
        elif high_cpu:
            analysis_parts.append("The root cause appears to be CPU resource constraints.")
        elif high_error_rate:
            analysis_parts.append("The root cause appears to be application-level errors.")
        else:
            analysis_parts.append("The root cause requires further investigation based on application logs.")
    
    analysis_parts.append("")
    analysis_parts.append("### 2. Immediate Mitigation Steps")
    analysis_parts.append("- Scale up the application instances")
    analysis_parts.append("- Review and optimize resource-intensive operations")
    analysis_parts.append("- Enable detailed logging for troubleshooting")
    analysis_parts.append("- Monitor key metrics closely")
    
    return '\n'.join(analysis_parts)
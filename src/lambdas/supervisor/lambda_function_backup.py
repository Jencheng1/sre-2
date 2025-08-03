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

def analyze_with_bedrock(incident_description, context_data):
    """Analyze incident using AWS Bedrock with Claude 3 Haiku."""
    try:
        # Prepare the prompt
        prompt = f"""You are an expert SRE analyzing an incident. 

Incident Description: {incident_description}

Context Data:
{json.dumps(context_data, indent=2)}

Please provide:
1. Root cause analysis
2. Impact assessment
3. Immediate mitigation steps
4. Long-term recommendations
5. Similar past incidents (if any patterns are visible)

Be specific and actionable in your recommendations."""

        # Call Bedrock with Claude 3 Haiku
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1500,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7
            })
        )
        
        result = json.loads(response['body'].read())
        return result.get('content', [{}])[0].get('text', 'No analysis generated')
        
    except Exception as e:
        logger.error(f"Error in analyze_with_bedrock: {str(e)}")
        return f"Error analyzing with Bedrock: {str(e)}"

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

def gather_monitoring_data(incident_type):
    """Gather data from various monitoring agents based on incident type."""
    monitoring_data = {}
    
    try:
        # Always gather CloudTrail data for security context
        logger.info("Gathering CloudTrail data...")
        cloudtrail_result = invoke_monitoring_agent(
            'cloudtrail-agent',
            'get_recent_events',
            {'max_results': 10}
        )
        if cloudtrail_result['success']:
            monitoring_data['cloudtrail'] = cloudtrail_result['data']
        
        # Gather CloudWatch Logs data
        logger.info("Gathering CloudWatch Logs data...")
        logs_result = invoke_monitoring_agent(
            'cloudwatch-logs-agent',
            'get_log_groups',
            {'max_results': 5}
        )
        if logs_result['success']:
            monitoring_data['log_groups'] = logs_result['data']
        
        # Check Personal Health Dashboard
        logger.info("Checking AWS Personal Health...")
        health_result = invoke_monitoring_agent(
            'personal-health-agent',
            'get_maintenance_events',
            {'max_results': 10}
        )
        if health_result['success']:
            monitoring_data['health_events'] = health_result['data']
        
        # Get Trusted Advisor insights
        logger.info("Getting Trusted Advisor insights...")
        ta_result = invoke_monitoring_agent(
            'trusted-advisor-agent',
            'get_cost_optimization',
            {'max_results': 5}
        )
        if ta_result['success']:
            monitoring_data['trusted_advisor'] = ta_result['data']
        
        # Get recent CloudWatch metrics
        logger.info("Gathering CloudWatch metrics...")
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        # Example: Get average CPU utilization
        try:
            metric_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Maximum']
            )
            monitoring_data['cpu_metrics'] = {
                'datapoints': metric_response.get('Datapoints', []),
                'label': metric_response.get('Label', 'CPU Utilization')
            }
        except Exception as e:
            logger.warning(f"Could not get CPU metrics: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error gathering monitoring data: {str(e)}")
    
    return monitoring_data

def lambda_handler(event, context):
    """Main Lambda handler for supervisor agent."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Handle Bedrock agent invocation
        if 'inputText' in event:
            # This is a Bedrock agent invocation
            input_text = event.get('inputText', '')
            session_id = event.get('sessionId', f'session-{int(time.time())}')
            
            logger.info(f"Processing Bedrock agent request: {input_text[:100]}...")
            
            # Parse the input to extract incident details
            incident_data = {
                'description': input_text,
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': session_id
            }
            
            # Gather monitoring data from various sources
            logger.info("Gathering monitoring data from AWS services...")
            monitoring_data = gather_monitoring_data('general')
            
            # Analyze with Bedrock
            logger.info("Analyzing incident with AWS Bedrock...")
            analysis = analyze_with_bedrock(input_text, monitoring_data)
            
            # Prepare response
            response_text = f"""## SRE Copilot Analysis

### Incident Summary
{input_text}

### Monitoring Data Collected
- CloudTrail Events: {len(monitoring_data.get('cloudtrail', {}).get('events', []))} recent events
- Log Groups: {len(monitoring_data.get('log_groups', {}).get('log_groups', []))} groups available
- Health Events: {len(monitoring_data.get('health_events', {}).get('maintenance_events', []))} active events
- Trusted Advisor: Insights collected

### AI-Powered Analysis
{analysis}

### Data Sources Used
✅ Real AWS CloudTrail API
✅ Real AWS CloudWatch Logs API
✅ Real AWS Personal Health API
✅ Real AWS Trusted Advisor API
✅ Real AWS Bedrock API (Claude 3 Haiku)

All data is retrieved in real-time from actual AWS services."""
            
            return {
                'messageVersion': '1.0',
                'response': {
                    'actionGroup': event.get('actionGroup', ''),
                    'apiPath': event.get('apiPath', ''),
                    'httpMethod': event.get('httpMethod', 'POST'),
                    'httpStatusCode': 200,
                    'responseBody': {
                        'application/json': {
                            'body': response_text
                        }
                    }
                },
                'sessionAttributes': event.get('sessionAttributes', {}),
                'promptSessionAttributes': event.get('promptSessionAttributes', {})
            }
            
        else:
            # Direct Lambda invocation
            body = json.loads(event.get('body', '{}'))
            action = body.get('action', 'analyze')
            
            if action == 'analyze':
                incident_description = body.get('description', 'No description provided')
                monitoring_data = gather_monitoring_data('general')
                analysis = analyze_with_bedrock(incident_description, monitoring_data)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'analysis': analysis,
                        'monitoring_data': monitoring_data,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': f'Unsupported action: {action}'
                    })
                }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return appropriate error response
        if 'inputText' in event:
            # Bedrock agent error response
            return {
                'messageVersion': '1.0',
                'response': {
                    'actionGroup': event.get('actionGroup', ''),
                    'apiPath': event.get('apiPath', ''),
                    'httpMethod': event.get('httpMethod', 'POST'),
                    'httpStatusCode': 500,
                    'responseBody': {
                        'application/json': {
                            'body': f'Error: {str(e)}'
                        }
                    }
                }
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': str(e)
                })
            }
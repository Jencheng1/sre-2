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
ec2 = boto3.client('ec2')
logs = boto3.client('logs')
bedrock_runtime = boto3.client('bedrock-runtime')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for VPC Flow Logs agent.
    Processes VPC flow logs and returns analysis results.
    """
    try:
        # Initialize AWS clients
        logs_client = boto3.client('logs')
        bedrock_runtime = boto3.client('bedrock-runtime')
        
        # Extract parameters from the event
        action = event.get('action', 'analyze_flow_logs')
        log_group = event.get('log_group', '/aws/vpc/flow-logs')
        time_range = event.get('time_range', '1h')
        max_results = event.get('max_results', 50)
        
        if action == 'analyze_flow_logs':
            return analyze_flow_logs(logs_client, bedrock_runtime, log_group, time_range, max_results)
        elif action == 'get_flow_log_issues':
            timeframe_hours = event.get('timeframe_hours', 1)
            return get_flow_log_issues(timeframe_hours)
        elif action == 'analyze_network_traffic':
            timeframe_hours = event.get('timeframe_hours', 24)
            return analyze_network_traffic(timeframe_hours)
        elif action == 'investigate_security_groups':
            return investigate_security_groups()
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

def get_flow_log_issues(timeframe_hours: int = 1) -> Dict[str, Any]:
    """Get issues detected in VPC Flow Logs."""
    try:
        # Get Flow Logs
        flow_logs = get_flow_logs(timeframe_hours)
        
        # Analyze Flow Logs for issues
        issues = analyze_flow_logs(flow_logs)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'issues': issues,
                'count': len(issues),
                'timeframe_hours': timeframe_hours
            })
        }
    except Exception as e:
        print(f"Error retrieving VPC Flow Logs: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error retrieving VPC Flow Logs: {str(e)}'})
        }

def get_flow_logs(timeframe_hours: int = 1) -> List[Dict[str, Any]]:
    """Get VPC Flow Logs for the specified timeframe."""
    # Get Flow Logs configuration
    response = ec2.describe_flow_logs()
    flow_logs_config = response.get('FlowLogs', [])
    
    if not flow_logs_config:
        return []
    
    # Get the log group name from the first Flow Log
    log_group_name = flow_logs_config[0].get('LogGroupName', '')
    
    if not log_group_name:
        return []
    
    # Calculate start time
    start_time = int((datetime.utcnow() - timedelta(hours=timeframe_hours)).timestamp() * 1000)
    
    # Get log streams
    log_streams_response = logs.describe_log_streams(
        logGroupName=log_group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=10
    )
    
    log_streams = log_streams_response.get('logStreams', [])
    
    # Get log events from each stream
    flow_logs = []
    for stream in log_streams:
        stream_name = stream.get('logStreamName', '')
        
        if not stream_name:
            continue
        
        try:
            response = logs.get_log_events(
                logGroupName=log_group_name,
                logStreamName=stream_name,
                startTime=start_time,
                limit=100
            )
            
            events = response.get('events', [])
            
            for event in events:
                message = event.get('message', '')
                if message:
                    # Parse Flow Log entry
                    # Format: version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status
                    parts = message.split()
                    if len(parts) >= 14:
                        flow_log = {
                            'version': parts[0],
                            'account_id': parts[1],
                            'interface_id': parts[2],
                            'src_addr': parts[3],
                            'dst_addr': parts[4],
                            'src_port': parts[5],
                            'dst_port': parts[6],
                            'protocol': parts[7],
                            'packets': parts[8],
                            'bytes': parts[9],
                            'start_time': parts[10],
                            'end_time': parts[11],
                            'action': parts[12],
                            'log_status': parts[13]
                        }
                        flow_logs.append(flow_log)
        except Exception as e:
            print(f"Error getting log events from stream {stream_name}: {e}")
    
    return flow_logs

def analyze_flow_logs(logs_client, bedrock_runtime, log_group: str, time_range: str, max_results: int) -> Dict[str, Any]:
    """Analyze VPC flow logs for network issues and security concerns."""
    try:
        # Calculate start time based on time range
        hours = int(time_range.replace('h', ''))
        start_time = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
        
        # Get recent flow logs
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            limit=max_results
        )
        
        log_events = response.get('events', [])
        if not log_events:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No flow logs found in the specified time range',
                    'logs': []
                })
            }
        
        # Parse flow logs
        flow_logs = parse_flow_logs(log_events)
        
        # Analyze logs using Bedrock
        analysis = analyze_with_bedrock(bedrock_runtime, flow_logs)
        
        # Process logs for specific issues
        issues = process_flow_logs(flow_logs)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'logs': flow_logs,
                'analysis': analysis,
                'issues': issues
            })
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_flow_logs: {str(e)}")
        raise

def parse_flow_logs(log_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse VPC flow log events into structured data."""
    flow_logs = []
    
    for event in log_events:
        try:
            # VPC flow logs are space-separated
            fields = event['message'].split()
            
            # Parse fields based on VPC flow log format
            flow_log = {
                'version': int(fields[0]),
                'account_id': fields[1],
                'interface_id': fields[2],
                'srcaddr': fields[3],
                'dstaddr': fields[4],
                'srcport': int(fields[5]),
                'dstport': int(fields[6]),
                'protocol': int(fields[7]),
                'packets': int(fields[8]),
                'bytes': int(fields[9]),
                'start': int(fields[10]),
                'end': int(fields[11]),
                'action': fields[12],
                'log_status': fields[13],
                'timestamp': event['timestamp']
            }
            
            flow_logs.append(flow_log)
            
        except Exception as e:
            logger.error(f"Error parsing flow log: {str(e)}")
            continue
    
    return flow_logs

def analyze_with_bedrock(bedrock_runtime, flow_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Use Bedrock to analyze patterns in VPC flow logs."""
    try:
        # Prepare logs for analysis
        logs_text = "\n".join([
            f"Source: {log['srcaddr']}:{log['srcport']} -> Destination: {log['dstaddr']}:{log['dstport']} | "
            f"Protocol: {log['protocol']} | Action: {log['action']} | Bytes: {log['bytes']}"
            for log in flow_logs[:20]  # Limit to 20 logs for prompt size
        ])
        
        # Prepare prompt for Claude
        prompt = f"""
        Analyze the following VPC flow logs for unusual patterns, potential security issues, or network problems:
        
        {logs_text}
        
        Please identify:
        1. Any unusual traffic patterns
        2. Potential security concerns
        3. Signs of network issues
        4. Recommendations for investigation
        
        Format your response as JSON with the following structure:
        {{
            "patterns_detected": [list of patterns],
            "security_concerns": [list of concerns],
            "network_issues": [list of issues],
            "recommendations": [list of recommendations]
        }}
        """
        
        # Call Claude via Bedrock
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'prompt': prompt,
                'max_tokens': 1000,
                'temperature': 0.7
            })
        )
        
        # Parse and return the analysis
        response_body = json.loads(response['body'].read())
        return json.loads(response_body['completion'])
        
    except Exception as e:
        logger.error(f"Error in analyze_with_bedrock: {str(e)}")
        return {
            'error': str(e),
            'patterns_detected': [],
            'security_concerns': [],
            'network_issues': [],
            'recommendations': ['Error analyzing flow logs with Bedrock']
        }

def process_flow_logs(flow_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process VPC flow logs for specific issues."""
    issues = []
    
    for log in flow_logs:
        try:
            # Check for rejected traffic
            if log['action'] == 'REJECT':
                issue = {
                    'id': f"{log['interface_id']}-{log['timestamp']}",
                    'timestamp': log['timestamp'],
                    'source': log['srcaddr'],
                    'destination': log['dstaddr'],
                    'protocol': log['protocol'],
                    'action': log['action'],
                    'severity': 'high',
                    'issue_type': 'rejected_traffic'
                }
                issues.append(issue)
            
            # Check for unusual port numbers
            elif log['dstport'] in [22, 23, 3389] and log['action'] == 'ACCEPT':
                issue = {
                    'id': f"{log['interface_id']}-{log['timestamp']}",
                    'timestamp': log['timestamp'],
                    'source': log['srcaddr'],
                    'destination': log['dstaddr'],
                    'protocol': log['protocol'],
                    'port': log['dstport'],
                    'severity': 'medium',
                    'issue_type': 'sensitive_port_access'
                }
                issues.append(issue)
            
            # Check for large data transfers
            elif log['bytes'] > 1000000:  # 1MB threshold
                issue = {
                    'id': f"{log['interface_id']}-{log['timestamp']}",
                    'timestamp': log['timestamp'],
                    'source': log['srcaddr'],
                    'destination': log['dstaddr'],
                    'protocol': log['protocol'],
                    'bytes': log['bytes'],
                    'severity': 'low',
                    'issue_type': 'large_data_transfer'
                }
                issues.append(issue)
                
        except Exception as e:
            logger.error(f"Error processing flow log: {str(e)}")
            continue
    
    return issues

def analyze_network_traffic(timeframe_hours: int = 24) -> Dict[str, Any]:
    """Analyze network traffic patterns."""
    try:
        # Get Flow Logs
        flow_logs = get_flow_logs(timeframe_hours)
        
        # Count traffic by source and destination
        src_counts = {}
        dst_counts = {}
        protocol_counts = {}
        
        for log in flow_logs:
            src_addr = log.get('src_addr', '')
            dst_addr = log.get('dst_addr', '')
            protocol = log.get('protocol', '')
            
            if src_addr:
                src_counts[src_addr] = src_counts.get(src_addr, 0) + 1
            
            if dst_addr:
                dst_counts[dst_addr] = dst_counts.get(dst_addr, 0) + 1
            
            if protocol:
                protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'src_counts': src_counts,
                'dst_counts': dst_counts,
                'protocol_counts': protocol_counts,
                'total_logs': len(flow_logs),
                'timeframe_hours': timeframe_hours
            })
        }
    except Exception as e:
        print(f"Error analyzing network traffic: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error analyzing network traffic: {str(e)}'})
        }

def investigate_security_groups() -> Dict[str, Any]:
    """Investigate security group configurations."""
    try:
        # Get security groups
        response = ec2.describe_security_groups()
        security_groups = response.get('SecurityGroups', [])
        
        # Analyze security groups
        issues = []
        
        for sg in security_groups:
            group_id = sg.get('GroupId', '')
            group_name = sg.get('GroupName', '')
            
            # Check for overly permissive inbound rules
            inbound_rules = sg.get('IpPermissions', [])
            for rule in inbound_rules:
                ip_protocol = rule.get('IpProtocol', '')
                from_port = rule.get('FromPort', 0)
                to_port = rule.get('ToPort', 0)
                
                # Check for open to world (0.0.0.0/0)
                for ip_range in rule.get('IpRanges', []):
                    cidr = ip_range.get('CidrIp', '')
                    if cidr == '0.0.0.0/0':
                        issue = {
                            'id': str(uuid.uuid4()),
                            'timestamp': datetime.utcnow().isoformat(),
                            'security_group_id': group_id,
                            'security_group_name': group_name,
                            'rule_type': 'inbound',
                            'protocol': ip_protocol,
                            'from_port': from_port,
                            'to_port': to_port,
                            'cidr': cidr,
                            'severity': 'high',
                            'issue_type': 'overly_permissive_rule',
                            'description': f'Security group {group_name} ({group_id}) has inbound rule open to world'
                        }
                        issues.append(issue)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'issues': issues,
                'count': len(issues),
                'security_groups_analyzed': len(security_groups)
            })
        }
    except Exception as e:
        print(f"Error investigating security groups: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error investigating security groups: {str(e)}'})
        } 
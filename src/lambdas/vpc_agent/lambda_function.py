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
flowlogs = boto3.client('logs')
bedrock_runtime = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    """
    Lambda handler for VPC agent.
    
    This function processes VPC flow logs and network traffic,
    focusing on rejected traffic, security group changes, and network ACL updates.
    """
    try:
        # Extract parameters from the event
        action = event.get('action', 'analyze_flow_logs')
        log_group = event.get('log_group', '/aws/vpc/flow-logs')
        time_range = event.get('time_range', '1h')
        max_results = event.get('max_results', 50)

        if action == 'analyze_flow_logs':
            return analyze_flow_logs(log_group, time_range, max_results)
        elif action == 'get_rejected_traffic':
            return get_rejected_traffic(log_group, time_range, max_results)
        elif action == 'get_security_group_changes':
            return get_security_group_changes()
        elif action == 'get_network_acl_changes':
            return get_network_acl_changes()
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

def analyze_flow_logs(log_group, time_range, max_results):
    """Analyze VPC flow logs for network issues."""
    try:
        # Calculate start time based on time range
        end_time = datetime.utcnow()
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            start_time = end_time - timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            start_time = end_time - timedelta(days=days)
        else:
            start_time = end_time - timedelta(hours=1)  # Default to 1 hour

        # Get flow logs
        flow_logs = get_flow_logs(log_group, start_time, end_time, max_results)
        
        # Process flow logs for analysis
        processed_logs = process_flow_logs(flow_logs)
        
        # Analyze logs using Bedrock
        analysis = analyze_with_bedrock(processed_logs)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'flow_logs': processed_logs,
                'analysis': analysis,
                'issues': identify_network_issues(processed_logs)
            })
        }

    except Exception as e:
        logger.error(f"Error in analyze_flow_logs: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_flow_logs(log_group, start_time, end_time, max_results):
    """Retrieve VPC flow logs from CloudWatch Logs."""
    try:
        # Get log streams
        log_streams = flowlogs.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=max_results
        )

        # Get log events
        flow_logs = []
        for stream in log_streams['logStreams']:
            events = flowlogs.get_log_events(
                logGroupName=log_group,
                logStreamName=stream['logStreamName'],
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                limit=max_results
            )
            flow_logs.extend(events['events'])

        return flow_logs

    except Exception as e:
        logger.error(f"Error in get_flow_logs: {str(e)}")
        return []

def process_flow_logs(flow_logs):
    """Process VPC flow logs for analysis."""
    processed_logs = []
    
    for log in flow_logs:
        try:
            # Parse the log message
            log_data = json.loads(log['message'])
            processed_log = {
                'timestamp': log['timestamp'],
                'version': log_data.get('version'),
                'account-id': log_data.get('account-id'),
                'interface-id': log_data.get('interface-id'),
                'srcaddr': log_data.get('srcaddr'),
                'dstaddr': log_data.get('dstaddr'),
                'srcport': log_data.get('srcport'),
                'dstport': log_data.get('dstport'),
                'protocol': log_data.get('protocol'),
                'packets': log_data.get('packets'),
                'bytes': log_data.get('bytes'),
                'start': log_data.get('start'),
                'end': log_data.get('end'),
                'action': log_data.get('action'),
                'log-status': log_data.get('log-status')
            }
            processed_logs.append(processed_log)
        except Exception as e:
            logger.error(f"Error processing log entry: {str(e)}")
            continue
    
    return processed_logs

def analyze_with_bedrock(flow_logs):
    """Analyze flow logs using Bedrock."""
    try:
        # Prepare the prompt for Bedrock
        prompt = {
            "prompt": f"""Analyze the following VPC flow logs for network issues:
            {json.dumps(flow_logs, indent=2)}
            
            Please provide:
            1. A summary of the network traffic patterns
            2. Any security concerns
            3. Performance issues
            4. Recommendations for improvement
            """,
            "max_tokens": 1000,
            "temperature": 0.7
        }

        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-v2',
            body=json.dumps(prompt)
        )

        # Parse and return the analysis
        analysis = json.loads(response['body'].read())
        return analysis

    except Exception as e:
        logger.error(f"Error in analyze_with_bedrock: {str(e)}")
        return {"error": str(e)}

def identify_network_issues(flow_logs):
    """Identify specific network issues in the flow logs."""
    issues = []
    
    for log in flow_logs:
        # Check for rejected traffic
        if log.get('action') == 'REJECT':
            issues.append({
                'type': 'rejected_traffic',
                'severity': 'high',
                'details': {
                    'srcaddr': log['srcaddr'],
                    'dstaddr': log['dstaddr'],
                    'protocol': log['protocol'],
                    'srcport': log['srcport'],
                    'dstport': log['dstport']
                }
            })
        
        # Check for unusual traffic patterns
        if int(log.get('bytes', 0)) > 1000000:  # More than 1MB
            issues.append({
                'type': 'large_traffic',
                'severity': 'medium',
                'details': {
                    'srcaddr': log['srcaddr'],
                    'dstaddr': log['dstaddr'],
                    'bytes': log['bytes'],
                    'protocol': log['protocol']
                }
            })
    
    return issues

def get_rejected_traffic(log_group, time_range, max_results):
    """Get rejected traffic from VPC flow logs."""
    try:
        # Calculate start time based on time range
        end_time = datetime.utcnow()
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            start_time = end_time - timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            start_time = end_time - timedelta(days=days)
        else:
            start_time = end_time - timedelta(hours=1)  # Default to 1 hour

        # Get flow logs
        flow_logs = get_flow_logs(log_group, start_time, end_time, max_results)
        
        # Filter for rejected traffic
        rejected_traffic = [
            log for log in flow_logs
            if json.loads(log['message']).get('action') == 'REJECT'
        ]
        
        # Process rejected traffic
        processed_rejections = process_flow_logs(rejected_traffic)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'rejected_traffic': processed_rejections,
                'analysis': analyze_with_bedrock(processed_rejections)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_rejected_traffic: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_security_group_changes():
    """Get security group changes from CloudTrail events."""
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
                        issues.append({
                            'type': 'overly_permissive_rule',
                            'severity': 'high',
                            'details': {
                                'security_group_id': group_id,
                                'security_group_name': group_name,
                                'rule_type': 'inbound',
                                'protocol': ip_protocol,
                                'from_port': from_port,
                                'to_port': to_port,
                                'cidr': cidr
                            }
                        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'security_group_issues': issues,
                'analysis': analyze_with_bedrock(issues)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_security_group_changes: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_network_acl_changes():
    """Get network ACL changes from CloudTrail events."""
    try:
        # Get network ACLs
        response = ec2.describe_network_acls()
        network_acls = response.get('NetworkAcls', [])
        
        # Analyze network ACLs
        issues = []
        
        for acl in network_acls:
            acl_id = acl.get('NetworkAclId', '')
            vpc_id = acl.get('VpcId', '')
            
            # Check for overly permissive rules
            entries = acl.get('Entries', [])
            for entry in entries:
                rule_number = entry.get('RuleNumber', 0)
                protocol = entry.get('Protocol', '')
                rule_action = entry.get('RuleAction', '')
                cidr_block = entry.get('CidrBlock', '')
                egress = entry.get('Egress', False)
                
                # Check for open to world (0.0.0.0/0)
                if cidr_block == '0.0.0.0/0' and rule_action == 'allow':
                    issues.append({
                        'type': 'overly_permissive_acl',
                        'severity': 'high',
                        'details': {
                            'network_acl_id': acl_id,
                            'vpc_id': vpc_id,
                            'rule_number': rule_number,
                            'protocol': protocol,
                            'rule_action': rule_action,
                            'cidr_block': cidr_block,
                            'egress': egress
                        }
                    })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'network_acl_issues': issues,
                'analysis': analyze_with_bedrock(issues)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_network_acl_changes: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def parse_flow_log(message: str) -> Dict[str, str]:
    """Parse VPC Flow Log entry."""
    try:
        # Flow log format: version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status
        fields = message.split()
        if len(fields) >= 13:
            return {
                'version': fields[0],
                'account-id': fields[1],
                'interface-id': fields[2],
                'srcaddr': fields[3],
                'dstaddr': fields[4],
                'srcport': fields[5],
                'dstport': fields[6],
                'protocol': fields[7],
                'packets': fields[8],
                'bytes': fields[9],
                'start': fields[10],
                'end': fields[11],
                'action': fields[12],
                'log-status': fields[13] if len(fields) > 13 else ''
            }
    except Exception as e:
        print(f"Error parsing flow log: {e}")
    return {}

def determine_rejection_severity(log_entry: Dict[str, str]) -> str:
    """Determine the severity of rejected traffic."""
    # High severity rejections
    if log_entry.get('protocol') == '6':  # TCP
        if log_entry.get('dstport') in ['22', '23', '3389', '5900']:  # SSH, Telnet, RDP, VNC
            return 'high'
    
    # Medium severity rejections
    if log_entry.get('protocol') in ['6', '17']:  # TCP or UDP
        if log_entry.get('dstport') in ['80', '443', '3306', '5432', '6379']:  # HTTP, HTTPS, MySQL, PostgreSQL, Redis
            return 'medium'
    
    return 'low'

def determine_security_group_severity(group: Dict[str, Any]) -> str:
    """Determine the severity of security group changes."""
    # High severity security groups
    if group.get('GroupName', '').lower() in ['default', 'admin', 'root']:
        return 'high'
    
    # Medium severity security groups
    if any(port in str(group) for port in ['22', '23', '3389', '5900']):
        return 'medium'
    
    return 'low'

def determine_network_acl_severity(entry: Dict[str, Any]) -> str:
    """Determine the severity of network ACL changes."""
    # High severity ACL entries
    if entry.get('RuleAction') == 'allow':
        if entry.get('Protocol') == '-1' or entry.get('CidrBlock') == '0.0.0.0/0':
            return 'high'
    
    # Medium severity ACL entries
    if entry.get('RuleAction') == 'allow':
        if entry.get('Protocol') in ['6', '17']:  # TCP or UDP
            return 'medium'
    
    return 'low' 
import json
import logging
import boto3
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def prioritize_incident(incident_data):
    """Determine incident priority based on impact and urgency."""
    try:
        impact = incident_data.get('impact', 'low').lower()
        urgency = incident_data.get('urgency', 'low').lower()
        
        # Priority matrix
        priority_matrix = {
            ('high', 'high'): 'P1',
            ('high', 'medium'): 'P2',
            ('medium', 'high'): 'P2',
            ('high', 'low'): 'P3',
            ('medium', 'medium'): 'P3',
            ('low', 'high'): 'P3',
            ('medium', 'low'): 'P4',
            ('low', 'medium'): 'P4',
            ('low', 'low'): 'P5'
        }
        
        return priority_matrix.get((impact, urgency), 'P3')
    except Exception as e:
        logger.error(f"Error determining priority: {e}")
        raise

def analyze_findings(analysis_results):
    """Analyze findings from different agents."""
    try:
        consolidated_findings = {
            'log_findings': [],
            'metric_findings': [],
            'critical_issues': [],
            'recommendations': []
        }
        
        for result in analysis_results:
            source = result.get('source', 'unknown')
            findings = result.get('findings', [])
            
            # Process findings based on source
            if source == 'log_analysis':
                consolidated_findings['log_findings'].extend(findings)
                # Extract critical issues from logs
                for finding in findings:
                    if finding.get('severity') == 'high':
                        consolidated_findings['critical_issues'].append({
                            'type': 'log_issue',
                            'description': finding.get('description'),
                            'timestamp': finding.get('timestamp')
                        })
                        
            elif source == 'metrics_analysis':
                consolidated_findings['metric_findings'].extend(findings)
                # Extract critical issues from metrics
                for finding in findings:
                    if finding.get('type') == 'threshold_breach':
                        consolidated_findings['critical_issues'].append({
                            'type': 'metric_breach',
                            'description': f"Metric threshold breach: {finding.get('value')} > {finding.get('threshold')}",
                            'timestamp': finding.get('timestamp')
                        })
        
        return consolidated_findings
    except Exception as e:
        logger.error(f"Error analyzing findings: {e}")
        raise

def generate_action_items(incident_data, findings):
    """Generate action items based on incident data and findings."""
    try:
        action_items = []
        
        # Add immediate actions based on critical issues
        for issue in findings.get('critical_issues', []):
            action_items.append({
                'priority': 'high',
                'action': f"Investigate and resolve {issue['type']}: {issue['description']}",
                'assigned_to': 'on-call engineer',
                'status': 'pending'
            })
            
        # Add actions based on log findings
        for finding in findings.get('log_findings', []):
            action_items.append({
                'priority': finding.get('severity', 'medium'),
                'action': f"Review and address log finding: {finding.get('description')}",
                'assigned_to': 'sre team',
                'status': 'pending'
            })
            
        # Add actions based on metric findings
        for finding in findings.get('metric_findings', []):
            action_items.append({
                'priority': 'medium',
                'action': f"Analyze metric anomaly: {finding.get('description')}",
                'assigned_to': 'sre team',
                'status': 'pending'
            })
            
        return action_items
    except Exception as e:
        logger.error(f"Error generating action items: {e}")
        raise

def generate_recommendations(findings):
    """Generate recommendations based on analysis findings."""
    try:
        recommendations = []
        
        # Add recommendations based on log patterns
        if findings.get('log_findings'):
            recommendations.append({
                'type': 'monitoring',
                'description': 'Review and update log alerting thresholds',
                'rationale': 'Multiple log-based issues detected'
            })
            
        # Add recommendations based on metric patterns
        if findings.get('metric_findings'):
            recommendations.append({
                'type': 'performance',
                'description': 'Review system capacity and scaling policies',
                'rationale': 'Metric anomalies detected'
            })
            
        # Add general recommendations
        if findings.get('critical_issues'):
            recommendations.append({
                'type': 'process',
                'description': 'Schedule post-mortem review',
                'rationale': 'Critical issues identified during incident'
            })
            
        return recommendations
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise

def coordinate_response(incident_data, analysis_results):
    """Coordinate incident response based on analysis results."""
    try:
        # Determine incident priority
        priority = prioritize_incident(incident_data)
        
        # Analyze findings from all sources
        consolidated_findings = analyze_findings(analysis_results)
        
        # Generate action items
        action_items = generate_action_items(incident_data, consolidated_findings)
        
        # Generate recommendations
        recommendations = generate_recommendations(consolidated_findings)
        
        return {
            'incident_priority': priority,
            'findings': consolidated_findings,
            'action_items': action_items,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error coordinating response: {e}")
        raise

def lambda_handler(event, context):
    """Lambda function handler."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract parameters from the event
        body = json.loads(event.get('body', '{}'))
        incident_data = body.get('incident_data')
        analysis_results = body.get('analysis_results', [])
        
        if not incident_data:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameter: incident_data'
                })
            }
            
        # Coordinate response
        response_plan = coordinate_response(incident_data, analysis_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_plan)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 
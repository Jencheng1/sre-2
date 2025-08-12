import json
import logging
import boto3
import requests
from datetime import datetime, timedelta
import time
import sys
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients with region
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
logs_client = boto3.client('logs', region_name='us-east-1')
ssm_client = boto3.client('ssm', region_name='us-east-1')

# Defect management endpoints
DEFECT_MANAGEMENT_ENDPOINTS = {
    "alm_octane": "http://localhost:9085",
    "jira": "http://localhost:9086"
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
    elif 'timeout' in desc_lower or 'connection' in desc_lower or 'api' in desc_lower:
        return 'defect_related'
    else:
        return 'general'

def correlate_with_defects(incident_description, incident_type, metrics_data):
    """Correlate incident with existing defects in ALM Octane and Jira"""
    correlation_results = {
        "alm_octane_defects": [],
        "jira_issues": [],
        "correlation_score": 0.0,
        "recommended_actions": [],
        "defect_evidence": []
    }
    
    try:
        # Query ALM Octane for related defects
        octane_defects = query_octane_defects(incident_description, incident_type)
        correlation_results["alm_octane_defects"] = octane_defects
        
        # Query Jira for related issues
        jira_issues = query_jira_issues(incident_description, incident_type)
        correlation_results["jira_issues"] = jira_issues
        
        # Calculate overall correlation score
        correlation_results["correlation_score"] = calculate_correlation_score(
            octane_defects, jira_issues, metrics_data
        )
        
        # Generate recommendations based on correlations
        correlation_results["recommended_actions"] = generate_defect_recommendations(
            octane_defects, jira_issues, incident_type
        )
        
        # Generate evidence for correlation
        correlation_results["defect_evidence"] = generate_defect_evidence(
            octane_defects, jira_issues, incident_description
        )
        
    except Exception as e:
        logger.error(f"Error correlating with defects: {str(e)}")
        correlation_results["error"] = str(e)
    
    return correlation_results

def query_octane_defects(incident_description, incident_type):
    """Query ALM Octane for defects related to the incident"""
    try:
        # Search for defects with similar keywords
        params = {
            "status": "all",
            "limit": 10
        }
        
        response = requests.get(
            f"{DEFECT_MANAGEMENT_ENDPOINTS['alm_octane']}/octane/defects",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            all_defects = response.json()
            
            # Filter defects based on incident description and type
            related_defects = []
            keywords = extract_keywords(incident_description)
            
            for defect in all_defects:
                relevance_score = calculate_defect_relevance(defect, keywords, incident_type)
                if relevance_score > 0.3:  # Minimum relevance threshold
                    defect["relevance_score"] = relevance_score
                    related_defects.append(defect)
            
            # Sort by relevance score
            related_defects.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            return related_defects[:5]  # Return top 5 most relevant
        
    except Exception as e:
        logger.error(f"Error querying ALM Octane: {str(e)}")
    
    return []

def query_jira_issues(incident_description, incident_type):
    """Query Jira for issues related to the incident"""
    try:
        # Search for bug-type issues
        params = {
            "issue_type": "Bug",
            "status": "all",
            "limit": 10
        }
        
        response = requests.get(
            f"{DEFECT_MANAGEMENT_ENDPOINTS['jira']}/jira/issues",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            all_issues = response.json()
            
            # Filter issues based on incident description and type
            related_issues = []
            keywords = extract_keywords(incident_description)
            
            for issue in all_issues:
                relevance_score = calculate_issue_relevance(issue, keywords, incident_type)
                if relevance_score > 0.3:  # Minimum relevance threshold
                    issue["relevance_score"] = relevance_score
                    related_issues.append(issue)
            
            # Sort by relevance score
            related_issues.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            return related_issues[:5]  # Return top 5 most relevant
        
    except Exception as e:
        logger.error(f"Error querying Jira: {str(e)}")
    
    return []

def extract_keywords(text):
    """Extract keywords from incident description"""
    # Common technical keywords that are important for correlation
    important_keywords = [
        'api', 'database', 'connection', 'timeout', 'authentication', 'ssl',
        'memory', 'cpu', 'performance', 'latency', 'error', 'failure',
        'gateway', 'service', 'cache', 'session', 'payment', 'search',
        'upload', 'file', 'security', 'certificate', 'pool', 'leak'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in important_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords

def calculate_defect_relevance(defect, keywords, incident_type):
    """Calculate how relevant a defect is to the incident"""
    relevance_score = 0.0
    
    # Check name/title relevance
    defect_name = defect.get("name", "").lower()
    for keyword in keywords:
        if keyword in defect_name:
            relevance_score += 0.3
    
    # Check description relevance
    defect_desc = defect.get("description", "").lower()
    for keyword in keywords:
        if keyword in defect_desc:
            relevance_score += 0.2
    
    # Check component relevance
    component = defect.get("component", "").lower()
    for keyword in keywords:
        if keyword in component:
            relevance_score += 0.25
    
    # Severity bonus
    severity = defect.get("severity", "").lower()
    if severity in ["critical", "high"]:
        relevance_score += 0.2
    
    # Status relevance (open defects are more relevant)
    status = defect.get("status", "").lower()
    if status in ["new", "in progress"]:
        relevance_score += 0.15
    
    # Environment match
    environment = defect.get("environment", "").lower()
    if "production" in environment:
        relevance_score += 0.1
    
    return min(relevance_score, 1.0)  # Cap at 1.0

def calculate_issue_relevance(issue, keywords, incident_type):
    """Calculate how relevant a Jira issue is to the incident"""
    relevance_score = 0.0
    
    # Check summary relevance
    summary = issue.get("summary", "").lower()
    for keyword in keywords:
        if keyword in summary:
            relevance_score += 0.3
    
    # Check description relevance
    description = issue.get("description", "").lower()
    for keyword in keywords:
        if keyword in description:
            relevance_score += 0.2
    
    # Priority bonus
    priority = issue.get("priority", {}).get("name", "").lower()
    if priority in ["blocker", "critical", "high"]:
        relevance_score += 0.2
    
    # Status relevance (open issues are more relevant)
    status = issue.get("status", {}).get("name", "").lower()
    if status in ["open", "in progress", "reopened"]:
        relevance_score += 0.15
    
    # Issue type match (bugs are most relevant for incidents)
    issue_type = issue.get("issuetype", {}).get("name", "").lower()
    if issue_type == "bug":
        relevance_score += 0.15
    
    return min(relevance_score, 1.0)  # Cap at 1.0

def calculate_correlation_score(octane_defects, jira_issues, metrics_data):
    """Calculate overall correlation score between incident and defects"""
    correlation_score = 0.0
    
    # ALM Octane defects contribution
    if octane_defects:
        avg_octane_relevance = sum(d.get("relevance_score", 0) for d in octane_defects) / len(octane_defects)
        correlation_score += avg_octane_relevance * 0.5
    
    # Jira issues contribution
    if jira_issues:
        avg_jira_relevance = sum(i.get("relevance_score", 0) for i in jira_issues) / len(jira_issues)
        correlation_score += avg_jira_relevance * 0.5
    
    # Metrics severity bonus
    if metrics_data:
        error_rate = metrics_data.get("ErrorRate", 0)
        response_time = metrics_data.get("ResponseTime", 0)
        
        if error_rate > 50:
            correlation_score += 0.1
        if response_time > 5000:
            correlation_score += 0.1
    
    return min(correlation_score, 1.0)

def generate_defect_recommendations(octane_defects, jira_issues, incident_type):
    """Generate recommendations based on correlated defects"""
    recommendations = []
    
    # ALM Octane-based recommendations
    for defect in octane_defects[:3]:  # Top 3 defects
        if defect.get("status", "").lower() in ["new", "in progress"]:
            recommendations.append(f"🔧 Review and prioritize ALM Octane defect {defect.get('id')}: {defect.get('name')}")
        
        if defect.get("severity") == "Critical":
            recommendations.append(f"🚨 Critical defect found - expedite fix for {defect.get('id')}")
    
    # Jira-based recommendations
    for issue in jira_issues[:3]:  # Top 3 issues
        if issue.get("status", {}).get("name", "").lower() in ["open", "in progress"]:
            recommendations.append(f"🎫 Review Jira issue {issue.get('key')}: {issue.get('summary')}")
        
        if issue.get("priority", {}).get("name", "") in ["Blocker", "Critical"]:
            recommendations.append(f"⚠️ High priority issue - review {issue.get('key')} for incident correlation")
    
    # General defect management recommendations
    if octane_defects or jira_issues:
        recommendations.append("📊 Update defect tracking with incident details")
        recommendations.append("🔍 Investigate if this is a regression of previously fixed defects")
        recommendations.append("🏗️ Consider implementing additional monitoring for this component")
    
    return recommendations

def generate_defect_evidence(octane_defects, jira_issues, incident_description):
    """Generate evidence supporting defect correlation"""
    evidence = []
    
    # Evidence from ALM Octane defects
    for defect in octane_defects[:2]:
        evidence.append(f"ALM Octane defect {defect.get('id')} shows similar symptoms in {defect.get('component')}")
        if defect.get("relevance_score", 0) > 0.7:
            evidence.append(f"High correlation (score: {defect.get('relevance_score', 0):.2f}) with defect {defect.get('id')}")
    
    # Evidence from Jira issues
    for issue in jira_issues[:2]:
        evidence.append(f"Jira issue {issue.get('key')} in {issue.get('project', {}).get('key')} project shows similar patterns")
        if issue.get("relevance_score", 0) > 0.7:
            evidence.append(f"Strong correlation (score: {issue.get('relevance_score', 0):.2f}) with issue {issue.get('key')}")
    
    # Pattern-based evidence
    keywords = extract_keywords(incident_description)
    if "timeout" in keywords and "connection" in keywords:
        evidence.append("Incident shows connection timeout pattern commonly associated with database defects")
    
    if "authentication" in keywords:
        evidence.append("Authentication-related incident suggests session management or security defects")
    
    if "memory" in keywords or "performance" in keywords:
        evidence.append("Performance degradation indicates potential memory leak or optimization defects")
    
    return evidence

def create_defect_from_incident(incident_data, analysis_results):
    """Create a new defect in ALM Octane based on incident analysis"""
    try:
        # Determine if we should create a defect
        correlation_score = analysis_results.get("defect_correlation", {}).get("correlation_score", 0)
        
        if correlation_score < 0.5:  # Only create defect if no strong existing correlation
            defect_data = {
                "name": f"Incident-derived defect: {incident_data.get('title', 'Unknown incident')}",
                "description": f"Defect created from incident analysis.\n\nIncident Details:\n{incident_data.get('description', '')}\n\nRoot Cause Analysis:\n{analysis_results.get('root_cause_analysis', 'Analysis pending')}",
                "severity": map_incident_severity_to_defect(incident_data.get('severity', 'Medium')),
                "priority": map_incident_severity_to_defect(incident_data.get('severity', 'Medium')),
                "project": "SRE Project",
                "component": determine_component_from_incident(incident_data),
                "environment": "Production",
                "created_by": "SRE Copilot",
                "steps_to_reproduce": extract_steps_from_incident(incident_data),
                "expected_result": "System should operate normally without incidents",
                "actual_result": incident_data.get('description', '')
            }
            
            response = requests.post(
                f"{DEFECT_MANAGEMENT_ENDPOINTS['alm_octane']}/octane/defects",
                json=defect_data,
                timeout=10
            )
            
            if response.status_code == 201:
                created_defect = response.json()
                logger.info(f"Created ALM Octane defect: {created_defect.get('id')}")
                return created_defect
        
    except Exception as e:
        logger.error(f"Error creating defect from incident: {str(e)}")
    
    return None

def create_jira_issue_from_incident(incident_data, analysis_results):
    """Create a new Jira issue based on incident analysis"""
    try:
        # Determine if we should create an issue
        correlation_score = analysis_results.get("defect_correlation", {}).get("correlation_score", 0)
        
        if correlation_score < 0.5:  # Only create issue if no strong existing correlation
            issue_data = {
                "project": "SREPROJ",
                "summary": f"Incident: {incident_data.get('title', 'System incident')}",
                "description": f"Issue created from SRE incident analysis.\n\n*Incident Details:*\n{incident_data.get('description', '')}\n\n*Analysis Results:*\n{analysis_results.get('root_cause_analysis', 'Analysis in progress')}\n\n*Recommended Actions:*\n" + "\n".join(analysis_results.get("defect_correlation", {}).get("recommended_actions", [])),
                "issue_type": "Bug",
                "priority": map_incident_severity_to_jira_priority(incident_data.get('severity', 'Medium')),
                "assignee": "SRE Team",
                "reporter": "SRE Copilot",
                "labels": ["incident-derived", "sre", "root-cause-analysis"]
            }
            
            response = requests.post(
                f"{DEFECT_MANAGEMENT_ENDPOINTS['jira']}/jira/issues",
                json=issue_data,
                timeout=10
            )
            
            if response.status_code == 201:
                created_issue = response.json()
                logger.info(f"Created Jira issue: {created_issue.get('key')}")
                return created_issue
        
    except Exception as e:
        logger.error(f"Error creating Jira issue from incident: {str(e)}")
    
    return None

def map_incident_severity_to_defect(incident_severity):
    """Map incident severity to defect severity"""
    mapping = {
        "Critical": "Critical",
        "High": "High", 
        "Medium": "Medium",
        "Low": "Low"
    }
    return mapping.get(incident_severity, "Medium")

def map_incident_severity_to_jira_priority(incident_severity):
    """Map incident severity to Jira priority"""
    mapping = {
        "Critical": "Blocker",
        "High": "Critical",
        "Medium": "High",
        "Low": "Medium"
    }
    return mapping.get(incident_severity, "High")

def determine_component_from_incident(incident_data):
    """Determine the most likely component based on incident data"""
    description = incident_data.get('description', '').lower()
    
    if 'api' in description or 'gateway' in description:
        return 'API Gateway'
    elif 'database' in description or 'connection' in description:
        return 'Database'
    elif 'auth' in description or 'login' in description:
        return 'Authentication'
    elif 'payment' in description or 'billing' in description:
        return 'Payment System'
    elif 'search' in description or 'index' in description:
        return 'Search Service'
    elif 'file' in description or 'upload' in description:
        return 'File Management'
    else:
        return 'General'

def extract_steps_from_incident(incident_data):
    """Extract reproduction steps from incident data"""
    description = incident_data.get('description', '')
    
    # Simple extraction - in practice, this would be more sophisticated
    steps = [
        "1. Monitor system under normal load",
        f"2. Observe conditions similar to: {description[:100]}...",
        "3. Check for error patterns and system metrics",
        "4. Reproduce issue if possible"
    ]
    
    return "\n".join(steps)

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
                Statistics=['Average', 'Maximum']
            )
            
            if response['Datapoints']:
                latest_point = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                metrics_data[metric_name] = {
                    'Average': latest_point.get('Average', 0),
                    'Maximum': latest_point.get('Maximum', 0),
                    'Timestamp': latest_point['Timestamp'].isoformat()
                }
            else:
                metrics_data[metric_name] = {'Average': 0, 'Maximum': 0}
                
        except Exception as e:
            logger.error(f"Error getting metric {metric_name}: {str(e)}")
            metrics_data[metric_name] = {'Average': 0, 'Maximum': 0}
    
    return metrics_data

def lambda_handler(event, context):
    """Enhanced Lambda handler with defect correlation"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract incident information
        incident_data = event.get('incident', {})
        incident_title = incident_data.get('title', 'Unknown Incident')
        incident_description = incident_data.get('description', '')
        incident_severity = incident_data.get('severity', 'Medium')
        
        logger.info(f"Processing incident: {incident_title}")
        
        # Determine incident type
        incident_type = analyze_incident_type(incident_description)
        logger.info(f"Incident type determined: {incident_type}")
        
        # Get system metrics
        metrics_data = get_demo_metrics()
        logger.info(f"Retrieved metrics data")
        
        # NEW: Correlate with defects
        defect_correlation = correlate_with_defects(
            incident_description, incident_type, metrics_data
        )
        logger.info(f"Defect correlation completed with score: {defect_correlation.get('correlation_score', 0)}")
        
        # Generate AI-powered root cause analysis with defect context
        root_cause_prompt = f"""
        You are an expert SRE analyzing a system incident with potential defect correlation.
        
        Incident Details:
        - Title: {incident_title}
        - Description: {incident_description}
        - Severity: {incident_severity}
        - Type: {incident_type}
        
        System Metrics:
        {json.dumps(metrics_data, indent=2)}
        
        Defect Correlation Analysis:
        - Correlation Score: {defect_correlation.get('correlation_score', 0):.2f}
        - Related ALM Octane Defects: {len(defect_correlation.get('alm_octane_defects', []))}
        - Related Jira Issues: {len(defect_correlation.get('jira_issues', []))}
        
        Evidence from Defect Analysis:
        {json.dumps(defect_correlation.get('defect_evidence', []), indent=2)}
        
        Please provide:
        1. Root cause analysis considering both system metrics and defect correlation
        2. Likelihood this incident is caused by an existing defect (0-100%)
        3. Specific recommendations that account for related defects
        4. Prevention strategies that include defect management improvements
        
        Be specific and actionable in your analysis.
        """
        
        # Call Bedrock for AI analysis
        bedrock_response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1500,
                'messages': [
                    {
                        'role': 'user',
                        'content': root_cause_prompt
                    }
                ]
            })
        )
        
        ai_analysis = json.loads(bedrock_response['body'].read())
        root_cause_analysis = ai_analysis['content'][0]['text']
        
        # Create defects/issues if correlation is low (indicating new issue)
        created_defect = None
        created_issue = None
        
        if defect_correlation.get('correlation_score', 0) < 0.5:
            # Low correlation - might be a new defect
            created_defect = create_defect_from_incident(incident_data, {
                'root_cause_analysis': root_cause_analysis,
                'defect_correlation': defect_correlation
            })
            
            created_issue = create_jira_issue_from_incident(incident_data, {
                'root_cause_analysis': root_cause_analysis,
                'defect_correlation': defect_correlation
            })
        
        # Compile comprehensive response
        response = {
            'incident_analysis': {
                'title': incident_title,
                'type': incident_type,
                'severity': incident_severity,
                'timestamp': datetime.utcnow().isoformat()
            },
            'metrics': metrics_data,
            'defect_correlation': defect_correlation,
            'root_cause_analysis': root_cause_analysis,
            'created_artifacts': {
                'alm_octane_defect': created_defect,
                'jira_issue': created_issue
            },
            'recommendations': defect_correlation.get('recommended_actions', []),
            'correlation_summary': {
                'defect_likelihood': defect_correlation.get('correlation_score', 0) * 100,
                'total_related_defects': len(defect_correlation.get('alm_octane_defects', [])),
                'total_related_issues': len(defect_correlation.get('jira_issues', [])),
                'evidence_points': len(defect_correlation.get('defect_evidence', []))
            }
        }
        
        logger.info("Enhanced incident analysis with defect correlation completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps(response, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process incident with defect correlation'
            })
        }
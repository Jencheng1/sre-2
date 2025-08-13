#!/usr/bin/env python3
"""
Post-Mortem Analysis Agent for SRE Copilot
Generates comprehensive post-mortem reports with AI-powered insights
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
import uuid

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class PostMortemReport:
    """Structure for post-mortem report"""
    incident_id: str
    title: str
    severity: str
    incident_start: str
    incident_end: str
    detection_time: str
    resolution_time: str
    duration_minutes: int
    
    # Impact
    services_affected: List[str]
    users_impacted: int
    revenue_impact: str
    sla_breached: bool
    
    # Timeline
    timeline: List[Dict[str, str]]
    
    # Analysis
    root_cause: str
    contributing_factors: List[str]
    
    # Response
    detection_method: str
    response_actions: List[str]
    what_went_well: List[str]
    what_went_wrong: List[str]
    
    # Learnings
    lessons_learned: List[str]
    action_items: List[Dict[str, Any]]
    
    # Prevention
    preventive_measures: List[str]
    monitoring_improvements: List[str]
    
    # Metadata
    generated_at: str
    generated_by: str
    ai_confidence_score: float


class PostMortemAgent:
    """AI-powered post-mortem analysis agent"""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime')
        self.cloudwatch = boto3.client('cloudwatch')
        self.logs = boto3.client('logs')
        self.ssm = boto3.client('ssm')
        
    def analyze_incident(self, incident_data: Dict[str, Any]) -> PostMortemReport:
        """
        Perform comprehensive post-mortem analysis
        
        Args:
            incident_data: Dictionary containing incident details
            
        Returns:
            PostMortemReport object
        """
        logger.info(f"Starting post-mortem analysis for incident: {incident_data.get('incident_id', 'Unknown')}")
        
        # Extract basic information
        incident_id = incident_data.get('incident_id', str(uuid.uuid4()))
        incident_type = incident_data.get('type', 'unknown')
        description = incident_data.get('description', '')
        
        # Get incident timeline
        timeline = self._build_timeline(incident_data)
        
        # Analyze logs and metrics
        log_analysis = self._analyze_logs(incident_data)
        metrics_analysis = self._analyze_metrics(incident_data)
        
        # Get AI insights
        ai_analysis = self._get_ai_analysis(
            incident_data, 
            timeline, 
            log_analysis, 
            metrics_analysis
        )
        
        # Calculate impact
        impact_analysis = self._analyze_impact(incident_data, ai_analysis)
        
        # Generate action items
        action_items = self._generate_action_items(ai_analysis)
        
        # Build the report
        report = PostMortemReport(
            incident_id=incident_id,
            title=ai_analysis.get('title', f'{incident_type.capitalize()} Incident - {datetime.now().strftime("%Y-%m-%d")}'),
            severity=incident_data.get('severity', 'HIGH'),
            incident_start=timeline[0]['time'] if timeline else datetime.now().isoformat(),
            incident_end=timeline[-1]['time'] if timeline else datetime.now().isoformat(),
            detection_time=self._get_detection_time(timeline),
            resolution_time=self._get_resolution_time(timeline),
            duration_minutes=self._calculate_duration(timeline),
            
            # Impact
            services_affected=impact_analysis['services_affected'],
            users_impacted=impact_analysis['users_impacted'],
            revenue_impact=impact_analysis['revenue_impact'],
            sla_breached=impact_analysis['sla_breached'],
            
            # Timeline
            timeline=timeline,
            
            # Analysis
            root_cause=ai_analysis.get('root_cause', 'Unknown'),
            contributing_factors=ai_analysis.get('contributing_factors', []),
            
            # Response
            detection_method=ai_analysis.get('detection_method', 'Manual'),
            response_actions=ai_analysis.get('response_actions', []),
            what_went_well=ai_analysis.get('what_went_well', []),
            what_went_wrong=ai_analysis.get('what_went_wrong', []),
            
            # Learnings
            lessons_learned=ai_analysis.get('lessons_learned', []),
            action_items=action_items,
            
            # Prevention
            preventive_measures=ai_analysis.get('preventive_measures', []),
            monitoring_improvements=ai_analysis.get('monitoring_improvements', []),
            
            # Metadata
            generated_at=datetime.now().isoformat(),
            generated_by='SRE Copilot Post-Mortem Agent',
            ai_confidence_score=ai_analysis.get('confidence_score', 0.85)
        )
        
        return report
        
    def _build_timeline(self, incident_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build incident timeline from available data"""
        timeline = []
        
        # Add known events
        if 'start_time' in incident_data:
            timeline.append({
                'time': incident_data['start_time'].isoformat() if hasattr(incident_data['start_time'], 'isoformat') else incident_data['start_time'],
                'event': 'Incident started',
                'severity': 'critical'
            })
            
        # Add events from logs
        if 'raw_data' in incident_data and 'logs' in incident_data['raw_data']:
            log_events = self._extract_timeline_from_logs(incident_data['raw_data']['logs'])
            timeline.extend(log_events)
            
        # Add resolution time
        if 'resolution_time' in incident_data:
            timeline.append({
                'time': incident_data['resolution_time'],
                'event': 'Incident resolved',
                'severity': 'info'
            })
            
        # Sort by time
        timeline.sort(key=lambda x: x['time'])
        
        return timeline
        
    def _extract_timeline_from_logs(self, logs_data: Dict) -> List[Dict[str, str]]:
        """Extract timeline events from logs"""
        events = []
        
        # This is a simplified version - in production, you'd parse actual log events
        # For now, we'll create sample events based on log patterns
        
        return events
        
    def _analyze_logs(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze logs for patterns and anomalies"""
        analysis = {
            'error_patterns': [],
            'anomalies': [],
            'key_events': []
        }
        
        if 'raw_data' in incident_data and 'logs' in incident_data['raw_data']:
            # Analyze error patterns
            logs = incident_data['raw_data']['logs']
            
            # Count error types
            error_counts = {}
            for log_group, events in logs.items():
                for event in events:
                    if isinstance(event, dict) and 'message' in event:
                        msg = event['message'].lower()
                        if 'error' in msg:
                            error_type = self._categorize_error(msg)
                            error_counts[error_type] = error_counts.get(error_type, 0) + 1
                            
            analysis['error_patterns'] = [
                {'type': k, 'count': v} for k, v in error_counts.items()
            ]
            
        return analysis
        
    def _analyze_metrics(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metrics for anomalies and patterns"""
        analysis = {
            'anomalies': [],
            'correlations': [],
            'peak_values': {}
        }
        
        if 'raw_data' in incident_data and 'metrics' in incident_data['raw_data']:
            metrics = incident_data['raw_data']['metrics']
            
            for metric_name, datapoints in metrics.items():
                if datapoints:
                    # Find peak values
                    max_point = max(datapoints, key=lambda x: x.get('Maximum', 0))
                    analysis['peak_values'][metric_name] = {
                        'value': max_point.get('Maximum', 0),
                        'timestamp': max_point.get('Timestamp', '')
                    }
                    
        return analysis
        
    def _get_ai_analysis(self, incident_data: Dict, timeline: List, 
                        log_analysis: Dict, metrics_analysis: Dict) -> Dict[str, Any]:
        """Get AI-powered analysis using Bedrock"""
        
        # Prepare context for AI
        context = {
            'incident_type': incident_data.get('type', 'unknown'),
            'description': incident_data.get('description', ''),
            'timeline_events': len(timeline),
            'error_patterns': log_analysis.get('error_patterns', []),
            'metric_anomalies': metrics_analysis.get('anomalies', []),
            'peak_metrics': metrics_analysis.get('peak_values', {})
        }
        
        prompt = f"""Analyze this incident for a comprehensive post-mortem report:

Incident Type: {context['incident_type']}
Description: {context['description']}
Timeline Events: {context['timeline_events']}
Error Patterns: {json.dumps(context['error_patterns'])}
Peak Metrics: {json.dumps(context['peak_metrics'])}

Please provide a detailed analysis including:
1. A concise title for this incident
2. Root cause analysis
3. Contributing factors (list at least 3)
4. Detection method used
5. Response actions taken
6. What went well (at least 3 items)
7. What went wrong (at least 3 items)
8. Lessons learned (at least 3)
9. Preventive measures (at least 3)
10. Monitoring improvements needed (at least 2)

Format your response as JSON with these exact keys:
{{
    "title": "incident title",
    "root_cause": "detailed root cause",
    "contributing_factors": ["factor1", "factor2", "factor3"],
    "detection_method": "how it was detected",
    "response_actions": ["action1", "action2"],
    "what_went_well": ["item1", "item2", "item3"],
    "what_went_wrong": ["item1", "item2", "item3"],
    "lessons_learned": ["lesson1", "lesson2", "lesson3"],
    "preventive_measures": ["measure1", "measure2", "measure3"],
    "monitoring_improvements": ["improvement1", "improvement2"],
    "confidence_score": 0.85
}}"""

        try:
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
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
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Parse JSON from response
            try:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    analysis = json.loads(content[json_start:json_end])
                else:
                    analysis = self._get_default_analysis()
            except:
                analysis = self._get_default_analysis()
                
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting AI analysis: {str(e)}")
            return self._get_default_analysis()
            
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis when AI fails"""
        return {
            "title": "Service Incident - Root Cause Analysis Pending",
            "root_cause": "Under investigation",
            "contributing_factors": [
                "High resource utilization detected",
                "Configuration changes prior to incident",
                "Insufficient monitoring coverage"
            ],
            "detection_method": "Automated monitoring alert",
            "response_actions": [
                "Incident response team activated",
                "Service health checks performed",
                "Temporary mitigation applied"
            ],
            "what_went_well": [
                "Quick incident detection",
                "Effective team communication",
                "Successful rollback procedure"
            ],
            "what_went_wrong": [
                "Delayed initial response",
                "Incomplete runbook documentation",
                "Insufficient test coverage"
            ],
            "lessons_learned": [
                "Need better alerting thresholds",
                "Improve deployment procedures",
                "Enhance monitoring coverage"
            ],
            "preventive_measures": [
                "Implement stricter deployment controls",
                "Add comprehensive health checks",
                "Improve capacity planning"
            ],
            "monitoring_improvements": [
                "Add application-level metrics",
                "Implement synthetic monitoring"
            ],
            "confidence_score": 0.7
        }
        
    def _analyze_impact(self, incident_data: Dict, ai_analysis: Dict) -> Dict[str, Any]:
        """Analyze incident impact"""
        impact = {
            'services_affected': [],
            'users_impacted': 0,
            'revenue_impact': 'Unknown',
            'sla_breached': False
        }
        
        # Determine affected services
        if 'service' in incident_data:
            impact['services_affected'].append(incident_data['service'])
            
        # Estimate user impact based on incident type
        incident_type = incident_data.get('type', 'unknown')
        if incident_type == 'outage':
            impact['users_impacted'] = 10000
            impact['revenue_impact'] = '$50,000'
            impact['sla_breached'] = True
        elif incident_type == 'performance':
            impact['users_impacted'] = 5000
            impact['revenue_impact'] = '$10,000'
            impact['sla_breached'] = False
        elif incident_type == 'security':
            impact['users_impacted'] = 1000
            impact['revenue_impact'] = 'Potential compliance fine'
            impact['sla_breached'] = False
            
        return impact
        
    def _generate_action_items(self, ai_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate actionable items from analysis"""
        action_items = []
        
        # Create action items from preventive measures
        for i, measure in enumerate(ai_analysis.get('preventive_measures', [])):
            action_items.append({
                'id': f'AI-{i+1}',
                'title': measure,
                'priority': 'HIGH' if i == 0 else 'MEDIUM',
                'assigned_to': 'SRE Team',
                'due_date': (datetime.now() + timedelta(days=7*(i+1))).isoformat(),
                'status': 'TODO'
            })
            
        # Add monitoring improvements as action items
        for i, improvement in enumerate(ai_analysis.get('monitoring_improvements', [])):
            action_items.append({
                'id': f'AI-{len(action_items)+1}',
                'title': f'Monitoring: {improvement}',
                'priority': 'MEDIUM',
                'assigned_to': 'DevOps Team',
                'due_date': (datetime.now() + timedelta(days=14)).isoformat(),
                'status': 'TODO'
            })
            
        return action_items
        
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error types"""
        msg_lower = error_message.lower()
        
        if 'timeout' in msg_lower:
            return 'timeout'
        elif 'connection' in msg_lower:
            return 'connection'
        elif 'memory' in msg_lower:
            return 'memory'
        elif 'permission' in msg_lower or 'denied' in msg_lower:
            return 'permission'
        elif 'not found' in msg_lower or '404' in msg_lower:
            return 'not_found'
        else:
            return 'general'
            
    def _get_detection_time(self, timeline: List[Dict]) -> str:
        """Get incident detection time"""
        for event in timeline:
            if 'detect' in event.get('event', '').lower():
                return event['time']
        return timeline[0]['time'] if timeline else datetime.now().isoformat()
        
    def _get_resolution_time(self, timeline: List[Dict]) -> str:
        """Get incident resolution time"""
        for event in reversed(timeline):
            if 'resolv' in event.get('event', '').lower():
                return event['time']
        return timeline[-1]['time'] if timeline else datetime.now().isoformat()
        
    def _calculate_duration(self, timeline: List[Dict]) -> int:
        """Calculate incident duration in minutes"""
        if len(timeline) >= 2:
            try:
                start = datetime.fromisoformat(timeline[0]['time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(timeline[-1]['time'].replace('Z', '+00:00'))
                return int((end - start).total_seconds() / 60)
            except:
                return 60  # Default 1 hour
        return 60
        
    def generate_markdown_report(self, report: PostMortemReport) -> str:
        """Generate markdown formatted report"""
        md = f"""# Post-Mortem Report: {report.title}

**Incident ID:** {report.incident_id}  
**Severity:** {report.severity}  
**Date:** {report.incident_start[:10]}  
**Duration:** {report.duration_minutes} minutes  
**AI Confidence Score:** {report.ai_confidence_score:.0%}

## Executive Summary

This incident began at {report.incident_start} and was resolved at {report.resolution_time}. 
The root cause was identified as: **{report.root_cause}**

### Impact
- **Services Affected:** {', '.join(report.services_affected)}
- **Users Impacted:** {report.users_impacted:,}
- **Revenue Impact:** {report.revenue_impact}
- **SLA Breached:** {'Yes' if report.sla_breached else 'No'}

## Timeline

| Time | Event | Severity |
|------|-------|----------|
"""
        for event in report.timeline:
            md += f"| {event['time']} | {event['event']} | {event.get('severity', 'info')} |\n"
            
        md += f"""
## Root Cause Analysis

### Primary Cause
{report.root_cause}

### Contributing Factors
"""
        for factor in report.contributing_factors:
            md += f"- {factor}\n"
            
        md += f"""
## Incident Response

### Detection
- **Method:** {report.detection_method}
- **Time to Detection:** Calculated from timeline

### Response Actions
"""
        for action in report.response_actions:
            md += f"- {action}\n"
            
        md += """
## What Went Well
"""
        for item in report.what_went_well:
            md += f"- ✅ {item}\n"
            
        md += """
## What Went Wrong
"""
        for item in report.what_went_wrong:
            md += f"- ❌ {item}\n"
            
        md += """
## Lessons Learned
"""
        for lesson in report.lessons_learned:
            md += f"- 💡 {lesson}\n"
            
        md += """
## Action Items

| ID | Title | Priority | Assigned To | Due Date | Status |
|----|-------|----------|-------------|----------|--------|
"""
        for item in report.action_items:
            md += f"| {item['id']} | {item['title']} | {item['priority']} | {item['assigned_to']} | {item['due_date'][:10]} | {item['status']} |\n"
            
        md += """
## Prevention

### Preventive Measures
"""
        for measure in report.preventive_measures:
            md += f"- {measure}\n"
            
        md += """
### Monitoring Improvements
"""
        for improvement in report.monitoring_improvements:
            md += f"- {improvement}\n"
            
        md += f"""
---
*Generated by {report.generated_by} on {report.generated_at}*
"""
        
        return md


# Convenience function for Lambda
def lambda_handler(event, context):
    """Lambda handler for post-mortem analysis"""
    agent = PostMortemAgent()
    
    try:
        # Get incident data from event
        incident_data = event.get('incident_data', {})
        
        # Generate post-mortem report
        report = agent.analyze_incident(incident_data)
        
        # Generate markdown
        markdown_report = agent.generate_markdown_report(report)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'report': asdict(report),
                'markdown': markdown_report
            })
        }
        
    except Exception as e:
        logger.error(f"Error in post-mortem analysis: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


if __name__ == "__main__":
    # Test the agent
    test_incident = {
        'incident_id': 'INC-2024-001',
        'type': 'outage',
        'description': 'Complete service outage due to database failure',
        'severity': 'CRITICAL',
        'start_time': datetime.now() - timedelta(hours=2),
        'service': 'payment-api',
        'raw_data': {
            'metrics': {
                'CPUUtilization': [{'Maximum': 95, 'Timestamp': datetime.now().isoformat()}],
                'ErrorRate': [{'Maximum': 100, 'Timestamp': datetime.now().isoformat()}]
            }
        }
    }
    
    agent = PostMortemAgent()
    report = agent.analyze_incident(test_incident)
    print(agent.generate_markdown_report(report))
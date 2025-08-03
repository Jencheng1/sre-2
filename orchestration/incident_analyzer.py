"""
Enhanced Incident Analyzer with MCP Integration
"""

import json
from datetime import datetime
from typing import Dict, List, Any
from lambdas.mcp_orchestrator import MCPOrchestrator
from feedback.context_enhancer import ContextEnhancer, ContextualRecommender

class IncidentAnalyzer:
    """Analyzes incidents using AWS data and MCP external sources"""
    
    def __init__(self):
        self.mcp_orchestrator = MCPOrchestrator()
        self.context_enhancer = ContextEnhancer()
        self.recommender = ContextualRecommender()
        
    def analyze_with_mcp(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive incident analysis with MCP data"""
        analysis_id = f"ANAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Step 1: Gather AWS data (placeholder - would call actual AWS services)
        aws_data = self._gather_aws_data(incident)
        
        # Step 2: Gather MCP data
        mcp_data = self.mcp_orchestrator.gather_external_context(incident)
        
        # Step 3: Get enhanced context from historical feedback
        enhanced_context = self.context_enhancer.get_enhanced_context(incident)
        
        # Step 4: Correlate all data sources
        correlations = self._correlate_data(aws_data, mcp_data, enhanced_context)
        
        # Step 5: Determine root cause
        root_cause_analysis = self._analyze_root_cause(incident, correlations)
        
        # Step 6: Get recommendations
        recommendations = self.recommender.get_recommendations(incident, root_cause_analysis)
        
        # Step 7: Build comprehensive analysis
        analysis = {
            "analysis_id": analysis_id,
            "incident_id": incident["id"],
            "timestamp": datetime.now().isoformat(),
            "root_cause": root_cause_analysis["root_cause"],
            "confidence": root_cause_analysis["confidence"],
            "evidence": root_cause_analysis["evidence"],
            "mcp_correlations": self._extract_mcp_correlations(mcp_data),
            "recommended_actions": self._generate_actions(root_cause_analysis, recommendations),
            "historical_context": {
                "similar_incidents": enhanced_context.get("historical_resolutions", []),
                "common_patterns": enhanced_context.get("common_patterns", [])
            },
            "external_insights": self._extract_insights(mcp_data),
            "recommendations": recommendations
        }
        
        return analysis
    
    def _gather_aws_data(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Gather AWS service data (placeholder)"""
        # In real implementation, this would call CloudWatch, CloudTrail, etc.
        return {
            "cloudwatch_metrics": {
                "cpu_utilization": 85,
                "network_in": 1000000,
                "network_out": 500000
            },
            "cloudtrail_events": [
                {
                    "event_name": "ModifySecurityGroup",
                    "timestamp": datetime.now().isoformat(),
                    "user": "admin"
                }
            ],
            "vpc_flow_logs": {
                "rejected_connections": 150,
                "top_talkers": ["10.0.1.50", "10.0.2.100"]
            }
        }
    
    def _correlate_data(self, aws_data: Dict[str, Any], mcp_data: Dict[str, Any], 
                       enhanced_context: Dict[str, Any]) -> Dict[str, Any]:
        """Correlate data from all sources"""
        correlations = {
            "network_correlations": [],
            "application_correlations": [],
            "infrastructure_correlations": [],
            "timeline_correlations": []
        }
        
        # Network correlations
        if "splunk" in mcp_data and mcp_data["splunk"].get("status") == "success":
            network_metrics = mcp_data["splunk"].get("network_metrics", [])
            if network_metrics:
                avg_latency = sum(m.get("avg_latency", 0) for m in network_metrics) / len(network_metrics)
                if avg_latency > 200:
                    correlations["network_correlations"].append({
                        "finding": "High network latency detected",
                        "source": "Splunk",
                        "value": f"{avg_latency:.0f}ms average",
                        "severity": "high"
                    })
        
        # Application correlations
        if "dynatrace" in mcp_data and mcp_data["dynatrace"].get("status") == "success":
            mq_metrics = mcp_data["dynatrace"].get("mq_metrics", {})
            if mq_metrics and mq_metrics.get("queue_depth", 0) > 1000:
                correlations["application_correlations"].append({
                    "finding": "Message queue backlog detected",
                    "source": "Dynatrace",
                    "value": f"{mq_metrics['queue_depth']} messages",
                    "severity": "medium"
                })
        
        # Infrastructure correlations
        if "servicenow" in mcp_data and mcp_data["servicenow"].get("status") == "success":
            recent_changes = mcp_data["servicenow"].get("recent_changes", [])
            if recent_changes:
                correlations["infrastructure_correlations"].append({
                    "finding": f"{len(recent_changes)} recent changes detected",
                    "source": "ServiceNow",
                    "changes": [c.get("short_description", "") for c in recent_changes[:3]],
                    "severity": "medium"
                })
        
        # Code change correlations
        if "gitlab" in mcp_data and mcp_data["gitlab"].get("status") == "success":
            recent_commits = mcp_data["gitlab"].get("recent_commits", [])
            if recent_commits:
                correlations["timeline_correlations"].append({
                    "finding": "Recent code deployments detected",
                    "source": "GitLab",
                    "commits": len(recent_commits),
                    "last_commit": recent_commits[0].get("message", "") if recent_commits else "",
                    "severity": "low"
                })
        
        return correlations
    
    def _analyze_root_cause(self, incident: Dict[str, Any], 
                           correlations: Dict[str, Any]) -> Dict[str, Any]:
        """Determine root cause based on correlations"""
        # Scoring system for different correlation types
        scores = {
            "network_issue": 0,
            "application_issue": 0,
            "infrastructure_issue": 0,
            "deployment_issue": 0
        }
        
        evidence = []
        
        # Score based on correlations
        for corr in correlations.get("network_correlations", []):
            if corr["severity"] == "high":
                scores["network_issue"] += 3
                evidence.append(corr)
        
        for corr in correlations.get("application_correlations", []):
            if corr["severity"] in ["high", "medium"]:
                scores["application_issue"] += 2
                evidence.append(corr)
        
        for corr in correlations.get("infrastructure_correlations", []):
            scores["infrastructure_issue"] += 2
            evidence.append(corr)
        
        for corr in correlations.get("timeline_correlations", []):
            scores["deployment_issue"] += 1
            evidence.append(corr)
        
        # Determine root cause
        max_score = max(scores.values())
        if max_score == 0:
            root_cause = "Unable to determine root cause"
            confidence = 0.3
        else:
            root_cause_type = max(scores, key=scores.get)
            root_cause = self._format_root_cause(root_cause_type, evidence)
            confidence = min(0.9, max_score / 10)
        
        return {
            "root_cause": root_cause,
            "confidence": confidence,
            "evidence": evidence,
            "scores": scores
        }
    
    def _format_root_cause(self, cause_type: str, evidence: List[Dict[str, Any]]) -> str:
        """Format root cause description"""
        cause_map = {
            "network_issue": "Network connectivity/latency issue",
            "application_issue": "Application performance degradation",
            "infrastructure_issue": "Infrastructure configuration change",
            "deployment_issue": "Recent deployment impact"
        }
        
        base_cause = cause_map.get(cause_type, "Unknown issue")
        
        # Add specific details from evidence
        if evidence:
            top_evidence = evidence[0]
            if "value" in top_evidence:
                base_cause += f" - {top_evidence['finding']} ({top_evidence['value']})"
            else:
                base_cause += f" - {top_evidence['finding']}"
        
        return base_cause
    
    def _extract_mcp_correlations(self, mcp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key correlations from MCP data"""
        correlations = {}
        
        for server, data in mcp_data.items():
            if isinstance(data, dict):  # Make sure data is a dict
                if server == "splunk":
                    correlations["splunk"] = {
                        "network_issues": bool(data.get("network_metrics")),
                        "data_points": len(data.get("network_metrics", [])) if data.get("network_metrics") else 0
                    }
                elif server == "dynatrace":
                    correlations["dynatrace"] = {
                        "mq_issues": bool(data.get("mq_metrics")),
                        "active_problems": len(data.get("problems", []))
                    }
                elif server == "servicenow":
                    correlations["servicenow"] = {
                        "related_incidents": len(data.get("related_incidents", [])),
                        "recent_changes": len(data.get("recent_changes", []))
                    }
                elif server == "confluence":
                    correlations["confluence_kb"] = {
                        "relevant_articles": len(data.get("kb_articles", [])),
                        "top_article": data.get("kb_articles", [{}])[0].get("title", "") if data.get("kb_articles") else ""
                    }
                elif server == "gitlab":
                    correlations["gitlab"] = {
                        "code_matches": len(data.get("code_search", [])),
                        "recent_commits": len(data.get("recent_commits", []))
                    }
        
        return correlations
    
    def _generate_actions(self, root_cause_analysis: Dict[str, Any], 
                         recommendations: Dict[str, Any]) -> List[str]:
        """Generate recommended actions"""
        actions = []
        
        # Base actions based on root cause type
        cause_type = None
        for cause, score in root_cause_analysis["scores"].items():
            if score == max(root_cause_analysis["scores"].values()):
                cause_type = cause
                break
        
        if cause_type == "network_issue":
            actions.extend([
                "Check DNS resolution and Route53 health checks",
                "Verify security group and NACL rules",
                "Analyze VPC flow logs for dropped packets",
                "Review network topology for bottlenecks"
            ])
        elif cause_type == "application_issue":
            actions.extend([
                "Review application logs for errors",
                "Check message queue depth and processing rate",
                "Analyze database connection pools",
                "Review application metrics and traces"
            ])
        elif cause_type == "infrastructure_issue":
            actions.extend([
                "Review recent infrastructure changes",
                "Verify auto-scaling policies",
                "Check instance health and resource utilization",
                "Review load balancer configuration"
            ])
        elif cause_type == "deployment_issue":
            actions.extend([
                "Review recent deployment logs",
                "Check for configuration changes",
                "Verify deployment rollback procedures",
                "Compare with previous stable version"
            ])
        
        # Add recommendations from historical data
        if recommendations.get("additional_checks"):
            for check in recommendations["additional_checks"][:2]:
                actions.append(check["check"])
        
        # Deduplicate and limit
        return list(dict.fromkeys(actions))[:10]
    
    def _extract_insights(self, mcp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key insights from MCP data"""
        insights = []
        
        # Splunk insights
        if "splunk" in mcp_data and mcp_data["splunk"].get("network_metrics"):
            metrics = mcp_data["splunk"]["network_metrics"]
            if metrics:
                avg_latency = sum(m.get("avg_latency", 0) for m in metrics) / len(metrics)
                insights.append({
                    "source": "Splunk",
                    "insight": f"Network latency averaging {avg_latency:.0f}ms",
                    "type": "metric"
                })
        
        # Dynatrace insights
        if "dynatrace" in mcp_data and mcp_data["dynatrace"].get("problems"):
            problems = mcp_data["dynatrace"]["problems"]
            if problems:
                insights.append({
                    "source": "Dynatrace",
                    "insight": f"{len(problems)} active problems detected",
                    "type": "alert"
                })
        
        # ServiceNow insights
        if "servicenow" in mcp_data and mcp_data["servicenow"].get("recent_changes"):
            changes = mcp_data["servicenow"]["recent_changes"]
            if changes:
                insights.append({
                    "source": "ServiceNow",
                    "insight": f"{len(changes)} changes scheduled in the next 7 days",
                    "type": "change"
                })
        
        # Confluence insights
        if "confluence" in mcp_data and mcp_data["confluence"].get("kb_articles"):
            articles = mcp_data["confluence"]["kb_articles"]
            if articles:
                insights.append({
                    "source": "Confluence",
                    "insight": f"Found {len(articles)} relevant KB articles",
                    "type": "knowledge"
                })
        
        return insights
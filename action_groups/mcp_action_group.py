"""
AWS Bedrock Action Group for MCP Integration
"""

import json
from typing import Dict, List, Any
from lambdas.mcp_orchestrator import MCPOrchestrator

class MCPActionGroup:
    """Action group handler for Bedrock agent MCP integration"""
    
    def __init__(self):
        self.orchestrator = MCPOrchestrator()
        self.supported_actions = {
            "get_network_latency": self._get_network_latency,
            "get_mq_metrics": self._get_mq_metrics,
            "search_incidents": self._search_incidents,
            "search_knowledge_base": self._search_knowledge_base,
            "analyze_code_changes": self._analyze_code_changes,
            "get_all_context": self._get_all_context
        }
    
    def execute_action(self, action_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the requested action"""
        action_name = action_input.get("action")
        parameters = action_input.get("parameters", {})
        
        if action_name not in self.supported_actions:
            return {
                "error": f"Unsupported action: {action_name}",
                "supported_actions": list(self.supported_actions.keys())
            }
        
        try:
            # Execute the action
            action_handler = self.supported_actions[action_name]
            result = action_handler(parameters)
            
            return {
                "success": True,
                "action": action_name,
                **result
            }
            
        except Exception as e:
            return {
                "success": False,
                "action": action_name,
                "error": str(e)
            }
    
    def _get_network_latency(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get network latency from Splunk"""
        context = {
            "type": "network_latency",
            "time_range": params.get("time_range", "-1h"),
            "host_filter": params.get("host_filter", "*")
        }
        
        results = self.orchestrator.gather_external_context(context)
        splunk_data = results.get("splunk", {})
        
        if splunk_data.get("status") == "success":
            return {
                "latency_data": splunk_data.get("network_metrics", []),
                "source": "splunk"
            }
        else:
            return {
                "latency_data": [],
                "error": "Failed to retrieve Splunk data"
            }
    
    def _get_mq_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get MQ metrics from Dynatrace"""
        context = {
            "type": "mq_performance",
            "service": params.get("service", ""),
            "queue_name": params.get("queue_name", "")
        }
        
        results = self.orchestrator.gather_external_context(context)
        dynatrace_data = results.get("dynatrace", {})
        
        if dynatrace_data.get("status") == "success":
            return {
                "mq_metrics": dynatrace_data.get("mq_metrics", {}),
                "problems": dynatrace_data.get("problems", []),
                "source": "dynatrace"
            }
        else:
            return {
                "mq_metrics": {},
                "error": "Failed to retrieve Dynatrace data"
            }
    
    def _search_incidents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search incidents in ServiceNow"""
        context = {
            "type": params.get("incident_type", ""),
            "category": params.get("category", ""),
            "state": params.get("state", "active")
        }
        
        results = self.orchestrator.gather_external_context(context)
        servicenow_data = results.get("servicenow", {})
        
        if servicenow_data.get("status") == "success":
            return {
                "incidents": servicenow_data.get("related_incidents", []),
                "changes": servicenow_data.get("recent_changes", []),
                "source": "servicenow"
            }
        else:
            return {
                "incidents": [],
                "error": "Failed to retrieve ServiceNow data"
            }
    
    def _search_knowledge_base(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base in Confluence"""
        context = {
            "type": "kb_search",
            "query": params.get("query", ""),
            "symptoms": params.get("symptoms", [])
        }
        
        results = self.orchestrator.gather_external_context(context)
        confluence_data = results.get("confluence", {})
        
        if confluence_data.get("status") == "success":
            return {
                "kb_articles": confluence_data.get("kb_articles", []),
                "source": "confluence"
            }
        else:
            return {
                "kb_articles": [],
                "error": "Failed to retrieve Confluence data"
            }
    
    def _analyze_code_changes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code changes from GitLab"""
        context = {
            "type": "code_analysis",
            "service": params.get("service", ""),
            "search_term": params.get("search_term", "")
        }
        
        results = self.orchestrator.gather_external_context(context)
        gitlab_data = results.get("gitlab", {})
        
        if gitlab_data.get("status") == "success":
            return {
                "code_matches": gitlab_data.get("code_search", []),
                "recent_commits": gitlab_data.get("recent_commits", []),
                "source": "gitlab"
            }
        else:
            return {
                "code_matches": [],
                "error": "Failed to retrieve GitLab data"
            }
    
    def _get_all_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get context from all MCP servers"""
        context = params.get("incident_context", {})
        
        all_results = self.orchestrator.gather_external_context(context)
        
        # Summarize results
        summary = {
            "sources_queried": list(all_results.keys()),
            "successful_sources": [k for k, v in all_results.items() 
                                 if v.get("status") == "success"],
            "failed_sources": [k for k, v in all_results.items() 
                             if v.get("status") != "success"],
            "data": all_results
        }
        
        return summary


def lambda_handler(event, context):
    """AWS Lambda handler for Bedrock action group"""
    action_group = MCPActionGroup()
    
    # Extract action and parameters from Bedrock event
    action = event.get("action", "")
    parameters = event.get("parameters", {})
    
    # Execute action
    result = action_group.execute_action({
        "action": action,
        "parameters": parameters
    })
    
    # Return response in Bedrock format
    return {
        "statusCode": 200,
        "body": json.dumps(result),
        "headers": {
            "Content-Type": "application/json"
        }
    }
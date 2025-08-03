"""
MCP Orchestrator for Lambda integration
Coordinates calls to multiple MCP servers
"""

import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import requests
from config.mcp_config import MCPConfigManager

class MCPOrchestrator:
    def __init__(self):
        self.config_manager = MCPConfigManager()
        self.session = None
        
    def gather_external_context(self, incident_context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather context from all enabled MCP servers"""
        enabled_servers = self.config_manager.get_enabled_servers()
        results = {}
        
        # Use ThreadPoolExecutor for parallel calls
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            
            for server_name in enabled_servers:
                future = executor.submit(self._call_mcp_server, server_name, incident_context)
                futures[server_name] = future
            
            # Collect results
            for server_name, future in futures.items():
                try:
                    results[server_name] = future.result(timeout=30)
                except Exception as e:
                    results[server_name] = {
                        "error": str(e),
                        "status": "failed"
                    }
        
        return results
    
    def _call_mcp_server(self, server_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP server based on the incident context"""
        server_config = self.config_manager.get_mcp_config(server_name)
        if not server_config or not server_config.get("enabled"):
            return {"status": "disabled"}
        
        headers = self.config_manager.get_auth_headers(server_name)
        endpoint = server_config["endpoint"]
        
        try:
            if server_name == "splunk":
                return self._call_splunk(endpoint, headers, context)
            elif server_name == "dynatrace":
                return self._call_dynatrace(endpoint, headers, context)
            elif server_name == "servicenow":
                return self._call_servicenow(endpoint, headers, context)
            elif server_name == "confluence":
                return self._call_confluence(endpoint, headers, context)
            elif server_name == "gitlab":
                return self._call_gitlab(endpoint, headers, context)
            else:
                return {"status": "unknown_server"}
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _call_splunk(self, endpoint: str, headers: Dict[str, str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Splunk MCP for network metrics"""
        # Determine query based on incident type
        query = self._build_splunk_query(context)
        
        response = requests.post(
            f"{endpoint}/search",
            headers=headers,
            json={
                "query": query,
                "time_range": "-1h"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "network_metrics": data.get("results", []),
                "query": query
            }
        else:
            return {
                "status": "error",
                "code": response.status_code
            }
    
    def _call_dynatrace(self, endpoint: str, headers: Dict[str, str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Dynatrace MCP for MQ and APM metrics"""
        results = {
            "status": "success",
            "mq_metrics": None,
            "apm_metrics": None,
            "problems": []
        }
        
        # Get MQ metrics if relevant
        if "queue" in str(context).lower() or "mq" in str(context).lower():
            response = requests.get(
                f"{endpoint}/metrics",
                headers=headers,
                params={
                    "type": "mq",
                    "entity": context.get("service", ""),
                    "time_range": "-30m"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                results["mq_metrics"] = response.json()
        
        # Get APM metrics
        if context.get("service"):
            response = requests.get(
                f"{endpoint}/metrics",
                headers=headers,
                params={
                    "type": "apm",
                    "entity": context["service"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                results["apm_metrics"] = response.json()
        
        # Get active problems
        response = requests.get(
            f"{endpoint}/problems",
            headers=headers,
            params={"status": "OPEN"},
            timeout=30
        )
        
        if response.status_code == 200:
            results["problems"] = response.json()
        
        return results
    
    def _call_servicenow(self, endpoint: str, headers: Dict[str, str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Call ServiceNow MCP for incident history"""
        results = {
            "status": "success",
            "related_incidents": [],
            "recent_changes": []
        }
        
        # Get related incidents
        filters = {
            "category": self._determine_category(context),
            "state": "active"
        }
        
        response = requests.get(
            f"{endpoint}/incidents",
            headers=headers,
            params=filters,
            timeout=30
        )
        
        if response.status_code == 200:
            results["related_incidents"] = response.json()
        
        # Get recent changes
        response = requests.get(
            f"{endpoint}/changes",
            headers=headers,
            params={"state": "scheduled"},
            timeout=30
        )
        
        if response.status_code == 200:
            results["recent_changes"] = response.json()
        
        return results
    
    def _call_confluence(self, endpoint: str, headers: Dict[str, str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Confluence MCP for KB articles"""
        # Build search query based on context
        query = self._build_kb_query(context)
        
        response = requests.get(
            f"{endpoint}/search",
            headers=headers,
            params={
                "query": query,
                "space_key": "SRE"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "kb_articles": response.json(),
                "query": query
            }
        else:
            return {
                "status": "error",
                "code": response.status_code
            }
    
    def _call_gitlab(self, endpoint: str, headers: Dict[str, str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Call GitLab MCP for code analysis"""
        results = {
            "status": "success",
            "code_search": [],
            "recent_commits": []
        }
        
        # Search for relevant code
        if context.get("service"):
            response = requests.get(
                f"{endpoint}/search",
                headers=headers,
                params={
                    "query": context["service"],
                    "project_id": f"backend/{context['service']}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                results["code_search"] = response.json()
        
        # Get recent commits
        response = requests.get(
            f"{endpoint}/commits",
            headers=headers,
            params={
                "since": (datetime.now().isoformat()),
                "project_id": ""
            },
            timeout=30
        )
        
        if response.status_code == 200:
            results["recent_commits"] = response.json()
        
        return results
    
    def _build_splunk_query(self, context: Dict[str, Any]) -> str:
        """Build Splunk query based on context"""
        incident_type = context.get("type", "")
        
        if "latency" in incident_type:
            return "index=network sourcetype=latency | stats avg(latency) by host"
        elif "outage" in incident_type:
            return "index=availability sourcetype=healthcheck | where status!=\"OK\""
        else:
            return "index=* | head 100"
    
    def _build_kb_query(self, context: Dict[str, Any]) -> str:
        """Build KB search query based on context"""
        keywords = []
        
        if context.get("type"):
            keywords.append(context["type"])
        
        if context.get("symptoms"):
            keywords.extend(context["symptoms"][:2])  # First 2 symptoms
        
        return " ".join(keywords)
    
    def _determine_category(self, context: Dict[str, Any]) -> str:
        """Determine ServiceNow category from context"""
        incident_type = context.get("type", "").lower()
        
        if "network" in incident_type or "latency" in incident_type:
            return "Network"
        elif "database" in incident_type:
            return "Database"
        elif "hardware" in incident_type:
            return "Hardware"
        else:
            return "Software"


class AsyncMCPOrchestrator:
    """Async version for better performance"""
    
    def __init__(self):
        self.config_manager = MCPConfigManager()
    
    async def gather_all_mcp_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather data from all MCP servers concurrently"""
        enabled_servers = self.config_manager.get_enabled_servers()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for server_name in enabled_servers:
                task = self._call_mcp_async(session, server_name, context)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Map results to server names
            return {
                server: result if not isinstance(result, Exception) else {"error": str(result)}
                for server, result in zip(enabled_servers, results)
            }
    
    async def _call_mcp_async(self, session: aiohttp.ClientSession, 
                              server_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Async call to MCP server"""
        server_config = self.config_manager.get_mcp_config(server_name)
        if not server_config or not server_config.get("enabled"):
            return {"status": "disabled"}
        
        headers = self.config_manager.get_auth_headers(server_name)
        endpoint = server_config["endpoint"]
        
        # Similar implementation to sync version but using aiohttp
        # This is a placeholder - in real implementation, would make actual async calls
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return {
            "status": "success",
            "data": f"Async data from {server_name}",
            "timestamp": datetime.now().isoformat()
        }
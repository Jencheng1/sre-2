"""
Async orchestrator for concurrent MCP calls
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Any
from config.mcp_config import MCPConfigManager

class AsyncMCPOrchestrator:
    """Async orchestrator for better performance with concurrent MCP calls"""
    
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
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Map results to server names
            return {
                server: result if not isinstance(result, Exception) else {"error": str(result), "status": "failed"}
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
        timeout = aiohttp.ClientTimeout(total=server_config.get("timeout", 30))
        
        try:
            if server_name == "splunk":
                return await self._call_splunk_async(session, endpoint, headers, context, timeout)
            elif server_name == "dynatrace":
                return await self._call_dynatrace_async(session, endpoint, headers, context, timeout)
            elif server_name == "servicenow":
                return await self._call_servicenow_async(session, endpoint, headers, context, timeout)
            elif server_name == "confluence":
                return await self._call_confluence_async(session, endpoint, headers, context, timeout)
            elif server_name == "gitlab":
                return await self._call_gitlab_async(session, endpoint, headers, context, timeout)
            else:
                return {"status": "unknown_server"}
                
        except asyncio.TimeoutError:
            return {"status": "timeout", "error": f"Request to {server_name} timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _call_splunk_async(self, session: aiohttp.ClientSession, endpoint: str, 
                                headers: Dict[str, str], context: Dict[str, Any], 
                                timeout: aiohttp.ClientTimeout) -> Dict[str, Any]:
        """Async Splunk call"""
        query = self._build_splunk_query(context)
        
        async with session.post(
            f"{endpoint}/search",
            headers=headers,
            json={"query": query, "time_range": "-1h"},
            timeout=timeout
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "status": "success",
                    "network_metrics": data.get("results", []),
                    "query": query
                }
            else:
                return {"status": "error", "code": response.status}
    
    async def _call_dynatrace_async(self, session: aiohttp.ClientSession, endpoint: str,
                                   headers: Dict[str, str], context: Dict[str, Any],
                                   timeout: aiohttp.ClientTimeout) -> Dict[str, Any]:
        """Async Dynatrace call"""
        results = {"status": "success", "mq_metrics": None, "problems": []}
        
        # Concurrent sub-requests
        tasks = []
        
        # MQ metrics task
        if "queue" in str(context).lower() or "mq" in str(context).lower():
            tasks.append(self._get_dynatrace_mq_async(session, endpoint, headers, context, timeout))
        
        # Problems task
        tasks.append(self._get_dynatrace_problems_async(session, endpoint, headers, timeout))
        
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in task_results:
                if isinstance(result, dict):
                    results.update(result)
        
        return results
    
    async def _get_dynatrace_mq_async(self, session, endpoint, headers, context, timeout):
        """Get MQ metrics from Dynatrace"""
        params = {
            "type": "mq",
            "entity": context.get("service", ""),
            "time_range": "-30m"
        }
        
        async with session.get(f"{endpoint}/metrics", headers=headers, params=params, timeout=timeout) as response:
            if response.status == 200:
                return {"mq_metrics": await response.json()}
            return {}
    
    async def _get_dynatrace_problems_async(self, session, endpoint, headers, timeout):
        """Get problems from Dynatrace"""
        async with session.get(f"{endpoint}/problems", headers=headers, params={"status": "OPEN"}, timeout=timeout) as response:
            if response.status == 200:
                return {"problems": await response.json()}
            return {}
    
    async def _call_servicenow_async(self, session: aiohttp.ClientSession, endpoint: str,
                                    headers: Dict[str, str], context: Dict[str, Any],
                                    timeout: aiohttp.ClientTimeout) -> Dict[str, Any]:
        """Async ServiceNow call"""
        results = {"status": "success", "related_incidents": [], "recent_changes": []}
        
        # Concurrent requests for incidents and changes
        tasks = [
            self._get_servicenow_incidents_async(session, endpoint, headers, context, timeout),
            self._get_servicenow_changes_async(session, endpoint, headers, timeout)
        ]
        
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in task_results:
            if isinstance(result, dict):
                results.update(result)
        
        return results
    
    async def _get_servicenow_incidents_async(self, session, endpoint, headers, context, timeout):
        """Get incidents from ServiceNow"""
        filters = {
            "category": self._determine_category(context),
            "state": "active"
        }
        
        async with session.get(f"{endpoint}/incidents", headers=headers, params=filters, timeout=timeout) as response:
            if response.status == 200:
                return {"related_incidents": await response.json()}
            return {}
    
    async def _get_servicenow_changes_async(self, session, endpoint, headers, timeout):
        """Get changes from ServiceNow"""
        async with session.get(f"{endpoint}/changes", headers=headers, params={"state": "scheduled"}, timeout=timeout) as response:
            if response.status == 200:
                return {"recent_changes": await response.json()}
            return {}
    
    async def _call_confluence_async(self, session: aiohttp.ClientSession, endpoint: str,
                                   headers: Dict[str, str], context: Dict[str, Any],
                                   timeout: aiohttp.ClientTimeout) -> Dict[str, Any]:
        """Async Confluence call"""
        query = self._build_kb_query(context)
        
        params = {"query": query, "space_key": "SRE"}
        
        async with session.get(f"{endpoint}/search", headers=headers, params=params, timeout=timeout) as response:
            if response.status == 200:
                return {
                    "status": "success",
                    "kb_articles": await response.json(),
                    "query": query
                }
            else:
                return {"status": "error", "code": response.status}
    
    async def _call_gitlab_async(self, session: aiohttp.ClientSession, endpoint: str,
                               headers: Dict[str, str], context: Dict[str, Any],
                               timeout: aiohttp.ClientTimeout) -> Dict[str, Any]:
        """Async GitLab call"""
        results = {"status": "success", "code_search": [], "recent_commits": []}
        
        tasks = []
        
        # Code search task
        if context.get("service"):
            tasks.append(self._search_gitlab_code_async(session, endpoint, headers, context, timeout))
        
        # Recent commits task
        tasks.append(self._get_gitlab_commits_async(session, endpoint, headers, timeout))
        
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in task_results:
                if isinstance(result, dict):
                    results.update(result)
        
        return results
    
    async def _search_gitlab_code_async(self, session, endpoint, headers, context, timeout):
        """Search GitLab code"""
        params = {
            "query": context["service"],
            "project_id": f"backend/{context['service']}"
        }
        
        async with session.get(f"{endpoint}/search", headers=headers, params=params, timeout=timeout) as response:
            if response.status == 200:
                return {"code_search": await response.json()}
            return {}
    
    async def _get_gitlab_commits_async(self, session, endpoint, headers, timeout):
        """Get recent GitLab commits"""
        params = {
            "since": datetime.now().isoformat(),
            "project_id": ""
        }
        
        async with session.get(f"{endpoint}/commits", headers=headers, params=params, timeout=timeout) as response:
            if response.status == 200:
                return {"recent_commits": await response.json()}
            return {}
    
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
            keywords.extend(context["symptoms"][:2])
        
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
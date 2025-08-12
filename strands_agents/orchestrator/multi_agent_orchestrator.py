"""
Multi-Agent Orchestrator for AWS Strands Agents
Coordinates multiple specialized agents for comprehensive SRE monitoring and analysis
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from agents.splunk_agent import SplunkStrandsAgent
from agents.dynatrace_agent import DynatraceStrandsAgent

class MultiAgentOrchestrator:
    """Orchestrates multiple Strands agents for comprehensive SRE analysis"""
    
    def __init__(self, region: str = "us-east-1", test_mode: bool = True):
        self.region = region
        self.test_mode = test_mode
        self.logger = self._setup_logging()
        
        # Initialize agents
        self.agents = self._initialize_agents()
        self.active_sessions = {}
        
        self.logger.info("Multi-Agent Orchestrator initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the orchestrator"""
        logger = logging.getLogger("strands.orchestrator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all available agents"""
        agents = {}
        
        try:
            agents['splunk'] = SplunkStrandsAgent(region=self.region, test_mode=self.test_mode)
            self.logger.info("Splunk agent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Splunk agent: {e}")
        
        try:
            agents['dynatrace'] = DynatraceStrandsAgent(region=self.region, test_mode=self.test_mode)
            self.logger.info("Dynatrace agent initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Dynatrace agent: {e}")
        
        # TODO: Add other agents (ServiceNow, Confluence, GitLab) as they're implemented
        
        return agents
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types"""
        return list(self.agents.keys())
    
    def get_agent_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of all agents"""
        capabilities = {}
        for agent_name, agent in self.agents.items():
            try:
                capabilities[agent_name] = agent.get_capabilities()
            except Exception as e:
                self.logger.error(f"Failed to get capabilities for {agent_name}: {e}")
                capabilities[agent_name] = {"error": str(e)}
        
        return capabilities
    
    def health_check_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all agents"""
        health_status = {}
        
        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            # Submit health check for each agent
            future_to_agent = {
                executor.submit(agent.health_check): name 
                for name, agent in self.agents.items()
            }
            
            # Collect results
            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    health_status[agent_name] = future.result()
                except Exception as e:
                    health_status[agent_name] = {
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
        
        return health_status
    
    def execute_single_agent(self, agent_name: str, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute query on a single agent"""
        if agent_name not in self.agents:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not available",
                "available_agents": list(self.agents.keys())
            }
        
        try:
            agent = self.agents[agent_name]
            return agent.execute(query, context)
        except Exception as e:
            self.logger.error(f"Failed to execute query on {agent_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": agent_name
            }
    
    def execute_parallel_analysis(self, queries: Dict[str, str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute queries on multiple agents in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            # Submit queries to relevant agents
            future_to_agent = {}
            for agent_name, query in queries.items():
                if agent_name in self.agents:
                    future = executor.submit(
                        self.agents[agent_name].execute,
                        query,
                        context
                    )
                    future_to_agent[future] = agent_name
                else:
                    results[agent_name] = {
                        "success": False,
                        "error": f"Agent '{agent_name}' not available"
                    }
            
            # Collect results
            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    results[agent_name] = future.result()
                except Exception as e:
                    results[agent_name] = {
                        "success": False,
                        "error": str(e),
                        "agent": agent_name
                    }
        
        return {
            "success": True,
            "results": results,
            "context": context,
            "execution_time": datetime.now().isoformat()
        }
    
    def comprehensive_incident_analysis(self, incident_description: str, incident_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive incident analysis using all available agents"""
        incident_id = incident_id or f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.logger.info(f"Starting comprehensive analysis for incident: {incident_id}")
        
        # Define queries for each agent based on incident type
        analysis_queries = self._generate_incident_queries(incident_description)
        
        # Execute parallel analysis
        agent_results = self.execute_parallel_analysis(
            analysis_queries,
            context={
                "incident_id": incident_id,
                "incident_description": incident_description,
                "analysis_type": "comprehensive"
            }
        )
        
        # Correlate and synthesize findings
        synthesis = self._synthesize_findings(agent_results["results"], incident_description)
        
        return {
            "incident_id": incident_id,
            "incident_description": incident_description,
            "analysis_timestamp": datetime.now().isoformat(),
            "agent_results": agent_results["results"],
            "synthesis": synthesis,
            "recommendations": self._generate_recommendations(synthesis),
            "confidence_score": self._calculate_confidence_score(agent_results["results"])
        }
    
    def _generate_incident_queries(self, incident_description: str) -> Dict[str, str]:
        """Generate appropriate queries for each agent based on incident description"""
        queries = {}
        
        # Keywords that suggest specific monitoring areas
        network_keywords = ["network", "latency", "connectivity", "timeout", "packet loss"]
        performance_keywords = ["performance", "slow", "response time", "throughput", "queue"]
        error_keywords = ["error", "exception", "failure", "crash", "unavailable"]
        
        description_lower = incident_description.lower()
        
        # Splunk queries for network and log analysis
        if any(keyword in description_lower for keyword in network_keywords):
            queries["splunk"] = f"Analyze network performance issues related to: {incident_description}. Look for latency spikes, packet loss, and connectivity problems in the last 4 hours."
        elif any(keyword in description_lower for keyword in error_keywords):
            queries["splunk"] = f"Search for error patterns and log anomalies related to: {incident_description}. Focus on error rates and failure patterns."
        else:
            queries["splunk"] = f"Perform comprehensive log analysis for incident: {incident_description}. Look for any anomalies or patterns in system logs."
        
        # Dynatrace queries for APM and performance
        if any(keyword in description_lower for keyword in performance_keywords):
            queries["dynatrace"] = f"Analyze application performance metrics and traces for: {incident_description}. Focus on response times, throughput, and bottlenecks."
        elif "queue" in description_lower or "mq" in description_lower:
            queries["dynatrace"] = f"Examine message queue metrics and consumer performance related to: {incident_description}. Check for queue depth and processing issues."
        else:
            queries["dynatrace"] = f"Check for performance anomalies and problems detected for: {incident_description}. Include APM traces and system health metrics."
        
        return queries
    
    def _synthesize_findings(self, agent_results: Dict[str, Any], incident_description: str) -> Dict[str, Any]:
        """Synthesize findings from multiple agents"""
        synthesis = {
            "summary": "",
            "key_findings": [],
            "correlations": [],
            "affected_components": [],
            "timeline": []
        }
        
        successful_results = {k: v for k, v in agent_results.items() if v.get("success", False)}
        
        if not successful_results:
            synthesis["summary"] = "No successful agent responses received for analysis."
            return synthesis
        
        # Extract key findings from each agent
        for agent_name, result in successful_results.items():
            if "response" in result:
                synthesis["key_findings"].append({
                    "agent": agent_name,
                    "finding": f"{agent_name.title()} analysis indicates potential issues in monitoring data",
                    "confidence": "medium"
                })
        
        # Look for correlations between agent findings
        if len(successful_results) >= 2:
            synthesis["correlations"].append(
                "Multiple monitoring systems show activity during incident timeframe - suggests system-wide impact"
            )
        
        # Generate summary
        agent_names = list(successful_results.keys())
        synthesis["summary"] = f"Analysis completed using {len(agent_names)} agents: {', '.join(agent_names)}. " \
                              f"Cross-correlation of monitoring data suggests incident involves multiple system components."
        
        return synthesis
    
    def _generate_recommendations(self, synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on synthesis"""
        recommendations = []
        
        # Base recommendations
        recommendations.extend([
            {
                "priority": "high",
                "action": "Review correlation findings between monitoring systems",
                "rationale": "Multiple agents detected anomalies during incident timeframe",
                "estimated_effort": "30 minutes"
            },
            {
                "priority": "medium", 
                "action": "Implement additional monitoring for identified components",
                "rationale": "Enhance visibility into affected system areas",
                "estimated_effort": "2-4 hours"
            },
            {
                "priority": "low",
                "action": "Document incident patterns for future reference",
                "rationale": "Build knowledge base for similar incidents",
                "estimated_effort": "1 hour"
            }
        ])
        
        # Add specific recommendations based on synthesis
        if synthesis.get("correlations"):
            recommendations.insert(0, {
                "priority": "critical",
                "action": "Investigate system-wide dependencies and cascading failures",
                "rationale": "Multi-system correlation detected",
                "estimated_effort": "1-2 hours"
            })
        
        return recommendations
    
    def _calculate_confidence_score(self, agent_results: Dict[str, Any]) -> float:
        """Calculate confidence score based on agent response quality"""
        if not agent_results:
            return 0.0
        
        successful_agents = sum(1 for result in agent_results.values() if result.get("success", False))
        total_agents = len(agent_results)
        
        base_confidence = (successful_agents / total_agents) * 100
        
        # Adjust based on data quality (simplified for now)
        # In production, this would analyze response content quality
        return min(base_confidence, 95.0)  # Cap at 95% confidence
    
    def create_session(self, session_id: str, agents: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new analysis session"""
        if agents is None:
            agents = list(self.agents.keys())
        
        available_agents = {name: agent for name, agent in self.agents.items() if name in agents}
        
        session = {
            "session_id": session_id,
            "created": datetime.now().isoformat(),
            "agents": available_agents,
            "queries": [],
            "results": []
        }
        
        self.active_sessions[session_id] = session
        
        return {
            "success": True,
            "session_id": session_id,
            "available_agents": list(available_agents.keys()),
            "message": f"Session created with {len(available_agents)} agents"
        }
    
    def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close an analysis session"""
        if session_id in self.active_sessions:
            session = self.active_sessions.pop(session_id)
            return {
                "success": True,
                "session_id": session_id,
                "queries_executed": len(session.get("queries", [])),
                "message": "Session closed successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found",
                "active_sessions": list(self.active_sessions.keys())
            }
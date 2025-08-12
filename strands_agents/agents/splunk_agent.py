"""
Splunk Strands Agent for network latency monitoring and log analysis
Replaces the Splunk MCP server with enhanced security and scalability
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from base.base_agent import BaseStrandsAgent, StrandsToolFactory

class SplunkStrandsAgent(BaseStrandsAgent):
    """Splunk monitoring agent using AWS Strands framework"""
    
    def __init__(self, region: str = "us-east-1", test_mode: bool = True):
        super().__init__(
            agent_name="splunk",
            region=region,
            test_mode=test_mode
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a Splunk monitoring specialist agent focused on network latency analysis and log searching.

Your capabilities include:
1. Executing Splunk search queries to analyze network performance
2. Retrieving network latency metrics for specific hosts
3. Monitoring and reporting network alerts
4. Analyzing packet loss and connection issues
5. Providing insights on network performance trends

You have access to tools for:
- splunk_search: Execute SPL (Splunk Processing Language) queries
- splunk_metrics: Get specific network metrics for hosts
- splunk_alerts: Retrieve and analyze network alerts

Always provide detailed analysis and actionable recommendations when responding to network monitoring queries.
When analyzing network issues, consider factors like:
- Average and peak latency values
- Packet loss percentages
- Host-specific patterns
- Time-based trends
- Critical thresholds

Respond in a professional, technical manner suitable for SRE teams."""
    
    def _create_tools(self) -> List[Any]:
        """Create Splunk-specific tools"""
        return [
            StrandsToolFactory.create_search_tool(
                name="splunk_search",
                description="Execute Splunk SPL query to search logs and analyze network data",
                search_func=self._search_tool,
                parameters={
                    "query": {"type": "string", "description": "SPL query to execute"},
                    "time_range": {"type": "string", "description": "Time range (e.g., -1h, -24h)", "default": "-1h"},
                    "max_results": {"type": "integer", "description": "Maximum results to return", "default": 100}
                }
            ),
            StrandsToolFactory.create_metrics_tool(
                name="splunk_metrics",
                description="Get network metrics for specific hosts or services",
                metrics_func=self._metrics_tool,
                parameters={
                    "host": {"type": "string", "description": "Host to get metrics for", "default": "*"},
                    "metric": {"type": "string", "description": "Metric type (latency, packet_loss, throughput)", "default": "latency"}
                }
            ),
            StrandsToolFactory.create_monitoring_tool(
                name="splunk_alerts",
                description="Retrieve and analyze network alerts from Splunk",
                func=self._alerts_tool,
                parameters={
                    "severity": {"type": "string", "description": "Alert severity filter (critical, high, medium, low, all)", "default": "all"},
                    "time_range": {"type": "string", "description": "Time range for alerts", "default": "-4h"}
                }
            )
        ]
    
    def _get_specific_capabilities(self) -> List[str]:
        return [
            "Network latency monitoring",
            "SPL query execution",
            "Log analysis and correlation",
            "Network alert management",
            "Packet loss analysis",
            "Performance trend analysis",
            "Host-specific metrics",
            "Real-time monitoring"
        ]
    
    def _search_tool(self, query: str, time_range: str = "-1h", max_results: int = 100) -> Dict[str, Any]:
        """Execute Splunk search query"""
        try:
            self.logger.info(f"Executing Splunk search: {query}")
            
            if self.test_mode:
                # Generate realistic test data
                results = self._generate_search_results(query, max_results)
                return {
                    "success": True,
                    "query": query,
                    "time_range": time_range,
                    "results": results,
                    "count": len(results),
                    "execution_time": f"{random.uniform(0.5, 3.0):.2f}s"
                }
            else:
                # In production, this would make actual Splunk API calls
                # Implementation would depend on specific Splunk setup
                return self._execute_real_splunk_search(query, time_range, max_results)
                
        except Exception as e:
            self.logger.error(f"Splunk search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _metrics_tool(self, host: str = "*", metric: str = "latency") -> Dict[str, Any]:
        """Get network metrics for specific hosts"""
        try:
            self.logger.info(f"Getting Splunk metrics for host: {host}, metric: {metric}")
            
            if self.test_mode:
                return self._generate_metrics_data(host, metric)
            else:
                # In production, this would query actual Splunk metrics
                return self._get_real_splunk_metrics(host, metric)
                
        except Exception as e:
            self.logger.error(f"Metrics retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "host": host,
                "metric": metric
            }
    
    def _alerts_tool(self, severity: str = "all", time_range: str = "-4h") -> Dict[str, Any]:
        """Get network alerts from Splunk"""
        try:
            self.logger.info(f"Getting Splunk alerts: severity={severity}, time_range={time_range}")
            
            if self.test_mode:
                return self._generate_alerts_data(severity, time_range)
            else:
                # In production, this would query actual Splunk alerts
                return self._get_real_splunk_alerts(severity, time_range)
                
        except Exception as e:
            self.logger.error(f"Alert retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "severity": severity
            }
    
    def _generate_search_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Generate realistic search results for testing"""
        results = []
        
        # Simulate different types of network events
        event_types = [
            "network_latency", "packet_loss", "connection_timeout", 
            "bandwidth_exceeded", "dns_resolution"
        ]
        
        for i in range(min(max_results, random.randint(10, 50))):
            event_type = random.choice(event_types)
            
            result = {
                "_time": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
                "host": f"prod-app-{random.randint(1, 20):02d}",
                "source": f"/var/log/network/{event_type}.log",
                "sourcetype": "network_monitoring",
                "event_type": event_type,
                "_raw": self._generate_raw_log_entry(event_type)
            }
            
            # Add event-specific fields
            if event_type == "network_latency":
                result.update({
                    "avg_latency": random.uniform(50, 500),
                    "max_latency": random.uniform(500, 2000),
                    "destination": f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}"
                })
            elif event_type == "packet_loss":
                result.update({
                    "packet_loss_percent": random.uniform(0, 15),
                    "packets_sent": random.randint(1000, 10000),
                    "packets_received": random.randint(850, 9999)
                })
            
            results.append(result)
        
        return results
    
    def _generate_raw_log_entry(self, event_type: str) -> str:
        """Generate realistic raw log entries"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if event_type == "network_latency":
            return f"{timestamp} INFO NetworkMonitor: Latency check to destination completed - avg: {random.uniform(50, 500):.2f}ms"
        elif event_type == "packet_loss":
            return f"{timestamp} WARN NetworkMonitor: Packet loss detected - {random.uniform(0, 15):.2f}% loss over last 5 minutes"
        elif event_type == "connection_timeout":
            return f"{timestamp} ERROR NetworkMonitor: Connection timeout to service endpoint after {random.randint(10, 60)}s"
        elif event_type == "bandwidth_exceeded":
            return f"{timestamp} WARN NetworkMonitor: Bandwidth utilization exceeded threshold - current: {random.uniform(80, 100):.1f}%"
        else:  # dns_resolution
            return f"{timestamp} INFO NetworkMonitor: DNS resolution completed in {random.uniform(1, 50):.2f}ms"
    
    def _generate_metrics_data(self, host: str, metric: str) -> Dict[str, Any]:
        """Generate realistic metrics data for testing"""
        metrics_data = {
            "success": True,
            "host": host,
            "metric": metric,
            "timestamp": datetime.now().isoformat()
        }
        
        if metric == "latency":
            metrics_data.update({
                "value": random.uniform(50, 200),
                "unit": "ms",
                "threshold": 500,
                "status": "normal" if random.uniform(50, 200) < 300 else "warning"
            })
        elif metric == "packet_loss":
            loss_percent = random.uniform(0, 5)
            metrics_data.update({
                "value": loss_percent,
                "unit": "percent",
                "threshold": 2.0,
                "status": "normal" if loss_percent < 2.0 else "critical"
            })
        elif metric == "throughput":
            metrics_data.update({
                "value": random.uniform(100, 1000),
                "unit": "Mbps",
                "threshold": 800,
                "status": "normal"
            })
        
        return metrics_data
    
    def _generate_alerts_data(self, severity: str, time_range: str) -> Dict[str, Any]:
        """Generate realistic alerts data for testing"""
        alerts = []
        severities = ["critical", "high", "medium", "low"]
        
        # Generate 5-15 alerts
        for i in range(random.randint(5, 15)):
            alert_severity = random.choice(severities)
            
            alert = {
                "id": f"SPLUNK-ALERT-{i:04d}",
                "title": self._generate_alert_title(alert_severity),
                "severity": alert_severity,
                "status": random.choice(["active", "acknowledged", "resolved"]),
                "host_count": random.randint(1, 10),
                "duration": f"{random.randint(5, 120)}m",
                "first_seen": (datetime.now() - timedelta(hours=random.randint(1, 12))).isoformat(),
                "last_seen": datetime.now().isoformat(),
                "affected_hosts": [
                    f"prod-app-{j:02d}" for j in range(random.randint(1, 5))
                ],
                "search_query": self._generate_alert_search_query(alert_severity)
            }
            
            alerts.append(alert)
        
        # Filter by severity if not 'all'
        if severity != "all":
            alerts = [a for a in alerts if a["severity"] == severity]
        
        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts),
            "severity_filter": severity,
            "time_range": time_range
        }
    
    def _generate_alert_title(self, severity: str) -> str:
        """Generate realistic alert titles based on severity"""
        if severity == "critical":
            return random.choice([
                "Network connectivity completely lost to production subnet",
                "Packet loss exceeding 50% on critical path",
                "DNS resolution failures affecting multiple services"
            ])
        elif severity == "high":
            return random.choice([
                "High network latency detected (>1000ms)",
                "Significant packet loss (>10%) on main network path",
                "Connection timeouts increasing rapidly"
            ])
        elif severity == "medium":
            return random.choice([
                "Elevated network latency on subnet 10.0.x.0/24",
                "Intermittent packet loss detected",
                "Bandwidth utilization approaching threshold"
            ])
        else:  # low
            return random.choice([
                "Minor latency increase observed",
                "Occasional DNS resolution delays",
                "Network performance degradation trend"
            ])
    
    def _generate_alert_search_query(self, severity: str) -> str:
        """Generate the search query that triggered the alert"""
        if severity in ["critical", "high"]:
            return 'index=network_monitoring | where latency > 1000 OR packet_loss > 10 | stats count by host'
        else:
            return 'index=network_monitoring | where latency > 500 | stats avg(latency) by host | where avg(latency) > 300'
    
    # Placeholder methods for production implementation
    def _execute_real_splunk_search(self, query: str, time_range: str, max_results: int) -> Dict[str, Any]:
        """Execute real Splunk search - implement with actual Splunk SDK"""
        # This would use splunk-sdk or REST API calls
        raise NotImplementedError("Production Splunk integration not implemented")
    
    def _get_real_splunk_metrics(self, host: str, metric: str) -> Dict[str, Any]:
        """Get real Splunk metrics - implement with actual Splunk SDK"""
        raise NotImplementedError("Production Splunk integration not implemented")
    
    def _get_real_splunk_alerts(self, severity: str, time_range: str) -> Dict[str, Any]:
        """Get real Splunk alerts - implement with actual Splunk SDK"""
        raise NotImplementedError("Production Splunk integration not implemented")
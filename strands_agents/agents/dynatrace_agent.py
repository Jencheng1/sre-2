"""
Dynatrace Strands Agent for APM, MQ metrics, and performance monitoring
Replaces the Dynatrace MCP server with enhanced AWS Strands framework
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from base.base_agent import BaseStrandsAgent, StrandsToolFactory

class DynatraceStrandsAgent(BaseStrandsAgent):
    """Dynatrace APM and monitoring agent using AWS Strands framework"""
    
    def __init__(self, region: str = "us-east-1", test_mode: bool = True):
        super().__init__(
            agent_name="dynatrace",
            region=region,
            test_mode=test_mode
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a Dynatrace APM specialist agent focused on application performance monitoring, message queue analysis, and distributed tracing.

Your capabilities include:
1. Analyzing message queue (MQ) metrics including queue depth, processing rates, and error rates
2. Retrieving and analyzing APM traces for distributed applications
3. Monitoring application performance metrics and SLA compliance
4. Detecting and analyzing performance problems and anomalies
5. Providing insights on system dependencies and bottlenecks

You have access to tools for:
- dynatrace_mq_metrics: Get detailed message queue metrics and health status
- dynatrace_apm_traces: Retrieve distributed traces for performance analysis
- dynatrace_problems: Get detected problems, anomalies, and their root causes

When analyzing performance issues, always consider:
- Queue depth trends and consumer capacity
- Trace duration patterns and error rates
- Service dependencies and their impact
- SLA violations and business impact
- Historical performance baselines

Provide detailed technical analysis with actionable recommendations for performance optimization and issue resolution."""
    
    def _create_tools(self) -> List[Any]:
        """Create Dynatrace-specific tools"""
        return [
            StrandsToolFactory.create_metrics_tool(
                name="dynatrace_mq_metrics",
                description="Get message queue metrics including depth, rates, and consumer health",
                metrics_func=self._mq_metrics_tool,
                parameters={
                    "queue_name": {"type": "string", "description": "Name of the message queue to analyze", "default": "*"},
                    "time_range": {"type": "string", "description": "Time range for metrics (e.g., -30m, -1h)", "default": "-30m"},
                    "include_consumers": {"type": "boolean", "description": "Include consumer metrics", "default": True}
                }
            ),
            StrandsToolFactory.create_monitoring_tool(
                name="dynatrace_apm_traces",
                description="Retrieve and analyze distributed traces for performance monitoring",
                func=self._apm_traces_tool,
                parameters={
                    "service": {"type": "string", "description": "Service name to analyze traces for", "default": "*"},
                    "time_range": {"type": "string", "description": "Time range for traces", "default": "-1h"},
                    "error_traces_only": {"type": "boolean", "description": "Return only error traces", "default": False},
                    "min_duration": {"type": "integer", "description": "Minimum trace duration in ms", "default": 0}
                }
            ),
            StrandsToolFactory.create_monitoring_tool(
                name="dynatrace_problems",
                description="Get detected problems, anomalies, and root cause analysis",
                func=self._problems_tool,
                parameters={
                    "status": {"type": "string", "description": "Problem status (OPEN, RESOLVED, ALL)", "default": "OPEN"},
                    "impact": {"type": "string", "description": "Impact level filter (APPLICATION, SERVICE, INFRASTRUCTURE)", "default": "ALL"},
                    "time_range": {"type": "string", "description": "Time range for problems", "default": "-24h"}
                }
            )
        ]
    
    def _get_specific_capabilities(self) -> List[str]:
        return [
            "Message Queue monitoring and analysis",
            "Distributed tracing and APM",
            "Performance anomaly detection",
            "Service dependency mapping",
            "SLA monitoring and alerting",
            "Root cause analysis",
            "Consumer lag analysis",
            "Error rate correlation",
            "Throughput optimization"
        ]
    
    def _mq_metrics_tool(self, queue_name: str = "*", time_range: str = "-30m", include_consumers: bool = True) -> Dict[str, Any]:
        """Get message queue metrics from Dynatrace"""
        try:
            self.logger.info(f"Getting MQ metrics for queue: {queue_name}")
            
            if self.test_mode:
                return self._generate_mq_metrics(queue_name, time_range, include_consumers)
            else:
                return self._get_real_dynatrace_mq_metrics(queue_name, time_range, include_consumers)
                
        except Exception as e:
            self.logger.error(f"MQ metrics retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "queue_name": queue_name
            }
    
    def _apm_traces_tool(self, service: str = "*", time_range: str = "-1h", error_traces_only: bool = False, min_duration: int = 0) -> Dict[str, Any]:
        """Get APM traces from Dynatrace"""
        try:
            self.logger.info(f"Getting APM traces for service: {service}")
            
            if self.test_mode:
                return self._generate_apm_traces(service, time_range, error_traces_only, min_duration)
            else:
                return self._get_real_dynatrace_traces(service, time_range, error_traces_only, min_duration)
                
        except Exception as e:
            self.logger.error(f"APM traces retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "service": service
            }
    
    def _problems_tool(self, status: str = "OPEN", impact: str = "ALL", time_range: str = "-24h") -> Dict[str, Any]:
        """Get detected problems from Dynatrace"""
        try:
            self.logger.info(f"Getting Dynatrace problems: status={status}, impact={impact}")
            
            if self.test_mode:
                return self._generate_problems_data(status, impact, time_range)
            else:
                return self._get_real_dynatrace_problems(status, impact, time_range)
                
        except Exception as e:
            self.logger.error(f"Problems retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": status
            }
    
    def _generate_mq_metrics(self, queue_name: str, time_range: str, include_consumers: bool) -> Dict[str, Any]:
        """Generate realistic MQ metrics for testing"""
        # Generate base queue metrics
        base_depth = random.randint(100, 2000)
        enqueue_rate = random.uniform(20, 100)
        dequeue_rate = random.uniform(15, 95)
        
        metrics = {
            "success": True,
            "queue_name": queue_name if queue_name != "*" else "OrderProcessingQueue",
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "queue_metrics": {
                "depth": base_depth + random.randint(-50, 200),
                "enqueue_rate": enqueue_rate,
                "dequeue_rate": dequeue_rate,
                "message_rate": enqueue_rate + random.uniform(-10, 10),
                "error_rate": random.uniform(0, 5),
                "avg_processing_time": random.uniform(50, 500),
                "dlq_messages": random.randint(0, 50),
                "expired_messages": random.randint(0, 10),
                "throughput_mbps": random.uniform(10, 100)
            },
            "health_status": "healthy" if base_depth < 1500 and random.uniform(0, 5) < 2 else "warning",
            "sla_compliance": {
                "processing_time_sla": random.uniform(90, 99.9),
                "availability_sla": random.uniform(99, 100),
                "error_rate_sla": random.uniform(95, 100)
            }
        }
        
        # Add consumer information if requested
        if include_consumers:
            consumers = []
            consumer_count = random.randint(2, 8)
            
            for i in range(consumer_count):
                consumer = {
                    "consumer_id": f"consumer-{i+1:02d}",
                    "status": random.choice(["active", "active", "active", "idle", "error"]),
                    "messages_processed": random.randint(100, 1000),
                    "avg_processing_time": random.uniform(30, 200),
                    "error_count": random.randint(0, 10),
                    "last_activity": (datetime.now() - timedelta(minutes=random.randint(0, 30))).isoformat()
                }
                consumers.append(consumer)
            
            metrics["consumers"] = {
                "total_consumers": consumer_count,
                "active_consumers": len([c for c in consumers if c["status"] == "active"]),
                "consumer_details": consumers
            }
        
        return metrics
    
    def _generate_apm_traces(self, service: str, time_range: str, error_traces_only: bool, min_duration: int) -> Dict[str, Any]:
        """Generate realistic APM traces for testing"""
        traces = []
        service_name = service if service != "*" else "payment-service"
        
        # Generate 10-50 traces
        trace_count = random.randint(10, 50)
        
        for i in range(trace_count):
            duration = random.uniform(100, 5000)
            status = random.choice(["OK", "OK", "OK", "OK", "ERROR", "TIMEOUT"])
            
            # Skip if filtering for errors only and this isn't an error
            if error_traces_only and status == "OK":
                continue
            
            # Skip if below minimum duration
            if duration < min_duration:
                continue
            
            trace = {
                "trace_id": f"trace-{i:06d}",
                "service": service_name,
                "operation": random.choice([
                    "POST /api/payment/process",
                    "GET /api/payment/status", 
                    "PUT /api/order/update",
                    "DELETE /api/session/cleanup",
                    "GET /api/user/profile"
                ]),
                "duration_ms": round(duration, 2),
                "status": status,
                "spans_count": random.randint(3, 25),
                "start_time": (datetime.now() - timedelta(minutes=i*2)).isoformat(),
                "end_time": (datetime.now() - timedelta(minutes=i*2) + timedelta(milliseconds=duration)).isoformat(),
                "spans": self._generate_trace_spans(random.randint(3, 25), duration)
            }
            
            # Add error details for failed traces
            if status in ["ERROR", "TIMEOUT"]:
                trace["error_details"] = {
                    "error_type": random.choice(["ConnectionTimeout", "DatabaseError", "ValidationError", "ServiceUnavailable"]),
                    "error_message": "Operation failed due to downstream service error",
                    "stack_trace": "com.example.service.PaymentService.processPayment(PaymentService.java:142)"
                }
            
            traces.append(trace)
        
        # Calculate summary statistics
        if traces:
            durations = [t["duration_ms"] for t in traces]
            error_count = len([t for t in traces if t["status"] != "OK"])
            
            summary = {
                "total_traces": len(traces),
                "avg_duration_ms": round(sum(durations) / len(durations), 2),
                "p95_duration_ms": round(sorted(durations)[int(len(durations) * 0.95)], 2),
                "p99_duration_ms": round(sorted(durations)[int(len(durations) * 0.99)], 2),
                "error_rate_percent": round((error_count / len(traces)) * 100, 2),
                "throughput_rps": len(traces) / (60 if "-1h" in time_range else 30)  # Rough estimate
            }
        else:
            summary = {"message": "No traces found matching criteria"}
        
        return {
            "success": True,
            "service": service_name,
            "time_range": time_range,
            "filters": {
                "error_traces_only": error_traces_only,
                "min_duration": min_duration
            },
            "traces": traces,
            "summary": summary
        }
    
    def _generate_trace_spans(self, span_count: int, total_duration: float) -> List[Dict[str, Any]]:
        """Generate realistic spans for a trace"""
        spans = []
        remaining_duration = total_duration
        
        span_types = [
            ("database.query", "Database Query"),
            ("http.request", "HTTP Request"),
            ("queue.consume", "Message Queue Operation"),
            ("cache.get", "Cache Lookup"),
            ("service.call", "Service Call")
        ]
        
        for i in range(span_count):
            span_type, span_name = random.choice(span_types)
            # Distribute duration across spans
            max_span_duration = min(remaining_duration * 0.8, remaining_duration / (span_count - i))
            span_duration = random.uniform(1, max_span_duration) if max_span_duration > 1 else 1
            remaining_duration -= span_duration
            
            span = {
                "span_id": f"span-{i:04d}",
                "span_type": span_type,
                "operation_name": span_name,
                "duration_ms": round(span_duration, 2),
                "tags": {
                    "component": random.choice(["database", "http-client", "mq-client", "cache"]),
                    "span.kind": random.choice(["client", "server", "internal"])
                }
            }
            
            # Add specific tags based on span type
            if span_type == "database.query":
                span["tags"]["db.statement"] = "SELECT * FROM orders WHERE user_id = ?"
                span["tags"]["db.type"] = "postgresql"
            elif span_type == "http.request":
                span["tags"]["http.method"] = "GET"
                span["tags"]["http.status_code"] = random.choice([200, 200, 200, 404, 500])
            
            spans.append(span)
        
        return spans
    
    def _generate_problems_data(self, status: str, impact: str, time_range: str) -> Dict[str, Any]:
        """Generate realistic problems/anomalies data"""
        problems = []
        
        problem_templates = [
            {
                "title": "High MQ backlog detected in OrderProcessingQueue",
                "severity": "ERROR",
                "impact": "APPLICATION",
                "problem_type": "PERFORMANCE",
                "root_cause": "Consumer lag exceeding threshold - queue depth growing exponentially"
            },
            {
                "title": "Database connection pool exhaustion",
                "severity": "PERFORMANCE", 
                "impact": "SERVICE",
                "problem_type": "RESOURCE",
                "root_cause": "Maximum database connections reached - long-running queries blocking pool"
            },
            {
                "title": "Memory leak suspected in payment service",
                "severity": "PERFORMANCE",
                "impact": "SERVICE",
                "problem_type": "RESOURCE",
                "root_cause": "Memory usage continuously increasing - potential memory leak in payment processing"
            },
            {
                "title": "CPU saturation on application servers",
                "severity": "AVAILABILITY",
                "impact": "INFRASTRUCTURE", 
                "problem_type": "RESOURCE",
                "root_cause": "CPU utilization consistently above 90% - inadequate capacity for current load"
            },
            {
                "title": "Network packet loss affecting microservices",
                "severity": "ERROR",
                "impact": "APPLICATION",
                "problem_type": "CONNECTIVITY",
                "root_cause": "Network packet loss between services causing timeout and retry storms"
            }
        ]
        
        # Generate 3-8 problems
        for i in range(random.randint(3, 8)):
            template = random.choice(problem_templates)
            
            problem = {
                "id": f"DYNATRACE-PROB-{i:06d}",
                "title": template["title"],
                "status": random.choice(["OPEN", "OPEN", "ACKNOWLEDGED", "RESOLVED"]) if status == "ALL" else status,
                "severity": template["severity"],
                "impact": template["impact"],
                "problem_type": template["problem_type"],
                "affected_entities": random.randint(1, 15),
                "start_time": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
                "detection_time": (datetime.now() - timedelta(hours=random.randint(0, 24))).isoformat(),
                "root_cause": template["root_cause"],
                "affected_services": [
                    f"service-{j}" for j in range(random.randint(1, 5))
                ],
                "metrics": {
                    "response_time_increase": f"{random.uniform(150, 500):.1f}%",
                    "error_rate_increase": f"{random.uniform(200, 1000):.1f}%",
                    "throughput_decrease": f"{random.uniform(20, 80):.1f}%"
                }
            }
            
            # Add resolution details for resolved problems
            if problem["status"] == "RESOLVED":
                problem["resolution"] = {
                    "resolved_time": datetime.now().isoformat(),
                    "resolution_method": random.choice([
                        "Automatic scaling triggered",
                        "Manual intervention - service restart",
                        "Configuration update deployed",
                        "Infrastructure capacity increased"
                    ]),
                    "time_to_resolution": f"{random.randint(15, 120)} minutes"
                }
            
            problems.append(problem)
        
        # Filter by impact if not 'ALL'
        if impact != "ALL":
            problems = [p for p in problems if p["impact"] == impact]
        
        # Filter by status if not 'ALL'  
        if status != "ALL":
            problems = [p for p in problems if p["status"] == status]
        
        return {
            "success": True,
            "problems": problems,
            "count": len(problems),
            "filters": {
                "status": status,
                "impact": impact,
                "time_range": time_range
            },
            "summary": {
                "critical_problems": len([p for p in problems if p["severity"] == "ERROR"]),
                "performance_problems": len([p for p in problems if p["severity"] == "PERFORMANCE"]),
                "availability_problems": len([p for p in problems if p["severity"] == "AVAILABILITY"])
            }
        }
    
    # Placeholder methods for production implementation
    def _get_real_dynatrace_mq_metrics(self, queue_name: str, time_range: str, include_consumers: bool) -> Dict[str, Any]:
        """Get real Dynatrace MQ metrics - implement with actual Dynatrace API"""
        raise NotImplementedError("Production Dynatrace MQ integration not implemented")
    
    def _get_real_dynatrace_traces(self, service: str, time_range: str, error_traces_only: bool, min_duration: int) -> Dict[str, Any]:
        """Get real Dynatrace traces - implement with actual Dynatrace API"""
        raise NotImplementedError("Production Dynatrace traces integration not implemented")
    
    def _get_real_dynatrace_problems(self, status: str, impact: str, time_range: str) -> Dict[str, Any]:
        """Get real Dynatrace problems - implement with actual Dynatrace API"""
        raise NotImplementedError("Production Dynatrace problems integration not implemented")
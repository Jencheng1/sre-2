"""
Dynatrace MCP Server for MQ metrics and APM
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, request, jsonify
import threading

class DynatraceMCPServer:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/dynatrace/metrics', methods=['GET'])
        def metrics_endpoint():
            metric_type = request.args.get('type', 'mq')
            entity = request.args.get('entity', '')
            
            if metric_type == 'mq':
                return jsonify(self.get_mq_metrics(entity, request.args.get('time_range', '-30m')))
            else:
                return jsonify(self.get_apm_metrics(entity))
                
        @self.app.route('/dynatrace/traces', methods=['GET'])
        def traces_endpoint():
            service = request.args.get('service', '')
            time_range = request.args.get('time_range', '-1h')
            
            return jsonify(self.get_apm_traces(service, time_range))
            
        @self.app.route('/dynatrace/problems', methods=['GET'])
        def problems_endpoint():
            status = request.args.get('status', 'OPEN')
            
            return jsonify(self.get_problems(status))
    
    def get_mq_metrics(self, queue_name: str, time_range: str) -> Dict[str, Any]:
        """Get MQ metrics from Dynatrace"""
        if self.test_mode:
            # Generate realistic MQ metrics
            base_depth = random.randint(100, 1000)
            
            return {
                "queue_name": queue_name or "OrderProcessingQueue",
                "queue_depth": base_depth + random.randint(-50, 200),
                "message_rate": random.uniform(10, 100),
                "error_rate": random.uniform(0, 5),
                "avg_processing_time": random.uniform(50, 500),
                "consumer_count": random.randint(1, 10),
                "dlq_messages": random.randint(0, 50),
                "metrics": {
                    "enqueue_rate": random.uniform(20, 80),
                    "dequeue_rate": random.uniform(15, 75),
                    "expired_messages": random.randint(0, 10)
                },
                "timestamp": datetime.now().isoformat(),
                "time_range": time_range
            }
    
    def get_apm_traces(self, service: str, time_range: str) -> Dict[str, Any]:
        """Get APM traces"""
        if self.test_mode:
            traces = []
            
            for i in range(10):
                traces.append({
                    "trace_id": f"trace-{i:04d}",
                    "service": service or "payment-service",
                    "operation": random.choice(["POST /payment", "GET /status", "PUT /order"]),
                    "duration": random.uniform(100, 5000),
                    "status": random.choice(["OK", "OK", "OK", "ERROR"]),
                    "spans": random.randint(5, 20),
                    "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat()
                })
            
            return {
                "service": service,
                "time_range": time_range,
                "traces": traces,
                "total": len(traces)
            }
    
    def get_apm_metrics(self, service: str) -> Dict[str, Any]:
        """Get APM metrics for a service"""
        if self.test_mode:
            return {
                "service": service or "payment-service",
                "response_time": {
                    "avg": random.uniform(200, 500),
                    "p95": random.uniform(800, 1500),
                    "p99": random.uniform(1500, 3000)
                },
                "throughput": random.uniform(100, 1000),
                "error_rate": random.uniform(0, 5),
                "apdex": random.uniform(0.7, 0.95),
                "dependencies": [
                    {
                        "name": "database",
                        "calls": random.randint(1000, 5000),
                        "avg_duration": random.uniform(10, 50)
                    },
                    {
                        "name": "message-queue",
                        "calls": random.randint(500, 2000),
                        "avg_duration": random.uniform(20, 100)
                    }
                ]
            }
    
    def get_problems(self, status: str) -> List[Dict[str, Any]]:
        """Get detected problems/anomalies"""
        if self.test_mode:
            problems = []
            
            problem_types = [
                "High MQ backlog detected",
                "Slow database queries",
                "Memory leak suspected",
                "CPU saturation",
                "Network packet loss"
            ]
            
            for i in range(5):
                problems.append({
                    "id": f"PROB-{i:04d}",
                    "title": random.choice(problem_types),
                    "status": status,
                    "impact": random.choice(["APPLICATION", "SERVICE", "INFRASTRUCTURE"]),
                    "severity": random.choice(["ERROR", "PERFORMANCE", "AVAILABILITY"]),
                    "affected_entities": random.randint(1, 10),
                    "start_time": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                    "root_cause": "Under investigation"
                })
            
            return problems
    
    def start_server(self, port=8081):
        """Start the MCP server"""
        self.app.run(host='0.0.0.0', port=port, debug=False)


def start_dynatrace_mcp_server(port=8081, test_mode=True):
    """Start Dynatrace MCP server in a separate thread"""
    server = DynatraceMCPServer(test_mode=test_mode)
    thread = threading.Thread(target=server.start_server, args=(port,))
    thread.daemon = True
    thread.start()
    return server
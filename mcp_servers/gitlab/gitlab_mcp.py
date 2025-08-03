"""
GitLab MCP Server for source code analysis
"""

import json
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, request, jsonify
import threading

class GitLabMCPServer:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.app = Flask(__name__)
        self.repositories = []
        self.commits = []
        self.merge_requests = []
        self.code_files = []
        self.setup_routes()
        self.init_test_data()
        
    def init_test_data(self):
        """Initialize test repositories and code"""
        if self.test_mode:
            # Create test repositories
            repos = [
                {"id": "sre/monitoring", "name": "monitoring", "namespace": "sre"},
                {"id": "sre/infrastructure", "name": "infrastructure", "namespace": "sre"},
                {"id": "backend/payment-service", "name": "payment-service", "namespace": "backend"},
                {"id": "backend/order-service", "name": "order-service", "namespace": "backend"}
            ]
            
            # Create test code files
            code_samples = [
                {
                    "file_path": "src/monitors/NetworkLatencyMonitor.java",
                    "content": """
package com.sre.monitors;

import java.time.Duration;
import java.util.List;

public class NetworkLatencyMonitor {
    private static final Duration THRESHOLD = Duration.ofMillis(500);
    private final MetricsCollector metricsCollector;
    
    public void checkLatency(String endpoint) {
        long startTime = System.currentTimeMillis();
        Response response = httpClient.get(endpoint);
        long latency = System.currentTimeMillis() - startTime;
        
        if (latency > THRESHOLD.toMillis()) {
            alertManager.sendAlert(new LatencyAlert(endpoint, latency));
        }
        
        metricsCollector.record("network.latency", latency, Tags.of("endpoint", endpoint));
    }
}
                    """,
                    "project_id": "sre/monitoring"
                },
                {
                    "file_path": "src/services/QueueProcessor.py",
                    "content": """
import asyncio
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Message:
    id: str
    payload: Dict
    timestamp: datetime

class QueueProcessor:
    def __init__(self, queue_name: str, max_batch_size: int = 10):
        self.queue_name = queue_name
        self.max_batch_size = max_batch_size
        self.mq_client = MQClient()
        
    async def process_batch(self) -> List[Message]:
        messages = await self.mq_client.receive_messages(
            queue_name=self.queue_name,
            max_messages=self.max_batch_size
        )
        
        for message in messages:
            try:
                await self.process_message(message)
                await self.mq_client.delete_message(message.id)
            except Exception as e:
                logger.error(f"Failed to process message {message.id}: {e}")
                await self.send_to_dlq(message)
    
    async def send_to_dlq(self, message: Message):
        dlq_name = f"{self.queue_name}_dlq"
        await self.mq_client.send_message(dlq_name, message)
                    """,
                    "project_id": "backend/order-service"
                },
                {
                    "file_path": "terraform/modules/network/main.tf",
                    "content": """
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support = true
  
  tags = {
    Name = "${var.environment}-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "private" {
  count = length(var.availability_zones)
  
  vpc_id = aws_vpc.main.id
  cidr_block = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]
  
  tags = {
    Name = "${var.environment}-private-${count.index}"
    Type = "Private"
  }
}

resource "aws_route53_zone" "private" {
  name = "${var.environment}.internal"
  
  vpc {
    vpc_id = aws_vpc.main.id
  }
}
                    """,
                    "project_id": "sre/infrastructure"
                }
            ]
            
            # Create commits
            for i in range(20):
                self.commits.append({
                    "sha": hashlib.sha1(f"commit-{i}".encode()).hexdigest(),
                    "message": random.choice([
                        "Fix: Resolve high latency issue in network monitor",
                        "Feat: Add circuit breaker to payment service",
                        "Refactor: Optimize MQ batch processing",
                        "Fix: Memory leak in connection pool",
                        "Chore: Update monitoring thresholds",
                        "Fix: DNS resolution timeout",
                        "Feat: Add retry logic for failed requests"
                    ]),
                    "author": random.choice(["john.doe", "jane.smith", "bob.wilson"]),
                    "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    "project_id": random.choice([r["id"] for r in repos]),
                    "files_changed": random.randint(1, 10)
                })
            
            # Create merge requests
            for i in range(10):
                self.merge_requests.append({
                    "iid": i + 1,
                    "title": f"MR-{i}: {random.choice(['Fix network latency', 'Add monitoring', 'Update configs'])}",
                    "state": random.choice(["opened", "merged", "closed"]),
                    "source_branch": f"feature/fix-{i}",
                    "target_branch": "main",
                    "project_id": random.choice([r["id"] for r in repos])
                })
            
            self.repositories = repos
            self.code_files = code_samples
        
    def setup_routes(self):
        @self.app.route('/gitlab/search', methods=['GET'])
        def search_endpoint():
            query = request.args.get('query', '')
            project_id = request.args.get('project_id', '')
            
            return jsonify(self.search_code(query, project_id))
            
        @self.app.route('/gitlab/repos', methods=['GET'])
        def repos_endpoint():
            namespace = request.args.get('namespace', '')
            
            return jsonify(self.get_repositories(namespace))
            
        @self.app.route('/gitlab/commits', methods=['GET'])
        def commits_endpoint():
            project_id = request.args.get('project_id', '')
            since = request.args.get('since', '')
            
            return jsonify(self.get_recent_commits(project_id, since))
            
        @self.app.route('/gitlab/merge_requests', methods=['GET'])
        def merge_requests_endpoint():
            project_id = request.args.get('project_id', '')
            state = request.args.get('state', '')
            
            return jsonify(self.get_merge_requests(project_id, state))
    
    def search_code(self, query: str, project_id: str) -> List[Dict[str, Any]]:
        """Search code in repositories"""
        if self.test_mode:
            results = []
            query_lower = query.lower()
            
            for file in self.code_files:
                if (not project_id or file['project_id'] == project_id) and \
                   query_lower in file['content'].lower():
                    
                    # Find matching lines
                    lines = file['content'].split('\n')
                    matching_lines = []
                    
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            matching_lines.append({
                                "line_number": i + 1,
                                "content": line.strip()
                            })
                    
                    results.append({
                        "file_path": file['file_path'],
                        "project_id": file['project_id'],
                        "content": file['content'],
                        "matching_lines": matching_lines[:5],  # First 5 matches
                        "total_matches": len(matching_lines)
                    })
            
            return results
    
    def get_repositories(self, namespace: str) -> List[Dict[str, Any]]:
        """Get repositories"""
        if self.test_mode:
            if namespace:
                return [r for r in self.repositories if r['namespace'] == namespace]
            return self.repositories
    
    def get_recent_commits(self, project_id: str, since: str = None) -> List[Dict[str, Any]]:
        """Get recent commits"""
        if self.test_mode:
            results = self.commits.copy()
            
            if project_id:
                results = [c for c in results if c['project_id'] == project_id]
            
            if since:
                try:
                    since_date = datetime.fromisoformat(since.replace('Z', '+00:00'))
                    results = [c for c in results 
                             if datetime.fromisoformat(c['timestamp']) > since_date]
                except:
                    pass
            
            # Sort by timestamp descending
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            return results[:20]  # Return most recent 20
    
    def get_merge_requests(self, project_id: str, state: str) -> List[Dict[str, Any]]:
        """Get merge requests"""
        if self.test_mode:
            results = self.merge_requests.copy()
            
            if project_id:
                results = [mr for mr in results if mr['project_id'] == project_id]
            
            if state:
                results = [mr for mr in results if mr['state'] == state]
            
            return results
    
    def start_server(self, port=8084):
        """Start the MCP server"""
        self.app.run(host='0.0.0.0', port=port, debug=False)


def start_gitlab_mcp_server(port=8084, test_mode=True):
    """Start GitLab MCP server in a separate thread"""
    server = GitLabMCPServer(test_mode=test_mode)
    thread = threading.Thread(target=server.start_server, args=(port,))
    thread.daemon = True
    thread.start()
    return server
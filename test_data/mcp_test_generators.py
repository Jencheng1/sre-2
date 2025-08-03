"""
Test data generators for MCP services
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

class TestDataGenerators:
    """Generate test data for each MCP service"""
    
    def __init__(self):
        self.hosts = [f"prod-app-{i:02d}" for i in range(10)]
        self.services = ["payment-service", "order-service", "user-service", "inventory-service"]
        self.queues = ["OrderProcessingQueue", "PaymentQueue", "NotificationQueue", "InventoryQueue"]
        
    def generate_splunk_data(self, data_type: str, count: int = 10) -> List[Dict[str, Any]]:
        """Generate Splunk test data"""
        data = []
        
        if data_type == "network_latency":
            for i in range(count):
                data.append({
                    "host": random.choice(self.hosts),
                    "latency": random.uniform(50, 500),
                    "packet_loss": random.uniform(0, 5),
                    "jitter": random.uniform(1, 50),
                    "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
                    "interface": random.choice(["eth0", "eth1"]),
                    "destination": f"10.0.{random.randint(1,254)}.{random.randint(1,254)}"
                })
        
        elif data_type == "security_events":
            event_types = ["Failed Login", "Port Scan", "Suspicious Traffic", "Policy Violation"]
            for i in range(count):
                data.append({
                    "event_type": random.choice(event_types),
                    "source_ip": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
                    "destination_ip": f"10.0.{random.randint(1,254)}.{random.randint(1,254)}",
                    "severity": random.choice(["low", "medium", "high", "critical"]),
                    "timestamp": (datetime.now() - timedelta(minutes=i*10)).isoformat(),
                    "action": random.choice(["blocked", "allowed", "logged"])
                })
        
        elif data_type == "application_logs":
            log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
            for i in range(count):
                data.append({
                    "service": random.choice(self.services),
                    "level": random.choice(log_levels),
                    "message": self._generate_log_message(),
                    "timestamp": (datetime.now() - timedelta(seconds=i*30)).isoformat(),
                    "request_id": str(uuid.uuid4()),
                    "duration_ms": random.randint(10, 5000)
                })
        
        return data
    
    def generate_dynatrace_data(self, data_type: str, count: int = 5) -> List[Dict[str, Any]]:
        """Generate Dynatrace test data"""
        data = []
        
        if data_type == "mq_metrics":
            for i in range(count):
                queue_name = random.choice(self.queues)
                data.append({
                    "queue_name": queue_name,
                    "queue_depth": random.randint(0, 5000),
                    "enqueue_rate": random.uniform(10, 100),
                    "dequeue_rate": random.uniform(8, 95),
                    "message_age_avg": random.uniform(100, 5000),
                    "message_age_max": random.uniform(5000, 20000),
                    "consumer_count": random.randint(1, 10),
                    "error_count": random.randint(0, 50),
                    "dlq_count": random.randint(0, 100),
                    "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat()
                })
        
        elif data_type == "apm_traces":
            operations = ["GET /api/orders", "POST /api/payment", "PUT /api/inventory", "DELETE /api/cart"]
            for i in range(count):
                data.append({
                    "trace_id": str(uuid.uuid4()),
                    "service": random.choice(self.services),
                    "operation": random.choice(operations),
                    "duration_ms": random.uniform(50, 5000),
                    "status_code": random.choice([200, 200, 200, 400, 500]),
                    "span_count": random.randint(3, 20),
                    "error": random.choice([False, False, False, True]),
                    "timestamp": (datetime.now() - timedelta(minutes=i*2)).isoformat()
                })
        
        elif data_type == "problems":
            problem_types = [
                "High response time",
                "Increased error rate", 
                "Memory leak detected",
                "CPU spike",
                "Database connection pool exhausted"
            ]
            for i in range(count):
                data.append({
                    "problem_id": f"PROB-{i:04d}",
                    "title": random.choice(problem_types),
                    "impact_level": random.choice(["SERVICE", "APPLICATION", "INFRASTRUCTURE"]),
                    "severity": random.choice(["PERFORMANCE", "ERROR", "AVAILABILITY"]),
                    "affected_entities": random.randint(1, 20),
                    "status": random.choice(["OPEN", "OPEN", "RESOLVED"]),
                    "start_time": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
                    "root_cause": "Under investigation"
                })
        
        return data
    
    def generate_servicenow_data(self, data_type: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate ServiceNow test data"""
        data = []
        
        if data_type == "incidents":
            categories = ["Network", "Hardware", "Software", "Database", "Security"]
            descriptions = [
                "Users reporting slow response times",
                "Database connection timeouts",
                "Network connectivity issues",
                "Application crashes intermittently",
                "Security scan detected vulnerabilities"
            ]
            
            for i in range(count):
                data.append({
                    "sys_id": str(uuid.uuid4()),
                    "number": f"INC{random.randint(1000000, 9999999)}",
                    "short_description": random.choice(descriptions),
                    "category": random.choice(categories),
                    "priority": random.choice(["1", "2", "3", "4"]),
                    "state": random.choice(["New", "In Progress", "Resolved"]),
                    "assignment_group": "SRE Team",
                    "created_on": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    "updated_on": (datetime.now() - timedelta(hours=random.randint(0, 24))).isoformat()
                })
        
        elif data_type == "changes":
            change_types = ["Standard", "Normal", "Emergency"]
            descriptions = [
                "Update load balancer configuration",
                "Deploy new application version",
                "Database schema migration",
                "Security patch installation",
                "Network firewall rule update"
            ]
            
            for i in range(count):
                data.append({
                    "sys_id": str(uuid.uuid4()),
                    "number": f"CHG{random.randint(1000000, 9999999)}",
                    "short_description": random.choice(descriptions),
                    "type": random.choice(change_types),
                    "risk": random.choice(["Low", "Medium", "High"]),
                    "state": random.choice(["Draft", "Scheduled", "Implement", "Review"]),
                    "start_date": (datetime.now() + timedelta(days=random.randint(1, 14))).isoformat(),
                    "end_date": (datetime.now() + timedelta(days=random.randint(15, 21))).isoformat()
                })
        
        elif data_type == "cmdb":
            ci_types = ["Server", "Application", "Database", "Network Device", "Storage"]
            for i in range(count):
                data.append({
                    "sys_id": str(uuid.uuid4()),
                    "name": f"{random.choice(['web', 'app', 'db', 'cache'])}-server-{i:02d}",
                    "ci_class": random.choice(ci_types),
                    "status": random.choice(["Operational", "Maintenance", "Retired"]),
                    "environment": random.choice(["Production", "Staging", "Development"]),
                    "location": random.choice(["us-east-1a", "us-east-1b", "us-west-2a"]),
                    "ip_address": f"10.0.{random.randint(1,254)}.{random.randint(1,254)}"
                })
        
        return data
    
    def generate_confluence_data(self, data_type: str, count: int = 5) -> List[Dict[str, Any]]:
        """Generate Confluence test data"""
        data = []
        
        kb_articles = [
            {
                "title": "Network Latency Troubleshooting Guide",
                "content": "Steps to diagnose and resolve network latency issues...",
                "tags": ["network", "latency", "troubleshooting"]
            },
            {
                "title": "Database Performance Tuning Best Practices",
                "content": "Optimize database queries and indexing strategies...",
                "tags": ["database", "performance", "tuning"]
            },
            {
                "title": "MQ Dead Letter Queue Handling",
                "content": "How to handle messages in dead letter queues...",
                "tags": ["mq", "dlq", "messaging"]
            },
            {
                "title": "Incident Response Runbook",
                "content": "Standard operating procedures for incident response...",
                "tags": ["incident", "runbook", "sre"]
            },
            {
                "title": "AWS Service Outage Procedures",
                "content": "Steps to take during AWS service disruptions...",
                "tags": ["aws", "outage", "disaster-recovery"]
            }
        ]
        
        for i in range(min(count, len(kb_articles))):
            article = kb_articles[i]
            data.append({
                "id": f"kb-{i:04d}",
                "title": article["title"],
                "content": article["content"],
                "excerpt": article["content"][:100] + "...",
                "space_key": "SRE",
                "url": f"https://confluence.example.com/display/SRE/{article['title'].replace(' ', '+')}",
                "author": random.choice(["john.doe", "jane.smith", "bob.wilson"]),
                "created": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                "updated": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "labels": article["tags"],
                "views": random.randint(100, 5000)
            })
        
        return data
    
    def generate_gitlab_data(self, data_type: str, count: int = 5) -> List[Dict[str, Any]]:
        """Generate GitLab test data"""
        data = []
        
        if data_type == "commits":
            commit_messages = [
                "Fix: Resolve memory leak in connection pool",
                "Feat: Add circuit breaker to payment service",
                "Refactor: Optimize database query performance",
                "Fix: Handle edge case in error logging",
                "Chore: Update dependencies to latest versions",
                "Fix: Correct race condition in cache update"
            ]
            
            authors = ["john.doe@example.com", "jane.smith@example.com", "bob.wilson@example.com"]
            
            for i in range(count):
                data.append({
                    "sha": f"{random.randint(1000000, 9999999):07x}",
                    "message": random.choice(commit_messages),
                    "author_name": random.choice(["John Doe", "Jane Smith", "Bob Wilson"]),
                    "author_email": random.choice(authors),
                    "created_at": (datetime.now() - timedelta(hours=i*4)).isoformat(),
                    "project_id": random.choice(["backend/payment-service", "backend/order-service"]),
                    "stats": {
                        "additions": random.randint(10, 200),
                        "deletions": random.randint(5, 100),
                        "total": random.randint(15, 300)
                    }
                })
        
        elif data_type == "merge_requests":
            titles = [
                "Add retry logic for external API calls",
                "Implement health check endpoint",
                "Fix database connection pooling",
                "Update monitoring thresholds",
                "Add request validation middleware"
            ]
            
            for i in range(count):
                data.append({
                    "iid": i + 1,
                    "title": random.choice(titles),
                    "state": random.choice(["opened", "merged", "closed"]),
                    "source_branch": f"feature/fix-{i}",
                    "target_branch": "main",
                    "author": random.choice(["John Doe", "Jane Smith", "Bob Wilson"]),
                    "created_at": (datetime.now() - timedelta(days=random.randint(0, 14))).isoformat(),
                    "updated_at": (datetime.now() - timedelta(hours=random.randint(0, 48))).isoformat()
                })
        
        return data
    
    def _generate_log_message(self) -> str:
        """Generate realistic log messages"""
        messages = [
            "Request processed successfully",
            "Database query took longer than expected",
            "Cache miss for key: user_preferences",
            "Connection pool size adjusted",
            "Rate limit exceeded for API endpoint",
            "Background job completed",
            "Health check passed",
            "Configuration reloaded",
            "Metric published to monitoring system"
        ]
        return random.choice(messages)
    
    def generate_incident_scenario(self) -> Dict[str, Any]:
        """Generate a complete incident scenario with data from all services"""
        incident_types = ["network_latency", "service_outage", "performance_degradation", "security_incident"]
        incident_type = random.choice(incident_types)
        
        scenario = {
            "incident": {
                "id": f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "type": incident_type,
                "service": random.choice(self.services),
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "start_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "symptoms": self._generate_symptoms(incident_type)
            },
            "splunk_data": self.generate_splunk_data("network_latency", 10),
            "dynatrace_data": {
                "mq_metrics": self.generate_dynatrace_data("mq_metrics", 5),
                "problems": self.generate_dynatrace_data("problems", 3)
            },
            "servicenow_data": {
                "incidents": self.generate_servicenow_data("incidents", 3),
                "changes": self.generate_servicenow_data("changes", 2)
            },
            "confluence_data": self.generate_confluence_data("kb_articles", 3),
            "gitlab_data": {
                "commits": self.generate_gitlab_data("commits", 5),
                "merge_requests": self.generate_gitlab_data("merge_requests", 3)
            }
        }
        
        return scenario
    
    def _generate_symptoms(self, incident_type: str) -> List[str]:
        """Generate symptoms based on incident type"""
        symptoms_map = {
            "network_latency": [
                "Response time > 5 seconds",
                "Intermittent timeouts",
                "Increased packet loss"
            ],
            "service_outage": [
                "Health checks failing",
                "503 errors from load balancer",
                "No response from service endpoints"
            ],
            "performance_degradation": [
                "CPU utilization > 90%",
                "Memory usage increasing",
                "Database query times elevated"
            ],
            "security_incident": [
                "Unusual traffic patterns",
                "Failed authentication attempts",
                "Suspicious API calls"
            ]
        }
        
        return symptoms_map.get(incident_type, ["Unknown symptoms"])
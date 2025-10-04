#!/usr/bin/env python3
"""
Incident Generator Module
Generates realistic incidents for the SRE Copilot system
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any

class IncidentGenerator:
    """Generate realistic incidents for testing and demo purposes"""
    
    def __init__(self):
        self.services = [
            "API Gateway", "Database Engine", "Web Portal", "Analytics Platform",
            "Mobile App Backend", "Payment Service", "User Authentication",
            "Search Service", "Notification Service", "Data Pipeline"
        ]
        
        self.incident_types = [
            "performance", "availability", "error", "security", "capacity"
        ]
        
        self.severities = ["Critical", "High", "Medium", "Low"]
        self.statuses = ["Open", "Investigating", "Resolved"]
        
        self.incident_templates = [
            {
                "type": "performance",
                "titles": [
                    "{service} experiencing high latency",
                    "Slow response times in {service}",
                    "{service} performance degradation detected",
                    "Response time spike in {service}"
                ],
                "descriptions": [
                    "Users are reporting slow response times when accessing {service}. Average response time has increased from 200ms to 2000ms.",
                    "Performance monitoring shows {service} is taking longer than usual to process requests. CPU usage is at 85%.",
                    "Multiple alerts triggered for high latency in {service}. Database queries are taking 10x longer than normal."
                ],
                "error_logs": [
                    "Request timeout after 30000ms",
                    "Connection pool exhausted",
                    "Query execution time exceeded threshold"
                ]
            },
            {
                "type": "availability",
                "titles": [
                    "{service} is down",
                    "Complete outage of {service}",
                    "{service} not responding to health checks",
                    "Service unavailable: {service}"
                ],
                "descriptions": [
                    "{service} is completely unavailable. All health checks are failing. Users cannot access the service.",
                    "Total outage detected for {service}. The service has been down for the last 5 minutes.",
                    "Critical: {service} is not responding. All instances are unreachable."
                ],
                "error_logs": [
                    "Connection refused",
                    "Service health check failed",
                    "No healthy instances available"
                ]
            },
            {
                "type": "error",
                "titles": [
                    "High error rate in {service}",
                    "{service} returning 5xx errors",
                    "Increased error count in {service}",
                    "API errors spiking in {service}"
                ],
                "descriptions": [
                    "Error rate for {service} has increased to 15% from baseline of 0.1%. Users are experiencing failures.",
                    "{service} is returning HTTP 500 errors for 20% of requests. Investigation needed.",
                    "Surge in error responses from {service}. Error logs show database connection issues."
                ],
                "error_logs": [
                    "Internal server error: Database connection failed",
                    "NullPointerException at line 145",
                    "Failed to process request: Invalid state"
                ]
            },
            {
                "type": "security",
                "titles": [
                    "Suspicious activity detected in {service}",
                    "Security alert: Unusual access pattern in {service}",
                    "Potential security breach in {service}",
                    "Anomalous behavior detected in {service}"
                ],
                "descriptions": [
                    "Security monitoring has detected unusual access patterns in {service}. Multiple failed authentication attempts from unknown IPs.",
                    "Potential security incident: {service} is receiving an abnormally high number of requests from a single IP address.",
                    "Security alert triggered for {service}. Unusual data access patterns detected in the last hour."
                ],
                "error_logs": [
                    "Authentication failed: Invalid credentials",
                    "Rate limit exceeded for IP: 192.168.1.100",
                    "Suspicious query pattern detected"
                ]
            }
        ]
    
    def generate_incident(self, incident_type: str = None, service: str = None) -> Dict[str, Any]:
        """Generate a single incident"""
        # Select random values if not provided
        if not incident_type:
            incident_type = random.choice(self.incident_types)
        if not service:
            service = random.choice(self.services)
        
        # Get template for incident type
        template = next((t for t in self.incident_templates if t["type"] == incident_type), 
                       self.incident_templates[0])
        
        # Generate incident ID
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Generate OpsItem ID
        ops_item_id = f"oi-{str(uuid.uuid4())[:12]}"
        
        # Select random title and description
        title = random.choice(template["titles"]).format(service=service)
        description = random.choice(template["descriptions"]).format(service=service)
        
        # Determine severity based on type
        if incident_type in ["availability", "security"]:
            severity = random.choice(["Critical", "High"])
        else:
            severity = random.choice(self.severities)
        
        # Generate timestamp (within last hour)
        timestamp = (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat() + "Z"
        
        incident = {
            "id": incident_id,
            "ops_item_id": ops_item_id,
            "title": title,
            "description": description,
            "severity": severity,
            "status": random.choice(self.statuses),
            "service": service,
            "type": incident_type,
            "timestamp": timestamp,
            "created_by": "CloudWatch Alarm",
            "assigned_to": random.choice(["SRE Team", "DevOps Team", "Platform Team"]),
            "affected_resources": [f"arn:aws:service:us-east-1:123456789012:{service.lower().replace(' ', '-')}"],
            "error_logs": random.sample(template["error_logs"], k=random.randint(1, len(template["error_logs"]))),
            "metrics": {
                "error_rate": f"{random.uniform(0.1, 25.0):.1f}%",
                "response_time": f"{random.randint(100, 5000)}ms",
                "availability": f"{random.uniform(85.0, 99.9):.1f}%"
            },
            "tags": [incident_type, service.lower().replace(' ', '-'), severity.lower()],
            "last_updated": timestamp
        }
        
        return incident
    
    def generate_multiple_incidents(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate multiple incidents"""
        incidents = []
        for _ in range(count):
            incident = self.generate_incident()
            incidents.append(incident)
        return incidents
    
    def generate_related_incidents(self, base_service: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate incidents related to a specific service"""
        incidents = []
        incident_types = random.sample(self.incident_types, k=min(count, len(self.incident_types)))
        
        for incident_type in incident_types:
            incident = self.generate_incident(incident_type=incident_type, service=base_service)
            incidents.append(incident)
        
        return incidents
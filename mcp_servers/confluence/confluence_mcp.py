"""
Confluence MCP Server for knowledge base articles
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, request, jsonify
import threading

class ConfluenceMCPServer:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.app = Flask(__name__)
        self.kb_articles = []
        self.setup_routes()
        self.init_test_data()
        
    def init_test_data(self):
        """Initialize test KB articles"""
        if self.test_mode:
            kb_topics = [
                {
                    "title": "Network Latency Troubleshooting Guide",
                    "content": """
                    # Network Latency Troubleshooting Guide
                    
                    ## Common Causes
                    1. DNS Resolution Issues
                    2. Network Congestion
                    3. Routing Problems
                    4. Firewall Rules
                    
                    ## Diagnostic Steps
                    1. Check DNS resolution time
                    2. Run traceroute to identify slow hops
                    3. Monitor network interface statistics
                    4. Check for packet loss
                    
                    ## Resolution Steps
                    1. Update DNS servers
                    2. Optimize routing tables
                    3. Implement QoS policies
                    4. Scale network capacity
                    """,
                    "labels": ["network", "latency", "troubleshooting"]
                },
                {
                    "title": "MQ Performance Optimization",
                    "content": """
                    # Message Queue Performance Optimization
                    
                    ## Key Metrics to Monitor
                    - Queue depth
                    - Message throughput
                    - Consumer lag
                    - Error rates
                    
                    ## Optimization Strategies
                    1. Increase consumer instances
                    2. Batch message processing
                    3. Implement circuit breakers
                    4. Use message compression
                    
                    ## Best Practices
                    - Set appropriate TTL
                    - Implement DLQ handling
                    - Monitor consumer health
                    - Regular capacity planning
                    """,
                    "labels": ["mq", "performance", "optimization"]
                },
                {
                    "title": "Incident Response Runbook",
                    "content": """
                    # Incident Response Runbook
                    
                    ## Initial Response
                    1. Acknowledge incident
                    2. Assess severity and impact
                    3. Notify stakeholders
                    4. Begin investigation
                    
                    ## Investigation Process
                    1. Gather metrics and logs
                    2. Correlate events
                    3. Identify root cause
                    4. Document findings
                    
                    ## Resolution and Recovery
                    1. Implement fix
                    2. Verify resolution
                    3. Monitor for recurrence
                    4. Update documentation
                    """,
                    "labels": ["incident", "runbook", "response"]
                },
                {
                    "title": "AWS Service Outage Procedures",
                    "content": """
                    # AWS Service Outage Procedures
                    
                    ## Detection
                    - Monitor AWS Service Health Dashboard
                    - Set up CloudWatch alarms
                    - Use multi-region health checks
                    
                    ## Mitigation Strategies
                    1. Failover to secondary region
                    2. Enable disaster recovery plan
                    3. Communicate with customers
                    4. Document timeline
                    
                    ## Post-Incident
                    - Conduct RCA
                    - Update runbooks
                    - Test failover procedures
                    """,
                    "labels": ["aws", "outage", "disaster-recovery"]
                },
                {
                    "title": "Database Performance Tuning",
                    "content": """
                    # Database Performance Tuning Guide
                    
                    ## Common Issues
                    - Slow queries
                    - Lock contention
                    - Connection pool exhaustion
                    - Index fragmentation
                    
                    ## Optimization Techniques
                    1. Query optimization
                    2. Index strategy review
                    3. Connection pooling
                    4. Caching implementation
                    
                    ## Monitoring
                    - Query execution time
                    - Lock wait time
                    - Buffer cache hit ratio
                    - Connection count
                    """,
                    "labels": ["database", "performance", "tuning"]
                }
            ]
            
            for i, article in enumerate(kb_topics):
                self.kb_articles.append({
                    "id": f"kb-{i:03d}",
                    "title": article["title"],
                    "content": article["content"],
                    "space_key": "SRE",
                    "url": f"https://confluence.example.com/display/SRE/{article['title'].replace(' ', '+')}",
                    "author": "SRE Team",
                    "created": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                    "updated": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    "labels": article["labels"],
                    "views": random.randint(100, 1000)
                })
        
    def setup_routes(self):
        @self.app.route('/confluence/search', methods=['GET'])
        def search_endpoint():
            query = request.args.get('query', '')
            space_key = request.args.get('space_key', '')
            
            return jsonify(self.search_content(query, space_key))
            
        @self.app.route('/confluence/pages/<page_id>', methods=['GET'])
        def page_endpoint(page_id):
            return jsonify(self.get_page(page_id))
            
        @self.app.route('/confluence/spaces', methods=['GET'])
        def spaces_endpoint():
            return jsonify(self.get_spaces())
    
    def search_content(self, query: str, space_key: str) -> List[Dict[str, Any]]:
        """Search Confluence content"""
        if self.test_mode:
            results = []
            query_lower = query.lower()
            
            for article in self.kb_articles:
                # Simple search in title, content, and labels
                if (query_lower in article['title'].lower() or
                    query_lower in article['content'].lower() or
                    any(query_lower in label for label in article['labels'])):
                    
                    if not space_key or article['space_key'] == space_key:
                        results.append({
                            "id": article['id'],
                            "title": article['title'],
                            "content": article['content'][:500] + "...",  # Preview
                            "url": article['url'],
                            "space_key": article['space_key'],
                            "labels": article['labels'],
                            "relevance_score": random.uniform(0.7, 1.0)
                        })
            
            # Sort by relevance
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get full page content"""
        if self.test_mode:
            for article in self.kb_articles:
                if article['id'] == page_id:
                    return article
            
            return {"error": "Page not found"}
    
    def get_spaces(self) -> List[Dict[str, Any]]:
        """Get available spaces"""
        if self.test_mode:
            return [
                {
                    "key": "SRE",
                    "name": "Site Reliability Engineering",
                    "description": "SRE team documentation and runbooks"
                },
                {
                    "key": "OPS",
                    "name": "Operations",
                    "description": "Operational procedures and guides"
                },
                {
                    "key": "ARCH",
                    "name": "Architecture",
                    "description": "System architecture documentation"
                }
            ]
    
    def start_server(self, port=8083):
        """Start the MCP server"""
        self.app.run(host='0.0.0.0', port=port, debug=False)


def start_confluence_mcp_server(port=8083, test_mode=True):
    """Start Confluence MCP server in a separate thread"""
    server = ConfluenceMCPServer(test_mode=test_mode)
    thread = threading.Thread(target=server.start_server, args=(port,))
    thread.daemon = True
    thread.start()
    return server
#!/usr/bin/env python3
"""
Start all MCP servers including defect management (ALM Octane & Jira)
"""

import time
import threading
import sys
import os
import json

# Add path for modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_servers.splunk.splunk_mcp import SplunkMCPServer
from mcp_servers.dynatrace.dynatrace_mcp import DynatraceMCPServer
from mcp_servers.servicenow.servicenow_mcp import ServiceNowMCPServer
from mcp_servers.confluence.confluence_mcp import ConfluenceMCPServer
from mcp_servers.gitlab.gitlab_mcp import GitLabMCPServer
from mcp_servers.alm_octane.alm_octane_mcp import ALMOctaneMCPServer
from mcp_servers.jira.jira_mcp import JiraMCPServer

def load_port_configuration():
    """Load port configuration from mcp_ports.json"""
    try:
        with open('mcp_ports.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load port configuration: {e}")
        return {
            "splunk": 9080,
            "dynatrace": 9081,
            "servicenow": 9082,
            "confluence": 9083,
            "gitlab": 9084,
            "alm_octane": 9085,
            "jira": 9086
        }

def start_server(name, server_class, port, test_mode=True):
    """Start a single MCP server"""
    print(f"Starting {name} MCP server on port {port}...")
    try:
        server = server_class(test_mode=test_mode)
        # Run in thread
        thread = threading.Thread(target=server.app.run, kwargs={
            'host': '0.0.0.0',
            'port': port,
            'debug': False,
            'use_reloader': False
        })
        thread.daemon = True
        thread.start()
        
        # Give it a moment to start
        time.sleep(0.5)
        
        print(f"✓ {name} MCP server started on port {port}")
        return server, thread
    except Exception as e:
        print(f"✗ Failed to start {name}: {e}")
        return None, None

def main():
    print("Starting Defect Management MCP Servers...")
    print("=" * 60)
    
    # Load port configuration
    ports = load_port_configuration()
    
    # Server configurations with defect management
    servers = [
        ("Splunk", SplunkMCPServer, ports["splunk"]),
        ("Dynatrace", DynatraceMCPServer, ports["dynatrace"]),
        ("ServiceNow", ServiceNowMCPServer, ports["servicenow"]),
        ("Confluence", ConfluenceMCPServer, ports["confluence"]),
        ("GitLab", GitLabMCPServer, ports["gitlab"]),
        ("ALM Octane", ALMOctaneMCPServer, ports["alm_octane"]),
        ("Jira", JiraMCPServer, ports["jira"])
    ]
    
    running_servers = []
    
    # Start all servers
    for name, server_class, port in servers:
        server, thread = start_server(name, server_class, port)
        if server and thread:
            running_servers.append((name, server, thread, port))
    
    print("\n" + "=" * 60)
    print(f"Successfully started {len(running_servers)} MCP servers:")
    for name, _, _, port in running_servers:
        print(f"  - {name}: http://localhost:{port}")
    
    print("\nTesting endpoints...")
    print("-" * 60)
    
    # Test each server
    import requests
    for name, _, _, port in running_servers:
        try:
            if name == "Splunk":
                # Test POST endpoint
                response = requests.post(
                    f"http://localhost:{port}/splunk/search",
                    json={"query": "test", "time_range": "-1h"},
                    timeout=2
                )
            elif name == "ServiceNow":
                # Test GET endpoint
                response = requests.get(f"http://localhost:{port}/servicenow/incidents", timeout=2)
            elif name == "ALM Octane":
                # Test defects endpoint
                response = requests.get(f"http://localhost:{port}/octane/defects", timeout=2)
            elif name == "Jira":
                # Test issues endpoint
                response = requests.get(f"http://localhost:{port}/jira/issues", timeout=2)
            else:
                # Test GET endpoints for others
                service = name.lower().replace(" ", "_")
                response = requests.get(f"http://localhost:{port}/{service}/search?query=test", timeout=2)
            
            if response.status_code in [200, 201]:
                print(f"✓ {name} endpoint test: OK")
            else:
                print(f"✗ {name} endpoint test: Failed (Status: {response.status_code})")
        except Exception as e:
            print(f"✗ {name} endpoint test: Error - {type(e).__name__}")
    
    print("\n" + "=" * 60)
    print("🚀 All MCP servers are running!")
    print("\n🔧 Defect Management Features:")
    print("  • ALM Octane: Comprehensive defect tracking & quality metrics")
    print("  • Jira: Agile issue tracking & sprint management")
    print("  • Integrated analytics and trend analysis")
    print("  • Automated defect correlation with SRE incidents")
    
    print("\n📊 Available Endpoints:")
    print("  ALM Octane:")
    print("    - GET  /octane/defects - List defects")
    print("    - POST /octane/defects - Create defect")
    print("    - GET  /octane/analytics/quality-metrics - Quality metrics")
    print("  Jira:")
    print("    - GET  /jira/issues - List issues")
    print("    - POST /jira/issues - Create issue")
    print("    - GET  /jira/analytics/defect-metrics - Defect analytics")
    
    print(f"\n🌐 Test the defect management APIs:")
    print(f"  curl http://localhost:{ports['alm_octane']}/octane/defects")
    print(f"  curl http://localhost:{ports['jira']}/jira/issues")
    
    print("\nPress Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping MCP servers...")
        print("Servers stopped.")

if __name__ == "__main__":
    main()
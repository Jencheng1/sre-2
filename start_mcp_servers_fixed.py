#!/usr/bin/env python3
"""
Start all MCP servers for production use - Fixed version
"""

import time
import threading
import sys
import os

# Add path for modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_servers.splunk.splunk_mcp import SplunkMCPServer
from mcp_servers.dynatrace.dynatrace_mcp import DynatraceMCPServer
from mcp_servers.servicenow.servicenow_mcp import ServiceNowMCPServer
from mcp_servers.confluence.confluence_mcp import ConfluenceMCPServer
from mcp_servers.gitlab.gitlab_mcp import GitLabMCPServer

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
    print("Starting MCP servers (Fixed version)...")
    print("=" * 50)
    
    # Server configurations
    servers = [
        ("Splunk", SplunkMCPServer, 8080),
        ("Dynatrace", DynatraceMCPServer, 8081),
        ("ServiceNow", ServiceNowMCPServer, 8082),
        ("Confluence", ConfluenceMCPServer, 8083),
        ("GitLab", GitLabMCPServer, 8084)
    ]
    
    running_servers = []
    
    # Start all servers
    for name, server_class, port in servers:
        server, thread = start_server(name, server_class, port)
        if server and thread:
            running_servers.append((name, server, thread, port))
    
    print("\n" + "=" * 50)
    print(f"Successfully started {len(running_servers)} MCP servers:")
    for name, _, _, port in running_servers:
        print(f"  - {name}: http://localhost:{port}")
    
    print("\nTesting endpoints...")
    print("-" * 50)
    
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
            else:
                # Test GET endpoints for others
                service = name.lower()
                response = requests.get(f"http://localhost:{port}/{service}/search?query=test", timeout=2)
            
            if response.status_code in [200, 201]:
                print(f"✓ {name} endpoint test: OK")
            else:
                print(f"✗ {name} endpoint test: Failed (Status: {response.status_code})")
        except Exception as e:
            print(f"✗ {name} endpoint test: Error - {type(e).__name__}")
    
    print("\n" + "=" * 50)
    print("All MCP servers are running!")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping MCP servers...")
        print("Servers stopped.")

if __name__ == "__main__":
    main()
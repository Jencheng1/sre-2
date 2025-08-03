#!/usr/bin/env python3
"""
Start all MCP servers on alternate ports (avoiding Docker conflicts)
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

# Alternative ports to avoid Docker conflicts
ALTERNATE_PORTS = {
    'splunk': 9080,      # Instead of 8080
    'dynatrace': 9081,   # Instead of 8081
    'servicenow': 9082,  # Instead of 8082
    'confluence': 9083,  # Instead of 8083
    'gitlab': 9084       # Instead of 8084
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
        import traceback
        traceback.print_exc()
        return None, None

def main():
    print("Starting MCP servers on alternate ports...")
    print("=" * 50)
    
    # Server configurations with alternate ports
    servers = [
        ("Splunk", SplunkMCPServer, ALTERNATE_PORTS['splunk']),
        ("Dynatrace", DynatraceMCPServer, ALTERNATE_PORTS['dynatrace']),
        ("ServiceNow", ServiceNowMCPServer, ALTERNATE_PORTS['servicenow']),
        ("Confluence", ConfluenceMCPServer, ALTERNATE_PORTS['confluence']),
        ("GitLab", GitLabMCPServer, ALTERNATE_PORTS['gitlab'])
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
    
    # Export the port mapping
    print("\nPort mapping:")
    for service, port in ALTERNATE_PORTS.items():
        print(f"  {service}: {port}")
    
    # Save port mapping to file for other components to use
    with open('mcp_ports.json', 'w') as f:
        import json
        json.dump(ALTERNATE_PORTS, f, indent=2)
    
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
            print(f"✗ {name} endpoint test: Error - {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("All MCP servers are running on alternate ports!")
    print("Port mapping saved to mcp_ports.json")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping MCP servers...")
        print("Servers stopped.")

if __name__ == "__main__":
    main()
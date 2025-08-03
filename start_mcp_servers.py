#!/usr/bin/env python3
"""
Start all MCP servers for production use
"""

import time
import threading
from mcp_servers.splunk.splunk_mcp import start_splunk_mcp_server
from mcp_servers.dynatrace.dynatrace_mcp import start_dynatrace_mcp_server
from mcp_servers.servicenow.servicenow_mcp import start_servicenow_mcp_server
from mcp_servers.confluence.confluence_mcp import start_confluence_mcp_server
from mcp_servers.gitlab.gitlab_mcp import start_gitlab_mcp_server

def main():
    print("Starting MCP servers...")
    
    # Start all servers
    servers = [
        ("Splunk", 8080, start_splunk_mcp_server),
        ("Dynatrace", 8081, start_dynatrace_mcp_server),
        ("ServiceNow", 8082, start_servicenow_mcp_server),
        ("Confluence", 8083, start_confluence_mcp_server),
        ("GitLab", 8084, start_gitlab_mcp_server)
    ]
    
    for name, port, start_func in servers:
        print(f"Starting {name} MCP server on port {port}...")
        try:
            start_func(port=port, test_mode=True)
            print(f"✓ {name} MCP server started")
        except Exception as e:
            print(f"✗ Failed to start {name}: {e}")
    
    print("\nAll MCP servers started!")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping MCP servers...")

if __name__ == "__main__":
    main()
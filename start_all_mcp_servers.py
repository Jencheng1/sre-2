#!/usr/bin/env python3
"""Start all MCP servers"""

import sys
import time
import subprocess
import os

# Add the parent directory to the path
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')

# Import and start MCP servers
from mcp_servers.splunk.splunk_mcp import SplunkMCPServer
from mcp_servers.dynatrace.dynatrace_mcp import DynatraceMCPServer
from mcp_servers.servicenow.servicenow_mcp import ServiceNowMCPServer
from mcp_servers.confluence.confluence_mcp import ConfluenceMCPServer
from mcp_servers.gitlab.gitlab_mcp import GitLabMCPServer
from mcp_servers.alm_octane.alm_octane_mcp import ALMOctaneMCPServer
from mcp_servers.jira.jira_mcp import JiraMCPServer

def start_servers():
    """Start all MCP servers"""
    servers = [
        ("Splunk", SplunkMCPServer, 8080),
        ("Dynatrace", DynatraceMCPServer, 8081),
        ("ServiceNow", ServiceNowMCPServer, 8082),
        ("Confluence", ConfluenceMCPServer, 8083),
        ("GitLab", GitLabMCPServer, 8084),
        ("ALM Octane", ALMOctaneMCPServer, 9085),
        ("Jira", JiraMCPServer, 9086),
    ]
    
    processes = []
    
    for name, server_class, port in servers:
        print(f"Starting {name} MCP server on port {port}...")
        
        # Create a script to run each server
        script_content = f"""
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.{name.lower().replace(' ', '_')}.{name.lower().replace(' ', '_')}_mcp import {server_class.__name__}

server = {server_class.__name__}(test_mode=True)
print(f"Starting {name} server on port {port}...")
server.start_server(port={port})
"""
        
        # Write and execute the script
        script_path = f"/tmp/start_{name.lower().replace(' ', '_')}_mcp.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Start the server process
        process = subprocess.Popen([sys.executable, script_path])
        processes.append((name, process))
        time.sleep(1)  # Give each server time to start
    
    print("\nAll MCP servers started!")
    print("\nServer URLs:")
    print("- Splunk: http://localhost:8080")
    print("- Dynatrace: http://localhost:8081")
    print("- ServiceNow: http://localhost:8082")
    print("- Confluence: http://localhost:8083")
    print("- GitLab: http://localhost:8084")
    print("- ALM Octane: http://localhost:9085")
    print("- Jira: http://localhost:9086")
    
    # Keep the script running
    try:
        while True:
            time.sleep(60)
            # Check if processes are still running
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"Warning: {name} server has stopped!")
    except KeyboardInterrupt:
        print("\nStopping all servers...")
        for name, proc in processes:
            proc.terminate()

if __name__ == "__main__":
    start_servers()
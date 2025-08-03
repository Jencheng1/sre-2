#!/usr/bin/env python3
"""
MCP Integration Test Runner
Starts all MCP servers and runs comprehensive test suite
"""

import sys
import time
import threading
import subprocess
from typing import List, Dict, Any

# Import MCP servers
from mcp_servers.splunk.splunk_mcp import start_splunk_mcp_server
from mcp_servers.dynatrace.dynatrace_mcp import start_dynatrace_mcp_server
from mcp_servers.servicenow.servicenow_mcp import start_servicenow_mcp_server
from mcp_servers.confluence.confluence_mcp import start_confluence_mcp_server
from mcp_servers.gitlab.gitlab_mcp import start_gitlab_mcp_server

def start_all_mcp_servers():
    """Start all MCP test servers"""
    print("Starting MCP test servers...")
    
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
            print(f"✗ Failed to start {name} MCP server: {e}")
    
    # Give servers time to start
    print("Waiting for servers to initialize...")
    time.sleep(2)
    print("All MCP servers started!")

def run_tests():
    """Run the test suite"""
    print("\nRunning MCP integration tests...")
    
    # Run unittest
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "test_mcp_integration", "-v"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """Main test runner"""
    print("=== MCP Integration Test Runner ===\n")
    
    try:
        # Start all MCP servers
        start_all_mcp_servers()
        
        # Run tests
        success = run_tests()
        
        if success:
            print("\n✓ All tests passed!")
            return 0
        else:
            print("\n✗ Some tests failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"\nError during test run: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.splunk.splunk_mcp import SplunkMCPServer

if __name__ == "__main__":
    server = SplunkMCPServer(test_mode=True)
    print("Starting Splunk MCP server on port 8080...")
    server.start_server(port=9080)
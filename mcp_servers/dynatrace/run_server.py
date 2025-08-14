#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.dynatrace.dynatrace_mcp import DynatraceMCPServer

if __name__ == "__main__":
    server = DynatraceMCPServer(test_mode=True)
    print("Starting Dynatrace MCP server on port 9081...")
    server.start_server(port=9081)

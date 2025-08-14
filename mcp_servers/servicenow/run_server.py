#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.servicenow.servicenow_mcp import ServiceNowMCPServer

if __name__ == "__main__":
    server = ServiceNowMCPServer(test_mode=True)
    print("Starting ServiceNow MCP server on port 9082...")
    server.start_server(port=9082)

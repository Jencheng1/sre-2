#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.jira.jira_mcp import JiraMCPServer

if __name__ == "__main__":
    server = JiraMCPServer(test_mode=True)
    print("Starting Jira MCP server on port 9086...")
    server.start_server(port=9086)

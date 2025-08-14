#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.confluence.confluence_mcp import ConfluenceMCPServer

if __name__ == "__main__":
    server = ConfluenceMCPServer(test_mode=True)
    print("Starting Confluence MCP server on port 9083...")
    server.start_server(port=9083)

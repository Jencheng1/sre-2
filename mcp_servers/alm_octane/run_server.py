#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.alm_octane.alm_octane_mcp import ALMOctaneMCPServer

if __name__ == "__main__":
    server = ALMOctaneMCPServer(test_mode=True)
    print("Starting ALM Octane MCP server on port 9085...")
    server.start_server(port=9085)

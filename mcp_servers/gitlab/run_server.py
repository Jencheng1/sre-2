#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.gitlab.gitlab_mcp import GitLabMCPServer

if __name__ == "__main__":
    server = GitLabMCPServer(test_mode=True)
    print("Starting GitLab MCP server on port 9084...")
    server.start_server(port=9084)

#!/bin/bash
# Start all MCP servers

echo "Starting MCP servers..."

# Create runner scripts
cat > mcp_servers/dynatrace/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.dynatrace.dynatrace_mcp import DynatraceMCPServer

if __name__ == "__main__":
    server = DynatraceMCPServer(test_mode=True)
    print("Starting Dynatrace MCP server on port 8081...")
    server.start_server(port=8081)
EOF

cat > mcp_servers/servicenow/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.servicenow.servicenow_mcp import ServiceNowMCPServer

if __name__ == "__main__":
    server = ServiceNowMCPServer(test_mode=True)
    print("Starting ServiceNow MCP server on port 8082...")
    server.start_server(port=8082)
EOF

cat > mcp_servers/confluence/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.confluence.confluence_mcp import ConfluenceMCPServer

if __name__ == "__main__":
    server = ConfluenceMCPServer(test_mode=True)
    print("Starting Confluence MCP server on port 8083...")
    server.start_server(port=8083)
EOF

cat > mcp_servers/gitlab/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.gitlab.gitlab_mcp import GitLabMCPServer

if __name__ == "__main__":
    server = GitLabMCPServer(test_mode=True)
    print("Starting GitLab MCP server on port 8084...")
    server.start_server(port=8084)
EOF

cat > mcp_servers/alm_octane/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.alm_octane.alm_octane_mcp import ALMOctaneMCPServer

if __name__ == "__main__":
    server = ALMOctaneMCPServer(test_mode=True)
    print("Starting ALM Octane MCP server on port 9085...")
    server.start_server(port=9085)
EOF

cat > mcp_servers/jira/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.jira.jira_mcp import JiraMCPServer

if __name__ == "__main__":
    server = JiraMCPServer(test_mode=True)
    print("Starting Jira MCP server on port 9086...")
    server.start_server(port=9086)
EOF

# Start all servers
nohup python3 mcp_servers/dynatrace/run_server.py > mcp_servers/dynatrace/server.log 2>&1 &
echo "Dynatrace PID: $!"

nohup python3 mcp_servers/servicenow/run_server.py > mcp_servers/servicenow/server.log 2>&1 &
echo "ServiceNow PID: $!"

nohup python3 mcp_servers/confluence/run_server.py > mcp_servers/confluence/server.log 2>&1 &
echo "Confluence PID: $!"

nohup python3 mcp_servers/gitlab/run_server.py > mcp_servers/gitlab/server.log 2>&1 &
echo "GitLab PID: $!"

nohup python3 mcp_servers/alm_octane/run_server.py > mcp_servers/alm_octane/server.log 2>&1 &
echo "ALM Octane PID: $!"

nohup python3 mcp_servers/jira/run_server.py > mcp_servers/jira/server.log 2>&1 &
echo "Jira PID: $!"

echo "All MCP servers started!"
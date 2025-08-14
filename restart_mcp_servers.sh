#!/bin/bash
# Restart all MCP servers with correct ports

echo "Stopping any existing MCP servers..."
pkill -f "run_server.py"
sleep 2

echo "Starting MCP servers with updated ports..."

# Splunk on 9080
nohup python3 mcp_servers/splunk/run_server.py > mcp_servers/splunk/server.log 2>&1 &
echo "Splunk PID: $! (port 9080)"

# Dynatrace on 9081
cat > mcp_servers/dynatrace/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.dynatrace.dynatrace_mcp import DynatraceMCPServer

if __name__ == "__main__":
    server = DynatraceMCPServer(test_mode=True)
    print("Starting Dynatrace MCP server on port 9081...")
    server.start_server(port=9081)
EOF

nohup python3 mcp_servers/dynatrace/run_server.py > mcp_servers/dynatrace/server.log 2>&1 &
echo "Dynatrace PID: $! (port 9081)"

# ServiceNow on 9082
cat > mcp_servers/servicenow/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.servicenow.servicenow_mcp import ServiceNowMCPServer

if __name__ == "__main__":
    server = ServiceNowMCPServer(test_mode=True)
    print("Starting ServiceNow MCP server on port 9082...")
    server.start_server(port=9082)
EOF

nohup python3 mcp_servers/servicenow/run_server.py > mcp_servers/servicenow/server.log 2>&1 &
echo "ServiceNow PID: $! (port 9082)"

# Confluence on 9083
cat > mcp_servers/confluence/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.confluence.confluence_mcp import ConfluenceMCPServer

if __name__ == "__main__":
    server = ConfluenceMCPServer(test_mode=True)
    print("Starting Confluence MCP server on port 9083...")
    server.start_server(port=9083)
EOF

nohup python3 mcp_servers/confluence/run_server.py > mcp_servers/confluence/server.log 2>&1 &
echo "Confluence PID: $! (port 9083)"

# GitLab on 9084
cat > mcp_servers/gitlab/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')
from mcp_servers.gitlab.gitlab_mcp import GitLabMCPServer

if __name__ == "__main__":
    server = GitLabMCPServer(test_mode=True)
    print("Starting GitLab MCP server on port 9084...")
    server.start_server(port=9084)
EOF

nohup python3 mcp_servers/gitlab/run_server.py > mcp_servers/gitlab/server.log 2>&1 &
echo "GitLab PID: $! (port 9084)"

# ALM Octane on 9085
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

nohup python3 mcp_servers/alm_octane/run_server.py > mcp_servers/alm_octane/server.log 2>&1 &
echo "ALM Octane PID: $! (port 9085)"

# Jira on 9086
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

nohup python3 mcp_servers/jira/run_server.py > mcp_servers/jira/server.log 2>&1 &
echo "Jira PID: $! (port 9086)"

echo "All MCP servers started with updated ports!"
echo ""
echo "Updated ports:"
echo "- Splunk: 9080"
echo "- Dynatrace: 9081"
echo "- ServiceNow: 9082"
echo "- Confluence: 9083"
echo "- GitLab: 9084"
echo "- ALM Octane: 9085"
echo "- Jira: 9086"
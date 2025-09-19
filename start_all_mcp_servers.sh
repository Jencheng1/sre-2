#!/bin/bash
# Script to start all MCP servers for the SRE Copilot Streamlit application

echo "Starting all MCP servers..."

# Function to start a server
start_server() {
    local name=$1
    local path=$2
    local port=$3
    
    echo "Starting $name server on port $port..."
    cd /home/ec2-user/sre/sre_mcp/mcp_servers/$path
    nohup python3 run_server.py > /home/ec2-user/sre/sre_mcp/logs/${name}_server.log 2>&1 &
    echo "$name server started with PID $!"
    sleep 2
}

# Create logs directory if it doesn't exist
mkdir -p /home/ec2-user/sre/sre_mcp/logs

# Start each MCP server based on mcp_ports.json
start_server "splunk" "splunk" 9080
start_server "dynatrace" "dynatrace" 9081
start_server "servicenow" "servicenow" 9082
start_server "confluence" "confluence" 9083
start_server "gitlab" "gitlab" 9084
start_server "alm_octane" "alm_octane" 9085
start_server "jira" "jira" 9086
start_server "fed_lpp" "fed_lpp" 9087
start_server "fedsearch" "fedsearch" 9088

# Knowledge base servers (if they exist)
if [ -d "/home/ec2-user/sre/sre_mcp/mcp_servers/stackoverflow" ]; then
    start_server "stackoverflow_kb" "stackoverflow" 9089
fi

if [ -d "/home/ec2-user/sre/sre_mcp/mcp_servers/github_kb" ]; then
    start_server "github_kb" "github_kb" 9090
fi

echo ""
echo "All MCP servers have been started!"
echo "Checking running servers..."
sleep 3

# Check which servers are listening
echo ""
echo "Active MCP servers:"
netstat -tulpn 2>/dev/null | grep -E ":(908[0-9]|909[0-9])" | grep LISTEN || echo "No servers listening yet, they may still be starting..."

echo ""
echo "You can check the logs in /home/ec2-user/sre/sre_mcp/logs/"
echo ""
echo "To stop all MCP servers, run: pkill -f 'python3.*run_server.py'"
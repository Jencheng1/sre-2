#!/usr/bin/env python3
"""Test MCP server connectivity"""

import requests
import json

# Load MCP ports
with open('mcp_ports.json', 'r') as f:
    MCP_PORTS = json.load(f)

print("Testing MCP Server Connectivity...")
print("=" * 50)

for service, port in MCP_PORTS.items():
    try:
        if service == 'splunk':
            response = requests.post(
                f"http://localhost:{port}/splunk/search",
                json={"query": "test", "time_range": "-1h"},
                timeout=2
            )
        elif service in ['dynatrace', 'servicenow']:
            response = requests.get(f"http://localhost:{port}/{service}/incidents", timeout=2)
        elif service in ['alm_octane']:
            response = requests.get(f"http://localhost:{port}/octane/defects", timeout=2)
        elif service == 'jira':
            response = requests.get(f"http://localhost:{port}/jira/issues", timeout=2)
        elif service == 'confluence':
            response = requests.get(f"http://localhost:{port}/confluence/pages", timeout=2)
        elif service == 'gitlab':
            response = requests.get(f"http://localhost:{port}/gitlab/projects", timeout=2)
        else:
            response = requests.get(f"http://localhost:{port}/{service}/search?query=test", timeout=2)
        
        status = '✅ ONLINE' if response.status_code in [200, 201, 405] else f'❌ ERROR ({response.status_code})'
        print(f"{service.upper():15} (port {port}): {status}")
    except Exception as e:
        print(f"{service.upper():15} (port {port}): ❌ OFFLINE - {str(e)[:50]}")

print("=" * 50)
print("\nRefresh your browser at http://localhost:8501 to see updated status in sidebar")
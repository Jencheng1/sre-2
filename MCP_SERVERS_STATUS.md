# 🚀 SRE Copilot - MCP Servers Status

## ✅ Active Services

### Core Platform
- **Streamlit Dashboard**: http://localhost:8501 ✅

### MCP Integration Servers

#### Defect Management
- **ALM Octane MCP**: http://localhost:9085 ✅
- **Jira MCP**: http://localhost:9086 ✅

#### Monitoring & Observability
- **Splunk MCP**: http://localhost:8080 ✅ 
- **Dynatrace MCP**: http://localhost:8081 ✅

#### ITSM & Collaboration
- **ServiceNow MCP**: http://localhost:8082 ✅
- **Confluence MCP**: http://localhost:8083 ✅
- **GitLab MCP**: http://localhost:8084 ✅

#### Knowledge Base & Search (Available but not started)
- **GitHub KB MCP**: Port 9090 (not started)
- **StackOverflow KB MCP**: Port 9089 (not started)
- **FedSearch MCP**: Port 9088 (not started)
- **Fed LPP MCP**: Port 9087 (not started)

## 🔌 Quick API Test Commands

```bash
# Test ALM Octane
curl http://localhost:9085/octane/defects | jq .

# Test Jira
curl http://localhost:9086/jira/issues | jq .

# Test Splunk
curl http://localhost:8080/splunk/search -X POST -H "Content-Type: application/json" -d '{"query": "error", "earliest": "-24h"}' | jq .

# Test Dynatrace
curl http://localhost:8081/dynatrace/problems | jq .

# Test ServiceNow
curl http://localhost:8082/servicenow/incidents | jq .

# Test Confluence
curl http://localhost:8083/confluence/pages | jq .

# Test GitLab
curl http://localhost:8084/gitlab/projects | jq .
```

## 🎯 Integration Features

### Splunk Integration
- **Real-time Log Search**: Query logs with SPL syntax
- **Alert Management**: Retrieve and manage Splunk alerts
- **Dashboard Integration**: Embedded Splunk visualizations
- **Correlation**: Auto-correlate log patterns with incidents

### Dynatrace Integration
- **APM Metrics**: Application performance monitoring
- **Problem Detection**: AI-powered anomaly detection
- **Service Topology**: Dependency mapping
- **Root Cause**: Automatic problem analysis

### ServiceNow Integration
- **Incident Management**: Full ITSM workflow
- **Change Requests**: Change approval process
- **CMDB Integration**: Configuration item tracking
- **SLA Monitoring**: Service level tracking

### Confluence Integration
- **Knowledge Articles**: Auto-generate documentation
- **Post-Mortem Templates**: Standardized reports
- **Best Practices**: Searchable knowledge base
- **Team Collaboration**: Shared incident spaces

### GitLab Integration
- **Code Analysis**: Link incidents to commits
- **CI/CD Pipeline**: Build failure correlation
- **Merge Requests**: Change tracking
- **Security Scanning**: Vulnerability detection

## 📊 Demo Scenarios with MCP Integrations

### Scenario: Production Outage with Multi-Tool Response
1. **Splunk**: Detects error spike in application logs
2. **Dynatrace**: Shows service degradation and dependency impact
3. **ServiceNow**: Auto-creates P1 incident ticket
4. **GitLab**: Identifies problematic deployment
5. **ALM Octane**: Creates defect for root cause
6. **Confluence**: Generates post-mortem document
7. **Jira**: Tracks remediation tasks

## 🚦 Service Health Check

Run this command to verify all services:
```bash
for port in 8080 8081 8082 8083 8084 8501 9085 9086; do 
  echo -n "Port $port: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null || echo "Not responding"
done
```

## 🔄 Restart Commands

If any service needs to be restarted:
```bash
# Kill all MCP servers
pkill -f "mcp.py"

# Restart all services
cd /home/ec2-user/sre/sre_mcp
./start_all_mcp_servers.sh
```

---
**All critical services are now running!** Access the main dashboard at http://localhost:8501
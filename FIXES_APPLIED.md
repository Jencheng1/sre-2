# 🔧 Fixes Applied to SRE Copilot

## Issues Fixed

### 1. ✅ Streamlit Widget Error
**Problem**: `DuplicateWidgetID` error for checkbox widget
**Solution**: Added unique key to the IP masking checkbox:
```python
key=key_manager.get_unique_key("show_ip_masking", ops_item_id)
```

### 2. ✅ MCP Port Conflicts
**Problem**: Port conflicts with Docker (8080-8084)
**Solution**: Updated all MCP ports to 9080-9086 range in `mcp_ports.json`

### 3. ✅ MCP Servers Not Running
**Problem**: MCP servers weren't starting properly
**Solution**: Created runner scripts for each server and restart script

## Current Status

### Working Services ✅
- **Splunk** (9080) - Log search and analysis
- **ServiceNow** (9082) - Incident management
- **ALM Octane** (9085) - Defect tracking
- **Jira** (9086) - Issue tracking
- **Streamlit Dashboard** (8501) - Main UI

### Services with Endpoint Issues (but running) ⚠️
- **Dynatrace** (9081) - 404 on /dynatrace/incidents
- **Confluence** (9083) - 404 on /confluence/pages  
- **GitLab** (9084) - 404 on /gitlab/projects

These services are running but may need endpoint path adjustments in the status check.

## Quick Commands

### Test MCP Connectivity
```bash
python3 test_mcp_status.py
```

### Restart All MCP Servers
```bash
./restart_mcp_servers.sh
```

### Check Service Logs
```bash
tail -f mcp_servers/splunk/server.log
tail -f mcp_servers/jira/server.log
# etc...
```

## Next Steps

1. **Refresh Browser** - Go to http://localhost:8501 and refresh
2. **Test Incident Analysis** - Create and analyze a test incident
3. **Check MCP Status** - Verify services show as online in sidebar

The duplicate widget error is fixed and core MCP services are operational!
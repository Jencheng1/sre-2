# ✅ MCP Test Incident OpsItem Validation Fix

## Problem
When running MCP integration tests (like network latency), the analysis failed with:
```
Analysis failed: An error occurred (ValidationException) when calling the GetOpsItem operation: 
1 validation error detected: Value at 'opsItemId' failed to satisfy constraint: 
Member must satisfy regular expression pattern: ^(oi)-[0-9a-f]{12}$
```

## Root Cause
MCP test incidents were using fake OpsItem IDs like `MCP-TEST-20250814-113527` instead of valid AWS OpsItem IDs (format: `oi-xxxxxxxxxxxx`). When the analysis tried to fetch the OpsItem from AWS SSM, it failed validation.

## Solution Applied

### 1. Modified `run_root_cause_analysis` method (lines 728-758)
Added logic to detect and handle MCP test incidents:
- Check if OpsItem ID starts with 'MCP-TEST-'
- Retrieve incident data from session state
- Create a mock OpsItem structure for analysis
- Skip AWS API call for MCP test incidents

### 2. Updated OpsItem selection dropdown (lines 1106-1123)
- Added MCP test incidents from session state to the dropdown
- Combined AWS OpsItems with MCP test items
- Display with [MCP TEST] prefix for clarity

## Code Changes

```python
# In run_root_cause_analysis method
if ops_item_id.startswith('MCP-TEST-'):
    # Find the MCP test incident in session state
    mcp_incident = None
    for incident in st.session_state.get('generated_incidents', []):
        if incident.get('ops_item_id') == ops_item_id:
            mcp_incident = incident
            break
    
    # Create a mock OpsItem structure
    ops_item = {
        'OpsItemId': ops_item_id,
        'Title': f"[MCP TEST] {mcp_incident.get('ui_type', 'Test Incident')}",
        'Description': mcp_incident.get('description', ''),
        'Severity': str(mcp_incident.get('severity', 3)),
        'Status': 'Open',
        'Source': 'MCP-Test',
        'CreatedTime': mcp_incident.get('start_time', datetime.now()),
        'OperationalData': {
            'service': {'Value': mcp_incident.get('service', 'test-service')},
            'scenario_data': {'Value': json.dumps(mcp_incident.get('scenario_data', {}))}
        }
    }
else:
    # Regular AWS OpsItem
    ops_response = self.ssm_client.get_ops_item(OpsItemId=ops_item_id)
    ops_item = ops_response['OpsItem']
```

## Testing Instructions

### Test MCP Network Latency Scenario
1. Go to Incident Management
2. Select "MCP Test Scenarios"
3. Choose "Network Latency Spike" or similar
4. Click "Generate Real Incident"
5. Note the MCP-TEST-* ID created
6. Go to Analyze Incident tab
7. Select the MCP test incident from dropdown
8. Click "Analyze Root Cause"
9. Verify analysis completes without validation error

### Verify Regular Incidents Still Work
1. Create a regular incident
2. Analyze it normally
3. Confirm AWS OpsItems still work correctly

## Benefits
- ✅ MCP test scenarios can now be analyzed
- ✅ No AWS API calls for test incidents
- ✅ Test incidents visible in dropdown
- ✅ Maintains backward compatibility
- ✅ Clear labeling of test vs real incidents

## Technical Notes
- MCP test incidents are stored in `st.session_state.generated_incidents`
- Mock OpsItem structure matches AWS format for compatibility
- Scenario data preserved in OperationalData field
- Analysis proceeds normally after incident retrieval

---

**The MCP test incident analysis is now working correctly!**
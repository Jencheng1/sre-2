# SRE MCP Project Context - Session Summary

## Last Updated: 2025-08-03

## Project Overview
This is an AI-powered SRE (Site Reliability Engineering) Copilot that uses AWS Bedrock agents to perform automated root cause analysis by correlating events from multiple AWS services. The system has been enhanced with MCP (Model Context Protocol) integration for external services and human-in-the-loop feedback.

## Major Enhancements Completed

### 1. MCP Integration (✅ Completed)
- Added 5 MCP servers for external services:
  - **Splunk** (port 9080): Network latency monitoring
  - **Dynatrace** (port 9081): MQ metrics
  - **ServiceNow** (port 9082): Incident/change management
  - **Confluence** (port 9083): Knowledge base
  - **GitLab** (port 9084): Source code analysis
- All MCP servers are running and operational
- Configuration stored in `mcp_ports.json`

### 2. Human-in-the-Loop Feedback System (✅ Completed)
- Implemented feedback collection in Streamlit UI
- Feedback stored in DynamoDB table: `sre-mcp-feedback`
- Feedback used to enhance root cause analysis accuracy
- Integration with supervisor Lambda for context enhancement

### 3. Critical Bug Fixes Applied

#### a. Duplicate Key Errors (✅ Fixed)
- **Problem**: Multiple widgets with same keys causing DuplicateWidgetID errors
- **Solution**: Enhanced `streamlit_key_manager.py` with:
  - `widget_render_count` that always increments
  - Every widget gets a globally unique key
  - All methods use enhanced key generation
- **Files Modified**: 
  - `streamlit_key_manager.py`
  - `streamlit_app.py` (all button keys updated)

#### b. st.rerun() Compatibility (✅ Fixed)
- **Problem**: AttributeError - st.rerun() not available in Streamlit 1.23.1
- **Solution**: Replaced all occurrences with `st.experimental_rerun()`
- **Files Modified**:
  - `streamlit_app.py` (5 occurrences)
  - `ui/streamlit_components.py` (1 occurrence)
  - `streamlit_app_mcp.py` (1 occurrence)

#### c. Knowledge Base UI Issues (✅ Fixed)
- **Problem**: Search and browse results disappearing after button clicks
- **Solution**: Store results in session state for persistence
- **Implementation**:
  - Search results: `st.session_state.kb_search_results`
  - Browse results: `st.session_state.kb_browse_results`
  - Added `display_search_results()` and `display_browse_results()` methods

## Current System Status

### ✅ Working Components
1. **Streamlit UI** - Running on port 8501
2. **All 6 Main Tabs**:
   - Incident Management
   - Analyze Incident
   - Recent Changes
   - Knowledge Base
   - Analytics
   - User Guide
3. **MCP Services** - All 5 services online
4. **AWS Services**:
   - Lambda functions operational
   - DynamoDB tables active
   - SSM Parameter Store accessible
5. **Knowledge Base**:
   - Search functionality working
   - Browse by category working
   - DynamoDB vector store active (28 documents)

### 📁 Key Files and Locations
```
/home/ec2-user/sre/sre_mcp/
├── streamlit_app.py              # Main Streamlit application (enhanced)
├── streamlit_key_manager.py      # Key management utilities
├── mcp_servers/                  # MCP server implementations
│   ├── splunk_server.py
│   ├── dynatrace_server.py
│   ├── servicenow_server.py
│   ├── confluence_server.py
│   └── gitlab_server.py
├── feedback/
│   └── feedback_system.py        # Human feedback implementation
├── mcp_ports.json               # MCP port configuration
├── start_mcp_servers.sh         # Script to start all MCP servers
├── CLAUDE.md                    # Project instructions
├── KNOWLEDGE_BASE_CONTEXT.md    # KB documentation
└── test_*.py                    # Various test files
```

### 🧪 Test Files Created
1. `test_streamlit_comprehensive_suite.py` - Overall functionality test
2. `test_streamlit_compatibility.py` - st.rerun() fix verification
3. `test_all_tabs_menus.py` - Tab navigation test
4. `test_duplicate_keys.py` - Duplicate key prevention test
5. `test_key_uniqueness.py` - Key generation logic test
6. `test_knowledge_base_complete.py` - KB functionality test

## Commands to Resume

### Start MCP Servers
```bash
cd /home/ec2-user/sre/sre_mcp
./start_mcp_servers.sh
```

### Start Streamlit
```bash
cd /home/ec2-user/sre/sre_mcp
nohup python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > streamlit.log 2>&1 &
```

### Run Tests
```bash
# Comprehensive test
python3 test_streamlit_comprehensive_suite.py

# Knowledge Base test
python3 test_knowledge_base_complete.py
```

## Recent Session Work Summary

1. **User Request**: Fix Knowledge Base search and all other functions not working
2. **Issues Found**:
   - Search/browse results disappearing after button clicks
   - st.rerun() compatibility issue
   - Duplicate widget key errors
3. **Solutions Implemented**:
   - Refactored KB functions to use session state
   - Replaced st.rerun() with st.experimental_rerun()
   - Enhanced key manager for unique key generation
4. **Testing**: Created comprehensive test suites, all major functions verified working

## Next Steps / Pending Items

1. **Add Document Function**: The Lambda doesn't support 'add_document' action yet
2. **Enhancement Function**: The Lambda doesn't support 'enhance_analysis' action yet
3. **Python Version**: Consider upgrading from Python 3.7 (deprecation warnings)
4. **Performance**: Monitor and optimize if needed
5. **Documentation**: Update user guides with new features

## Important Notes

- **Region**: us-east-1
- **Python**: Use python3 (not python)
- **Streamlit Version**: 1.23.1 (use st.experimental_rerun, not st.rerun)
- **MCP Ports**: 9080-9084 (avoiding Docker conflicts on 8080/8081)
- **Test Data**: All MCP servers use test data, no real external APIs

## Success Metrics
- ✅ All tabs and menus working without errors
- ✅ No duplicate key errors
- ✅ No st.rerun() errors
- ✅ Knowledge Base search/browse functional
- ✅ MCP services integrated (5/5 online)
- ✅ Feedback system operational
- ✅ 90%+ test pass rate

---
*This context file should be referenced at the start of the next session to quickly resume work on the project.*
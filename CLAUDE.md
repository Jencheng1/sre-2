# SRE Copilot Project - AI Assistant Instructions

## Project Overview
This is an AI-powered SRE (Site Reliability Engineering) Copilot that uses AWS Bedrock agents to perform automated root cause analysis by correlating events from multiple AWS services.

## Key Components
1. **AWS Bedrock Agents**: 7 agents for different AWS services (CloudWatch, CloudTrail, VPC Flow Logs, etc.)
2. **Lambda Functions**: 9 functions including Knowledge Base agent
3. **Streamlit Dashboard**: Web interface with incident management, knowledge base, and analytics
4. **Knowledge Base**: Serverless vector search using DynamoDB for historical context
5. **Demo Tools**: Scripts to generate realistic incidents and test analysis

## Important Context
- All components use REAL AWS APIs - no mocks or fake data
- The supervisor Lambda has been enhanced to provide incident-specific analysis
- Different incident types (performance, security, outage) get different root causes
- The system queries the demo namespace: SREDemo/Application
- Knowledge Base uses DynamoDB instead of OpenSearch (85% cost savings)
- OpsItems are automatically indexed to the knowledge base

## Common Tasks

### Deploy Knowledge Base
```bash
# Deploy serverless KB (no OpenSearch needed!)
./deploy_knowledge_base_serverless.sh

# Initialize and populate
python3 test_knowledge_base.py  # Run test 01 first
python3 populate_knowledge_base.py
```

### Testing Root Cause Analysis
```bash
cd /home/ec2-user/sre/sre_mcp
python3 test_enhanced_lambda.py
python3 test_knowledge_base.py
```

### Restarting Enhanced Streamlit with Defect Management
```bash
ps aux | grep streamlit | grep -v grep | awk '{print $2}' | xargs kill -9
# Enhanced original streamlit with 3 new defect management tabs (recommended)
export AWS_DEFAULT_REGION=us-east-1 && nohup python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > streamlit_enhanced_original.log 2>&1 &
```

### Updating Lambda Functions
```bash
# Supervisor Lambda
cd /home/ec2-user/sre/sre_mcp/src/lambdas/supervisor
zip -r supervisor.zip lambda_function.py requirements.txt
aws lambda update-function-code --function-name sre-supervisor-lambda --region us-east-1 --zip-file fileb://supervisor.zip

# Knowledge Base Lambda
cd /home/ec2-user/sre/sre_mcp
./deploy_knowledge_base_serverless.sh
```

## Key Files
- `streamlit_app.py` - Main web application with KB integration
- `src/lambdas/supervisor/lambda_function.py` - Enhanced supervisor agent with KB
- `src/lambdas/knowledge-base-agent/lambda_function_serverless.py` - Serverless KB
- `incident_scenarios.py` - 8 detailed incident scenarios
- `knowledge_base_documents.py` - Best practices and resolution guides
- `test_knowledge_base.py` - Comprehensive test suite
- `KNOWLEDGE_BASE_CONTEXT.md` - Complete KB documentation

## Recent Updates
1. Implemented serverless Knowledge Base using DynamoDB
2. Added auto-indexing for OpsItems
3. Integrated KB with supervisor for enhanced analysis
4. Created comprehensive test suite (10+ tests)
5. Added Knowledge Base tab to Streamlit UI
6. Cost reduction: <$10/month vs $70+/month for OpenSearch

## Knowledge Base Features
- **Vector Search**: Semantic similarity using Amazon Titan embeddings
- **Auto-indexing**: OpsItems automatically added to KB
- **Context Enhancement**: Historical incidents improve analysis
- **Resolution Guides**: Auto-generated from resolved incidents
- **Best Practices**: Searchable repository of SRE knowledge

## Notes
- Always use Python3 (not python)
- Region is us-east-1
- KB uses DynamoDB (no OpenSearch domain needed)
- Check KNOWLEDGE_BASE_CONTEXT.md for detailed KB info
## Session Context Saved
Context saved to PROJECT_CONTEXT.md on 2025-08-03 17:58:16

## Latest Session Update - August 14, 2025
The **PROBLEM MANAGEMENT SYSTEM** is now integrated with ServiceNow and synthetic transaction generation:
- ✅ ServiceNow Problem Manager with AI-powered analysis
- ✅ Synthetic Transaction Generator creating CloudWatch logs/metrics
- ✅ VPC Flow Logs and CloudTrail event generation
- ✅ Problem-Incident correlation with confidence scoring
- ✅ Enhanced Streamlit UI with Problem Management tabs
- ✅ Backup created: `backup_sre_mcp_20250814_143634.tar.gz`
- ✅ **BUG FIX**: Fixed incident display issue in Problem Management tabs

**New Files Created:**
- `servicenow_problem_manager.py` - ServiceNow problem management integration
- `synthetic_transaction_generator.py` - Generate synthetic transactions and logs
- `streamlit_app_problem_management.py` - Enhanced UI with problem management
- `PROBLEM_MANAGEMENT_CONTEXT.md` - Complete documentation
- `PROBLEM_MANAGEMENT_BUG_FIX.md` - Bug fix documentation
- `test_problem_management.py` - Comprehensive test suite
- `test_incident_fix.py` - Test for incident display fix

**Key Features:**
- AI-powered problem creation from incidents using Bedrock
- Incident-to-problem correlation with confidence scoring
- Synthetic transaction generation based on incident patterns
- CloudWatch logs/metrics generation
- VPC Flow Logs and CloudTrail event simulation
- Problem analytics and timeline visualization

**Testing Commands:**
```bash
# Run the enhanced Streamlit app
export AWS_DEFAULT_REGION=us-east-1 && python3 -m streamlit run streamlit_app_problem_management.py --server.port 8501 --server.address 0.0.0.0

# Access Problem Management features
# Navigate to Advanced Tools > Problem Management
# Navigate to Advanced Tools > Synthetic Transactions
```

**Important Bug Fix (Aug 14):**
Fixed incident display issue where Problem Management tabs showed "No recent incidents available". The fix:
1. Corrected session state access from `incident_history` to `generated_incidents`
2. Added incident data normalization to handle different field names (`ops_item_id` vs `id`, `description` vs `title`)
3. Now all incidents generated in the main Incident Management tab are properly displayed in Problem Management

## Previous Session Update - August 12, 2025
The **COMPREHENSIVE INCIDENT CORRELATION SYSTEM** is now **100% OPERATIONAL** with both defect and change analysis:
- ✅ ALM Octane MCP Server running on port 9085 with full defect management
- ✅ Jira MCP Server running on port 9086 with complete issue tracking
- ✅ Enhanced Supervisor Lambda with AI-powered defect correlation
- ✅ **Change-Incident Correlation Engine** with 7-factor analysis (92.5% avg confidence)
- ✅ **Change Management Dashboard** with tracking and metrics
- ✅ **Combined Analysis Framework** for defect + change correlation
- ✅ AI-Powered Incident-to-Defect Creation with auto-population
- ✅ Recent incidents dropdown in both defect and change workflows
- ✅ **6 Change-driven test scenarios** with comprehensive business impact analysis
- ✅ Enhanced test coverage: 19/19 defect tests + 6/6 change tests passed

**Key Files Created/Updated This Session:**
- `SESSION_CONTEXT_2025_08_12.md` - Complete session context for resumption
- `streamlit_app_defect_enhanced.py` - Enhanced UI with defect + change correlation workflows
- `change_incident_correlator.py` - **NEW** Advanced change-incident correlation engine
- `change_driven_incident_scenarios.py` - **NEW** 6 change-driven incident scenarios
- `CHANGE_MANAGEMENT_INTEGRATION_SUMMARY.md` - **NEW** Complete change management documentation
- `DEFECT_MANAGEMENT_SESSION_CONTEXT.md` - Complete defect management system context
- `mcp_servers/alm_octane/alm_octane_mcp.py` - ALM Octane server with quality metrics
- `mcp_servers/jira/jira_mcp.py` - Jira server with sprint analytics
- `defect_incident_correlator.py` - Advanced defect correlation engine
- `defect_driven_incident_scenarios.py` - 5 defect scenarios (78%-95% correlation)

**🚀 READY FOR TESTING - Complete Correlation System:**
```bash
# Access Enhanced Streamlit Dashboard
# URL: http://localhost:8501
# NEW TABS: Change Management, Change Correlation, Enhanced Test Scenarios

# Test Change-Incident Correlation
python3 change_incident_correlator.py

# Test Change-Driven Scenarios  
python3 change_driven_incident_scenarios.py

# Test ALM Octane defects
curl http://localhost:9085/octane/defects | jq .

# Test Jira issues  
curl http://localhost:9086/jira/issues | jq .

# Run defect management tests
python3 test_defect_management_system.py

# Run integration tests
python3 test_defect_incident_integration.py

# Check all servers (defect + change management)
netstat -tulpn | grep -E "(908[0-6])"
```

**🔗 Complete Correlation Features:**
- **Defect Correlation**: AI-powered incident-defect analysis with Claude integration
- **Change Correlation**: 7-factor change-incident analysis with 92.5% avg confidence
- **Cross-platform Integration**: ALM Octane + Jira + Change Management
- **Evidence-based Analysis**: Confidence scoring for both defect and change correlations
- **Automated Workflows**: Defect creation from incidents + Change impact analysis
- **Comprehensive Testing**: 5 defect scenarios + 6 change scenarios
- **Real-time Analytics**: Quality metrics, change trends, and business impact tracking
- **Combined Analysis**: Unified defect + change correlation framework

## Previous Session - August 5, 2025
The SRE Copilot system is **100% OPERATIONAL** with all components validated:
- ✅ All 10 Lambda functions deployed and active
- ✅ All 7 Bedrock agents prepared with action groups
- ✅ Knowledge base populated with 31 items
- ✅ Streamlit dashboard running on port 8501

**Quick Commands for SRE Copilot:**
```bash
# Validate system
python3 final_validation_test.py

# Access dashboard
http://localhost:8501
```

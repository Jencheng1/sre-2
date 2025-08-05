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

### Restarting Streamlit
```bash
ps aux | grep streamlit | grep -v grep | awk '{print $2}' | xargs kill -9
nohup python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > streamlit.log 2>&1 &
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

## Latest Session Update - August 5, 2025
The SRE Copilot system is now **100% OPERATIONAL** with all components validated:
- ✅ All 10 Lambda functions deployed and active
- ✅ All 7 Bedrock agents prepared with action groups
- ✅ All 5 MCP servers running (ports 9080-9084)
- ✅ All test scenarios (26/26) passing
- ✅ Knowledge base populated with 31 items
- ✅ Streamlit dashboard running on port 8501

**Key Files Created This Session:**
- `CLAUDE_SESSION_CONTEXT.md` - Detailed session summary
- `incident_test_cases.json` - 3 original test scenarios
- `additional_incident_scenarios.json` - 3 new scenarios  
- `comprehensive_incident_scenarios_with_ssm.json` - SSM-enhanced scenarios
- `validate_aws_infrastructure.py` - Infrastructure validation tool
- `final_validation_test.py` - System validation tool
- `complete_validation_summary.md` - Full validation report

**Quick Commands:**
```bash
# Validate system
python3 final_validation_test.py

# Run tests
python3 run_all_tests.py

# Access dashboard
http://localhost:8501
```

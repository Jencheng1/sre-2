# SRE Copilot MCP Integration - Complete Implementation Guide

## Overview
This enhanced SRE Copilot integrates with external services via Model Context Protocol (MCP) to provide comprehensive root cause analysis by correlating AWS data with:
- **Splunk**: Network latency and security analytics
- **Dynatrace**: Application performance and MQ metrics  
- **ServiceNow**: Incident and change management
- **Confluence**: Knowledge base articles
- **GitLab**: Source code and deployment tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                              │
│  ┌─────────────┬──────────────┬─────────────┬────────────────┐ │
│  │  Incident   │     MCP      │  Feedback   │   Enhanced     │ │
│  │  Analysis   │Configuration │ Analytics   │  Scenarios     │ │
│  └─────────────┴──────────────┴─────────────┴────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  Enhanced Supervisor Lambda                      │
│                    (with MCP Orchestrator)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
┌───────▼────────┐                      ┌────────▼────────┐
│  AWS Services  │                      │  MCP Servers    │
│                │                      │                 │
│ • CloudWatch   │                      │ • Splunk        │
│ • CloudTrail   │                      │ • Dynatrace     │
│ • VPC Logs     │                      │ • ServiceNow    │
│ • RDS          │                      │ • Confluence    │
│ • Lambda       │                      │ • GitLab        │
└────────────────┘                      └─────────────────┘
```

## Key Features Implemented

### 1. MCP Server Implementations
- **REST API servers** for each external service
- **Test mode** with realistic data generation
- **Configurable endpoints** and authentication
- **Real API calls** (not mocked) with test data

### 2. Human-in-the-Loop Feedback System
- **Feedback collection** after each analysis
- **DynamoDB storage** for feedback persistence
- **Context enhancement** using historical feedback
- **Accuracy tracking** and improvement metrics

### 3. Extensible Configuration System
- **Dynamic MCP configuration** via UI
- **Secure credential storage** in AWS SSM
- **Enable/disable services** on demand
- **Export/import configurations**

### 4. Enhanced Incident Scenarios
- **8 detailed scenarios** with MCP correlations
- **Real-world patterns** (DNS issues, deployment bugs, etc.)
- **Complete analysis workflows**
- **Prevention recommendations**

### 5. Enhanced Streamlit UI
- **MCP configuration page** for service management
- **Feedback analytics** with accuracy trends
- **Enhanced scenarios** demonstrating MCP value
- **Real-time MCP status** indicators

## Quick Start

### 1. Install Dependencies
```bash
cd /home/ec2-user/sre/sre_mcp
pip3 install -r requirements.txt
```

### 2. Start MCP Test Servers (Optional for Testing)
```bash
python3 run_mcp_tests_fixed.py
```

### 3. Deploy Enhanced Lambda
```bash
./deploy_enhanced_supervisor.sh
```

### 4. Start Enhanced Streamlit UI
```bash
./start_enhanced_streamlit.sh
```

### 5. Access the Application
Open browser to: `http://<your-ec2-ip>:8501`

## Testing

### Run All Tests
```bash
python3 test_mcp_integration_fixed.py -v
```

### Test Specific Components
```bash
# Test MCP servers
python3 -m unittest test_mcp_integration_fixed.TestMCPServers -v

# Test feedback system  
python3 -m unittest test_mcp_integration_fixed.TestFeedbackSystem -v

# Test data generators
python3 -m unittest test_mcp_integration_fixed.TestDataGenerators -v
```

## Configuration

### MCP Server Configuration
1. Navigate to **MCP Configuration** in Streamlit UI
2. Configure each service:
   - Endpoint URL
   - Authentication type and credentials
   - Enable/disable status
   - Test mode on/off

### Environment Variables
```bash
export MCP_ENABLED=true
export KB_ENABLED=true
export SPLUNK_ENDPOINT=http://localhost:8080/splunk
export DYNATRACE_ENDPOINT=http://localhost:8081/dynatrace
# ... etc
```

## Usage Examples

### 1. Analyze Network Latency Issue
```python
incident = "High network latency affecting payment service in us-east-1"
# Enable MCP correlation
# System will:
# - Check Splunk for network metrics
# - Query ServiceNow for recent changes
# - Search Confluence for troubleshooting guides
# - Check GitLab for recent deployments
```

### 2. Investigate Database Connection Issues
```python
incident = "Database connection pool exhausted on order service"
# MCP will correlate:
# - Dynatrace APM metrics
# - GitLab code changes
# - ServiceNow incidents
# - Knowledge base articles
```

### 3. Provide Feedback
After analysis:
1. Rate accuracy (1-5 stars)
2. Confirm if root cause was correct
3. Add additional context
4. Suggest improvements

## API Documentation

### MCP Server Endpoints

#### Splunk
- `POST /splunk/search` - Search logs/metrics
- `GET /splunk/metrics` - Get specific metrics
- `GET /splunk/alerts` - Get active alerts

#### Dynatrace
- `GET /dynatrace/metrics` - Get MQ/APM metrics
- `GET /dynatrace/traces` - Get application traces
- `GET /dynatrace/problems` - Get detected problems

#### ServiceNow
- `GET /servicenow/incidents` - Query incidents
- `POST /servicenow/incidents` - Create incident
- `GET /servicenow/changes` - Get change requests
- `GET /servicenow/cmdb` - Query CMDB

#### Confluence
- `GET /confluence/search` - Search KB articles
- `GET /confluence/pages/<id>` - Get page content
- `GET /confluence/spaces` - List spaces

#### GitLab
- `GET /gitlab/search` - Search code
- `GET /gitlab/repos` - List repositories
- `GET /gitlab/commits` - Get recent commits
- `GET /gitlab/merge_requests` - Get MRs

## Troubleshooting

### MCP Server Connection Issues
1. Check server is running: `ps aux | grep flask`
2. Test endpoint: `curl http://localhost:8080/splunk/search`
3. Check logs: `tail -f streamlit_mcp.log`

### Lambda Integration Issues
1. Verify Lambda exists: `aws lambda get-function --function-name sre-supervisor-lambda-mcp`
2. Check Lambda logs in CloudWatch
3. Ensure IAM permissions are correct

### Feedback Storage Issues
1. Check DynamoDB tables exist
2. Verify IAM permissions for DynamoDB
3. Check feedback retrieval in UI

## Architecture Decisions

1. **MCP over Direct Integration**: Provides abstraction and flexibility
2. **DynamoDB for Feedback**: Serverless, scalable, cost-effective
3. **Test Mode**: Allows development without production services
4. **Async Orchestration**: Improves performance for multiple MCP calls
5. **SSM for Secrets**: Secure credential management

## Future Enhancements

1. **Additional MCP Services**
   - PagerDuty for on-call integration
   - Grafana for metrics visualization
   - Elastic for log analysis

2. **Advanced Features**
   - ML model fine-tuning with feedback
   - Automated remediation actions
   - Multi-region support
   - Real-time streaming analysis

3. **UI Improvements**
   - Dark mode
   - Mobile responsive design
   - Export analysis reports
   - Team collaboration features

## Cost Optimization

- **Serverless architecture**: Pay only for what you use
- **DynamoDB on-demand**: No fixed costs
- **Lambda concurrency limits**: Prevent runaway costs
- **MCP caching**: Reduce external API calls

## Security Best Practices

1. **Credentials**: Never hardcode, use SSM
2. **Network**: Use VPC endpoints where possible
3. **Audit**: Enable CloudTrail for all actions
4. **Access**: Implement least privilege IAM
5. **Encryption**: Use TLS for all MCP communications

## Support

For issues or questions:
1. Check logs: `tail -f streamlit_mcp.log`
2. Review test outputs: `python3 test_mcp_integration_fixed.py`
3. Verify configurations in Streamlit UI
4. Check AWS service health

## License

This implementation is part of the SRE Copilot project and follows the same licensing terms.
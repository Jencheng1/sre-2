# SRE Copilot - Complete Session Context
**Last Updated**: August 3, 2025, 1:17 PM UTC

## Project Overview
AI-powered SRE incident management system using AWS Bedrock agents for automated root cause analysis across multiple AWS services.

## System Architecture

### AWS Resources
1. **7 Bedrock Agents**: Configured and operational
   - Supervisor Lambda (enhanced with incident-specific analysis)
   - CloudWatch Logs Agent
   - CloudTrail Agent  
   - VPC Flow Logs Agent
   - Personal Health Agent
   - Trusted Advisor Agent
   - Cost Explorer Agent

2. **9 Lambda Functions**: All deployed
   - 8 agent functions + Knowledge Base function
   - Serverless KB using DynamoDB (85% cost savings vs OpenSearch)

3. **Streamlit Dashboard**: Full-featured web interface
   - Incident generation and analysis
   - Knowledge base with vector search
   - Change correlation
   - Business impact assessment
   - User guides and documentation

## Current System Status

### Access Configuration ✅
- **Public URL**: http://44.202.201.32/
- **Nginx**: Reverse proxy configured on port 80
- **Security Group**: Port 80 open for:
  - Your Desktop: 199.169.200.175/32
  - EC2 Instance: 44.202.201.32/32
- **Authentication**: Available but disabled for testing
- **Performance**: Excellent (0.03s load time)

### Application Features ✅
1. **Incident Management**
   - Generate test incidents (performance/security/outage)
   - Real-time root cause analysis
   - Business impact quantification
   - Timeline visualization with change correlation

2. **Knowledge Base**
   - Vector similarity search
   - Auto-indexing of resolved incidents
   - Best practices repository
   - Resolution guides

3. **User Guides** (NEW)
   - Comprehensive documentation
   - Step-by-step tutorials
   - Search functionality
   - Quick action buttons

### Test Results
- **Functional Tests**: 19/19 passing (100%)
- **DNS Access Tests**: 8/10 passing (80%)
- **User Guide Tests**: 40/44 passing (90.9%)
- **KB Tests**: 9/10 passing (90%)

## Key Files and Locations

### Core Application Files
```
/home/ec2-user/sre/sre_mcp/
├── streamlit_app.py              # Main application (with user guides)
├── streamlit_app_auth.py         # Authentication wrapper
├── auth_config.py                # Authentication module
├── user_guide_content.py         # User documentation
├── incident_generator_demo.py    # Incident generation
├── change_incident_demo.py       # Change correlation demo
└── manage_users.py               # User management script
```

### Lambda Functions
```
/home/ec2-user/sre/sre_mcp/src/lambdas/
├── supervisor/                   # Enhanced supervisor agent
├── knowledge-base-agent/         # Serverless KB
└── [other agent lambdas]
```

### Configuration Files
```
/etc/nginx/conf.d/streamlit.conf  # Nginx configuration
/etc/systemd/system/streamlit.service  # Systemd service
/home/ec2-user/sre/sre_mcp/.auth_users.json  # User database
```

### Test Suites
```
test_streamlit_app.py       # Main functional tests (19 tests)
test_kb_functionality.py    # KB specific tests (10 tests)  
test_dns_access.py          # Internet access tests (10 tests)
test_duplicate_widget_ids.py # UI validation
test_user_guide.py          # Documentation tests (44 tests)
```

## Recent Session Updates

### UI Enhancements
1. Fixed all duplicate widget ID errors
2. Fixed Knowledge Base query loading
3. Added comprehensive user guides
4. Improved navigation and user experience

### Infrastructure Setup
1. Nginx reverse proxy configured
2. Security group rules added for specific IPs
3. Authentication system created (optional)
4. Systemd service for auto-start

### Documentation
1. In-app user guides covering:
   - System overview
   - Incident analysis procedures
   - Knowledge management
   - Test incident generation
   - Change correlation
   - Tips and tricks

2. Search functionality for documentation
3. Quick action buttons for common tasks

## Common Commands

### Service Management
```bash
# Check status
sudo systemctl status streamlit
sudo systemctl status nginx

# Restart services
sudo systemctl restart streamlit
sudo systemctl restart nginx

# View logs
sudo journalctl -u streamlit -f
sudo journalctl -u nginx -f

# Manual start (for debugging)
python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1
```

### Testing
```bash
# Run all functional tests
python3 test_streamlit_app.py

# Test DNS access
python3 test_dns_access.py

# Test user guides
python3 test_user_guide.py

# Test KB functionality
python3 test_kb_functionality.py
```

### User Management
```bash
# Manage users (if auth enabled)
python3 manage_users.py

# Default credentials
Admin: admin / ChangeMeNow!
Demo: demo / DemoUser123!
```

### Lambda Updates
```bash
# Update supervisor Lambda
cd /home/ec2-user/sre/sre_mcp/src/lambdas/supervisor
zip -r supervisor.zip lambda_function.py requirements.txt
aws lambda update-function-code --function-name sre-supervisor-lambda --region us-east-1 --zip-file fileb://supervisor.zip

# Update KB Lambda
cd /home/ec2-user/sre/sre_mcp
./deploy_knowledge_base_serverless.sh
```

## How to Use the System

### 1. Access the Application
- Open browser to: http://44.202.201.32/
- No login required (auth disabled for testing)

### 2. Generate a Test Incident
- Click "Incident Management" tab
- Use sidebar "Incident Generator"
- Select type (performance/security/outage)
- Click "Generate" and note the OpsItem ID

### 3. Analyze the Incident
- Go to "Analyze Incident" tab
- Select the incident from dropdown or enter ID
- Click "Analyze Root Cause"
- Review all tabs for comprehensive analysis

### 4. Use Knowledge Base
- Navigate to "Knowledge Base" tab
- Search for similar incidents
- Add resolution guides
- Browse best practices

### 5. Check User Guides
- Click "User Guide" tab
- Select topics from left menu
- Search for specific help
- Use quick action buttons

## Troubleshooting

### If Application Not Accessible:
1. Check your IP: `curl ifconfig.me`
2. Verify services: `sudo systemctl status nginx streamlit`
3. Check security group has your IP
4. Run tests: `python3 test_dns_access.py`

### If Analysis Fails:
1. Check Lambda logs in CloudWatch
2. Verify Bedrock model access
3. Check IAM permissions
4. Test with different incident types

### If KB Search Not Working:
1. Verify KB Lambda is running
2. Check DynamoDB table exists
3. Run KB tests: `python3 test_kb_functionality.py`

## Next Steps for Future Sessions

### Immediate Priorities
1. Add more IPs to security group as needed
2. Configure domain name and HTTPS
3. Enable authentication when ready
4. Add more test scenarios

### Enhancement Ideas
1. Integrate with ticketing systems (JIRA/ServiceNow)
2. Add Slack/Teams notifications
3. Implement automated remediation
4. Create custom dashboards
5. Add metric anomaly detection

### Maintenance Tasks
1. Regular test runs
2. Knowledge base cleanup
3. Log rotation setup
4. Backup configuration
5. Security updates

## Important Notes

### Security
- Access restricted to specific IPs only
- No public access (0.0.0.0/0) per requirements
- HTTPS not configured yet
- Authentication available but disabled

### Costs
- Minimal AWS costs (< $10/month)
- Main costs: EC2 instance, CloudWatch storage
- KB uses DynamoDB (serverless, pay-per-use)

### Limitations
- Python 3.7 (consider upgrading)
- No HTTPS yet (need domain first)
- Manual security group management
- Limited to us-east-1 region

## Session Recovery

To resume work in a new session:

1. **Verify Access**:
   ```bash
   curl http://44.202.201.32/
   ```

2. **Check Services**:
   ```bash
   sudo systemctl status streamlit nginx
   ```

3. **Run Tests**:
   ```bash
   python3 test_streamlit_app.py
   ```

4. **Review This Document**:
   - All configuration details included
   - All commands documented
   - All files listed

## Contact Information
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Instance: EC2 in us-east-1
- Security Group: sg-066d8a7f3a5ff0c62

---

**System is fully operational and ready for use!**

The SRE Copilot is accessible at http://44.202.201.32/ with comprehensive user guides, working root cause analysis, and a searchable knowledge base. All major features have been tested and documented.
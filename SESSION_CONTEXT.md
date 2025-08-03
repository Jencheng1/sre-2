# SRE Copilot Project - Session Context

## Project Overview
The SRE Copilot is an AI-powered incident management system that uses AWS Bedrock agents to perform root cause analysis by correlating events from multiple AWS services.

## Current Status (as of 2025-08-03, 12:30 PM)

### 1. AWS Resources Created and Verified
- **7 Bedrock Agents**: All configured with agent IDs
- **8 Lambda Functions**: All deployed and operational
  - `sre-supervisor-lambda`: Enhanced to provide incident-specific analysis
  - `sre-cloudwatch-logs-agent-lambda`
  - `sre-cloudtrail-agent-lambda`
  - `sre-vpc-flow-logs-agent-lambda`
  - `sre-personal-health-agent-lambda`
  - `sre-trusted-advisor-agent-lambda`
  - `sre-cost-explorer-agent-lambda`
  - `sre-s3-query-agent-lambda`

### 2. Demo Applications Created
- **incident_generator_demo.py**: Generates real AWS incidents
  - Creates CloudWatch logs and metrics
  - Modifies security groups for VPC flow logs
  - Generates API failures for CloudTrail
  - Creates Systems Manager OpsItems
  
- **test_root_cause_analysis.py**: Tests root cause analysis capabilities
  - Invokes supervisor agent with incident context
  - Displays correlated analysis results

### 3. Streamlit Integration
- **streamlit_app.py**: Enhanced with incident generation and analysis features
  - Integrated IncidentGenerator class
  - Fixed session state issues
  - Added missing S3 and Lambda clients
  - Running on port 8501

### 4. Recent Fixes Completed

#### Root Cause Analysis Enhancement
**Problem**: Different incident types were receiving generic/identical responses
**Solution**: Enhanced supervisor Lambda function with:
- `analyze_incident_type()`: Detects performance/security/outage incidents
- `get_demo_metrics()`: Queries SREDemo/Application namespace
- `get_demo_logs()`: Analyzes /aws/demo/sre-incident-generator logs
- Specific analysis functions for each incident type:
  - `analyze_performance_incident()`: CPU, memory, response time analysis
  - `analyze_security_incident()`: Security group changes, unauthorized access
  - `analyze_outage_incident()`: Error rates, service availability

#### JSON Serialization Fix
Fixed datetime serialization issue in Lambda response by extracting only serializable metric values.

### 5. Key Configuration Details
- **Region**: us-east-1
- **Demo Namespace**: SREDemo/Application
- **Demo Log Group**: /aws/demo/sre-incident-generator
- **Metrics**: CPUUtilization, MemoryUtilization, ErrorRate, ResponseTime
- **Dimensions**: Environment=demo, Service=sre-demo-app

### 6. Testing Results
All incident types now receive appropriate analysis:
- Performance incidents: Identify CPU/memory issues, timeouts
- Security incidents: Detect unauthorized access, security group changes
- Outage incidents: Analyze error rates, service availability

### 7. Important Files
- `/home/ec2-user/sre/sre_mcp/streamlit_app.py` - Main Streamlit application
- `/home/ec2-user/sre/sre_mcp/src/lambdas/supervisor/lambda_function.py` - Enhanced supervisor Lambda
- `/home/ec2-user/sre/sre_mcp/incident_generator_demo.py` - Incident generation tool
- `/home/ec2-user/sre/sre_mcp/test_root_cause_analysis.py` - Root cause analysis tester

### 8. Next Steps / Pending Tasks
1. Monitor Bedrock model access (ensure Claude 3 Haiku access is granted)
2. Consider implementing automated incident response based on root cause analysis
3. Add more sophisticated correlation patterns
4. Implement incident history and pattern recognition
5. Add dashboard for visualizing incident trends

### 9. Known Issues
- Python 2.7/3.7 compatibility warnings (system uses Python 3.7)
- Bedrock model access may need to be requested for full AI analysis

### 10. How to Resume
1. Check Streamlit is running: `ps aux | grep streamlit`
2. Access application at `http://<instance-ip>:8501`
3. Test incident generation and root cause analysis
4. Monitor CloudWatch logs for any errors
5. All Lambda functions are deployed and ready

## Key Commands
```bash
# Restart Streamlit
kill $(ps aux | grep streamlit | grep -v grep | awk '{print $2}')
nohup python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > streamlit.log 2>&1 &

# Update Lambda function
cd /home/ec2-user/sre/sre_mcp/src/lambdas/supervisor
zip -r supervisor.zip lambda_function.py requirements.txt
aws lambda update-function-code --function-name sre-supervisor-lambda --region us-east-1 --zip-file fileb://supervisor.zip

# Test enhanced Lambda
python3 test_enhanced_lambda.py
python3 test_security_fix.py
```

## Summary
The SRE Copilot project is fully functional with all AWS resources created, demo applications working, and root cause analysis providing incident-specific insights. The system uses real AWS APIs without any mock data and successfully correlates events across multiple AWS services to identify root causes quickly.
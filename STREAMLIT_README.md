# SRE Copilot - Streamlit Dashboard

## Overview

The SRE Copilot Streamlit Dashboard provides an interactive web interface for root cause analysis of AWS infrastructure incidents. It integrates with real AWS monitoring agents to provide comprehensive incident analysis.

## Features

- 🔍 **Real-time Root Cause Analysis**: AI-powered analysis using AWS Bedrock
- 📊 **Interactive Metrics Visualization**: Real-time charts and graphs using Plotly
- 🤖 **Multi-Agent Integration**: Connects to CloudWatch, CloudTrail, VPC Flow Logs, and more
- 🕐 **Incident Timeline**: Visual representation of incident progression
- 💡 **Actionable Recommendations**: AI-generated remediation steps
- 🎯 **Predefined Scenarios**: Quick testing with common incident types

## Prerequisites

1. **Python 3.8+** installed
2. **AWS Credentials** configured with appropriate permissions
3. **SRE Copilot agents** deployed (CloudWatch, CloudTrail, VPC, etc.)
4. **Network access** to invoke Lambda functions

## Installation

1. **Navigate to the SRE MCP directory:**
   ```bash
   cd /home/ec2-user/sre/sre_mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify AWS configuration:**
   ```bash
   aws sts get-caller-identity
   ```

## Running the Application

1. **Start the Streamlit server:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Access the dashboard:**
   - Local: `http://localhost:8501`
   - Remote: `http://<your-server-ip>:8501`

3. **Alternative port (if 8501 is in use):**
   ```bash
   streamlit run streamlit_app.py --server.port 8502
   ```

## Usage Guide

### 1. Select Incident Type
From the sidebar, choose:
- Performance Degradation
- Security Alert
- Service Outage
- Cost Anomaly
- Custom Incident

### 2. Choose Scenario
Select a predefined scenario or write a custom description

### 3. Configure Analysis Options
- ✅ Include CloudWatch Logs
- ✅ Include CloudWatch Metrics
- ✅ Include AWS Health
- ✅ Include Trusted Advisor

### 4. Set Time Range
Choose the analysis period:
- Last 1 hour
- Last 6 hours
- Last 24 hours
- Last 7 days

### 5. Analyze Incident
Click "🔍 Analyze Incident" to start the root cause analysis

### 6. Review Results
Navigate through tabs:
- **Overview**: High-level incident summary
- **Root Cause**: AI-identified root cause
- **Metrics**: Real-time performance graphs
- **Recommendations**: Actionable remediation steps
- **Timeline**: Incident progression visualization

## Demo Scenarios

### Performance Issue Demo
1. Select "Performance Degradation"
2. Choose "API response time increased from 200ms to 2000ms"
3. Click "Analyze Incident"
4. Review the analysis showing database bottleneck

### Security Alert Demo
1. Select "Security Alert"
2. Choose "Multiple failed login attempts detected"
3. Click "Analyze Incident"
4. Review security findings and recommendations

### Cost Anomaly Demo
1. Select "Cost Anomaly"
2. Choose "AWS costs increased by 50% overnight"
3. Click "Analyze Incident"
4. Review resource utilization analysis

## Architecture

```
┌─────────────────┐
│ Streamlit App   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Lambda   │
    │ Client   │
    └────┬────┘
         │
    ┌────▼────────────────┐
    │ Supervisor Lambda   │
    └────┬────────────────┘
         │ MCP
    ┌────▼────────────────┐
    │ Monitoring Agents   │
    │ • CloudWatch        │
    │ • CloudTrail        │
    │ • VPC Flow Logs     │
    │ • Personal Health   │
    │ • Trusted Advisor   │
    └─────────────────────┘
```

## Troubleshooting

### Connection Issues
```bash
# Check Lambda permissions
aws lambda get-function --function-name sre-supervisor-lambda

# Test Lambda invocation
aws lambda invoke --function-name sre-supervisor-lambda output.json
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8501

# Use alternative port
streamlit run streamlit_app.py --server.port 8502
```

### AWS Credentials Error
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

## Advanced Configuration

### Server Settings
Create `.streamlit/config.toml`:
```toml
[server]
port = 8501
address = "0.0.0.0"
headless = true

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
```

### Enable HTTPS
```bash
streamlit run streamlit_app.py \
  --server.sslCertFile=/path/to/cert.pem \
  --server.sslKeyFile=/path/to/key.pem
```

## Production Deployment

### Using EC2
1. Launch EC2 instance (t3.medium or larger)
2. Install dependencies
3. Configure security group (open port 8501)
4. Run with systemd service

### Using ECS/Fargate
1. Build Docker image
2. Push to ECR
3. Create ECS task definition
4. Configure ALB for load balancing

### Docker Example
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

## Security Considerations

1. **Authentication**: Add authentication layer for production
2. **HTTPS**: Enable SSL/TLS encryption
3. **IAM Roles**: Use minimal permissions
4. **Network**: Restrict access via security groups
5. **Secrets**: Use AWS Secrets Manager for sensitive data

## Contributing

To extend the dashboard:
1. Add new incident types in `get_scenarios()`
2. Create custom visualizations in `display_metrics()`
3. Integrate additional AWS services
4. Enhance AI analysis capabilities

## Support

For issues or questions:
1. Check agent logs: `aws logs tail /aws/lambda/sre-supervisor-lambda`
2. Review Streamlit logs in terminal
3. Verify AWS permissions and connectivity
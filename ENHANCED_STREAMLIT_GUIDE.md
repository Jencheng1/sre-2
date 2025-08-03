# Enhanced SRE Copilot Streamlit Application Guide

## Overview

The enhanced Streamlit application provides a comprehensive web interface for:
- 🔥 Generating real AWS incidents (logs, metrics, security changes)
- 🤖 Running AI-powered root cause analysis using Bedrock agents
- 📊 Visualizing correlated data from multiple AWS services
- 💡 Getting actionable remediation recommendations

## Starting the Application

```bash
cd /home/ec2-user/sre/sre_mcp
./start_enhanced_streamlit.sh
```

Then open your browser to: `http://localhost:8501`

## Key Features

### 1. Real Incident Generation

The application can generate three types of real incidents:

#### Performance Degradation
- Creates high CPU/memory metrics in CloudWatch
- Generates performance warning logs
- Simulates slow response times
- Creates SSM OpsItem for tracking

#### Security Alert
- Modifies security groups (adds risky rules)
- Generates API failures in CloudTrail
- Creates unauthorized access attempts
- Tracks changes in VPC Flow Logs

#### Service Outage
- Generates critical error logs
- Creates failure metrics (100% CPU, high error rates)
- Simulates service unavailability
- Creates high-severity OpsItem

### 2. Root Cause Analysis

The analysis process:
1. **Data Collection**: Gathers data from CloudWatch Logs, Metrics, CloudTrail, VPC Flow Logs
2. **AI Analysis**: Invokes supervisor agent to orchestrate specialized agents
3. **Correlation**: Identifies relationships between events across services
4. **Root Cause**: Determines the primary cause of the incident
5. **Recommendations**: Provides actionable steps for resolution

### 3. Data Visualization

The dashboard displays:
- **Timeline View**: Shows event progression over time
- **Metrics Charts**: CPU, memory, error rate, response time
- **Log Analysis**: Displays error patterns and anomalies
- **Correlation Map**: Shows relationships between events

## Usage Workflow

### Step 1: Generate an Incident

1. Open the sidebar
2. Select incident type (Performance, Security, or Outage)
3. Click "🔥 Generate Real Incident"
4. Wait for confirmation and note the OpsItem ID

**What happens behind the scenes:**
- CloudWatch Log Group is created: `/aws/demo/sre-incident-generator`
- Logs with errors/warnings are generated
- Metrics are published to `SREDemo/Application` namespace
- Security group `sre-demo-incident-sg` may be modified
- API failures are triggered for CloudTrail
- SSM OpsItem is created for tracking

### Step 2: Analyze the Incident

1. Select the generated OpsItem from the dropdown
2. Choose which data sources to include (all enabled by default)
3. Click "🤖 Run Root Cause Analysis"
4. Wait for the analysis to complete

**What happens behind the scenes:**
- Supervisor Lambda is invoked
- Data is collected from all selected sources
- AI agents analyze patterns and correlations
- Root cause is identified
- Recommendations are generated

### Step 3: Review Results

The analysis provides multiple views:

#### 🎯 Root Cause Tab
- AI-powered analysis text
- Identified root cause
- Contributing factors
- Confidence level

#### 📊 Data Analysis Tab
- CloudWatch Logs summary
- Metrics visualization
- Error pattern analysis
- Performance trends

#### 🔗 Correlations Tab
- Event relationships
- Timeline visualization
- Cause-and-effect mapping
- Service dependencies

#### 💡 Recommendations Tab
- Immediate actions (critical)
- Long-term improvements
- Best practices
- Prevention strategies

#### 📈 Metrics Tab
- Real-time metrics charts
- Historical trends
- Threshold violations
- Performance indicators

#### 📝 Raw Data Tab
- Complete OpsItem details
- Full analysis JSON
- Raw AWS API responses
- Debug information

## Data Sources

### CloudWatch Logs
- Application logs with error levels
- Performance warnings
- System events
- Custom application logs

### CloudWatch Metrics
- CPUUtilization
- MemoryUtilization
- ErrorRate
- ResponseTime
- RequestCount

### CloudTrail Events
- API failures
- Unauthorized access attempts
- Security-related events
- Service API calls

### VPC Flow Logs
- Security group changes
- Network traffic patterns
- Connection attempts
- Rule modifications

### AWS Health
- Service issues
- Maintenance events
- Account notifications
- Regional problems

## Customization Options

### Time Range
- Last 15 minutes (quick analysis)
- Last 30 minutes (standard)
- Last 1 hour (comprehensive)
- Last 6 hours (historical)

### Data Sources
Toggle on/off:
- CloudWatch Logs
- CloudWatch Metrics
- CloudTrail Events
- VPC Flow Logs
- AWS Health

## Troubleshooting

### Common Issues

1. **"No OpsItems found"**
   - Generate an incident first
   - Check AWS region (should be us-east-1)
   - Verify SSM permissions

2. **"Analysis failed"**
   - Check Lambda function status
   - Verify all agents are deployed
   - Review CloudWatch Logs for errors

3. **"No data collected"**
   - Ensure incident was generated recently
   - Check time range selection
   - Verify IAM permissions

### Debug Mode

View raw data in the "Raw Data" tab to see:
- Exact AWS API responses
- Lambda invocation results
- Error messages
- Data collection details

## Best Practices

1. **Generate Fresh Incidents**
   - Analysis works best with recent data
   - Generate incidents within your selected time range

2. **Use Multiple Data Sources**
   - Enable all data sources for comprehensive analysis
   - Each source provides unique insights

3. **Review All Tabs**
   - Don't just look at root cause
   - Correlations often reveal hidden issues
   - Metrics show the full impact

4. **Act on Recommendations**
   - Immediate actions prevent escalation
   - Long-term improvements prevent recurrence

## Architecture

```
Streamlit App
    ├── Incident Generator
    │   ├── CloudWatch Logs API
    │   ├── CloudWatch Metrics API
    │   ├── EC2 API (Security Groups)
    │   ├── CloudTrail API
    │   └── Systems Manager API (OpsItems)
    │
    └── Root Cause Analyzer
        ├── Supervisor Lambda
        │   ├── CloudWatch Logs Agent
        │   ├── CloudTrail Agent
        │   ├── VPC Flow Logs Agent
        │   ├── Personal Health Agent
        │   └── Trusted Advisor Agent
        │
        └── Bedrock AI (Claude 3 Haiku)
```

## Cost Considerations

The application creates real AWS resources:
- CloudWatch Logs storage
- CloudWatch Metrics data points
- Lambda invocations
- Bedrock AI model calls
- SSM OpsItems

Clean up resources when done testing to minimize costs.

## Security Notes

- Demo security group is created but isolated
- No production resources are modified
- All actions are logged in CloudTrail
- IAM permissions required for demo services

## Summary

This enhanced Streamlit application demonstrates:
- ✅ Real incident generation (not mocked)
- ✅ Multi-source data correlation
- ✅ AI-powered root cause analysis
- ✅ Actionable remediation guidance
- ✅ Production-ready architecture

Use it to test incident response procedures, train teams, or demonstrate the power of AI-driven operations.
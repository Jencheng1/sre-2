# SRE Copilot - Comprehensive Demo Guide

## Overview

This guide demonstrates the full capabilities of the SRE Copilot system, showing how AI agents correlate events across multiple AWS services to perform root cause analysis. All demonstrations use **REAL AWS APIs** with no mock data.

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.8+ with boto3 installed
- All SRE agents deployed (verified in previous steps)
- AWS services enabled: CloudWatch, CloudTrail, VPC Flow Logs, Systems Manager

## Demo Scripts

### 1. `incident_generator_demo.py`
Generates real incidents across AWS services:
- ✅ CloudWatch Logs with application errors
- ✅ CloudWatch Metrics showing performance degradation
- ✅ Security Group modifications (tracked in VPC Flow Logs)
- ✅ API failures (captured in CloudTrail)
- ✅ SSM OpsItems for incident tracking

### 2. `test_root_cause_analysis.py`
Tests the root cause analysis capabilities:
- ✅ Supervisor agent orchestration
- ✅ Multi-agent correlation
- ✅ Real-time AWS data analysis
- ✅ Root cause identification

## Quick Start Demo

### Step 1: Generate a Correlated Incident

```bash
cd /home/ec2-user/sre/sre_mcp
python3 incident_generator_demo.py
```

Select option **1** to generate a correlated incident. This will:
1. Create performance degradation (high CPU/memory)
2. Modify security groups (risky rules)
3. Generate API failures
4. Create application errors
5. Create an SSM OpsItem

**Note the OpsItem ID** that is created - you'll use this in Step 2.

### Step 2: Analyze the Incident

```bash
python3 test_root_cause_analysis.py
```

Select option **2** and enter the OpsItem ID from Step 1.

The supervisor agent will:
1. Orchestrate all monitoring agents
2. Collect data from CloudWatch Logs, Metrics, CloudTrail, VPC Flow Logs
3. Correlate events across services
4. Identify the root cause
5. Provide remediation recommendations

## Detailed Scenarios

### Scenario 1: Security-Induced Outage

This scenario demonstrates how a security group change causes application failures.

1. **Generate the incident:**
   ```bash
   python3 incident_generator_demo.py
   # Select option 1
   ```

2. **What happens:**
   - Security group opens SSH/RDP to 0.0.0.0/0
   - Application starts experiencing connection issues
   - Error rates spike, performance degrades
   - API calls begin failing

3. **Analyze:**
   ```bash
   python3 test_root_cause_analysis.py
   # Select option 1
   ```

4. **Expected findings:**
   - Root cause: Security group modification
   - Timeline showing correlation between SG change and failures
   - Recommendation to review security group rules

### Scenario 2: Performance Cascade

Generate continuous load to simulate performance issues:

1. **Start continuous load:**
   ```bash
   python3 incident_generator_demo.py
   # Select option 2 (5-minute load test)
   ```

2. **While running, analyze in another terminal:**
   ```bash
   python3 test_root_cause_analysis.py
   # Select option 3 (correlation scenarios)
   ```

### Scenario 3: API Failure Investigation

Test specific API failure patterns:

1. **Generate API failures:**
   ```bash
   python3 incident_generator_demo.py
   # Select option 3, then option 8
   ```

2. **Analyze CloudTrail events:**
   ```bash
   python3 test_root_cause_analysis.py
   # Select option 1
   ```

## Verification Steps

### 1. Verify Real AWS Data

Check CloudWatch Logs:
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/demo/sre-incident" --region us-east-1
```

Check CloudWatch Metrics:
```bash
aws cloudwatch get-metric-statistics \
  --namespace "SREDemo/Application" \
  --metric-name "CPUUtilization" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --dimensions Name=Environment,Value=demo Name=Service,Value=sre-demo-app \
  --region us-east-1
```

Check SSM OpsItems:
```bash
aws ssm describe-ops-items --region us-east-1 --output table
```

### 2. Monitor Agent Activity

Watch Lambda invocations:
```bash
aws logs tail /aws/lambda/sre-supervisor-lambda --follow --region us-east-1
```

### 3. Check CloudTrail

View recent API calls:
```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AuthorizeSecurityGroupIngress \
  --region us-east-1
```

## Advanced Testing

### Custom Incident Patterns

Create your own incident patterns by combining different scenarios:

```python
# In incident_generator_demo.py, select option 3 for specific scenarios
# Combine multiple scenarios to create complex incidents
```

### Integration with Existing Monitoring

The agents can analyze your existing AWS resources:
1. Point the analysis at your log groups
2. Specify your CloudWatch namespaces
3. Analyze your real security groups

## Troubleshooting

### Common Issues

1. **"No data found" errors**
   - Ensure you've generated incidents recently (within 30 minutes)
   - Check the AWS region matches (us-east-1)

2. **Lambda timeout errors**
   - Normal for complex analysis
   - Increase Lambda timeout in AWS console if needed

3. **Permission errors**
   - Ensure IAM roles have necessary permissions
   - Check Lambda execution roles

### Debug Mode

Enable detailed logging:
```bash
export DEBUG=true
python3 test_root_cause_analysis.py
```

## Best Practices

1. **Generate incidents before analysis**
   - Agents analyze real-time data
   - Create incidents within the analysis time window

2. **Use meaningful incident descriptions**
   - Helps agents focus their analysis
   - Improves correlation accuracy

3. **Monitor AWS costs**
   - Demo generates real AWS resources
   - Clean up resources after testing

## Cleanup

Remove demo resources:
```bash
python3 incident_generator_demo.py
# Select option 4
```

## Summary

This demo system proves that the SRE Copilot:
- ✅ Uses 100% real AWS APIs
- ✅ Performs actual root cause analysis
- ✅ Correlates events across services
- ✅ Provides actionable insights
- ✅ No mock or fake data

The supervisor agent successfully orchestrates specialized agents to analyze complex incidents and identify root causes by correlating data from CloudWatch, CloudTrail, VPC Flow Logs, and other AWS services.
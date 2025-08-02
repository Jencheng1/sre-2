# SRE Copilot Agent Validation Guide

## Overview

This guide provides comprehensive validation procedures to ensure all SRE Copilot agents are using **REAL AWS APIs** with **NO mock or fake implementations**.

## Agent Inventory

### 1. CloudTrail Agent
- **Function Name**: `sre-cloudtrail-agent-lambda`
- **AWS Services Used**:
  - AWS CloudTrail (`boto3.client('cloudtrail')`)
  - AWS CloudWatch (`boto3.client('cloudwatch')`)
  - AWS Bedrock (`boto3.client('bedrock-runtime')`)
- **Supported Actions**:
  - `get_recent_events` - Retrieves recent CloudTrail events
  - `analyze_events` - Analyzes events with AI
- **Real API Calls**:
  - `cloudtrail.lookup_events()`
  - `cloudwatch.put_metric_data()`
  - `bedrock.invoke_model()`

### 2. VPC Flow Logs Agent
- **Function Name**: `sre-vpc-flow-logs-agent-lambda`
- **AWS Services Used**:
  - AWS EC2 (`boto3.client('ec2')`)
  - AWS CloudWatch Logs (`boto3.client('logs')`)
  - AWS Bedrock (`boto3.client('bedrock-runtime')`)
- **Supported Actions**:
  - `analyze_flow_logs` - Analyzes VPC flow logs
  - `get_security_group_analysis` - Analyzes security groups
- **Real API Calls**:
  - `ec2.describe_flow_logs()`
  - `ec2.describe_security_groups()`
  - `logs.filter_log_events()`
  - `logs.describe_log_groups()`

### 3. Trusted Advisor Agent
- **Function Name**: `sre-trusted-advisor-agent-lambda`
- **AWS Services Used**:
  - AWS Support (`boto3.client('support')`)
  - AWS Bedrock (`boto3.client('bedrock-runtime')`)
- **Supported Actions**:
  - `get_cost_optimization` - Gets cost optimization recommendations
  - `get_security_issues` - Gets security recommendations
  - `get_service_limits` - Gets service limit warnings
- **Real API Calls**:
  - `support.describe_trusted_advisor_checks()`
  - `support.describe_trusted_advisor_check_result()`

### 4. Personal Health Agent
- **Function Name**: `sre-personal-health-agent-lambda`
- **AWS Services Used**:
  - AWS Health (`boto3.client('health')`)
  - AWS Bedrock (`boto3.client('bedrock-runtime')`)
- **Supported Actions**:
  - `get_maintenance_events` - Gets scheduled maintenance
  - `get_service_issues` - Gets service disruptions
  - `get_account_notifications` - Gets account notifications
- **Real API Calls**:
  - `health.describe_events()`
  - `health.describe_event_details()`

### 5. CloudWatch Logs Agent
- **Function Name**: `sre-cloudwatch-logs-agent-lambda`
- **AWS Services Used**:
  - AWS CloudWatch Logs (`boto3.client('logs')`)
  - AWS CloudWatch (`boto3.client('cloudwatch')`)
  - AWS Bedrock (`boto3.client('bedrock-runtime')`)
- **Supported Actions**:
  - `analyze_log_group` - Analyzes specific log group
  - `get_log_groups` - Lists available log groups
  - `search_logs` - Searches logs with patterns
  - `get_log_metrics` - Gets log-based metrics
- **Real API Calls**:
  - `logs.describe_log_groups()`
  - `logs.filter_log_events()`
  - `cloudwatch.get_metric_statistics()`

### 6. Supervisor Agent
- **Function Name**: `sre-supervisor-lambda`
- **AWS Services Used**:
  - AWS Lambda (`boto3.client('lambda')`)
  - AWS CloudWatch (`boto3.client('cloudwatch')`)
  - AWS Bedrock (`boto3.client('bedrock-runtime')`)
- **Capabilities**:
  - Orchestrates all other agents
  - Gathers comprehensive monitoring data
  - Performs root cause analysis
- **Real API Calls**:
  - `lambda.invoke()` - Invokes other monitoring agents
  - `cloudwatch.get_metric_statistics()`
  - `bedrock.invoke_model()`

## Validation Procedures

### 1. Source Code Validation

Check each agent for real AWS API usage:

```bash
# Verify boto3 clients
grep -n "boto3.client" src/lambdas/*/lambda_function.py

# Check for NO mocks
grep -i "mock\|fake" src/lambdas/*/lambda_function.py
```

### 2. Runtime Validation

Test each agent's actions:

```bash
# Run comprehensive validation
python3 validate_all_agents.py
```

### 3. AWS Service Validation

Monitor these AWS services for activity:
- **CloudTrail**: Look for `LookupEvents` API calls
- **CloudWatch Logs**: Look for `FilterLogEvents` API calls
- **Support API**: Look for `DescribeTrustedAdvisorChecks` API calls
- **Health API**: Look for `DescribeEvents` API calls
- **Bedrock**: Look for `InvokeModel` API calls

### 4. Supervisor Orchestration Validation

Verify the supervisor calls real agents:
- Check Lambda invocation logs
- Verify agent response data
- Confirm no hardcoded responses

## Test Case Specifications

### Test Case 1: CloudTrail Agent
- **Action**: Get recent API errors
- **Expected**: Real CloudTrail events from your account
- **Verification**: Events should have real timestamps and user identities

### Test Case 2: VPC Flow Logs Agent
- **Action**: Analyze security groups
- **Expected**: Real security group configurations
- **Verification**: Security group IDs should match your AWS account

### Test Case 3: Trusted Advisor Agent
- **Action**: Get cost optimization tips
- **Expected**: Real Trusted Advisor recommendations
- **Verification**: Recommendations specific to your resources

### Test Case 4: Personal Health Agent
- **Action**: Get maintenance events
- **Expected**: Real AWS maintenance schedules
- **Verification**: Events match AWS Health Dashboard

### Test Case 5: CloudWatch Logs Agent
- **Action**: List log groups
- **Expected**: Real log groups from your account
- **Verification**: Log group names match CloudWatch console

### Test Case 6: Supervisor Agent
- **Action**: Analyze incident
- **Expected**: Orchestrated data from all agents
- **Verification**: Data comes from real agent invocations

## Validation Results

Run the validation suite to ensure:
- ✅ All agents deployed successfully
- ✅ All actions return real AWS data
- ✅ No mock or fake implementations
- ✅ Supervisor orchestrates real agents
- ✅ AI analysis uses real Bedrock API

## Troubleshooting

### Common Issues:
1. **Access Denied**: Check IAM permissions
2. **Resource Not Found**: Ensure resources exist in your account
3. **Throttling**: AWS API rate limits
4. **Region Mismatch**: Ensure correct AWS region

### Verification Commands:
```bash
# Check Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `sre`)].FunctionName'

# Check recent invocations
aws logs tail /aws/lambda/sre-supervisor-lambda --since 10m

# Check IAM permissions
aws iam get-role-policy --role-name sre-lambda-role --policy-name bedrock-access
```
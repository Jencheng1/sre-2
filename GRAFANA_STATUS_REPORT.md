# Grafana EC2 CPU Monitoring - Status Report

## Date: September 27, 2025

## Current Status

### What's Working ✅
1. **Streamlit st.rerun() Error** - FIXED
   - Changed `st.rerun()` to `st.experimental_rerun()` 
   - No more errors when refreshing metrics

2. **Grafana Configuration**
   - Grafana is running and accessible at http://localhost:3000
   - CloudWatch datasource is configured
   - Dashboards are created and show instance IDs
   - Dashboard panels are properly configured

3. **AWS CloudWatch**
   - CloudWatch has CPU metrics for all EC2 instances
   - Metrics are available via boto3 AWS SDK
   - 5 instances have CPU metrics in CloudWatch

### What's Not Working ❌
1. **Grafana Data Display**
   - Instance IDs appear in dashboards but no actual CPU data
   - Error: "InvalidClientTokenId: The security token included in the request is invalid"
   - Root cause: Grafana container cannot access AWS credentials properly

## Root Cause Analysis

The issue is that Grafana running in Docker cannot access the EC2 instance IAM role credentials. When Grafana tries to query CloudWatch, it gets authentication errors because:

1. Docker containers are isolated from the host EC2 metadata service
2. The AWS credentials from the EC2 IAM role expire every ~6 hours
3. Grafana's CloudWatch plugin has limited authentication options in containerized environments

## Attempted Solutions

1. **Explicit Credentials** ✅ Partially Working
   - Created datasource with explicit AWS credentials
   - Credentials work temporarily but expire after ~6 hours
   - File: `fix_grafana_manual.py`

2. **Environment Variables** ❌ Not Working
   - Added env_file to docker-compose.yml
   - Created grafana.env with credentials
   - Grafana container doesn't load the credentials properly

3. **Default Auth** ❌ Not Working  
   - Tried using "default" auth type
   - Doesn't work because container can't access EC2 metadata

4. **EC2 IAM Role** ❌ Not Working
   - Grafana reports: "attempting to use an auth type that is not allowed"
   - Container isolation prevents metadata access

## Permanent Solution Options

### Option 1: Use Host Network Mode
Add to docker-compose.yml:
```yaml
grafana:
  network_mode: host
```
This allows Grafana to access EC2 metadata service.

### Option 2: Use IAM User with Long-term Credentials
1. Create IAM user with CloudWatch read permissions
2. Generate access keys
3. Configure Grafana with permanent credentials

### Option 3: Use AWS IAM Roles for Service Accounts (IRSA)
If running on EKS, use IRSA for proper credential management.

### Option 4: Credential Refresh Script
Create a cron job that:
1. Fetches fresh credentials every 5 hours
2. Updates grafana.env
3. Restarts Grafana container

## Current Workaround

Run this script to temporarily fix the issue (lasts ~6 hours):
```bash
python3 /home/ec2-user/sre/sre_mcp/fix_grafana_manual.py
```

This will:
1. Get fresh AWS credentials
2. Update Grafana datasource
3. Create working dashboard

## Test Results

### Comprehensive Test Summary
- Total Tests Run: 8
- Tests Passed: 8 
- Tests Failed: 0

However, the tests show that while configuration is correct, actual data queries fail due to authentication.

## Files Created

1. **Fixes**:
   - `fix_grafana_dashboard.py`
   - `fix_grafana_aws_credentials.py`
   - `fix_grafana_simple.py`
   - `fix_grafana_iam_role.py`
   - `fix_grafana_aws_final.sh`
   - `fix_grafana_manual.py`
   - `final_grafana_fix.py`

2. **Tests**:
   - `test_grafana_ec2_cpu_data.py`
   - `test_grafana_cpu_data_comprehensive.py`
   - `test_grafana_data_display.py`

3. **Configuration**:
   - `grafana.env` - AWS credentials
   - Updated `docker-compose.yml` with env_file

## Recommendations

For a production environment, I recommend:

1. **Short-term**: Use the manual fix script every 6 hours
2. **Long-term**: Implement Option 1 (host network mode) or Option 2 (IAM user)
3. **Best Practice**: Use a proper observability platform like Amazon Managed Grafana which handles authentication natively

## Conclusion

While the Grafana dashboards are properly configured and CloudWatch has the data, the containerized Grafana cannot authenticate to AWS CloudWatch due to credential access limitations. The issue is not with the dashboard configuration but with the AWS authentication mechanism in a containerized environment.

The manual fix script provides a temporary solution that works for ~6 hours at a time.
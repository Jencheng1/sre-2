# Problem Management Integration Context

## Overview
This document describes the ServiceNow Problem Management integration added to the SRE Copilot system on August 14, 2025.

## New Features

### 1. ServiceNow Problem Management
- **Location**: `servicenow_problem_manager.py`
- **Features**:
  - AI-powered problem creation from incidents
  - Incident-to-problem correlation with confidence scoring
  - Problem state and priority management
  - Root cause analysis and workaround documentation
  - Mock ServiceNow integration (can be replaced with real API)

### 2. Synthetic Transaction Generator
- **Location**: `synthetic_transaction_generator.py`
- **Features**:
  - Generate synthetic transactions based on incident patterns
  - Create CloudWatch logs with realistic error patterns
  - Generate CloudWatch metrics (success rate, duration, etc.)
  - Create VPC Flow Logs simulating network traffic
  - Generate CloudTrail events for security incidents
  - Pattern-based transaction generation for different incident types

### 3. Enhanced Streamlit UI
- **Location**: `streamlit_app_problem_management.py`
- **New Tabs**: Problem Management, Synthetic Transactions
- **Features**:
  - Problem overview with detailed views
  - AI-powered problem creation from incidents
  - Incident-to-problem correlation workflow
  - Problem analytics and metrics
  - Synthetic transaction generation interface
  - Transaction timeline visualization

## Implementation Details

### Problem Management Flow
1. **Problem Creation**:
   - Select incident from dropdown
   - AI analyzes incident and suggests problem details
   - Creates problem record with appropriate priority/category
   - Links incident to problem automatically

2. **Problem Correlation**:
   - AI analyzes incident against existing problems
   - Provides confidence scores for correlations
   - Allows manual correlation if needed
   - Tracks all related incidents per problem

### Synthetic Transaction Types
- **API Calls**: REST API transactions with various endpoints
- **Database Queries**: SELECT, UPDATE, INSERT operations
- **File Operations**: Read/write operations
- **Network Requests**: External service calls
- **Authentication**: Login/logout attempts
- **Data Processing**: Batch processing operations

### Generated Resources
1. **CloudWatch Logs**:
   - Log group: `/aws/lambda/sre-synthetic-transactions`
   - Structured JSON logs with severity levels
   - Transaction IDs for correlation

2. **CloudWatch Metrics**:
   - Namespace: `SREDemo/SyntheticTransactions`
   - Metrics: TransactionCount, SuccessRate, AverageDuration
   - Dimensions by transaction type and incident ID

3. **VPC Flow Logs**:
   - Simulated network traffic patterns
   - ACCEPT/REJECT actions based on incident type
   - Saved to JSON files for analysis

4. **CloudTrail Events**:
   - API call events for security incidents
   - Authentication events with success/failure
   - Error codes for failed operations

## Data Storage
- **Problems**: Stored in `servicenow_problems.json`
- **VPC Flow Logs**: `vpc_flow_logs_[timestamp].json`
- **CloudTrail Events**: `cloudtrail_events_[timestamp].json`

## AI Integration
- Uses AWS Bedrock Claude 3 Sonnet for:
  - Problem analysis and categorization
  - Root cause identification
  - Workaround suggestions
  - Correlation confidence scoring

## Testing
To test the new features:
1. Generate an incident using the sidebar
2. Navigate to Problem Management tab
3. Create a problem from the incident
4. Test correlation with new incidents
5. Generate synthetic transactions
6. View the generated logs and metrics

## Future Enhancements
- Real ServiceNow API integration
- Problem resolution tracking
- Known Error Database (KEDB) integration
- Automated problem detection from multiple incidents
- Integration with change management
- SLA tracking for problem resolution
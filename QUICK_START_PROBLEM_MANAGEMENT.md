# Quick Start Guide - Problem Management

## Check Current Status
```bash
# 1. Check if Streamlit is running
ps aux | grep streamlit | grep -v grep

# 2. Check MCP servers
netstat -tulpn | grep -E "(908[0-6])"
```

## Start the Application
```bash
# If not running, start it:
export AWS_DEFAULT_REGION=us-east-1 && nohup python3 -m streamlit run streamlit_app_problem_management.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > streamlit_problem_management.log 2>&1 &
```

## Access the Application
1. Open browser to http://localhost:8501
2. Navigate to "Advanced Tools" in top navigation

## Using Problem Management

### Create a Problem from Incident
1. First, generate an incident using the sidebar
2. Go to "Advanced Tools" > "Problem Management" 
3. Click "Create Problem" tab
4. Select your incident from dropdown
5. Click "Create Problem with AI Analysis"

### Generate Synthetic Transactions
1. Go to "Advanced Tools" > "Synthetic Transactions"
2. Select an incident from dropdown
3. Click "Generate Synthetic Transactions"
4. View generated logs, metrics, and charts

### Correlate Incidents to Problems
1. Go to "Problem Management" > "Correlate to Problem" tab
2. Select an incident
3. Click "Find Correlating Problems" for AI suggestions
4. Or manually select a problem and link

## File Locations
- Problems stored in: `servicenow_problems.json`
- VPC Flow Logs: `vpc_flow_logs_*.json`
- CloudTrail Events: `cloudtrail_events_*.json`
- CloudWatch Logs: `/aws/lambda/sre-synthetic-transactions`

## Troubleshooting

### If incidents don't appear in dropdowns:
The bug fix is already applied. Incidents should appear automatically.

### If you get Bedrock errors:
This is normal for correlation analysis. The system will use fallback values.

### To clean up test data:
```bash
rm -f servicenow_problems.json
rm -f vpc_flow_logs_*.json cloudtrail_events_*.json
```

## Key Files
- Main UI: `streamlit_app_problem_management.py`
- Problem Logic: `servicenow_problem_manager.py`
- Transaction Generator: `synthetic_transaction_generator.py`

## Test the System
```bash
# Run all tests
python3 test_problem_management.py
python3 verify_problem_management_fix.py
```
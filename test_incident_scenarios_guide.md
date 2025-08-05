# How to Test the Incident Scenarios

## Method 1: Using Streamlit Dashboard (Recommended)

### Access the Dashboard
```bash
# Open in your browser
http://localhost:8501
# or
http://10.0.1.217:8501
```

### Testing Each Scenario

#### 1. EC2 Service Quota Exceeded

**Steps:**
1. Go to the **Incident Dashboard** tab
2. Click **"Generate Demo Incident"**
3. Select **"EC2 Quota Exceeded"** from the dropdown
4. Click **"Generate"**
5. Watch as the system:
   - Creates CloudTrail logs with `InstanceLimitExceeded` errors
   - Generates Trusted Advisor alerts for service limits
   - Creates Personal Health Dashboard notifications
   - Correlates with Change Calendar (if a scaling change was scheduled)
   - Provides root cause: "EC2 quota insufficient for m5.large instances"

**Expected Analysis:**
- **Root Cause:** EC2 service quota (20 instances) insufficient for requested 25 m5.large instances
- **Recommendations:** Request quota increase via Service Quotas console
- **Correlation:** Links to approved change request for scaling

#### 2. Network Security Group Misconfiguration

**Steps:**
1. In the Incident Dashboard, click **"Generate Demo Incident"**
2. Select **"Security Group Misconfiguration"**
3. Click **"Generate"**
4. The system will:
   - Show VPC Flow Logs with REJECT actions
   - Display security group changes in CloudTrail
   - Identify blocked subnets and ports
   - Correlate with compliance change requests

**Expected Analysis:**
- **Root Cause:** Security group rules removed during compliance update, blocking internal traffic on port 443
- **Recommendations:** Restore ingress rules for 10.0.0.0/8 on port 443
- **Impact:** Backend services unreachable from application servers

#### 3. API Throttling Incident

**Steps:**
1. Click **"Generate Demo Incident"**
2. Select **"API Throttling - High Load"**
3. Click **"Generate"**
4. System demonstrates:
   - CloudTrail logs showing `RequestLimitExceeded` errors
   - Auto-scaling attempting rapid instance launches
   - API call rate exceeding limits
   - Emergency change correlation

**Expected Analysis:**
- **Root Cause:** Auto-scaling making 150 RunInstances API calls/minute, exceeding 100/minute limit
- **Recommendations:** Implement exponential backoff and request limit increase
- **Contributing Factors:** No retry logic in deployment scripts

## Method 2: Using Command Line Testing

### Test with Supervisor Lambda
```bash
# EC2 Quota Test
aws lambda invoke \
  --function-name sre-supervisor-lambda \
  --payload '{
    "incident_type": "quota",
    "incident_id": "TEST-QUOTA-001",
    "description": "EC2 instance launch failed due to quota",
    "affected_resources": ["m5.large"],
    "error_details": {
      "error_code": "InstanceLimitExceeded",
      "quota_id": "L-1216C47A",
      "current_limit": 20,
      "requested": 25
    }
  }' \
  --region us-east-1 \
  response.json

# View results
cat response.json | jq '.body' | jq -r . | jq .
```

### Test with MCP Correlations
```bash
# Security Group Test with MCP
aws lambda invoke \
  --function-name sre-supervisor-lambda-mcp \
  --payload '{
    "incident_type": "network",
    "incident_id": "TEST-NET-001",
    "description": "Multiple instances unreachable after security group change",
    "affected_resources": ["sg-0123456789abcdef0"],
    "network_details": {
      "reject_count": 150,
      "affected_ports": [443, 3306],
      "blocked_subnets": ["10.0.1.0/24", "10.0.2.0/24"]
    }
  }' \
  --region us-east-1 \
  response.json
```

## Method 3: Using Python Test Scripts

### Run Specific Scenario Tests
```python
# Create test_specific_scenarios.py
import json
import requests

# Test EC2 Quota Scenario
def test_ec2_quota():
    # Load test data
    with open('incident_test_cases.json', 'r') as f:
        data = json.load(f)
    
    ec2_scenario = data['test_cases'][0]  # EC2 quota scenario
    
    # Simulate incident
    print("Testing EC2 Quota Exceeded...")
    print(f"Scenario: {ec2_scenario['name']}")
    print(f"Root Cause: {ec2_scenario['root_cause_analysis']['root_cause']}")
    print(f"Recommendations: {ec2_scenario['recommendations']['immediate']}")

# Test via Streamlit API (if implemented)
def test_via_streamlit():
    response = requests.post(
        'http://localhost:8501/api/generate_incident',
        json={'incident_type': 'ec2_quota'}
    )
    print(response.json())

if __name__ == '__main__':
    test_ec2_quota()
```

## Method 4: Direct Knowledge Base Query

### Search for Similar Incidents
```bash
# Query knowledge base for quota issues
aws lambda invoke \
  --function-name sre-knowledge-base-agent-lambda \
  --payload '{
    "action": "search",
    "query": "EC2 quota exceeded m5.large",
    "limit": 5
  }' \
  --region us-east-1 \
  kb_response.json

# Search for security group issues
aws lambda invoke \
  --function-name sre-knowledge-base-agent-lambda \
  --payload '{
    "action": "search",
    "query": "security group blocking port 443",
    "limit": 5
  }' \
  --region us-east-1 \
  kb_response.json
```

## Viewing Test Results

### In Streamlit Dashboard:
1. **Incident Details** - Shows the generated incident with all metadata
2. **Root Cause Analysis** - Displays AI-generated analysis
3. **Correlation Timeline** - Shows sequence of events
4. **Recommendations** - Lists immediate and long-term fixes
5. **Knowledge Base** - Shows similar historical incidents

### In CloudWatch Logs:
```bash
# View Lambda logs
aws logs tail /aws/lambda/sre-supervisor-lambda --follow

# View specific incident analysis
aws logs filter-log-events \
  --log-group-name /aws/lambda/sre-supervisor-lambda \
  --filter-pattern "TEST-QUOTA-001"
```

## Verification Steps

1. **Check MCP Correlations:**
   - Splunk should show log patterns
   - ServiceNow should list related changes
   - Confluence should suggest KB articles

2. **Verify SSM Integration:**
   - OpsItems should be created automatically
   - Change Calendar should show correlated changes

3. **Validate Analysis Quality:**
   - Root cause should match expected scenario
   - Recommendations should be actionable
   - Timeline should show proper event sequence

## Quick Test All Three Scenarios

```bash
# Run the test suite for all scenarios
python3 run_all_tests.py

# This will test:
# ✓ EC2 Service Quota Exceeded
# ✓ Network Connectivity Issue  
# ✓ API Throttling Incident
# And show pass/fail for each
```

## Expected Outputs

### EC2 Quota:
- **Error:** `InstanceLimitExceeded`
- **Root Cause:** Quota limit reached (20/20)
- **Fix:** Request increase for L-1216C47A

### Security Group:
- **Error:** VPC Flow Logs showing REJECT
- **Root Cause:** Ingress rules removed
- **Fix:** Restore security group rules

### API Throttling:
- **Error:** `RequestLimitExceeded`
- **Root Cause:** Too many API calls
- **Fix:** Implement exponential backoff

## Tips for Testing

1. **Use the Streamlit UI** for the best visual experience
2. **Check the Knowledge Base tab** to see if incidents are being indexed
3. **Monitor the MCP server logs** to see external correlations
4. **Use CloudWatch Insights** to analyze patterns across incidents
5. **Create variations** of scenarios to test edge cases
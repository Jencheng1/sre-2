# AI-Powered Root Cause Analysis Investigation Results

## Issue Summary
The AI-powered root cause analysis is failing because the current supervisor Lambda function (`lambda_function.py`) is NOT using AWS Bedrock for AI analysis. Instead, it's using hardcoded rule-based logic.

## Key Findings

### 1. Current Lambda Function (lambda_function.py)
- **NO Bedrock invoke_model calls**
- Uses hardcoded rules in functions like:
  - `analyze_performance_incident()` - Checks CPU/Memory thresholds
  - `analyze_security_incident()` - Pattern matching on keywords
  - `analyze_outage_incident()` - Error rate checks
- Falls back to generic messages like "Under investigation" when patterns don't match
- Has try/except block that catches all errors and returns a fallback message

### 2. Backup Lambda Function (lambda_function_backup.py) 
- **DOES have Bedrock AI integration**
- Contains `analyze_with_bedrock()` function that:
  - Uses Claude 3 Haiku model (`anthropic.claude-3-haiku-20240307-v1:0`)
  - Sends incident context to AI for analysis
  - Returns AI-generated root cause analysis
- Properly handles Bedrock errors

### 3. Enhanced Lambda Functions
- `lambda_function_defect_enhanced.py` - Uses Claude 3 Sonnet for defect correlation
- `lambda_function_mcp.py` - Another variant with different features

## Root Cause
The supervisor Lambda was likely updated to remove AI dependencies at some point, possibly to:
1. Reduce costs (Bedrock API calls cost money)
2. Improve reliability (no dependency on external AI service)
3. Speed up response times (no AI latency)

However, this removed the "AI-powered" aspect of the analysis.

## Error Handling
The current lambda has this fallback in the exception handler:
```python
except Exception as e:
    logger.error(f"Error in supervisor handler: {str(e)}")
    
    # Return a meaningful error response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'analysis': f"""
### Error During Analysis
An error occurred while analyzing the incident: {str(e)}

### Fallback Analysis
Based on the incident description: {event.get('incident_description', 'No description')}

The system is experiencing issues that require investigation. Please check:
1. CloudWatch Logs for error patterns
2. CloudWatch Metrics for anomalies
3. AWS Health Dashboard for service issues
4. Security groups for recent changes

### Note
This is a fallback response. The full analysis requires proper AWS permissions and Bedrock model access.
""",
            'incident_type': 'unknown',
            'error': str(e)
        })
    }
```

## Solutions

### Option 1: Restore AI Integration (Recommended)
1. Copy the `analyze_with_bedrock()` function from `lambda_function_backup.py`
2. Integrate it into the current analysis flow
3. Keep the rule-based analysis as a fallback when AI fails

### Option 2: Use the Backup Lambda
1. Replace current `lambda_function.py` with `lambda_function_backup.py`
2. Test thoroughly to ensure all features still work

### Option 3: Hybrid Approach
1. Use rule-based analysis for quick initial assessment
2. Enhance with AI analysis for deeper insights
3. Combine both outputs for comprehensive analysis

## Testing Commands
```bash
# Test current lambda (no AI)
python3 test_enhanced_lambda.py

# Deploy backup lambda with AI
cd /home/ec2-user/sre/sre_mcp/src/lambdas/supervisor
cp lambda_function_backup.py lambda_function.py
zip -r supervisor.zip lambda_function.py requirements.txt
aws lambda update-function-code --function-name sre-supervisor-lambda --region us-east-1 --zip-file fileb://supervisor.zip

# Test ServiceNow problem manager (uses AI)
python3 servicenow_problem_manager.py
```

## Verification
To verify if AI is being used, look for:
1. Bedrock API calls in CloudWatch Logs
2. Longer response times (AI adds 2-5 seconds)
3. More detailed, contextual analysis in responses
4. Billing for Bedrock usage in AWS Cost Explorer
# AWS Bedrock Model Access Guide

## Model Required

The SRE Copilot agents require access to:

**Claude 3 Haiku (anthropic.claude-3-haiku-20240307-v1:0)**

## How to Request Access

### Option 1: AWS Console (Recommended)

1. **Navigate to AWS Bedrock Console**
   - Go to: https://console.aws.amazon.com/bedrock/
   - Select your region: **us-east-1** (N. Virginia)

2. **Go to Model Access**
   - In the left sidebar, click on "Model access"
   - You'll see a list of available models

3. **Request Access to Claude 3 Haiku**
   - Find "Claude 3 Haiku" in the list
   - Click "Request model access" or "Manage model access"
   - Select the checkbox for "Claude 3 Haiku"
   - Click "Request model access"
   - Accept the End User License Agreement (EULA)

4. **Wait for Approval**
   - Access is usually granted within a few minutes
   - You'll see the status change from "Access requested" to "Access granted"

### Option 2: AWS CLI

```bash
# List available models
aws bedrock list-foundation-models --region us-east-1

# The request access via CLI is not directly available, 
# you need to use the console for initial access request
```

## Models Used by Different Agents

| Agent | Model ID | Purpose |
|-------|----------|---------|
| Supervisor | anthropic.claude-3-haiku-20240307-v1:0 | Orchestration & Analysis |
| CloudWatch Logs | anthropic.claude-3-haiku-20240307-v1:0 | Log Analysis |
| CloudTrail | anthropic.claude-v2 or claude-3-haiku | Security Analysis |
| VPC Flow Logs | anthropic.claude-3-haiku-20240307-v1:0 | Network Analysis |
| Personal Health | anthropic.claude-3-haiku-20240307-v1:0 | Health Event Analysis |
| Trusted Advisor | anthropic.claude-3-haiku-20240307-v1:0 | Recommendation Analysis |

## Verification

After access is granted, verify with:

```bash
# Test model access
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --content-type application/json \
  --accept application/json \
  --body '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":10,"anthropic_version":"bedrock-2023-05-31"}' \
  --region us-east-1 \
  test-output.json
```

## Alternative Models

If you cannot get access to Claude 3 Haiku, you can modify the Lambda functions to use:

1. **Claude Instant** (anthropic.claude-instant-v1)
   - Faster, more cost-effective
   - Good for simple analysis

2. **Claude 2** (anthropic.claude-v2)
   - Previous generation
   - Still very capable

3. **Amazon Titan** (amazon.titan-text-express-v1)
   - Amazon's own model
   - No additional access needed

## Cost Considerations

- Claude 3 Haiku: ~$0.25 per million input tokens, $1.25 per million output tokens
- Very cost-effective for the analysis workload
- Each analysis typically uses <1000 tokens

## Next Steps

1. Request access to Claude 3 Haiku via AWS Console
2. Wait for approval (usually minutes)
3. Re-run the root cause analysis in Streamlit
4. The AI analysis will work properly

## Troubleshooting

If you continue to see access errors after requesting:
1. Verify you're in the correct region (us-east-1)
2. Check IAM permissions include bedrock:InvokeModel
3. Ensure the Lambda execution role has Bedrock permissions
4. Try logging out and back into AWS Console to refresh permissions
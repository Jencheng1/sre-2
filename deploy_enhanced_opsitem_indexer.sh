#!/bin/bash

# Deploy enhanced OpsItem indexer that triggers automatic AI analysis

set -e

echo "Deploying enhanced OpsItem indexer Lambda..."

LAMBDA_NAME="sre-opsitem-indexer"
REGION="us-east-1"
RUNTIME="python3.9"
HANDLER="lambda_function.lambda_handler"

cd src/lambdas/opsitem-indexer

# Backup original lambda_function.py
if [ -f lambda_function.py ]; then
    cp lambda_function.py lambda_function_original.py
    echo "Backed up original lambda_function.py"
fi

# Use enhanced version
cp lambda_function_enhanced.py lambda_function.py
echo "Using enhanced lambda_function.py with automatic AI analysis"

# Create deployment package
echo "Creating deployment package..."
zip -r opsitem-indexer.zip lambda_function.py

# Check if Lambda exists
if aws lambda get-function --function-name $LAMBDA_NAME --region $REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_NAME \
        --zip-file fileb://opsitem-indexer.zip \
        --region $REGION
        
    echo "Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name $LAMBDA_NAME \
        --timeout 300 \
        --memory-size 512 \
        --environment Variables="{
            KB_LAMBDA_NAME=sre-knowledge-base-agent-lambda,
            SUPERVISOR_LAMBDA_NAME=sre-supervisor-lambda
        }" \
        --region $REGION
else
    echo "Lambda function not found. Creating new function..."
    
    # Get account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Create IAM role if it doesn't exist
    ROLE_NAME="sre-opsitem-indexer-role"
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"
    
    # Check if role exists
    if ! aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
        echo "Creating IAM role..."
        
        # Create trust policy
        cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
        
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document file://trust-policy.json
            
        # Attach policies
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
            
        # Create custom policy
        cat > lambda-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetOpsItem",
                "ssm:UpdateOpsItem",
                "lambda:InvokeFunction",
                "cloudwatch:GetMetricStatistics",
                "logs:DescribeLogStreams",
                "logs:FilterLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
EOF
        
        aws iam put-role-policy \
            --role-name $ROLE_NAME \
            --policy-name OpsItemIndexerPolicy \
            --policy-document file://lambda-policy.json
            
        # Wait for role to be ready
        echo "Waiting for IAM role to propagate..."
        sleep 10
    fi
    
    # Create Lambda function
    aws lambda create-function \
        --function-name $LAMBDA_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://opsitem-indexer.zip \
        --timeout 300 \
        --memory-size 512 \
        --environment Variables="{
            KB_LAMBDA_NAME=sre-knowledge-base-agent-lambda,
            SUPERVISOR_LAMBDA_NAME=sre-supervisor-lambda
        }" \
        --region $REGION
fi

# Update EventBridge rule target to use this Lambda
echo ""
echo "Updating EventBridge rule target..."

# Remove old target
aws events remove-targets \
    --rule sre-opsitem-indexing \
    --ids "1" \
    --region $REGION 2>/dev/null || true

# Add Lambda permission for EventBridge
aws lambda add-permission \
    --function-name $LAMBDA_NAME \
    --statement-id AllowEventsInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$REGION:$ACCOUNT_ID:rule/sre-opsitem-indexing \
    --region $REGION 2>/dev/null || true

# Add new target
aws events put-targets \
    --rule sre-opsitem-indexing \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$LAMBDA_NAME" \
    --region $REGION

# Clean up
rm -f trust-policy.json lambda-policy.json opsitem-indexer.zip

echo ""
echo "Enhanced OpsItem indexer deployed successfully!"
echo ""
echo "The EventBridge rule 'sre-opsitem-indexing' will now:"
echo "1. Trigger on OpsItem creation/update"
echo "2. Index the OpsItem to knowledge base"
echo "3. Automatically invoke supervisor Lambda for AI root cause analysis"
echo "4. Update the OpsItem with analysis results"
echo ""
echo "To test: Create an OpsItem via the Streamlit dashboard and watch the automatic analysis!"
#!/bin/bash

# Update supervisor Lambda to automatically invoke all AI agents

set -e

echo "Updating supervisor Lambda for automatic AI analysis..."

LAMBDA_NAME="sre-supervisor-lambda"
REGION="us-east-1"

cd src/lambdas/supervisor

# Backup original
if [ -f lambda_function.py ]; then
    cp lambda_function.py lambda_function_manual.py
    echo "Backed up original lambda_function.py"
fi

# Use enhanced auto-analysis version
cp lambda_function_auto_analysis.py lambda_function.py
echo "Using enhanced lambda_function.py with automatic agent invocation"

# Create requirements.txt if not exists
if [ ! -f requirements.txt ]; then
    echo "boto3" > requirements.txt
fi

# Create deployment package
echo "Creating deployment package..."
zip -r supervisor.zip lambda_function.py requirements.txt

# Update Lambda function code
echo "Updating Lambda function..."
aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --zip-file fileb://supervisor.zip \
    --region $REGION

# Update function configuration for longer timeout
echo "Updating function configuration..."
aws lambda update-function-configuration \
    --function-name $LAMBDA_NAME \
    --timeout 300 \
    --memory-size 1024 \
    --region $REGION

# Clean up
rm -f supervisor.zip

echo ""
echo "Supervisor Lambda updated successfully!"
echo ""
echo "The supervisor Lambda will now:"
echo "1. Automatically invoke ALL specialized agent Lambdas"
echo "2. Collect comprehensive data from all AWS services"
echo "3. Generate detailed AI-powered root cause analysis"
echo "4. Return complete analysis with all agent findings"
echo ""
echo "This works with both manual dashboard triggers and automatic EventBridge triggers!"

cd ../../..
#!/bin/bash

# Deploy All SRE Lambda Functions
# This script deploys all Lambda functions for the SRE Copilot project

set -e  # Exit on error

echo "=========================================="
echo "SRE Copilot Lambda Deployment Script"
echo "=========================================="
echo ""

# Configuration
REGION="us-east-1"
ROLE_NAME="sre-lambda-role"
RUNTIME="python3.9"
TIMEOUT="300"
MEMORY="512"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if Lambda exists
function check_lambda() {
    local function_name=$1
    aws lambda get-function --function-name $function_name --region $REGION 2>/dev/null
    return $?
}

# Function to create or update Lambda
function deploy_lambda() {
    local function_name=$1
    local handler=$2
    local source_dir=$3
    local description=$4
    
    echo -e "${YELLOW}Deploying $function_name...${NC}"
    
    # Check if source directory exists
    if [ ! -d "$source_dir" ]; then
        echo -e "${RED}Source directory not found: $source_dir${NC}"
        return 1
    fi
    
    # Check if lambda_function.py exists
    if [ ! -f "$source_dir/lambda_function.py" ]; then
        echo -e "${RED}lambda_function.py not found in: $source_dir${NC}"
        return 1
    fi
    
    # Create deployment package
    cd $source_dir
    
    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        echo "Installing dependencies..."
        pip install -r requirements.txt -t . --upgrade 2>/dev/null || true
    fi
    
    # Create zip file
    echo "Creating deployment package..."
    zip -r /tmp/${function_name}.zip . -x "*.pyc" "__pycache__/*" "*.dist-info/*" > /dev/null 2>&1
    
    # Go back to original directory
    cd - > /dev/null
    
    # Get IAM role ARN
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --region $REGION --query 'Role.Arn' --output text 2>/dev/null)
    if [ -z "$ROLE_ARN" ]; then
        echo -e "${RED}IAM role $ROLE_NAME not found. Please run Terraform first.${NC}"
        return 1
    fi
    
    # Check if Lambda exists
    if check_lambda $function_name; then
        # Update existing Lambda
        echo "Updating existing Lambda function..."
        aws lambda update-function-code \
            --function-name $function_name \
            --zip-file fileb:///tmp/${function_name}.zip \
            --region $REGION > /dev/null
        
        # Update configuration
        aws lambda update-function-configuration \
            --function-name $function_name \
            --timeout $TIMEOUT \
            --memory-size $MEMORY \
            --region $REGION > /dev/null
    else
        # Create new Lambda
        echo "Creating new Lambda function..."
        aws lambda create-function \
            --function-name $function_name \
            --runtime $RUNTIME \
            --role $ROLE_ARN \
            --handler $handler \
            --zip-file fileb:///tmp/${function_name}.zip \
            --timeout $TIMEOUT \
            --memory-size $MEMORY \
            --description "$description" \
            --region $REGION > /dev/null
    fi
    
    # Clean up
    rm -f /tmp/${function_name}.zip
    
    echo -e "${GREEN}✓ $function_name deployed successfully${NC}"
    echo ""
}

# Main deployment
echo "Starting Lambda deployments..."
echo ""

# Deploy all Lambda functions based on Terraform configuration
deploy_lambda "sre-log-analyzer-lambda" "lambda_function.lambda_handler" \
    "src/lambdas/log_analyzer" "SRE Log Analyzer Lambda Function"

deploy_lambda "sre-metrics-analyzer-lambda" "lambda_function.lambda_handler" \
    "src/lambdas/metrics_analyzer" "SRE Metrics Analyzer Lambda Function"

deploy_lambda "sre-supervisor-lambda" "lambda_function.lambda_handler" \
    "src/lambdas/supervisor" "SRE Supervisor Lambda Function"

deploy_lambda "sre-cloudtrail-agent-lambda" "lambda_function.lambda_handler" \
    "src/lambdas/cloudtrail_agent" "SRE CloudTrail Agent Lambda Function"

deploy_lambda "sre-vpc-flow-logs-agent-lambda" "lambda_function.lambda_handler" \
    "src/lambdas/vpc_flow_logs_agent" "SRE VPC Flow Logs Agent Lambda Function"

deploy_lambda "sre-trusted-advisor-agent-lambda" "lambda_function.lambda_handler" \
    "src/lambdas/trusted_advisor_agent" "SRE Trusted Advisor Agent Lambda Function"

deploy_lambda "sre-personal-health-agent-lambda" "lambda_function.lambda_handler" \
    "src/lambdas/personal_health_agent" "SRE Personal Health Agent Lambda Function"

deploy_lambda "sre-vpc-agent-lambda" "lambda_function.lambda_handler" \
    "src/lambdas/vpc_agent" "SRE VPC Agent Lambda Function"

deploy_lambda "sre-cloudwatch-logs-agent-lambda" "lambda_function.lambda_handler" \
    "src/lambdas/cloudwatch_logs_agent" "SRE CloudWatch Logs Agent Lambda Function"

# Deploy Knowledge Base Lambda (if exists)
if [ -f "src/lambdas/knowledge-base-agent/lambda_function_serverless.py" ]; then
    echo -e "${YELLOW}Deploying Knowledge Base Lambda...${NC}"
    ./deploy_knowledge_base_serverless.sh
fi

# Deploy OpsItem Indexer Lambda (if exists)
if [ -f "src/lambdas/opsitem-indexer/lambda_function.py" ]; then
    deploy_lambda "sre-opsitem-indexer-lambda" "lambda_function.lambda_handler" \
        "src/lambdas/opsitem-indexer" "SRE OpsItem Indexer Lambda Function"
fi

echo ""
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo ""

# List deployed functions
echo "Deployed Lambda Functions:"
aws lambda list-functions --region $REGION --query 'Functions[?starts_with(FunctionName, `sre-`)].FunctionName' --output table

echo ""
echo -e "${GREEN}All Lambda deployments completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Verify functions in AWS Console: https://console.aws.amazon.com/lambda/home?region=$REGION"
echo "2. Check CloudWatch logs for any errors"
echo "3. Run test scripts to validate functionality"
echo ""
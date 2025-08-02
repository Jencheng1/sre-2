#!/bin/bash

# Set environment variables
export AWS_REGION="us-east-1"
export STACK_NAME="sre-copilot-agents"

# Create deployment package for each Lambda function
echo "Creating deployment packages for Lambda functions..."

# CloudTrail Agent
cd src/lambdas/cloudtrail_agent
zip -r ../../deploy/cloudtrail_agent.zip lambda_function.py
cd ../..

# VPC Agent
cd src/lambdas/vpc_agent
zip -r ../../deploy/vpc_agent.zip lambda_function.py
cd ../..

# Trusted Advisor Agent
cd src/lambdas/trusted_advisor_agent
zip -r ../../deploy/trusted_advisor_agent.zip lambda_function.py
cd ../..

# Personal Health Agent
cd src/lambdas/personal_health_agent
zip -r ../../deploy/personal_health_agent.zip lambda_function.py
cd ../..

# Deploy using AWS SAM
echo "Deploying Lambda functions and action groups..."
sam deploy \
    --template-file template.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        Environment=prod \
        CloudTrailAgentName=cloudtrail-agent \
        VPCAgentName=vpc-agent \
        TrustedAdvisorAgentName=trusted-advisor-agent \
        PersonalHealthAgentName=personal-health-agent \
    --no-fail-on-empty-changeset

# Get the Lambda function ARNs
CLOUDTRAIL_LAMBDA_ARN=$(aws lambda get-function --function-name cloudtrail-agent --query 'Configuration.FunctionArn' --output text)
VPC_LAMBDA_ARN=$(aws lambda get-function --function-name vpc-agent --query 'Configuration.FunctionArn' --output text)
TRUSTED_ADVISOR_LAMBDA_ARN=$(aws lambda get-function --function-name trusted-advisor-agent --query 'Configuration.FunctionArn' --output text)
PERSONAL_HEALTH_LAMBDA_ARN=$(aws lambda get-function --function-name personal-health-agent --query 'Configuration.FunctionArn' --output text)

# Create action groups using Python script
echo "Creating action groups..."
python src/core/configure_agents.py \
    --cloudtrail-lambda-arn $CLOUDTRAIL_LAMBDA_ARN \
    --vpc-lambda-arn $VPC_LAMBDA_ARN \
    --trusted-advisor-lambda-arn $TRUSTED_ADVISOR_LAMBDA_ARN \
    --personal-health-lambda-arn $PERSONAL_HEALTH_LAMBDA_ARN

echo "Deployment completed successfully!" 
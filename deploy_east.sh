#!/bin/bash

# Set AWS region
export AWS_DEFAULT_REGION=us-east-1

echo "Initializing Terraform..."
cd terraform
terraform init -reconfigure

echo "Planning Terraform changes..."
terraform plan -var="aws_region=us-east-1"

echo "Applying Terraform changes..."
terraform apply -var="aws_region=us-east-1" -auto-approve

echo "Deployment to us-east-1 completed."

# Verify Lambda functions
echo "Verifying Lambda functions..."
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `sre-`)]'

echo "Verifying CloudWatch Log Groups..."
aws logs describe-log-groups --query 'logGroups[?starts_with(logGroupName, `/aws/lambda/sre-`)]' 
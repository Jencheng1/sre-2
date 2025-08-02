#!/bin/bash

# Set AWS region
export AWS_DEFAULT_REGION=us-west-1

echo "Deleting Lambda functions in us-west-1..."

# Delete Lambda functions
aws lambda delete-function --function-name sre-log-analyzer-lambda || true
aws lambda delete-function --function-name sre-metrics-analyzer-lambda || true
aws lambda delete-function --function-name sre-supervisor-lambda || true

echo "Deleting CloudWatch Log Groups..."
# Delete CloudWatch Log Groups
aws logs delete-log-group --log-group-name /aws/lambda/sre-log-analyzer-lambda || true
aws logs delete-log-group --log-group-name /aws/lambda/sre-metrics-analyzer-lambda || true
aws logs delete-log-group --log-group-name /aws/lambda/sre-supervisor-lambda || true

echo "Deleting IAM role and policies..."
# Detach policies from role
aws iam detach-role-policy --role-name sre-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole || true

# Delete custom policy
aws iam delete-role-policy --role-name sre-lambda-role --policy-name bedrock-access || true

# Delete role
aws iam delete-role --role-name sre-lambda-role || true

echo "Cleanup in us-west-1 completed." 
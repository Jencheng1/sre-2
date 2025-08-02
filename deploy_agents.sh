#!/bin/bash

# Set environment variables
export AWS_REGION="us-east-1"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create deployment packages for Lambda functions
echo "Packaging CloudTrail agent..."
powershell Compress-Archive -Path "src/lambdas/cloudtrail_agent/*" -DestinationPath "sre-cloudtrail-agent-lambda.zip" -Force

echo "Packaging VPC agent..."
powershell Compress-Archive -Path "src/lambdas/vpc_agent/*" -DestinationPath "sre-vpc-agent-lambda.zip" -Force

echo "Packaging Trusted Advisor agent..."
powershell Compress-Archive -Path "src/lambdas/trusted_advisor_agent/*" -DestinationPath "sre-trusted-advisor-agent-lambda.zip" -Force

echo "Packaging Personal Health agent..."
powershell Compress-Archive -Path "src/lambdas/personal_health_agent/*" -DestinationPath "sre-personal-health-agent-lambda.zip" -Force

# Create and test new agents
echo "Creating and testing new agents..."
python src/test_new_agents.py

# Create action groups
echo "Creating action groups..."
python src/create_action_groups.py

echo "Deployment completed successfully!" 
#!/bin/bash

# Deploy Knowledge Base Lambda Function

echo "SRE Knowledge Base Deployment Script"
echo "===================================="

REGION="us-east-1"
FUNCTION_NAME="sre-knowledge-base-agent-lambda"
ROLE_NAME="sre-knowledge-base-lambda-role"
OPENSEARCH_DOMAIN="sre-knowledge-base"

# Check if Lambda function exists
echo "Checking if Lambda function exists..."
aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Lambda function already exists. Updating code..."
    ACTION="update"
else
    echo "Lambda function does not exist. Creating..."
    ACTION="create"
fi

# Create IAM role if it doesn't exist
if [ "$ACTION" == "create" ]; then
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

    # Create role
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://trust-policy.json \
        --region $REGION 2>/dev/null || echo "Role might already exist"
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
        --region $REGION
    
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonOpenSearchServiceFullAccess \
        --region $REGION
    
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess \
        --region $REGION
    
    # Create inline policy for Lambda invoke
    cat > lambda-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction",
                "es:*"
            ],
            "Resource": "*"
        }
    ]
}
EOF

    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name KnowledgeBaseLambdaPolicy \
        --policy-document file://lambda-policy.json \
        --region $REGION
    
    echo "Waiting for role to be ready..."
    sleep 10
fi

# Package Lambda function
echo "Packaging Lambda function..."
cd src/lambdas/knowledge-base-agent

# Install dependencies
pip install -r requirements.txt -t . 2>/dev/null || echo "Dependencies might already be installed"

# Create deployment package
zip -r ../../../knowledge-base-lambda.zip . -x "*.pyc" "__pycache__/*"
cd ../../..

# Get role ARN
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text --region $REGION)

if [ "$ACTION" == "create" ]; then
    # Create Lambda function
    echo "Creating Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://knowledge-base-lambda.zip \
        --timeout 60 \
        --memory-size 512 \
        --environment Variables="{OPENSEARCH_ENDPOINT='$OPENSEARCH_DOMAIN.us-east-1.es.amazonaws.com',OPENSEARCH_INDEX='sre-knowledge-base'}" \
        --region $REGION
else
    # Update Lambda function code
    echo "Updating Lambda function code..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://knowledge-base-lambda.zip \
        --region $REGION
    
    # Update environment variables
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment Variables="{OPENSEARCH_ENDPOINT='$OPENSEARCH_DOMAIN.us-east-1.es.amazonaws.com',OPENSEARCH_INDEX='sre-knowledge-base'}" \
        --region $REGION
fi

# Check OpenSearch domain
echo ""
echo "Checking OpenSearch domain..."
aws opensearch describe-domain --domain-name $OPENSEARCH_DOMAIN --region $REGION 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "WARNING: OpenSearch domain '$OPENSEARCH_DOMAIN' does not exist!"
    echo ""
    echo "To create OpenSearch domain, run:"
    echo "aws opensearch create-domain \\"
    echo "  --domain-name $OPENSEARCH_DOMAIN \\"
    echo "  --engine-version 'OpenSearch_2.11' \\"
    echo "  --cluster-config 'InstanceType=t3.small.search,InstanceCount=1' \\"
    echo "  --ebs-options 'EBSEnabled=true,VolumeType=gp3,VolumeSize=10' \\"
    echo "  --node-to-node-encryption-options 'Enabled=true' \\"
    echo "  --encryption-at-rest-options 'Enabled=true' \\"
    echo "  --domain-endpoint-options 'EnforceHTTPS=true,TLSSecurityPolicy=Policy-Min-TLS-1-2-2019-07' \\"
    echo "  --advanced-security-options 'Enabled=true,InternalUserDatabaseEnabled=false,MasterUserOptions={MasterUserARN=$ROLE_ARN}' \\"
    echo "  --region $REGION"
    echo ""
    echo "Note: OpenSearch domain creation takes 15-20 minutes"
else
    echo "OpenSearch domain exists!"
fi

# Clean up
rm -f trust-policy.json lambda-policy.json knowledge-base-lambda.zip

echo ""
echo "Deployment complete!"
echo ""
echo "Lambda function: $FUNCTION_NAME"
echo "To test the function, run: python3 populate_knowledge_base.py"
echo ""
echo "To view in AWS Console:"
echo "https://console.aws.amazon.com/lambda/home?region=$REGION#/functions/$FUNCTION_NAME"
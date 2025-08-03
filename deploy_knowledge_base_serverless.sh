#!/bin/bash

# Deploy Serverless Knowledge Base Lambda Function

echo "SRE Knowledge Base Serverless Deployment Script"
echo "=============================================="

REGION="us-east-1"
FUNCTION_NAME="sre-knowledge-base-agent-lambda"
ROLE_NAME="sre-knowledge-base-lambda-role"
KB_TABLE="sre-knowledge-base"
KB_VECTORS_TABLE="sre-knowledge-base-vectors"

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
        --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess \
        --region $REGION
    
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess \
        --region $REGION
    
    # Create inline policy for Lambda invoke and SSM
    cat > lambda-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction",
                "ssm:GetOpsItem",
                "ssm:DescribeOpsItems"
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

# Copy serverless version as main file
cp lambda_function_serverless.py lambda_function.py

# Create minimal requirements for serverless
cat > requirements_serverless.txt <<EOF
boto3>=1.26.0
numpy>=1.24.0
EOF

# Install dependencies
pip install -r requirements_serverless.txt -t . 2>/dev/null || echo "Dependencies might already be installed"

# Create deployment package
zip -r ../../../knowledge-base-lambda.zip . -x "*.pyc" "__pycache__/*" "lambda_function_serverless.py" "requirements.txt"
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
        --environment Variables="{KB_TABLE_NAME='$KB_TABLE',KB_VECTORS_TABLE_NAME='$KB_VECTORS_TABLE'}" \
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
        --environment Variables="{KB_TABLE_NAME='$KB_TABLE',KB_VECTORS_TABLE_NAME='$KB_VECTORS_TABLE'}" \
        --region $REGION
fi

# Create CloudWatch Events rule for OpsItem auto-indexing
echo ""
echo "Setting up OpsItem auto-indexing..."

# Create event rule
aws events put-rule \
    --name sre-opsitem-indexing \
    --description "Auto-index OpsItems to knowledge base" \
    --event-pattern '{
        "source": ["aws.ssm"],
        "detail-type": ["AWS API Call via CloudTrail"],
        "detail": {
            "eventName": ["CreateOpsItem", "UpdateOpsItem"]
        }
    }' \
    --region $REGION 2>/dev/null || echo "Rule might already exist"

# Add Lambda permission
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id AllowEventsInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$REGION:*:rule/sre-opsitem-indexing \
    --region $REGION 2>/dev/null || echo "Permission might already exist"

# Add Lambda as target
aws events put-targets \
    --rule sre-opsitem-indexing \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:*:function:$FUNCTION_NAME" \
    --region $REGION 2>/dev/null || echo "Target might already exist"

# Clean up
rm -f trust-policy.json lambda-policy.json knowledge-base-lambda.zip
cd src/lambdas/knowledge-base-agent
rm -f lambda_function.py  # Remove copy
cd ../../..

echo ""
echo "Deployment complete!"
echo ""
echo "Lambda function: $FUNCTION_NAME"
echo "DynamoDB tables: $KB_TABLE, $KB_VECTORS_TABLE"
echo "Auto-indexing: Enabled for OpsItems"
echo ""
echo "Next steps:"
echo "1. Initialize tables: python3 test_knowledge_base.py (run test_01_create_tables)"
echo "2. Populate knowledge base: python3 populate_knowledge_base.py"
echo "3. Test functionality: python3 test_knowledge_base.py"
echo "4. Access via Streamlit UI at port 8501"
echo ""
echo "To view in AWS Console:"
echo "https://console.aws.amazon.com/lambda/home?region=$REGION#/functions/$FUNCTION_NAME"
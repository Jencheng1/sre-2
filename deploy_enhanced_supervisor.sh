#!/bin/bash

# Deploy Enhanced Supervisor Lambda with MCP Integration

echo "Deploying Enhanced Supervisor Lambda with MCP Integration..."

# Set variables
LAMBDA_NAME="sre-supervisor-lambda-mcp"
EXISTING_LAMBDA="sre-supervisor-lambda"
REGION="us-east-1"
ZIP_FILE="supervisor_mcp.zip"

# Create deployment directory
cd /home/ec2-user/sre/sre_mcp/src/lambdas/supervisor
mkdir -p deployment_mcp

# Copy Lambda function
cp lambda_function_mcp.py deployment_mcp/lambda_function.py

# Copy MCP modules
echo "Copying MCP modules..."
cp -r /home/ec2-user/sre/sre_mcp/lambdas deployment_mcp/
cp -r /home/ec2-user/sre/sre_mcp/feedback deployment_mcp/
cp -r /home/ec2-user/sre/sre_mcp/orchestration deployment_mcp/
cp -r /home/ec2-user/sre/sre_mcp/config deployment_mcp/

# Create requirements file for Lambda
cat > deployment_mcp/requirements.txt << EOF
requests==2.31.0
numpy==1.21.6
scikit-learn==1.0.2
EOF

# Create the deployment package
cd deployment_mcp
zip -r ../$ZIP_FILE . -x "*.pyc" -x "__pycache__/*"
cd ..

# Check if Lambda exists
aws lambda get-function --function-name $LAMBDA_NAME --region $REGION 2>/dev/null

if [ $? -eq 0 ]; then
    # Update existing Lambda
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_NAME \
        --zip-file fileb://$ZIP_FILE \
        --region $REGION
else
    # Get existing Lambda configuration
    echo "Creating new Lambda function based on existing configuration..."
    
    # Get the role ARN from existing Lambda
    ROLE_ARN=$(aws lambda get-function --function-name $EXISTING_LAMBDA --region $REGION --query 'Configuration.Role' --output text)
    
    # Create new Lambda function
    aws lambda create-function \
        --function-name $LAMBDA_NAME \
        --runtime python3.9 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://$ZIP_FILE \
        --timeout 300 \
        --memory-size 512 \
        --region $REGION \
        --environment Variables="{MCP_ENABLED=true,KB_ENABLED=true}"
        
    # Add permissions for MCP
    echo "Adding permissions for MCP integration..."
    
    # Add SSM permissions for config
    aws lambda add-permission \
        --function-name $LAMBDA_NAME \
        --statement-id AllowSSMAccess \
        --action lambda:InvokeFunction \
        --principal ssm.amazonaws.com \
        --region $REGION 2>/dev/null || true
fi

# Update environment variables
echo "Updating environment variables..."
aws lambda update-function-configuration \
    --function-name $LAMBDA_NAME \
    --environment Variables="{
        MCP_ENABLED=true,
        KB_ENABLED=true,
        SPLUNK_ENDPOINT=http://localhost:8080/splunk,
        DYNATRACE_ENDPOINT=http://localhost:8081/dynatrace,
        SERVICENOW_ENDPOINT=http://localhost:8082/servicenow,
        CONFLUENCE_ENDPOINT=http://localhost:8083/confluence,
        GITLAB_ENDPOINT=http://localhost:8084/gitlab
    }" \
    --region $REGION

# Clean up
rm -rf deployment_mcp
rm -f $ZIP_FILE

echo "Enhanced Supervisor Lambda deployment complete!"
echo "Lambda function name: $LAMBDA_NAME"
echo ""
echo "To test the enhanced Lambda, use:"
echo "aws lambda invoke --function-name $LAMBDA_NAME --payload '{\"action\":\"analyze\",\"incident_description\":\"High network latency affecting payment service\",\"enable_mcp\":true}' output.json --region $REGION"
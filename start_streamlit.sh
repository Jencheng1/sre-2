#!/bin/bash

# SRE Copilot Streamlit Dashboard Startup Script

echo "=================================="
echo "SRE Copilot - Streamlit Dashboard"
echo "=================================="

# Check if running on EC2 or local
if [ -f /etc/ec2-release ]; then
    echo "Running on EC2 instance"
    export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
fi

# Check Python version
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Check AWS credentials
echo "Checking AWS credentials..."
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ AWS credentials configured"
else
    echo "❌ AWS credentials not configured. Please run 'aws configure'"
    exit 1
fi

# Check Lambda functions
echo "Checking Lambda functions..."
for func in supervisor cloudwatch-logs-agent personal-health-agent; do
    aws lambda get-function --function-name sre-$func-lambda > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Lambda function sre-$func-lambda exists"
    else
        echo "⚠️  Lambda function sre-$func-lambda not found"
    fi
done

# Set Streamlit configuration
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_PORT=${PORT:-8501}
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Get public IP if on EC2
if [ -f /etc/ec2-release ]; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    echo ""
    echo "Dashboard will be available at:"
    echo "  Local:  http://localhost:$STREAMLIT_SERVER_PORT"
    echo "  Public: http://$PUBLIC_IP:$STREAMLIT_SERVER_PORT"
    echo ""
    echo "⚠️  Make sure port $STREAMLIT_SERVER_PORT is open in your security group!"
else
    echo ""
    echo "Dashboard will be available at:"
    echo "  http://localhost:$STREAMLIT_SERVER_PORT"
fi

echo ""
echo "Starting Streamlit application..."
echo "Press Ctrl+C to stop"
echo ""

# Start Streamlit
streamlit run streamlit_app.py \
    --server.address=$STREAMLIT_SERVER_ADDRESS \
    --server.port=$STREAMLIT_SERVER_PORT \
    --server.headless=true \
    --browser.gatherUsageStats=false
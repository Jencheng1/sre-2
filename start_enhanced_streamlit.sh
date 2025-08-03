#!/bin/bash

# Start Enhanced Streamlit App with MCP Integration

echo "Starting Enhanced SRE Copilot with MCP Integration..."

# Kill any existing Streamlit processes
echo "Stopping existing Streamlit instances..."
pkill -f streamlit || true
sleep 2

# Set environment variables
export PYTHONPATH=/home/ec2-user/sre/sre_mcp:$PYTHONPATH
export AWS_DEFAULT_REGION=us-east-1

# Start the enhanced Streamlit app
echo "Starting Enhanced Streamlit app on port 8501..."
nohup python3 -m streamlit run streamlit_app_mcp.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    > streamlit_mcp.log 2>&1 &

echo "Enhanced Streamlit app started!"
echo "Access the application at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
echo ""
echo "To view logs: tail -f streamlit_mcp.log"
echo "To stop: pkill -f streamlit"
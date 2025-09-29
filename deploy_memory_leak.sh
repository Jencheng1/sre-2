#!/bin/bash
# Deploy Memory Leak Script
# Deploys the payment demo with intentional memory leak for demonstration

echo "========================================"
echo "MEMORY LEAK DEPLOYMENT SCRIPT"
echo "========================================"
echo ""
echo "This will deploy a version with an intentional memory leak"
echo "for demonstrating SRE monitoring and detection capabilities."
echo ""

# Set environment
export AWS_DEFAULT_REGION=us-east-1

# Change to the correct directory
cd /home/ec2-user/sre/sre_mcp

# Run the simple deployment
echo "Deploying demo services..."
python3 simple_demo_deploy.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Demo services deployed!"
    echo ""
    echo "Services running:"
    echo "- Bank A: http://localhost:8083/api"
    echo "- Bank B: http://localhost:8082/api"
    echo "- Jaeger: http://localhost:16686"
    echo ""
    echo "Note: Both services are now UP with MQ working!"
    echo ""
    echo "Monitor metrics at:"
    echo "- Streamlit UI: http://localhost:8501"
    echo "- Grafana: http://localhost:3001"
    echo ""
    echo "Generate load with: ./generate_load.sh"
else
    echo ""
    echo "❌ Deployment failed. Check the logs above."
    exit 1
fi
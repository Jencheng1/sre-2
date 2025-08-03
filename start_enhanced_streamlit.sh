#!/bin/bash
# Start the enhanced Streamlit application

echo "🚀 Starting Enhanced SRE Copilot Dashboard..."
echo "================================================"
echo ""
echo "Features:"
echo "✅ Generate real AWS incidents"
echo "✅ Analyze with Bedrock AI agents"
echo "✅ Correlate CloudWatch, CloudTrail, VPC logs"
echo "✅ Get root cause analysis and remediation"
echo ""
echo "================================================"
echo ""

# Set AWS region
export AWS_DEFAULT_REGION=us-east-1

# Start Streamlit
streamlit run streamlit_app_enhanced.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.serverAddress localhost \
    --browser.gatherUsageStats false
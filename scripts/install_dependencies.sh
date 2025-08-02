#!/bin/bash

# SRE Copilot Dependencies Installation Script
# This script installs all necessary dependencies for the SRE Copilot with AWS Bedrock

echo "=== Installing SRE Copilot Dependencies ==="
echo "Creating Python virtual environment..."

# Create and activate virtual environment
python3 -m venv sre-copilot-venv
source sre-copilot-venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install AWS SDK and related packages
echo "Installing AWS SDK and core dependencies..."
pip install boto3 botocore awscli

# Install OpenSearch client
echo "Installing OpenSearch client..."
pip install opensearch-py requests-aws4auth

# Install data processing libraries
echo "Installing data processing libraries..."
pip install pandas numpy matplotlib seaborn

# Install utilities for log processing
echo "Installing log processing utilities..."
pip install logparser python-dateutil

# Install dashboard processing libraries
echo "Installing dashboard processing libraries..."
pip install pillow opencv-python-headless

# Install AWS Bedrock specific libraries
echo "Installing AWS Bedrock specific libraries..."
pip install amazon-bedrock-runtime

# Install monitoring tools
echo "Installing monitoring tools..."
pip install prometheus-client

# Install web framework for UI (if needed)
echo "Installing web framework for UI..."
pip install flask flask-cors

# Create requirements.txt for future reference
pip freeze > requirements.txt

echo "Dependencies installation complete. The following packages were installed:"
cat requirements.txt

echo ""
echo "To activate this environment in the future, run:"
echo "source sre-copilot-venv/bin/activate"

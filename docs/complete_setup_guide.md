# SRE Copilot with AWS Bedrock - Complete Setup Guide

This comprehensive guide walks you through the complete process of setting up the SRE Copilot with AWS Bedrock, a multi-agent system for root cause analysis of incidents in AWS environments.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Environment Setup](#environment-setup)
5. [AWS Resources Configuration](#aws-resources-configuration)
6. [Agent Configuration](#agent-configuration)
7. [Testing and Validation](#testing-and-validation)
8. [Troubleshooting](#troubleshooting)
9. [Usage Guide](#usage-guide)
10. [Maintenance and Updates](#maintenance-and-updates)

## Introduction

The SRE Copilot is a sophisticated multi-agent system built on AWS Bedrock that helps Site Reliability Engineers (SREs) identify the root causes of incidents by analyzing logs, metrics, and dashboards. It uses specialized AI agents powered by different foundation models to provide comprehensive analysis and recommendations.

## Architecture Overview

The SRE Copilot consists of five specialized agents:

1. **Supervisor Agent** (Amazon Nova Pro): Coordinates the specialized agents and orchestrates the root cause analysis process.
2. **Log Analysis Agent** (Anthropic Claude 3 Haiku): Analyzes log data to identify patterns, anomalies, and error conditions.
3. **Metrics Analysis Agent** (Amazon Titan Text): Analyzes time-series metrics to identify anomalies and performance issues.
4. **Dashboard Analysis Agent** (Amazon Nova Lite): Interprets dashboard visualizations to extract insights and identify patterns.
5. **Knowledge Base Agent** (Amazon Titan Text): Maintains and queries historical incident data to provide context and suggest solutions.

These agents collaborate through a multi-agent framework, with the Supervisor Agent coordinating the analysis process.

## Prerequisites

Before deploying the SRE Copilot, ensure you have:

- AWS Account with access to AWS Bedrock
- IAM permissions to create and manage:
  - AWS Bedrock agents and knowledge bases
  - CloudWatch logs, metrics, and dashboards
  - IAM roles and policies
  - OpenSearch Serverless collections
- Python 3.8 or higher
- AWS CLI installed and configured
- Git for cloning the repository

## Environment Setup

### 1. Install and Configure AWS CLI

Ensure AWS CLI is installed and configured with appropriate credentials:

```bash
# Check if AWS CLI is installed
aws --version

# If not installed, install it
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Configure AWS CLI
aws configure
```

### 2. Set Up Python Environment

Create a virtual environment and install required dependencies:

```bash
# Clone the repository
git clone https://github.com/yourusername/sre-copilot.git
cd sre-copilot

# Create and activate virtual environment
python3 -m venv sre-copilot-venv
source sre-copilot-venv/bin/activate

# Install dependencies
./scripts/install_dependencies.sh
```

### 3. Verify AWS Permissions

Ensure your AWS credentials have the necessary permissions:

```bash
# Check AWS identity
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models
```

### 4. Check AWS Bedrock Model Availability

Verify that the required foundation models are available in your AWS account:

```bash
aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'nova') || contains(modelId, 'claude') || contains(modelId, 'titan')].modelId"
```

## AWS Resources Configuration

### 1. Create IAM Role for SRE Copilot

1. Navigate to the IAM console
2. Create a new role with the following permissions:
   - AmazonBedrockFullAccess
   - CloudWatchFullAccess
   - AmazonOpenSearchServerlessFullAccess
3. Use the following policy document:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*",
        "cloudwatch:*",
        "logs:*",
        "aoss:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. Create OpenSearch Serverless Collection

1. Navigate to the OpenSearch Serverless console
2. Create a new collection:
   - Name: `sre-incidents`
   - Data access policy: Create a new policy with the following settings:
     - Name: `sre-incidents-access`
     - Rules: Allow the SRE Copilot IAM role full access

```json
{
  "Rules": [
    {
      "ResourceType": "collection",
      "Resource": [
        "collection/sre-incidents"
      ],
      "Permission": [
        "aoss:CreateCollectionItems",
        "aoss:DeleteCollectionItems",
        "aoss:UpdateCollectionItems",
        "aoss:DescribeCollectionItems"
      ]
    },
    {
      "ResourceType": "index",
      "Resource": [
        "index/sre-incidents/*"
      ],
      "Permission": [
        "aoss:ReadDocument",
        "aoss:WriteDocument"
      ]
    }
  ],
  "Principal": [
    "arn:aws:iam::123456789012:role/SRECopilotRole"
  ]
}
```

### 3. Create Vector Index

Create a vector index for the OpenSearch Serverless collection:

1. Name: `sre-incidents-index`
2. Mapping:

```json
{
  "mappings": {
    "properties": {
      "incident_id": {
        "type": "keyword"
      },
      "description": {
        "type": "text"
      },
      "root_cause": {
        "type": "text"
      },
      "resolution": {
        "type": "text"
      },
      "services_affected": {
        "type": "keyword"
      },
      "embedding": {
        "type": "knn_vector",
        "dimension": 1536
      }
    }
  }
}
```

### 4. Enable AWS Bedrock Foundation Models

1. Navigate to the AWS Bedrock console
2. Go to Model access
3. Request access to the following models:
   - Amazon Nova Pro
   - Amazon Nova Lite
   - Amazon Titan Text
   - Anthropic Claude 3 Haiku
   - Amazon Titan Embeddings

## Agent Configuration

### 1. Configure SRE Copilot Agents

Run the agent configuration script to create and configure all the required agents:

```bash
# Using the Python module
python -m src.core.configure_agents

# Or using the console script (if installed via pip)
sre-configure
```

This script will:
- Create the Supervisor Agent
- Create the specialized agents (Log Analysis, Metrics Analysis, Dashboard Analysis, Knowledge Base)
- Create the knowledge base
- Set up agent collaboration
- Save the configuration to a JSON file

### 2. Customize Agent Instructions (Optional)

If you want to customize the agent instructions, you can provide a custom configuration file:

```bash
python -m src.core.configure_agents --config custom_config.json
```

## Testing and Validation

### 1. Verify Agent Status

Run the testing script to verify that all agents are properly configured and in the PREPARED state:

```bash
# Using the Python module
python -m src.core.test_functionality

# Or using the console script (if installed via pip)
sre-test
```

### 2. Test Agent Functionality

The testing script includes tests for:
- Supervisor Agent functionality
- Agent collaboration
- Knowledge base queries

You can also run individual tests:

```bash
# Test the supervisor agent
python -m src.core.test_functionality --test supervisor

# Test agent collaboration
python -m src.core.test_functionality --test collaboration

# Test knowledge base
python -m src.core.test_functionality --test knowledge_base
```

## Troubleshooting

### Common Issues and Solutions

1. **Agent Creation Fails**
   - Verify that you have enabled the required foundation models
   - Check that your IAM role has the necessary permissions
   - Ensure you're in a region where AWS Bedrock is available

2. **Knowledge Base Creation Fails**
   - Verify that the OpenSearch Serverless collection exists
   - Check that the vector index is properly configured
   - Ensure the IAM role has the correct permissions

3. **Agent Testing Fails**
   - Verify that all agents are in the PREPARED state
   - Check the agent logs for specific error messages
   - Ensure the knowledge base is in the AVAILABLE state

### Viewing Agent Logs

To view logs for debugging:

```bash
# View CloudWatch logs for the agents
aws logs get-log-events --log-group-name /aws/bedrock/agents --log-stream-name <agent-id>
```

## Usage Guide

For detailed usage instructions, see the [Usage Guide](usage_guide.md).

## Maintenance and Updates

### Regular Maintenance Tasks

1. **Update Foundation Models**
   - Periodically check for new versions of the foundation models
   - Update the agent configurations to use the latest models

2. **Backup Knowledge Base**
   - Regularly backup the OpenSearch Serverless collection
   - Export incident data to a secure location

3. **Monitor Agent Performance**
   - Check agent response times and accuracy
   - Adjust agent instructions as needed

### Updating the SRE Copilot

To update the SRE Copilot:

1. Pull the latest changes from the repository
2. Run the update script:

```bash
git pull
pip install -e .
```

## Conclusion

You have successfully set up the SRE Copilot with AWS Bedrock. This multi-agent system will help your SRE team quickly identify the root causes of incidents by analyzing logs, metrics, and dashboards.

For additional support or to report issues, please open an issue on the GitHub repository.

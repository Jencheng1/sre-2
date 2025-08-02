# AWS Resources Setup for SRE Copilot

This guide provides detailed instructions for setting up the necessary AWS resources for the SRE Copilot system.

## Table of Contents

1. [IAM Role Setup](#iam-role-setup)
2. [OpenSearch Serverless Configuration](#opensearch-serverless-configuration)
3. [AWS Bedrock Model Access](#aws-bedrock-model-access)
4. [CloudWatch Configuration](#cloudwatch-configuration)
5. [Security Best Practices](#security-best-practices)

## IAM Role Setup

### Create the SRE Copilot Role

1. Navigate to the IAM console in your AWS account
2. Click on "Roles" in the left navigation pane
3. Click "Create role"
4. Select "AWS service" as the trusted entity type
5. Choose "Lambda" as the use case (we'll modify the trust policy later)
6. Click "Next"
7. Attach the following AWS managed policies:
   - `AmazonBedrockFullAccess`
   - `CloudWatchFullAccess`
   - `AmazonOpenSearchServerlessFullAccess`
8. Click "Next"
9. Name the role `SRECopilotRole`
10. Add a description: "Role for SRE Copilot to access AWS Bedrock, CloudWatch, and OpenSearch"
11. Click "Create role"

### Create Custom Policy

1. Navigate to the IAM console
2. Click on "Policies" in the left navigation pane
3. Click "Create policy"
4. Switch to the JSON editor and paste the following policy:

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

5. Click "Next"
6. Name the policy `SRECopilotPolicy`
7. Add a description: "Policy for SRE Copilot to access AWS Bedrock, CloudWatch, and OpenSearch"
8. Click "Create policy"

### Attach Custom Policy to Role

1. Navigate to the IAM console
2. Click on "Roles" in the left navigation pane
3. Search for and select `SRECopilotRole`
4. Click on the "Permissions" tab
5. Click "Add permissions" and select "Attach policies"
6. Search for and select `SRECopilotPolicy`
7. Click "Add permissions"

### Modify Trust Relationship

1. While still on the `SRECopilotRole` page, click on the "Trust relationships" tab
2. Click "Edit trust policy"
3. Replace the existing policy with the following:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "lambda.amazonaws.com",
          "bedrock.amazonaws.com",
          "aoss.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

4. Click "Update policy"

## OpenSearch Serverless Configuration

### Create OpenSearch Serverless Collection

1. Navigate to the Amazon OpenSearch Service console
2. Click on "Collections" in the left navigation pane
3. Click "Create collection"
4. Select "Standard collection"
5. Enter the following details:
   - Name: `sre-incidents`
   - Description: "Collection for SRE Copilot incident data"
6. Under "Security", select "Create new IAM role"
7. Click "Next"
8. Review the settings and click "Create"

### Create Data Access Policy

1. In the OpenSearch Service console, click on "Data access policies" in the left navigation pane
2. Click "Create policy"
3. Enter the following details:
   - Name: `sre-incidents-access`
   - Description: "Access policy for SRE Copilot incident data"
4. Under "Policy definition", use the JSON editor to paste the following policy:

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
    "arn:aws:iam::ACCOUNT_ID:role/SRECopilotRole"
  ]
}
```

5. Replace `ACCOUNT_ID` with your AWS account ID
6. Click "Create"

### Create Vector Index

1. Wait for the `sre-incidents` collection to become active
2. Navigate to the collection's dashboard
3. Click on "Indexes" in the left navigation pane
4. Click "Create index"
5. Enter the following details:
   - Index name: `sre-incidents-index`
   - Index mapping: Use the JSON editor to paste the following mapping:

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

6. Click "Create"

## AWS Bedrock Model Access

### Request Access to Foundation Models

1. Navigate to the AWS Bedrock console
2. Click on "Model access" in the left navigation pane
3. Click "Manage model access"
4. Select the following models:
   - Amazon Nova Pro (amazon.nova-pro-v1:0)
   - Amazon Nova Lite (amazon.nova-lite-v1:0)
   - Amazon Titan Text (amazon.titan-text-express-v1)
   - Anthropic Claude 3 Haiku (anthropic.claude-3-haiku-20240307-v1:0)
   - Amazon Titan Embeddings (amazon.titan-embed-text-v1)
5. Click "Save changes"
6. Wait for access to be granted (this may take some time)

### Verify Model Access

1. In the AWS Bedrock console, click on "Model access"
2. Verify that all the requested models show "Access granted"
3. You can also verify via AWS CLI:

```bash
aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'nova') || contains(modelId, 'claude') || contains(modelId, 'titan')].modelId"
```

## CloudWatch Configuration

### Create Log Groups

1. Navigate to the CloudWatch console
2. Click on "Log groups" in the left navigation pane
3. Click "Create log group"
4. Enter the name `/aws/bedrock/agents`
5. Click "Create"
6. Repeat to create additional log groups as needed for your services

### Set Up Metrics Dashboard

1. In the CloudWatch console, click on "Dashboards" in the left navigation pane
2. Click "Create dashboard"
3. Enter the name `SRECopilotDashboard`
4. Click "Create dashboard"
5. Add widgets for relevant metrics:
   - EC2 CPU Utilization
   - RDS Database Connections
   - Lambda Invocations and Errors
   - API Gateway Latency
   - Custom application metrics

## Security Best Practices

### Least Privilege Access

Review the IAM policies created above and restrict them further if possible:

1. Limit the resources that can be accessed
2. Specify exact actions needed instead of using wildcards
3. Add conditions to restrict when the permissions can be used

### Encryption

1. Enable encryption for the OpenSearch Serverless collection
2. Use AWS KMS for encryption keys
3. Enable encryption for CloudWatch Logs

### Network Security

1. Use VPC endpoints for AWS services
2. Restrict network access to the OpenSearch Serverless collection
3. Use security groups to control traffic

### Monitoring and Auditing

1. Enable AWS CloudTrail to log API calls
2. Set up CloudWatch Alarms for suspicious activities
3. Regularly review access logs

### Regular Reviews

1. Periodically review IAM permissions
2. Rotate credentials regularly
3. Update policies as requirements change

## Conclusion

You have now set up all the necessary AWS resources for the SRE Copilot system. These resources provide the foundation for the SRE Copilot to analyze incidents, store knowledge, and provide recommendations.

For the next steps in setting up the SRE Copilot, refer to the [Complete Setup Guide](complete_setup_guide.md).

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.2.0"
}

provider "aws" {
  region = "us-east-1"
}

# Create IAM role for Lambda functions
resource "aws_iam_role" "sre_lambda_role" {
  name = "sre-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.sre_lambda_role.name
}

# Add Bedrock access policy
resource "aws_iam_role_policy" "bedrock_access" {
  name = "bedrock-access"
  role = aws_iam_role.sre_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# Add CloudTrail access policy
resource "aws_iam_role_policy" "cloudtrail_access" {
  name = "cloudtrail-access"
  role = aws_iam_role.sre_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudtrail:LookupEvents",
          "cloudtrail:DescribeTrails",
          "cloudtrail:GetTrailStatus",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# Add VPC Flow Logs access policy
resource "aws_iam_role_policy" "vpc_flow_logs_access" {
  name = "vpc-flow-logs-access"
  role = aws_iam_role.sre_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeFlowLogs",
          "ec2:DescribeSecurityGroups",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "logs:FilterLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Add Trusted Advisor access policy
resource "aws_iam_role_policy" "trusted_advisor_access" {
  name = "trusted-advisor-access"
  role = aws_iam_role.sre_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "support:DescribeTrustedAdvisorChecks",
          "support:DescribeTrustedAdvisorCheckResult",
          "support:DescribeTrustedAdvisorCheckSummaries"
        ]
        Resource = "*"
      }
    ]
  })
}

# Add Personal Health access policy
resource "aws_iam_role_policy" "personal_health_access" {
  name = "personal-health-access"
  role = aws_iam_role.sre_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "health:DescribeEvents",
          "health:DescribeEventDetails",
          "health:DescribeAffectedEntities"
        ]
        Resource = "*"
      }
    ]
  })
}

# Add CloudWatch Logs access policy
resource "aws_iam_role_policy" "cloudwatch_logs_access" {
  name = "cloudwatch-logs-access"
  role = aws_iam_role.sre_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "logs:FilterLogEvents",
          "logs:DescribeMetricFilters",
          "logs:PutMetricFilter",
          "logs:DeleteMetricFilter"
        ]
        Resource = "*"
      }
    ]
  })
}

# Create Lambda functions
module "log_analyzer_lambda" {
  source = "./modules/lambda"

  function_name    = "sre-log-analyzer-lambda"
  description     = "SRE Log Analyzer Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.sre_lambda_role.arn
  source_dir      = "../src/lambdas/log_analyzer"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 256

  environment_variables = {
    LOG_LEVEL = "INFO"
  }

  tags = {
    Environment = var.environment
    Service     = "sre-copilot"
  }
}

module "metrics_analyzer_lambda" {
  source = "./modules/lambda"

  function_name    = "sre-metrics-analyzer-lambda"
  description     = "SRE Metrics Analyzer Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.sre_lambda_role.arn
  source_dir      = "../src/lambdas/metrics_analyzer"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 256

  environment_variables = {
    LOG_LEVEL = "INFO"
  }

  tags = {
    Environment = var.environment
    Service     = "sre-copilot"
  }
}

module "supervisor_lambda" {
  source = "./modules/lambda"

  function_name    = "sre-supervisor-lambda"
  description     = "SRE Supervisor Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.sre_lambda_role.arn
  source_dir      = "../src/lambdas/supervisor"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 256

  environment_variables = {
    LOG_LEVEL = "INFO"
  }

  tags = {
    Environment = var.environment
    Service     = "sre-copilot"
  }
}

# CloudTrail Agent Lambda
module "cloudtrail_agent_lambda" {
  source = "./modules/lambda"

  function_name    = "sre-cloudtrail-agent-lambda"
  description     = "SRE CloudTrail Agent Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.sre_lambda_role.arn
  source_dir      = "../src/lambdas/cloudtrail_agent"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 256

  environment_variables = {
    LOG_LEVEL = "INFO"
  }

  tags = {
    Environment = var.environment
    Service     = "sre-copilot"
  }
}

# VPC Flow Logs Agent Lambda
module "vpc_flow_logs_agent_lambda" {
  source = "./modules/lambda"

  function_name    = "sre-vpc-flow-logs-agent-lambda"
  description     = "SRE VPC Flow Logs Agent Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.sre_lambda_role.arn
  source_dir      = "../src/lambdas/vpc_flow_logs_agent"
  runtime         = "python3.9"
  timeout         = 60
  memory_size     = 256

  environment_variables = {
    LOG_LEVEL = "INFO"
    SUPERVISOR_ID = "XKVWGESIAX"  # From sre_copilot_config.json
  }

  tags = {
    Environment = var.environment
    Service     = "sre-copilot"
  }
}

# Trusted Advisor Agent Lambda
module "trusted_advisor_agent_lambda" {
  source = "./modules/lambda"

  function_name    = "sre-trusted-advisor-agent-lambda"
  description     = "SRE Trusted Advisor Agent Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.sre_lambda_role.arn
  source_dir      = "../src/lambdas/trusted_advisor_agent"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 256

  environment_variables = {
    LOG_LEVEL = "INFO"
  }

  tags = {
    Environment = var.environment
    Service     = "sre-copilot"
  }
}

# Personal Health Agent Lambda
module "personal_health_agent_lambda" {
  source = "./modules/lambda"

  function_name    = "sre-personal-health-agent-lambda"
  description     = "SRE Personal Health Agent Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.sre_lambda_role.arn
  source_dir      = "../src/lambdas/personal_health_agent"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 256

  environment_variables = {
    LOG_LEVEL = "INFO"
  }

  tags = {
    Environment = var.environment
    Service     = "sre-copilot"
  }
}

module "vpc_agent_lambda" {
  source = "./modules/lambda"

  function_name    = "sre-vpc-agent-lambda"
  description     = "SRE VPC Agent Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.sre_lambda_role.arn
  source_dir      = "../src/lambdas/vpc_agent"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 256

  environment_variables = {
    LOG_LEVEL = "INFO"
  }

  tags = {
    Environment = var.environment
    Service     = "sre-copilot"
  }
}

# CloudWatch Logs Agent Lambda
module "cloudwatch_logs_agent_lambda" {
  source = "./modules/lambda"

  function_name    = "sre-cloudwatch-logs-agent-lambda"
  description     = "SRE CloudWatch Logs Agent Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.sre_lambda_role.arn
  source_dir      = "../src/lambdas/cloudwatch_logs_agent"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 256

  environment_variables = {
    LOG_LEVEL = "INFO"
  }

  tags = {
    Environment = var.environment
    Service     = "sre-copilot"
  }
} 

# Add Lambda invoke policy for supervisor
resource "aws_iam_role_policy" "lambda_invoke_access" {
  name = "lambda-invoke-access"
  role = aws_iam_role.sre_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:*:*:function:sre-*"
      }
    ]
  })
}

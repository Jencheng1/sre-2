# SRE Copilot Infrastructure

This Terraform configuration deploys the infrastructure required for the SRE Copilot system, including Lambda functions for log analysis, metrics analysis, and incident response supervision.

## Prerequisites

- Terraform >= 1.2.0
- AWS CLI configured with appropriate credentials
- Python 3.9 or later
- AWS account with appropriate permissions

## Directory Structure

```
terraform/
├── main.tf              # Main Terraform configuration
├── variables.tf         # Variable definitions
├── outputs.tf          # Output definitions
└── modules/
    └── lambda/         # Lambda function module
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Configuration

1. Update the variables in `variables.tf` to match your environment:
   - `aws_region`: AWS region where resources will be deployed
   - `environment`: Environment name (e.g., dev, prod)
   - `project_name`: Project name for resource naming

2. Initialize Terraform:
```bash
terraform init
```

3. Review the planned changes:
```bash
terraform plan
```

4. Apply the configuration:
```bash
terraform apply
```

## Deployed Resources

The configuration creates the following resources:

1. IAM Role and Policies:
   - Lambda execution role with basic permissions
   - Bedrock access policy

2. Lambda Functions:
   - Log Analyzer (`sre-log-analyzer-lambda`)
   - Metrics Analyzer (`sre-metrics-analyzer-lambda`)
   - Supervisor (`sre-supervisor-lambda`)

3. CloudWatch Log Groups:
   - One log group per Lambda function
   - 14-day log retention by default

## Module Usage

The Lambda module can be used independently for other functions:

```hcl
module "custom_lambda" {
  source = "./modules/lambda"

  function_name    = "custom-function"
  description     = "Custom Lambda Function"
  handler         = "lambda_function.lambda_handler"
  lambda_role_arn = aws_iam_role.lambda_role.arn
  source_dir      = "../src/lambdas/custom"
  runtime         = "python3.9"
  
  environment_variables = {
    KEY = "value"
  }

  tags = {
    Environment = "dev"
  }
}
```

## Outputs

The configuration provides the following outputs:

- `lambda_role_arn`: ARN of the Lambda IAM role
- `log_analyzer_lambda`: Details of the Log Analyzer Lambda function
- `metrics_analyzer_lambda`: Details of the Metrics Analyzer Lambda function
- `supervisor_lambda`: Details of the Supervisor Lambda function

## Cleanup

To remove all created resources:

```bash
terraform destroy
```

## Notes

- The Lambda functions are deployed with Python 3.9 runtime
- Dependencies are installed automatically during deployment
- CloudWatch logs are retained for 14 days by default
 
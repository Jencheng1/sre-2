output "lambda_role_arn" {
  description = "ARN of the Lambda IAM role"
  value       = aws_iam_role.sre_lambda_role.arn
}

output "log_analyzer_lambda" {
  description = "Log Analyzer Lambda function details"
  value = {
    arn         = module.log_analyzer_lambda.function_arn
    name        = module.log_analyzer_lambda.function_name
    invoke_arn  = module.log_analyzer_lambda.invoke_arn
    log_group   = module.log_analyzer_lambda.log_group_name
  }
}

output "metrics_analyzer_lambda" {
  description = "Metrics Analyzer Lambda function details"
  value = {
    arn         = module.metrics_analyzer_lambda.function_arn
    name        = module.metrics_analyzer_lambda.function_name
    invoke_arn  = module.metrics_analyzer_lambda.invoke_arn
    log_group   = module.metrics_analyzer_lambda.log_group_name
  }
}

output "supervisor_lambda" {
  description = "Supervisor Lambda function details"
  value = {
    arn         = module.supervisor_lambda.function_arn
    name        = module.supervisor_lambda.function_name
    invoke_arn  = module.supervisor_lambda.invoke_arn
    log_group   = module.supervisor_lambda.log_group_name
  }
}

output "cloudtrail_agent_lambda" {
  description = "CloudTrail Agent Lambda function details"
  value = {
    arn         = module.cloudtrail_agent_lambda.function_arn
    name        = module.cloudtrail_agent_lambda.function_name
    invoke_arn  = module.cloudtrail_agent_lambda.invoke_arn
    log_group   = module.cloudtrail_agent_lambda.log_group_name
  }
}

output "vpc_flow_logs_agent_lambda" {
  description = "VPC Flow Logs Agent Lambda function details"
  value = {
    arn         = module.vpc_flow_logs_agent_lambda.function_arn
    name        = module.vpc_flow_logs_agent_lambda.function_name
    invoke_arn  = module.vpc_flow_logs_agent_lambda.invoke_arn
    log_group   = module.vpc_flow_logs_agent_lambda.log_group_name
  }
}

output "trusted_advisor_agent_lambda" {
  description = "Trusted Advisor Agent Lambda function details"
  value = {
    arn         = module.trusted_advisor_agent_lambda.function_arn
    name        = module.trusted_advisor_agent_lambda.function_name
    invoke_arn  = module.trusted_advisor_agent_lambda.invoke_arn
    log_group   = module.trusted_advisor_agent_lambda.log_group_name
  }
}

output "personal_health_agent_lambda" {
  description = "Personal Health Agent Lambda function details"
  value = {
    arn         = module.personal_health_agent_lambda.function_arn
    name        = module.personal_health_agent_lambda.function_name
    invoke_arn  = module.personal_health_agent_lambda.invoke_arn
    log_group   = module.personal_health_agent_lambda.log_group_name
  }
}

output "cloudtrail_agent_lambda_arn" {
  description = "ARN of the CloudTrail Agent Lambda function"
  value       = module.cloudtrail_agent_lambda.function_arn
}

output "vpc_agent_lambda_arn" {
  description = "ARN of the VPC Agent Lambda function"
  value       = module.vpc_agent_lambda.function_arn
}

output "trusted_advisor_agent_lambda_arn" {
  description = "ARN of the Trusted Advisor Agent Lambda function"
  value       = module.trusted_advisor_agent_lambda.function_arn
}

output "personal_health_agent_lambda_arn" {
  description = "ARN of the Personal Health Agent Lambda function"
  value       = module.personal_health_agent_lambda.function_arn
} 
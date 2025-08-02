locals {
  lambda_zip_path = "${path.module}/lambda_function.zip"
  temp_dir       = "${path.module}/temp"
}

# Create temporary directory and copy source files
resource "null_resource" "prepare_lambda" {
  triggers = {
    source_code = fileexists("${var.source_dir}/requirements.txt") ? filesha256("${var.source_dir}/requirements.txt") : "no-requirements"
    lambda_file = filesha256("${var.source_dir}/lambda_function.py")
  }

  provisioner "local-exec" {
    command = <<EOT
      rm -rf ${local.temp_dir}
      mkdir -p ${local.temp_dir}
      cp ${var.source_dir}/lambda_function.py ${local.temp_dir}/
      if [ -f "${var.source_dir}/requirements.txt" ]; then
        cp ${var.source_dir}/requirements.txt ${local.temp_dir}/
        cd ${local.temp_dir}
        pip install -r requirements.txt -t .
        find . -type d -name "__pycache__" -exec rm -rf {} +
        find . -type f -name "*.pyc" -delete
        find . -type d -name "*.dist-info" -exec rm -rf {} +
      fi
    EOT

    interpreter = ["bash", "-c"]
  }
}

# Create ZIP file from temporary directory
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = local.temp_dir
  output_path = local.lambda_zip_path

  depends_on = [
    null_resource.prepare_lambda
  ]
}

# Create Lambda function
resource "aws_lambda_function" "function" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.function_name
  role            = var.lambda_role_arn
  handler         = var.handler
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = var.runtime
  timeout         = var.timeout
  memory_size     = var.memory_size
  description     = var.description

  environment {
    variables = var.environment_variables
  }

  depends_on = [
    data.archive_file.lambda_zip
  ]

  tags = var.tags
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags

  lifecycle {
    prevent_destroy = false
  }
}

# Lambda function URL (optional)
resource "aws_lambda_function_url" "function_url" {
  count              = var.create_function_url ? 1 : 0
  function_name      = aws_lambda_function.function.function_name
  authorization_type = "AWS_IAM"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["*"]
    expose_headers    = ["*"]
    max_age          = 86400
  }
} 
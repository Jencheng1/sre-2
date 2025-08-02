#!/usr/bin/env bash

echo "Starting cleanup process..."

# Function names
LAMBDA_FUNCTIONS=(
    "sre-log-analyzer-lambda"
    "sre-metrics-analyzer-lambda"
    "sre-supervisor-lambda"
)

# Local directories to clean
LAMBDA_DIRS=(
    "src/lambdas/log_analyzer"
    "src/lambdas/metrics_analyzer"
    "src/lambdas/supervisor"
)

# Clean AWS resources
echo "Cleaning up AWS resources..."

# Delete CloudWatch Log Groups
for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo "Deleting log group for $func..."
    aws logs delete-log-group --log-group-name "/aws/lambda/$func" --region us-east-1 || true
done

# Clean up local files
echo "Cleaning up local files..."

# Clean up Terraform artifacts
rm -rf terraform/.terraform
rm -f terraform/.terraform.lock.hcl
rm -f terraform/terraform.tfstate*

# Clean up Lambda directories
for dir in "${LAMBDA_DIRS[@]}"; do
    echo "Cleaning up $dir..."
    
    # Remove Python artifacts
    find "$dir" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$dir" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "$dir" -type f -name "*.pyo" -delete 2>/dev/null || true
    find "$dir" -type f -name "*.pyd" -delete 2>/dev/null || true
    find "$dir" -type f -name "*.so" -delete 2>/dev/null || true
    find "$dir" -type f -name "*.dll" -delete 2>/dev/null || true
    find "$dir" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
    rm -rf "$dir"/boto* 2>/dev/null || true
    rm -rf "$dir"/python_dateutil* 2>/dev/null || true
    rm -rf "$dir"/numpy* 2>/dev/null || true
    rm -rf "$dir"/pandas* 2>/dev/null || true
done

# Clean up temporary directories
rm -rf terraform/modules/lambda/temp 2>/dev/null || true
rm -f terraform/modules/lambda/*.zip 2>/dev/null || true

echo "Cleanup complete!"

# Initialize Terraform
echo "Reinitializing Terraform..."
cd terraform
terraform init -reconfigure

echo "Ready to run 'terraform plan' and 'terraform apply'" 
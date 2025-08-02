#!/bin/bash

# Clean up Lambda artifacts
LAMBDA_DIRS=(
    "src/lambdas/log_analyzer"
    "src/lambdas/metrics_analyzer"
    "src/lambdas/supervisor"
)

echo "Cleaning up Lambda artifacts..."

# Clean up Terraform artifacts
rm -rf terraform/.terraform
rm -f terraform/.terraform.lock.hcl
rm -f terraform/terraform.tfstate*

# Clean up Lambda directories
for dir in "${LAMBDA_DIRS[@]}"; do
    echo "Cleaning up $dir..."
    
    # Remove Python artifacts
    find "$dir" -type d -name "__pycache__" -exec rm -rf {} +
    find "$dir" -type f -name "*.pyc" -delete
    find "$dir" -type f -name "*.pyo" -delete
    find "$dir" -type f -name "*.pyd" -delete
    find "$dir" -type f -name "*.so" -delete
    find "$dir" -type f -name "*.dll" -delete
    find "$dir" -type d -name "*.dist-info" -exec rm -rf {} +
    rm -rf "$dir"/boto*
    rm -rf "$dir"/python_dateutil*
    rm -rf "$dir"/numpy*
    rm -rf "$dir"/pandas*
done

# Clean up temporary directories
rm -rf terraform/modules/lambda/temp
rm -f terraform/modules/lambda/*.zip

echo "Cleanup complete!" 
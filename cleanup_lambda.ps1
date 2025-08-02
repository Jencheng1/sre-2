# Clean up Lambda artifacts
$lambdaDirs = @(
    "src/lambdas/log_analyzer",
    "src/lambdas/metrics_analyzer",
    "src/lambdas/supervisor"
)

Write-Host "Cleaning up Lambda artifacts..."

# Clean up Terraform artifacts
Remove-Item -Path "terraform/.terraform" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "terraform/.terraform.lock.hcl" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "terraform/terraform.tfstate*" -Force -ErrorAction SilentlyContinue

# Clean up Lambda directories
foreach ($dir in $lambdaDirs) {
    Write-Host "Cleaning up $dir..."
    
    # Remove Python artifacts
    Get-ChildItem -Path $dir -Include @(
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.so",
        "*.dll",
        "*.dist-info",
        "boto*",
        "python_dateutil*",
        "numpy*",
        "pandas*"
    ) -Recurse | Remove-Item -Recurse -Force
}

# Clean up temporary directories
Remove-Item -Path "terraform/modules/lambda/temp" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "terraform/modules/lambda/*.zip" -Force -ErrorAction SilentlyContinue

Write-Host "Cleanup complete!" 
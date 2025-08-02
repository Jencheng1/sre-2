# Clean up and prepare Lambda directories
$lambdaDirs = @(
    "src/lambdas/log_analyzer",
    "src/lambdas/metrics_analyzer",
    "src/lambdas/supervisor"
)

foreach ($dir in $lambdaDirs) {
    Write-Host "Cleaning up $dir..."
    
    # Remove existing artifacts
    Remove-Item -Path "$dir/__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$dir/*.pyc" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$dir/*.pyo" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$dir/*.pyd" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$dir/*.so" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$dir/*.dll" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$dir/boto*" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$dir/python_dateutil*" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$dir/numpy*" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$dir/pandas*" -Recurse -Force -ErrorAction SilentlyContinue
    
    # Fix line endings in Python files
    Get-ChildItem -Path $dir -Filter "*.py" | ForEach-Object {
        $content = Get-Content $_.FullName -Raw
        $content = $content -replace "`r`n", "`n"
        Set-Content -Path $_.FullName -Value $content -NoNewline
        Add-Content -Path $_.FullName -Value "`n"
    }
    
    # Fix line endings in requirements.txt
    $reqPath = Join-Path $dir "requirements.txt"
    if (Test-Path $reqPath) {
        $content = Get-Content $reqPath -Raw
        $content = $content -replace "`r`n", "`n"
        Set-Content -Path $reqPath -Value $content -NoNewline
        Add-Content -Path $reqPath -Value "`n"
    }
} 
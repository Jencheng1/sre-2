#!/bin/bash

echo "Running CPU Spike Demo and Grafana Integration Tests..."
echo "========================================================"

# Run tests with clean output
python3 test_cpu_spike_grafana_integration.py 2>&1 | grep -E "(TEST|✓|✗|Passed|Failed|SUMMARY|ALL TESTS)" | grep -v "DEBUG:" | grep -v "INFO:"

# Check test report
if [ -f cpu_spike_test_report_*.json ]; then
    echo ""
    echo "Test report generated:"
    ls -la cpu_spike_test_report_*.json | tail -1
fi
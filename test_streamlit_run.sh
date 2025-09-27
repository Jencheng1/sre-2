#!/bin/bash
# Test running the CPU spike demo in Streamlit

echo "=== Testing Streamlit CPU Spike Demo ==="

# Kill any existing streamlit processes
echo "Stopping any existing Streamlit processes..."
pkill -f streamlit || true
sleep 2

# Start the streamlit app in background
echo "Starting Streamlit app..."
export AWS_DEFAULT_REGION=us-east-1
nohup python3 -m streamlit run streamlit_app_cpu_spike.py --server.port 8502 --server.address 0.0.0.0 --server.headless true > streamlit_test.log 2>&1 &

echo "Waiting for Streamlit to start..."
sleep 5

# Check if it's running
if pgrep -f "streamlit run streamlit_app_cpu_spike.py" > /dev/null; then
    echo "✓ Streamlit is running on port 8502"
    echo "✓ Access it at http://localhost:8502"
    echo ""
    echo "To view logs: tail -f streamlit_test.log"
    echo "To stop: pkill -f streamlit"
else
    echo "✗ Streamlit failed to start"
    echo "Check streamlit_test.log for errors"
    cat streamlit_test.log
fi
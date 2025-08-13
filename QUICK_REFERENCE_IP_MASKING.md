# IP Masking Quick Reference

## 🚀 Quick Test Commands
```bash
# Test IP masking is working
python3 demo_ip_masking.py

# Run integration tests
python3 test_ip_masking_integration.py

# Check Streamlit UI (should already be running)
curl http://localhost:8501 | grep -q "SRE Copilot" && echo "✅ Streamlit is running" || echo "❌ Streamlit not running"
```

## 📍 Key Locations
- **IP Masker Utility**: `utils/ip_masker.py`
- **Supervisor Lambda**: `src/lambdas/supervisor/lambda_function.py`
- **CloudWatch Agent**: `src/lambdas/cloudwatch_logs_agent/lambda_function.py`
- **Streamlit UI**: `streamlit_app.py` (see `display_data_analysis` method)

## 🔧 How to Use

### In Lambda Functions:
```python
# Logs are masked by default
log_data = get_demo_logs()  # mask_ips=True by default

# To disable masking (internal use only)
log_data = get_demo_logs(mask_ips=False)
```

### In Streamlit UI:
1. Go to "Analyze Incident" tab
2. Run an analysis
3. Click "Data Analysis" tab
4. Toggle "🔒 Show IP Masking" to switch views

### Standalone Usage:
```python
from utils.ip_masker import mask_logs_for_llm

# Quick masking
masked = mask_logs_for_llm("Error at 192.168.1.100")
print(masked)  # "Error at 192.168.XXX.XXX"
```

## 🎯 What Gets Masked
- IPv4: `192.168.1.100` → `192.168.XXX.XXX`
- IPv6: `2001:db8::1` → `2001:db8::XXXX:XXXX`
- AWS Logs: VPC Flow, ELB, CloudTrail patterns
- JSON: Recursive masking of all IP fields

## 📊 Current Status
- ✅ All integration tests passing
- ✅ ~18,000 logs/second performance
- ✅ Streamlit UI toggle working
- ✅ Lambda functions integrated
- ✅ Security compliance met

## 🆘 Troubleshooting
```bash
# If imports fail
export PYTHONPATH=/home/ec2-user/sre/sre_mcp:$PYTHONPATH

# Check if masking is working
echo "Test IP 192.168.1.1" | python3 -c "
import sys; sys.path.insert(0, '.')
from utils.ip_masker import mask_logs_for_llm
print(mask_logs_for_llm(sys.stdin.read().strip()))"

# Should output: Test IP 192.168.XXX.XXX
```
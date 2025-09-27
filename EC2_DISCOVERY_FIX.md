# EC2 Discovery Fix Summary

## Issue
The CPU Spike Demo was showing "No EC2 instances found or accessible" even though EC2 instances were running.

## Root Cause
The EC2 instance filter in `cpu_spike_generator.py` was incorrectly filtering for:
```python
{'Name': 'platform', 'Values': ['linux']}
```

This filter was looking for instances with platform='linux', but EC2 instances don't have this platform value. The platform field is typically:
- Empty/None for Linux instances
- 'windows' for Windows instances

## Fix Applied
Removed the platform filter, keeping only the running state filter:
```python
response = self.ec2_client.describe_instances(
    Filters=[
        {'Name': 'instance-state-name', 'Values': ['running']}
    ]
)
```

## Results
✅ **Fixed!** The system now correctly discovers:
- 2 EC2 instances found
- Both have SSM agent enabled
- System readiness: 100%

## Verified Working
- **SRE-DEMO** (i-02bef13982a179478) - SSM Enabled ✅
- **sre-boston** (i-05ad220ef77a67ca7) - SSM Enabled ✅

## Access the Demo
1. Go to http://localhost:8501
2. Navigate to "🛠️ Advanced Tools"
3. Click "🚨 CPU Spike Demo"
4. You should now see the EC2 instances in the dropdown!

The CPU Spike Demo is now fully operational with real EC2 instances available for testing.
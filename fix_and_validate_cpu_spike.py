#!/usr/bin/env python3
"""
Fix and validate CPU Spike Demo functionality
"""

import os
import sys
import subprocess
import time

# Set environment
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

print("=== CPU Spike Demo Fix and Validation ===")

# Step 1: Test direct functionality
print("\n1. Testing direct CPU spike functionality...")
try:
    from cpu_spike_generator import CPUSpikeGenerator
    gen = CPUSpikeGenerator()
    instances = gen.get_available_ec2_instances()
    print(f"✓ Direct test successful: Found {len(instances)} instances")
    for inst in instances:
        print(f"  - {inst['name']} ({inst['instance_id']}): SSM={inst['ssm_enabled']}")
except Exception as e:
    print(f"✗ Direct test failed: {e}")
    sys.exit(1)

# Step 2: Check if instances were found
if not instances:
    print("\n✗ No EC2 instances found!")
    print("Possible issues:")
    print("1. No running EC2 instances in us-east-1")
    print("2. Missing IAM permissions")
    sys.exit(1)

# Check SSM instances
ssm_instances = [i for i in instances if i['ssm_enabled']]
if not ssm_instances:
    print("\n⚠ No SSM-enabled instances found!")
    print("The demo requires SSM agent on EC2 instances")
else:
    print(f"\n✓ Found {len(ssm_instances)} SSM-enabled instances")

# Step 3: Stop any running streamlit processes
print("\n2. Stopping any existing Streamlit processes...")
subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
time.sleep(2)

# Step 4: Provide instructions
print("\n✅ CPU Spike Demo is ready to use!")
print("\nTo run the demo:")
print("\n1. Use the main Streamlit app:")
print("   export AWS_DEFAULT_REGION=us-east-1")
print("   python3 -m streamlit run streamlit_app.py")
print("   Then navigate to: Advanced Tools > CPU Spike Demo")
print("\n2. Or use the standalone CPU spike app:")
print("   export AWS_DEFAULT_REGION=us-east-1")
print("   python3 -m streamlit run streamlit_app_cpu_spike.py")

if ssm_instances:
    print(f"\n✓ You have {len(ssm_instances)} EC2 instances ready for CPU spike testing")
else:
    print("\n⚠ No SSM-enabled instances - the demo won't be able to trigger spikes")
    print("  To fix: Ensure EC2 instances have SSM agent and proper IAM role")
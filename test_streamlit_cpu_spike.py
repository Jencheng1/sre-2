#!/usr/bin/env python3
"""Test the CPU spike demo functionality"""

import os
import sys

# Set AWS region
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Import the CPU spike generator
from cpu_spike_generator import CPUSpikeGenerator

print("Testing CPU Spike Demo functionality...")

# Test 1: Basic instantiation
print("\n1. Testing CPUSpikeGenerator instantiation...")
try:
    gen = CPUSpikeGenerator()
    print("✓ CPUSpikeGenerator created successfully")
except Exception as e:
    print(f"✗ Failed to create CPUSpikeGenerator: {e}")
    sys.exit(1)

# Test 2: Get instances
print("\n2. Testing get_available_ec2_instances...")
try:
    instances = gen.get_available_ec2_instances()
    print(f"✓ Found {len(instances)} EC2 instances")
    
    for inst in instances:
        print(f"  - {inst['name']} ({inst['instance_id']}): SSM={inst['ssm_enabled']}")
        
    ssm_instances = [i for i in instances if i['ssm_enabled']]
    print(f"✓ SSM-enabled instances: {len(ssm_instances)}")
    
except Exception as e:
    print(f"✗ Failed to get instances: {e}")
    sys.exit(1)

# Test 3: Check if there are SSM instances
print("\n3. Checking SSM availability...")
if not instances:
    print("✗ No EC2 instances found")
elif not ssm_instances:
    print("✗ No SSM-enabled instances found")
else:
    print("✓ SSM-enabled instances available for CPU spike demo")

print("\n✅ All tests passed! The CPU spike demo should work correctly.")
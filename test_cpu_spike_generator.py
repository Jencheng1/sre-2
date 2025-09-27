#!/usr/bin/env python3
"""Test CPU spike generator directly"""

import sys
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import and test
from cpu_spike_generator import CPUSpikeGenerator

print("=== Testing CPU Spike Generator ===")

generator = CPUSpikeGenerator()
instances = generator.get_available_ec2_instances()

print(f"\nTotal instances found: {len(instances)}")
for inst in instances:
    print(f"\n{inst['name']} ({inst['instance_id']}):")
    print(f"  Type: {inst['instance_type']}")
    print(f"  State: {inst['state']}")
    print(f"  SSM Enabled: {inst['ssm_enabled']}")
    print(f"  Private IP: {inst['private_ip']}")

ssm_instances = [i for i in instances if i['ssm_enabled']]
print(f"\nSSM-enabled instances: {len(ssm_instances)}")
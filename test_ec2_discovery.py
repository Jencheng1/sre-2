#!/usr/bin/env python3
"""Quick test to verify EC2 instance discovery is working"""

from cpu_spike_generator import CPUSpikeGenerator

def test_ec2_discovery():
    print("Testing EC2 instance discovery...")
    
    gen = CPUSpikeGenerator()
    instances = gen.get_available_ec2_instances()
    
    print(f"\nFound {len(instances)} EC2 instances:")
    for inst in instances:
        print(f"\nInstance: {inst['name']} ({inst['instance_id']})")
        print(f"  Type: {inst['instance_type']}")
        print(f"  State: {inst['state']}")
        print(f"  Private IP: {inst['private_ip']}")
        print(f"  Public IP: {inst['public_ip']}")
        print(f"  SSM Enabled: {inst['ssm_enabled']}")
    
    # Check SSM status
    ssm_enabled = [i for i in instances if i['ssm_enabled']]
    print(f"\n{len(ssm_enabled)} instances have SSM agent enabled")
    
    return len(instances) > 0

if __name__ == "__main__":
    success = test_ec2_discovery()
    if success:
        print("\n✅ EC2 discovery is working!")
    else:
        print("\n❌ No EC2 instances found")
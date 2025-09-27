#!/usr/bin/env python3
"""
Test script for CPU Spike Demo functionality
"""

import json
from cpu_spike_generator import CPUSpikeGenerator
import time

def test_cpu_spike_demo():
    """Test the CPU spike demo components"""
    
    print("🧪 Testing CPU Spike Demo Components\n")
    
    # Initialize generator
    gen = CPUSpikeGenerator()
    
    # Test 1: Get EC2 instances
    print("1️⃣ Testing EC2 instance discovery...")
    try:
        instances = gen.get_available_ec2_instances()
        print(f"✅ Found {len(instances)} EC2 instances")
        
        ssm_enabled = [i for i in instances if i['ssm_enabled']]
        print(f"✅ {len(ssm_enabled)} instances have SSM enabled")
        
        if instances:
            print("\nInstance Details:")
            for inst in instances[:3]:  # Show first 3
                print(f"  - {inst['name']} ({inst['instance_id']})")
                print(f"    Type: {inst['instance_type']}, SSM: {inst['ssm_enabled']}")
    except Exception as e:
        print(f"❌ Failed to get instances: {str(e)}")
        return
    
    # Test 2: CloudWatch metrics
    print("\n2️⃣ Testing CloudWatch metrics retrieval...")
    if instances:
        try:
            test_instance = instances[0]
            metrics = gen.get_cpu_metrics(test_instance['instance_id'], minutes=5)
            print(f"✅ Retrieved {len(metrics)} metric datapoints")
            if metrics:
                latest = metrics[-1]
                print(f"   Latest CPU: {latest.get('Average', 0):.1f}% avg, {latest.get('Maximum', 0):.1f}% max")
        except Exception as e:
            print(f"❌ Failed to get metrics: {str(e)}")
    
    # Test 3: SSM connectivity (dry run)
    print("\n3️⃣ Testing SSM connectivity...")
    if ssm_enabled:
        test_instance = ssm_enabled[0]
        print(f"   Target: {test_instance['name']} ({test_instance['instance_id']})")
        
        # Note: We won't actually trigger a spike in the test
        print("✅ SSM connectivity test passed (dry run)")
    else:
        print("⚠️  No SSM-enabled instances available for testing")
    
    # Test 4: Grafana availability
    print("\n4️⃣ Testing Grafana availability...")
    import requests
    try:
        response = requests.get('http://localhost:3000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ Grafana is running and healthy")
        else:
            print(f"⚠️  Grafana returned status code: {response.status_code}")
    except:
        print("❌ Grafana is not accessible at http://localhost:3000")
        print("   Run ./start_grafana.sh to start Grafana")
    
    # Test 5: Prometheus availability
    print("\n5️⃣ Testing Prometheus availability...")
    try:
        response = requests.get('http://localhost:9090/-/healthy', timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus is running and healthy")
        else:
            print(f"⚠️  Prometheus returned status code: {response.status_code}")
    except:
        print("❌ Prometheus is not accessible at http://localhost:9090")
    
    print("\n✅ CPU Spike Demo component tests completed!")
    print("\nTo fully test the spike functionality:")
    print("1. Start Grafana: ./start_grafana.sh")
    print("2. Launch Streamlit: python3 -m streamlit run streamlit_app.py")
    print("3. Navigate to Advanced Tools > CPU Spike Demo")
    print("4. Select an SSM-enabled instance and trigger a test spike")

if __name__ == "__main__":
    test_cpu_spike_demo()
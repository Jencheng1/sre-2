#!/usr/bin/env python3
"""
Complete Correlation Demo Runner
Demonstrates full correlation analysis with Java memory leak, changes, and monitoring
"""

import subprocess
import time
import sys

def run_command(description, command):
    """Run a command and display status"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print()
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Success!")
            if result.stdout:
                print("\nOutput:")
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        else:
            print("❌ Failed!")
            if result.stderr:
                print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🎯 COMPLETE CORRELATION DEMO")
    print("=" * 80)
    print("This demo will:")
    print("1. Setup Java/JVM monitoring in Grafana")
    print("2. Create change records in Systems Manager")
    print("3. Simulate a Java memory leak from a code change")
    print("4. Demonstrate correlation analysis")
    print("=" * 80)
    
    print("\n⚠️  Prerequisites:")
    print("- AWS credentials configured")
    print("- Grafana running on port 3000")
    print("- SRE-DEMO instance accessible")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    # Step 1: Setup Java monitoring
    if not run_command(
        "Step 1: Setting up Java/JVM Monitoring",
        "python3 setup_java_metrics_monitoring.py"
    ):
        print("\n⚠️  Java monitoring setup failed, but continuing...")
    
    time.sleep(3)
    
    # Step 2: Create change records
    if not run_command(
        "Step 2: Creating Change Records & Dashboard",
        "python3 create_change_record_demo.py"
    ):
        print("\n⚠️  Change record creation failed, but continuing...")
    
    time.sleep(3)
    
    # Step 3: Run memory leak simulation
    if not run_command(
        "Step 3: Simulating Java Memory Leak Scenario",
        "python3 java_memory_leak_test_case.py"
    ):
        print("\n❌ Memory leak simulation failed!")
        return 1
    
    # Summary
    print("\n" + "="*80)
    print("🎉 DEMO COMPLETE!")
    print("="*80)
    
    print("\n📊 GRAFANA DASHBOARDS:")
    print("1. Java Application Monitoring:")
    print("   http://localhost:3000/d/java-app-monitoring")
    print("   - Shows JVM heap usage, GC activity, thread count")
    print("   - Monitor memory growth pattern")
    
    print("\n2. Change Management Dashboard:")
    print("   http://localhost:3000/d/change-management")
    print("   - Shows change timeline with risk scores")
    print("   - Correlation with CPU/Memory spikes")
    
    print("\n3. EC2 Maximum CPU Dashboard:")
    print("   http://localhost:3000/d/ec2-max-cpu")
    print("   - Shows CPU spike correlation")
    
    print("\n🔍 STREAMLIT CORRELATION DEMO:")
    print("1. Open Streamlit dashboard")
    print("2. Go to 'Advanced Tools' > 'CPU Spike Demo'")
    print("3. Select 'SRE-DEMO' instance")
    print("4. Click 'Run Root Cause Analysis'")
    
    print("\n📈 EXPECTED CORRELATION RESULTS:")
    print("✓ Code change detected 2 hours before CPU spike")
    print("✓ Memory leak pattern identified in JVM metrics")
    print("✓ TransactionCache growth correlated with deployment")
    print("✓ GC overhead causing CPU spike")
    print("✓ Root cause: Unbounded cache in new code")
    
    print("\n🔗 KEY CORRELATIONS:")
    print("1. CHANGE → Memory Leak → CPU Spike")
    print("2. Timeline: Deploy (T-2h) → Memory Growth → GC Pressure → CPU 95%")
    print("3. Evidence: Logs show OutOfMemoryError, metrics show heap exhaustion")
    
    print("\n💡 DEMO INSIGHTS:")
    print("- Changes are tracked in Systems Manager OpsCenter")
    print("- Metrics flow through CloudWatch to Grafana")
    print("- Supervisor Lambda correlates all data sources")
    print("- Knowledge base captures patterns for future reference")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
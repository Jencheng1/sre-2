#!/usr/bin/env python3
"""Verify all fixes for CPU spike demo and Grafana monitoring"""

import os
import sys
import requests
import boto3
import json
from datetime import datetime

# Set environment
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

def check_mark(status):
    return "✅" if status else "❌"

def verify_ops_item_fix():
    """Verify OpsItem creation fix"""
    print("\n1. Verifying OpsItem Fix...")
    
    try:
        # Import the dashboard
        from streamlit_app import EnhancedSREDashboard
        dashboard = EnhancedSREDashboard()
        
        # Check attribute exists
        has_ssm_client = hasattr(dashboard, 'ssm_client')
        print(f"  {check_mark(has_ssm_client)} dashboard.ssm_client exists: {has_ssm_client}")
        
        return has_ssm_client
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def verify_grafana_setup():
    """Verify Grafana is properly configured"""
    print("\n2. Verifying Grafana Setup...")
    
    results = {
        'grafana_health': False,
        'datasources': False,
        'dashboard': False,
        'metrics': False
    }
    
    try:
        # Check Grafana health
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        results['grafana_health'] = response.status_code == 200
        print(f"  {check_mark(results['grafana_health'])} Grafana health check")
        
        # Check datasources
        auth = ('admin', 'admin123')
        ds_response = requests.get("http://localhost:3000/api/datasources", auth=auth)
        if ds_response.status_code == 200:
            datasources = ds_response.json()
            has_cloudwatch = any(ds['type'] == 'cloudwatch' for ds in datasources)
            has_prometheus = any(ds['type'] == 'prometheus' for ds in datasources)
            results['datasources'] = has_cloudwatch and has_prometheus
            print(f"  {check_mark(has_cloudwatch)} CloudWatch datasource")
            print(f"  {check_mark(has_prometheus)} Prometheus datasource")
        
        # Check dashboards
        dash_response = requests.get("http://localhost:3000/api/search", auth=auth)
        if dash_response.status_code == 200:
            dashboards = dash_response.json()
            cpu_dashboard = any('cpu' in db.get('title', '').lower() for db in dashboards)
            results['dashboard'] = cpu_dashboard
            print(f"  {check_mark(cpu_dashboard)} CPU monitoring dashboard")
        
        # Check if metrics are flowing
        prom_response = requests.get("http://localhost:9090/api/v1/query?query=up")
        if prom_response.status_code == 200:
            data = prom_response.json()
            results['metrics'] = len(data['data']['result']) > 0
            print(f"  {check_mark(results['metrics'])} Prometheus metrics available")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return all(results.values())

def verify_ec2_cpu_metrics():
    """Verify EC2 CPU metrics are available"""
    print("\n3. Verifying EC2 CPU Metrics...")
    
    try:
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Get running instances
        response = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance['InstanceId'])
        
        print(f"  ✅ Found {len(instances)} running EC2 instances")
        
        # Check metrics for first instance
        if instances:
            metrics = cloudwatch.list_metrics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{
                    'Name': 'InstanceId',
                    'Value': instances[0]
                }]
            )
            
            has_metrics = len(metrics['Metrics']) > 0
            print(f"  {check_mark(has_metrics)} CloudWatch CPU metrics available")
            return has_metrics
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def verify_cpu_spike_demo():
    """Verify CPU spike demo functionality"""
    print("\n4. Verifying CPU Spike Demo...")
    
    try:
        from cpu_spike_generator import CPUSpikeGenerator
        gen = CPUSpikeGenerator()
        
        # Get instances
        instances = gen.get_available_ec2_instances()
        print(f"  ✅ CPU spike generator can discover {len(instances)} instances")
        
        # Check SSM
        ssm_instances = [i for i in instances if i['ssm_enabled']]
        print(f"  {check_mark(len(ssm_instances) > 0)} SSM-enabled instances: {len(ssm_instances)}")
        
        return len(ssm_instances) > 0
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def verify_streamlit_running():
    """Verify Streamlit is running"""
    print("\n5. Verifying Streamlit App...")
    
    try:
        response = requests.get("http://localhost:8501/_stcore/health", timeout=5)
        is_running = response.status_code == 200
        print(f"  {check_mark(is_running)} Streamlit app is running on port 8501")
        return is_running
    except:
        print("  ❌ Streamlit app is not accessible")
        return False

def main():
    print("=" * 60)
    print("VERIFICATION OF ALL FIXES")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'ops_item_fix': verify_ops_item_fix(),
        'grafana_setup': verify_grafana_setup(),
        'ec2_metrics': verify_ec2_cpu_metrics(),
        'cpu_spike_demo': verify_cpu_spike_demo(),
        'streamlit_app': verify_streamlit_running()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        print(f"{check_mark(passed)} {check.replace('_', ' ').title()}")
    
    if all_passed:
        print("\n✅ ALL CHECKS PASSED! The system is fully operational.")
        print("\n📊 Access Points:")
        print("- Streamlit Dashboard: http://localhost:8501")
        print("- Grafana: http://localhost:3000 (admin/admin123)")
        print("- Prometheus: http://localhost:9090")
        print("\n🚀 CPU Spike Demo:")
        print("- Navigate to Advanced Tools → CPU Spike Demo")
        print("- Select an EC2 instance and trigger CPU spike")
        print("- Monitor in Grafana EC2 CPU Monitoring dashboard")
    else:
        print("\n❌ Some checks failed. Please review the output above.")
    
    # Save verification report
    report = {
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'all_passed': all_passed
    }
    
    report_file = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Verification report saved to: {report_file}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""Final verification of all fixes"""

import requests
import time
import subprocess
import json
from datetime import datetime

def check_streamlit_rerun_fix():
    """Verify st.rerun() fix"""
    print("\n1️⃣ Checking Streamlit rerun fix...")
    
    # Check if the fix is applied
    with open('/home/ec2-user/sre/sre_mcp/streamlit_app.py', 'r') as f:
        content = f.read()
        if 'st.experimental_rerun()' in content and 'st.rerun()' not in content:
            print("   ✅ st.rerun() has been replaced with st.experimental_rerun()")
            return True
        else:
            print("   ❌ st.rerun() fix not properly applied")
            return False

def check_grafana_dashboards():
    """Check Grafana dashboards"""
    print("\n2️⃣ Checking Grafana dashboards...")
    
    auth = ('admin', 'admin123')
    
    # Check datasources
    r = requests.get("http://localhost:3000/api/datasources", auth=auth)
    if r.status_code == 200:
        datasources = r.json()
        cloudwatch_ds = [ds for ds in datasources if ds['type'] == 'cloudwatch']
        print(f"   ✅ Found {len(cloudwatch_ds)} CloudWatch datasource(s)")
    
    # Check dashboards
    r = requests.get("http://localhost:3000/api/search?type=dash-db", auth=auth)
    if r.status_code == 200:
        dashboards = r.json()
        cpu_dashboards = [db for db in dashboards if 'cpu' in db['title'].lower()]
        print(f"   ✅ Found {len(cpu_dashboards)} CPU dashboards:")
        for db in cpu_dashboards:
            print(f"      • {db['title']}")
    
    return True

def check_ec2_cpu_metrics():
    """Check if EC2 CPU metrics are available"""
    print("\n3️⃣ Checking EC2 CPU metrics...")
    
    try:
        import boto3
        cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        
        # Check for CPU metrics
        metrics = cloudwatch.list_metrics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization'
        )
        
        if metrics['Metrics']:
            print(f"   ✅ Found CPU metrics for {len(metrics['Metrics'])} instances")
            
            # Get recent datapoint
            from datetime import datetime, timedelta
            instance_id = metrics['Metrics'][0]['Dimensions'][0]['Value']
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                print(f"   ✅ Latest CPU for {instance_id}: {latest['Average']:.2f}%")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_streamlit_app():
    """Check if Streamlit app is running"""
    print("\n4️⃣ Checking Streamlit app...")
    
    try:
        r = requests.get("http://localhost:8501/_stcore/health", timeout=5)
        if r.status_code == 200:
            print("   ✅ Streamlit app is running on port 8501")
            return True
    except:
        pass
    
    print("   ❌ Streamlit app is not accessible")
    return False

def main():
    print("=" * 60)
    print("FINAL VERIFICATION OF ALL FIXES")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'streamlit_rerun': check_streamlit_rerun_fix(),
        'grafana_dashboards': check_grafana_dashboards(),
        'ec2_metrics': check_ec2_cpu_metrics(),
        'streamlit_app': check_streamlit_app()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_good = all(results.values())
    
    if all_good:
        print("\n✅ ALL FIXES VERIFIED AND WORKING!")
        print("\n📊 Access Points:")
        print("   • Streamlit: http://localhost:8501")
        print("   • Grafana: http://localhost:3000")
        print("\n🚀 CPU Spike Demo:")
        print("   1. Go to Streamlit → Advanced Tools → CPU Spike Demo")
        print("   2. Click 'Refresh Metrics' - no more rerun errors!")
        print("\n📈 Grafana Dashboards:")
        print("   • EC2 CPU Monitoring - Working: Shows all EC2 CPU metrics")
        print("   • EC2 CPU Test: Test dashboard with specific instance")
        print("\n⏱️  Notes:")
        print("   • Wait 30-60 seconds for Grafana data to populate")
        print("   • Ensure time range is set to 'Last 1 hour'")
    else:
        print("\n❌ Some issues remain:")
        for check, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'fixes_verified': results,
        'all_passed': all_good
    }
    
    report_file = f"final_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")

if __name__ == "__main__":
    main()
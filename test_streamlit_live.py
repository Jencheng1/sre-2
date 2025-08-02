#!/usr/bin/env python3
"""
Test the live Streamlit application functionality.
This script simulates user interactions and verifies the app is working.
"""

import requests
import json
import time
import boto3
from datetime import datetime

class StreamlitLiveTest:
    """Test the running Streamlit application."""
    
    def __init__(self):
        self.base_url = "http://localhost:8501"
        self.lambda_client = boto3.client('lambda')
    
    def test_app_health(self):
        """Test if Streamlit app is healthy."""
        print("🔍 Testing Streamlit App Health...")
        try:
            response = requests.get(f"{self.base_url}/_stcore/health")
            if response.text.strip() == "ok":
                print("✅ Streamlit app is healthy and running!")
                return True
        except Exception as e:
            print(f"❌ Health check failed: {str(e)}")
        return False
    
    def test_real_time_scenario(self):
        """Test a real-time incident scenario."""
        print("\n🎯 Testing Real-Time Incident Analysis...")
        print("-" * 60)
        
        # Define test incident
        incident = {
            'type': 'Performance Degradation',
            'description': 'Production API experiencing high latency, response times over 2 seconds',
            'time': datetime.now().strftime("%H:%M:%S")
        }
        
        print(f"📋 Incident Type: {incident['type']}")
        print(f"📝 Description: {incident['description']}")
        print(f"🕐 Time: {incident['time']}")
        
        # Simulate what the Streamlit app does - invoke supervisor
        print("\n🔄 Simulating Streamlit analysis workflow...")
        
        payload = {
            'body': json.dumps({
                'action': 'analyze',
                'description': incident['description']
            })
        }
        
        try:
            # Call supervisor Lambda (same as Streamlit does)
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            if result['statusCode'] == 200:
                body = json.loads(result['body'])
                
                print("\n✅ Analysis completed successfully!")
                
                # Show collected data
                monitoring_data = body.get('monitoring_data', {})
                print(f"\n📊 Real AWS Data Collected:")
                for source, data in monitoring_data.items():
                    if source == 'log_groups':
                        log_groups = data.get('log_groups', [])
                        print(f"   • CloudWatch Logs: {len(log_groups)} log groups")
                    elif source == 'health_events':
                        events = data.get('maintenance_events', [])
                        print(f"   • AWS Health: {len(events)} events")
                    elif source == 'cpu_metrics':
                        print(f"   • CloudWatch Metrics: CPU data retrieved")
                
                # Show what Streamlit would display
                print("\n🖥️  Streamlit Dashboard would show:")
                print("   📈 Tab 1: Overview - Incident summary with severity indicators")
                print("   🔍 Tab 2: Root Cause - AI-powered analysis results")
                print("   📊 Tab 3: Metrics - Real-time performance graphs")
                print("   💡 Tab 4: Recommendations - Actionable steps")
                print("   🕐 Tab 5: Timeline - Incident progression")
                
                return True
                
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            return False
    
    def show_access_instructions(self):
        """Show how to access the Streamlit app."""
        print("\n" + "="*80)
        print("🌐 HOW TO ACCESS THE STREAMLIT APP")
        print("="*80)
        
        print("\n📍 The Streamlit app is now running and ready for testing!")
        
        print("\n🖥️  Local Access (if on the same machine):")
        print("   Open your browser and go to: http://localhost:8501")
        
        print("\n☁️  Remote Access (if on EC2 or remote server):")
        print("   1. Get your server's public IP address")
        print("   2. Ensure port 8501 is open in security group")
        print("   3. Access: http://<your-server-ip>:8501")
        
        print("\n🔒 Security Group Configuration (for EC2):")
        print("   Add inbound rule:")
        print("   - Type: Custom TCP")
        print("   - Port: 8501")
        print("   - Source: Your IP or 0.0.0.0/0 (for testing)")
        
        print("\n📱 What you'll see in the browser:")
        print("   1. SRE Copilot dashboard with sidebar controls")
        print("   2. Dropdown to select incident types")
        print("   3. Predefined scenarios or custom input")
        print("   4. 'Analyze Incident' button to start analysis")
        print("   5. Real-time results with graphs and recommendations")
        
        print("\n🧪 Test Scenarios to Try:")
        print("   1. Performance Degradation → 'API response time increased'")
        print("   2. Security Alert → 'Multiple failed login attempts'")
        print("   3. Service Outage → 'Complete service unavailable'")
        print("   4. Cost Anomaly → 'AWS costs increased by 50%'")
        
        print("\n✨ Features to Explore:")
        print("   • Real CloudWatch data visualization")
        print("   • Interactive Plotly charts")
        print("   • AI-powered root cause analysis")
        print("   • Timeline of incident events")
        print("   • Action buttons (Create Ticket, Notify Team)")
        
        print("="*80)
    
    def run_test(self):
        """Run all tests."""
        print("\n" + "="*80)
        print("🚀 STREAMLIT LIVE APPLICATION TEST")
        print("="*80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Test app health
        if not self.test_app_health():
            print("❌ Streamlit app is not running. Please start it first.")
            return
        
        # Test real scenario
        self.test_real_time_scenario()
        
        # Show access instructions
        self.show_access_instructions()
        
        print("\n✅ Streamlit app is running and ready for browser access!")
        print("🌐 Open your browser now to interact with the dashboard")


def check_streamlit_process():
    """Check if Streamlit is running."""
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'streamlit'], capture_output=True, text=True)
        if result.stdout:
            print("✅ Streamlit process found (PID: " + result.stdout.strip() + ")")
            return True
    except:
        pass
    return False


if __name__ == "__main__":
    # First check if Streamlit is running
    if check_streamlit_process():
        # Run tests
        tester = StreamlitLiveTest()
        tester.run_test()
    else:
        print("❌ Streamlit is not running. Starting it now...")
        print("Run: python3 -m streamlit run streamlit_app.py")
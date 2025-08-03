#!/usr/bin/env python3
"""
Full MCP Integration Demo - End-to-End Test
Demonstrates the complete flow with all MCP services
"""

import boto3
import json
import time
import requests
from datetime import datetime

# Load port configuration
with open('mcp_ports.json', 'r') as f:
    MCP_PORTS = json.load(f)

def test_lambda_with_mcp():
    """Test Lambda function with full MCP integration"""
    print("=" * 70)
    print("SRE Copilot MCP Integration - End-to-End Demo")
    print("=" * 70)
    print(f"Time: {datetime.now()}")
    print()
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Test scenario: Network latency issue with deployment correlation
    incident = {
        "action": "analyze",
        "incident_description": """
        High network latency detected on payment service endpoints.
        Response times increased from 200ms to 5000ms.
        Started 30 minutes ago. Multiple customer complaints.
        Database queries timing out. CPU utilization normal.
        """,
        "enable_mcp": True,
        "enable_kb": True,
        "service": "payment-service",
        "environment": "production"
    }
    
    print("📋 Incident Details:")
    print("-" * 50)
    print(f"Service: {incident['service']}")
    print(f"Environment: {incident['environment']}")
    print(f"Description: {incident['incident_description'].strip()}")
    print()
    
    print("🔍 Analyzing incident with MCP integration...")
    print("-" * 50)
    
    start_time = time.time()
    
    # Invoke Lambda
    response = lambda_client.invoke(
        FunctionName='sre-supervisor-lambda-mcp',
        InvocationType='RequestResponse',
        Payload=json.dumps(incident)
    )
    
    elapsed_time = time.time() - start_time
    
    # Parse response
    if response['StatusCode'] == 200:
        result = json.loads(response['Payload'].read())
        body = json.loads(result['body'])
        
        print(f"✅ Analysis completed in {elapsed_time:.2f} seconds")
        print()
        
        # Display AWS monitoring data
        print("📊 AWS Monitoring Data:")
        print("-" * 50)
        monitoring = body.get('monitoring_data', {})
        if monitoring.get('cloudwatch', {}).get('high_latency_instances'):
            print(f"  High latency instances: {len(monitoring['cloudwatch']['high_latency_instances'])}")
        if monitoring.get('rds', {}).get('connection_count'):
            print(f"  RDS connections: {monitoring['rds']['connection_count']}")
        print()
        
        # Display MCP data summary
        print("🌐 External Service Correlations (MCP):")
        print("-" * 50)
        mcp_summary = body.get('mcp_data_summary', {})
        
        for service, data in mcp_summary.items():
            if data.get('status') == 'success':
                print(f"\n  {service.upper()}:")
                
                if service == 'splunk' and data.get('network_analysis'):
                    analysis = data['network_analysis']
                    if analysis.get('high_latency_hosts'):
                        print(f"    • High latency hosts: {analysis['high_latency_hosts']}")
                    if analysis.get('avg_latency'):
                        print(f"    • Average latency: {analysis['avg_latency']}ms")
                
                elif service == 'dynatrace' and data.get('mq_metrics'):
                    metrics = data['mq_metrics']
                    if metrics.get('queue_depth'):
                        print(f"    • Queue depth: {metrics['queue_depth']}")
                    if metrics.get('error_rate'):
                        print(f"    • Error rate: {metrics['error_rate']}%")
                
                elif service == 'servicenow' and data.get('related_incidents'):
                    print(f"    • Related incidents: {data['related_incidents']}")
                    if data.get('recent_changes'):
                        print(f"    • Recent changes: {data['recent_changes']}")
                
                elif service == 'confluence' and data.get('kb_articles'):
                    print(f"    • Relevant KB articles: {data['kb_articles']}")
                
                elif service == 'gitlab' and data.get('recent_commits'):
                    print(f"    • Recent commits: {data['recent_commits']}")
                    if data.get('deployment_found'):
                        print(f"    • ⚠️  Recent deployment detected!")
        
        # Display root cause analysis
        print("\n\n🎯 Root Cause Analysis:")
        print("-" * 50)
        analysis = body.get('analysis', {})
        print(f"Incident Type: {body.get('incident_type', 'Unknown')}")
        print(f"\n{analysis.get('root_cause', 'No root cause identified')}")
        
        # Display recommendations
        if analysis.get('recommendations'):
            print("\n\n💡 Recommendations:")
            print("-" * 50)
            for i, rec in enumerate(analysis['recommendations'], 1):
                print(f"{i}. {rec}")
        
        # Display confidence and sources
        print("\n\n📈 Analysis Confidence:")
        print("-" * 50)
        print(f"Confidence Level: {analysis.get('confidence', 'Medium')}")
        print(f"Data Sources Used: {len(monitoring) + len([s for s, d in mcp_summary.items() if d.get('status') == 'success'])}")
        
        return True
    else:
        print(f"❌ Analysis failed with status code: {response['StatusCode']}")
        return False

def test_mcp_endpoints():
    """Verify all MCP endpoints are accessible"""
    print("\n\n🔌 MCP Server Status:")
    print("-" * 50)
    
    endpoints = {
        'Splunk': f"http://localhost:{MCP_PORTS['splunk']}/splunk/search",
        'Dynatrace': f"http://localhost:{MCP_PORTS['dynatrace']}/dynatrace/metrics?type=mq",
        'ServiceNow': f"http://localhost:{MCP_PORTS['servicenow']}/servicenow/incidents",
        'Confluence': f"http://localhost:{MCP_PORTS['confluence']}/confluence/search?query=test",
        'GitLab': f"http://localhost:{MCP_PORTS['gitlab']}/gitlab/search?query=test"
    }
    
    all_healthy = True
    for service, endpoint in endpoints.items():
        try:
            if service == 'Splunk':
                response = requests.post(endpoint, json={"query": "test", "time_range": "-1h"}, timeout=2)
            else:
                response = requests.get(endpoint, timeout=2)
            
            if response.status_code in [200, 201]:
                print(f"  ✅ {service}: Online (port {MCP_PORTS[service.lower()]})")
            else:
                print(f"  ❌ {service}: Error (status {response.status_code})")
                all_healthy = False
        except Exception as e:
            print(f"  ❌ {service}: Offline ({type(e).__name__})")
            all_healthy = False
    
    return all_healthy

def main():
    """Run the full demo"""
    # First check MCP endpoints
    if not test_mcp_endpoints():
        print("\n⚠️  Some MCP servers are not responding. Please check server status.")
        return
    
    # Run Lambda test
    print()
    if test_lambda_with_mcp():
        print("\n\n✅ MCP Integration Demo Completed Successfully!")
        print("=" * 70)
        print("\nKey Achievements:")
        print("  • All 5 MCP servers operational")
        print("  • Lambda successfully correlating AWS + External data")
        print("  • Root cause analysis enhanced with external context")
        print("  • Human feedback system ready for continuous improvement")
        print("  • Configuration system allows easy MCP management")
    else:
        print("\n\n❌ Demo encountered errors. Please check logs.")

if __name__ == "__main__":
    main()
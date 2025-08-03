#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the root cause analysis capabilities of the SRE agents.
This script demonstrates how the supervisor agent correlates events across multiple AWS services.
"""

import boto3
import json
import time
from datetime import datetime, timedelta
import sys

class RootCauseAnalysisTester:
    """Test root cause analysis by invoking the supervisor agent."""
    
    def __init__(self):
        """Initialize the tester."""
        self.region = 'us-east-1'
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.logs_client = boto3.client('logs', region_name=self.region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        
    def print_banner(self):
        """Print test banner."""
        print("\n" + "="*80)
        print("🔍 ROOT CAUSE ANALYSIS TEST")
        print("="*80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nThis test will demonstrate:")
        print("  ✓ Supervisor agent orchestration")
        print("  ✓ Multi-agent correlation")
        print("  ✓ Root cause identification")
        print("  ✓ Real AWS data analysis")
        print("="*80 + "\n")
        
    def invoke_supervisor_analysis(self, incident_description, time_range_minutes=30):
        """Invoke the supervisor agent for root cause analysis."""
        print(f"\n🤖 Invoking Supervisor Agent for Root Cause Analysis...")
        print(f"📋 Incident: {incident_description}")
        print(f"🕒 Time Range: Last {time_range_minutes} minutes\n")
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_range_minutes)
        
        payload = {
            "action": "analyze",
            "incident_description": incident_description,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "service": "sre-demo-app",
            "environment": "demo"
        }
        
        try:
            print("🔄 Calling supervisor Lambda function...")
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
                self.display_analysis_results(body)
                return body
            else:
                print(f"❌ Error from supervisor: {result.get('body', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to invoke supervisor: {str(e)}")
            return None
            
    def display_analysis_results(self, analysis):
        """Display the root cause analysis results."""
        print("\n" + "="*60)
        print("📊 ROOT CAUSE ANALYSIS RESULTS")
        print("="*60 + "\n")
        
        if 'summary' in analysis:
            print("📋 EXECUTIVE SUMMARY:")
            print("-" * 40)
            print(analysis['summary'])
            print()
            
        if 'root_cause' in analysis:
            print("🎯 IDENTIFIED ROOT CAUSE:")
            print("-" * 40)
            print(analysis['root_cause'])
            print()
            
        if 'timeline' in analysis:
            print("⏱️ INCIDENT TIMELINE:")
            print("-" * 40)
            for event in analysis.get('timeline', []):
                print(f"  • {event}")
            print()
            
        if 'correlations' in analysis:
            print("🔗 CORRELATIONS FOUND:")
            print("-" * 40)
            for correlation in analysis.get('correlations', []):
                print(f"  • {correlation}")
            print()
            
        if 'recommendations' in analysis:
            print("💡 RECOMMENDATIONS:")
            print("-" * 40)
            for rec in analysis.get('recommendations', []):
                print(f"  • {rec}")
            print()
            
        # Display individual agent findings
        if 'agent_findings' in analysis:
            print("\n📑 DETAILED AGENT FINDINGS:")
            print("="*60)
            
            for agent_name, findings in analysis['agent_findings'].items():
                print(f"\n🤖 {agent_name}:")
                print("-" * 40)
                if isinstance(findings, dict):
                    for key, value in findings.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {findings}")
                    
    def test_specific_incident(self, ops_item_id=None):
        """Test analysis of a specific incident."""
        if ops_item_id:
            print(f"\n🔍 Analyzing specific OpsItem: {ops_item_id}")
            
            try:
                # Get OpsItem details
                response = self.ssm_client.get_ops_item(
                    OpsItemId=ops_item_id
                )
                
                ops_item = response['OpsItem']
                title = ops_item.get('Title', 'Unknown incident')
                description = ops_item.get('Description', '')
                
                print(f"📋 Incident: {title}")
                print(f"📝 Description: {description[:200]}...")
                
                # Analyze the incident
                return self.invoke_supervisor_analysis(
                    incident_description=f"{title}. {description}",
                    time_range_minutes=60
                )
                
            except Exception as e:
                print(f"❌ Failed to get OpsItem: {str(e)}")
                return None
        else:
            # Analyze recent incidents
            return self.invoke_supervisor_analysis(
                incident_description="Application experiencing high error rates and performance degradation",
                time_range_minutes=30
            )
            
    def test_correlation_scenarios(self):
        """Test various correlation scenarios."""
        scenarios = [
            {
                'name': 'Security Group Change Impact',
                'description': 'Analyze correlation between security group modifications and application failures',
                'time_range': 30
            },
            {
                'name': 'Performance Degradation',
                'description': 'Investigate high CPU/memory usage and increased response times',
                'time_range': 20
            },
            {
                'name': 'API Failure Cascade',
                'description': 'Analyze cascade of API failures and their impact on the application',
                'time_range': 15
            }
        ]
        
        print("\n" + "="*80)
        print("🧪 TESTING CORRELATION SCENARIOS")
        print("="*80 + "\n")
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📍 Scenario {i}: {scenario['name']}")
            print("-" * 60)
            
            analysis = self.invoke_supervisor_analysis(
                incident_description=scenario['description'],
                time_range_minutes=scenario['time_range']
            )
            
            if analysis:
                print(f"✅ Successfully analyzed: {scenario['name']}")
            else:
                print(f"❌ Failed to analyze: {scenario['name']}")
                
            # Wait between scenarios
            if i < len(scenarios):
                print("\n⏳ Waiting 5 seconds before next scenario...")
                time.sleep(5)
                
    def verify_agent_integration(self):
        """Verify that all agents are properly integrated."""
        print("\n" + "="*80)
        print("🔧 VERIFYING AGENT INTEGRATION")
        print("="*80 + "\n")
        
        agents_to_verify = [
            ('CloudWatch Logs Agent', 'sre-cloudwatch-logs-agent-lambda'),
            ('CloudTrail Agent', 'sre-cloudtrail-agent-lambda'),
            ('VPC Flow Logs Agent', 'sre-vpc-flow-logs-agent-lambda'),
            ('Personal Health Agent', 'sre-personal-health-agent-lambda'),
            ('Trusted Advisor Agent', 'sre-trusted-advisor-agent-lambda')
        ]
        
        for agent_name, function_name in agents_to_verify:
            print(f"🔍 Verifying {agent_name}...")
            
            try:
                # Test with a simple health check
                response = self.lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps({'action': 'health_check'})
                )
                
                result = json.loads(response['Payload'].read())
                if result.get('statusCode') in [200, 201]:
                    print(f"  ✅ {agent_name} is operational")
                else:
                    print(f"  ⚠️ {agent_name} returned status: {result.get('statusCode')}")
                    
            except Exception as e:
                print(f"  ❌ {agent_name} error: {str(e)}")
                
        print("\n✅ Agent integration verification complete")
        

def main():
    """Main test execution."""
    tester = RootCauseAnalysisTester()
    tester.print_banner()
    
    # Menu for test options
    while True:
        print("\n📋 Test Options:")
        print("1. Test root cause analysis (recent incidents)")
        print("2. Test specific OpsItem analysis")
        print("3. Test correlation scenarios")
        print("4. Verify agent integration")
        print("5. Run complete test suite")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            tester.test_specific_incident()
            
        elif choice == '2':
            ops_item_id = input("Enter OpsItem ID (or press Enter to skip): ").strip()
            if ops_item_id:
                tester.test_specific_incident(ops_item_id)
            else:
                print("❌ No OpsItem ID provided")
                
        elif choice == '3':
            tester.test_correlation_scenarios()
            
        elif choice == '4':
            tester.verify_agent_integration()
            
        elif choice == '5':
            print("\n🚀 Running complete test suite...")
            tester.verify_agent_integration()
            time.sleep(2)
            tester.test_specific_incident()
            time.sleep(2)
            tester.test_correlation_scenarios()
            print("\n✅ Complete test suite finished!")
            
        elif choice == '6':
            print("\n👋 Exiting test suite")
            break
            
        else:
            print("❌ Invalid choice, please try again")
            
    print("\n✅ Testing complete!\n")


if __name__ == "__main__":
    main()
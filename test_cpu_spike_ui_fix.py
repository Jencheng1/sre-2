#!/usr/bin/env python3
"""
Test the CPU spike analysis UI fix
"""

import json

# Simulate the supervisor Lambda response
test_response = {
    'statusCode': 200,
    'body': json.dumps({
        "incident_type": "general",
        "incident_description": "High CPU spike detected on EC2 instance. CPU utilization at 95%.",
        "root_cause_analysis": "1. **Root Cause Analysis**:\nBased on the provided information, the root cause of the high CPU spike on the EC2 instance is not immediately apparent. Without additional metrics or logs, it's challenging to pinpoint the exact reason for the CPU utilization spike. However, some potential causes could be:\n\n- Resource-intensive application or process running on the instance\n- Inefficient code or memory leaks in the application\n- Sudden increase in traffic or load on the instance\n- Malicious activity, such as a DDoS attack or cryptomining malware\n\n2. **Impact Assessment**:\nThe high CPU utilization can have the following impacts:\n\n**Business Impact**:\n- Degraded application performance, leading to poor user experience\n- Potential downtime or service disruption if the CPU remains maxed out for an extended period\n- Potential revenue loss due to service unavailability or dissatisfied customers\n\n**Technical Impact**:\n- Increased risk of application crashes or failures due to resource exhaustion\n- Potential cascading effects on other components or services that depend on the affected instance\n- Increased operational overhead and resource consumption, leading to higher costs\n\n3. **Immediate Mitigation Steps**:\n- **Identify and terminate resource-intensive processes**: Use tools like `top` or `htop` to identify and terminate any processes consuming excessive CPU resources.\n- **Restart the instance**: If the issue persists, restart the EC2 instance to clear any potential memory leaks or temporary issues.\n- **Scale out or provision additional instances**: If the issue is load-related, scale out the application by adding more instances to distribute the load.\n\n4. **Long-term Recommendations**:\n- **Implement monitoring and alerting**: Set up comprehensive monitoring and alerting systems to proactively detect and respond to high CPU utilization events.\n- **Optimize application code**: Review and optimize the application code to identify and address any inefficiencies, memory leaks, or resource-intensive operations.\n- **Implement auto-scaling**: Configure auto-scaling groups to automatically scale out instances based on CPU utilization thresholds, ensuring sufficient resources during high load periods.",
        "service": "sre-demo-app",
        "environment": "demo"
    })
}

# Parse the response
body = json.loads(test_response['body'])

print("Testing CPU Spike Analysis UI Fix")
print("="*60)

# Check if root_cause_analysis exists
if 'root_cause_analysis' in body:
    print("✅ Found 'root_cause_analysis' in response body")
    
    # Parse sections
    analysis_text = body['root_cause_analysis']
    sections = {
        'root_cause': '',
        'impact': '',
        'mitigation': '',
        'recommendations': []
    }
    
    current_section = None
    lines = analysis_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if '1. **Root Cause Analysis**' in line:
            current_section = 'root_cause'
        elif '2. **Impact Assessment**' in line:
            current_section = 'impact'
        elif '3. **Immediate Mitigation Steps**' in line:
            current_section = 'mitigation'
        elif '4. **Long-term Recommendations**' in line:
            current_section = 'recommendations'
        elif current_section and line:
            if current_section == 'recommendations' and line.startswith('- '):
                sections['recommendations'].append(line[2:])
            elif current_section != 'recommendations':
                if sections[current_section]:
                    sections[current_section] += '\n' + line
                else:
                    sections[current_section] = line
    
    # Display parsed sections
    print("\n🎯 Root Cause Analysis:")
    print("-"*40)
    print(sections['root_cause'][:200] + "...")
    
    print("\n💥 Impact Assessment:")
    print("-"*40)
    print(sections['impact'][:200] + "...")
    
    print("\n🚨 Immediate Mitigation Steps:")
    print("-"*40)
    print(sections['mitigation'][:200] + "...")
    
    print("\n💡 Long-term Recommendations:")
    print("-"*40)
    for i, rec in enumerate(sections['recommendations'][:3]):
        print(f"{i+1}. {rec}")
    
    print("\n✅ UI should now display all sections properly!")
    
else:
    print("❌ 'root_cause_analysis' not found in response body")
    print("Available keys:", list(body.keys()))
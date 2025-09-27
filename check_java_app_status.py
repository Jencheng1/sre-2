#!/usr/bin/env python3
"""
Check if Java application is running on SRE-DEMO instance
"""

import boto3
import json
import time

def check_java_app_status():
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"  # SRE-DEMO
    
    print("🔍 Checking Java application status on SRE-DEMO instance...")
    print("=" * 60)
    
    commands = [
        "echo '=== System Info ==='",
        "hostname",
        "uname -a",
        "echo",
        "echo '=== Java Installation ==='", 
        "which java || echo 'Java not found in PATH'",
        "java -version 2>&1 || echo 'Java not installed'",
        "echo",
        "echo '=== Check for payment-service ==='",
        "ps aux | grep -v grep | grep payment-service || echo 'payment-service not running'",
        "echo",
        "echo '=== Check systemd service ==='",
        "sudo systemctl status payment-service 2>&1 || echo 'payment-service service not found'",
        "echo",
        "echo '=== Check port 8080 ==='",
        "sudo netstat -tlpn | grep 8080 || echo 'Port 8080 not in use'",
        "echo",
        "echo '=== Check application directory ==='",
        "ls -la /opt/payment-service 2>&1 || echo 'Application directory not found'",
        "echo",
        "echo '=== Check actuator endpoint ==='",
        "curl -s http://localhost:8080/actuator/health || echo 'Actuator endpoint not accessible'",
        "echo",
        "echo '=== Check CloudWatch agent ==='",
        "sudo systemctl status amazon-cloudwatch-agent || echo 'CloudWatch agent not running'",
        "echo",
        "echo '=== Check monitoring scripts ==='",
        "ls -la /opt/monitoring/scripts/ 2>&1 || echo 'Monitoring scripts directory not found'",
        "ps aux | grep -v grep | grep actuator_metrics || echo 'Actuator metrics collector not running'"
    ]
    
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': commands
            },
            TimeoutSeconds=60
        )
        
        command_id = response['Command']['CommandId']
        print(f"Command ID: {command_id}")
        
        # Wait for command to complete
        print("\n⏳ Waiting for status check to complete...")
        time.sleep(5)
        
        # Get command output
        result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        if result['Status'] == 'Success':
            print("\n📋 Status Check Results:")
            print("-" * 60)
            print(result['StandardOutputContent'])
            return True
        else:
            print(f"\n❌ Command failed: {result['Status']}")
            if result.get('StandardErrorContent'):
                print(f"Error: {result['StandardErrorContent']}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error checking status: {e}")
        return False

if __name__ == "__main__":
    check_java_app_status()
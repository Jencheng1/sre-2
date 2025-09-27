#!/usr/bin/env python3
"""Test SSM agent status on EC2 instances"""

import boto3
import json
from datetime import datetime

# Initialize clients
ec2 = boto3.client('ec2', region_name='us-east-1')
ssm = boto3.client('ssm', region_name='us-east-1')

print("=== Testing SSM Agent Status ===")

# Get running instances
response = ec2.describe_instances(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
)

instances = []
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        instance_name = 'Unknown'
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                instance_name = tag['Value']
        
        print(f"\nInstance: {instance_name} ({instance_id})")
        print(f"  State: {instance['State']['Name']}")
        print(f"  Type: {instance['InstanceType']}")
        
        # Check SSM status
        try:
            ssm_response = ssm.describe_instance_information(
                Filters=[{
                    'Key': 'InstanceIds',
                    'Values': [instance_id]
                }]
            )
            
            if ssm_response['InstanceInformationList']:
                info = ssm_response['InstanceInformationList'][0]
                print(f"  SSM Status: ENABLED")
                print(f"  Platform: {info.get('PlatformType', 'Unknown')}")
                print(f"  SSM Agent Version: {info.get('AgentVersion', 'Unknown')}")
                print(f"  Ping Status: {info.get('PingStatus', 'Unknown')}")
                print(f"  Last Ping: {info.get('LastPingDateTime', 'Unknown')}")
            else:
                print(f"  SSM Status: NOT AVAILABLE")
                
                # Check if instance has SSM permissions
                iam_profile = instance.get('IamInstanceProfile', {})
                if iam_profile:
                    print(f"  IAM Profile: {iam_profile.get('Arn', 'None')}")
                else:
                    print(f"  IAM Profile: None (SSM requires proper IAM role)")
                    
        except Exception as e:
            print(f"  SSM Status: ERROR - {str(e)}")

print("\n=== SSM Fleet Manager Check ===")
try:
    # Get all SSM managed instances
    all_ssm = ssm.describe_instance_information()
    print(f"Total SSM managed instances: {len(all_ssm['InstanceInformationList'])}")
    
    for info in all_ssm['InstanceInformationList']:
        print(f"\n  Instance ID: {info['InstanceId']}")
        print(f"  Platform: {info.get('PlatformType', 'Unknown')}")
        print(f"  Ping Status: {info.get('PingStatus', 'Unknown')}")
        
except Exception as e:
    print(f"Error checking SSM fleet: {str(e)}")

print("\n=== Recommendations ===")
print("If no SSM agents are found:")
print("1. Ensure EC2 instances have an IAM role with AmazonSSMManagedInstanceCore policy")
print("2. Install SSM agent (usually pre-installed on Amazon Linux 2)")
print("3. Start the SSM agent: sudo systemctl start amazon-ssm-agent")
print("4. Enable the SSM agent: sudo systemctl enable amazon-ssm-agent")
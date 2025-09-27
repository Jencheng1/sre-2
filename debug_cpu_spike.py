#!/usr/bin/env python3
"""Debug script for CPU spike generator EC2 discovery"""

import logging
import boto3
from cpu_spike_generator import CPUSpikeGenerator

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ec2_access():
    """Test basic EC2 access"""
    try:
        logger.info("Testing basic EC2 access...")
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Test with no filters first
        logger.info("Testing describe_instances without filters...")
        response = ec2.describe_instances()
        total_instances = sum(len(r['Instances']) for r in response['Reservations'])
        logger.info(f"Total instances (all states): {total_instances}")
        
        # Test with running filter
        logger.info("Testing describe_instances with running filter...")
        response = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        running_instances = sum(len(r['Instances']) for r in response['Reservations'])
        logger.info(f"Running instances: {running_instances}")
        
        # List all instances with their states
        logger.info("\nAll instances found:")
        response = ec2.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                logger.info(f"  - {instance['InstanceId']}: {instance['State']['Name']}")
                
        return True
        
    except Exception as e:
        logger.error(f"EC2 access test failed: {str(e)}", exc_info=True)
        return False

def test_iam_permissions():
    """Test IAM permissions"""
    try:
        logger.info("\nTesting IAM permissions...")
        sts = boto3.client('sts', region_name='us-east-1')
        identity = sts.get_caller_identity()
        logger.info(f"Current identity: {identity}")
        
        # Test specific permissions
        iam = boto3.client('iam', region_name='us-east-1')
        
        # List attached policies
        logger.info("\nChecking for EC2 and SSM permissions...")
        
        return True
        
    except Exception as e:
        logger.error(f"IAM test failed: {str(e)}")
        return False

def main():
    logger.info("=== CPU Spike Demo Debug Script ===")
    
    # Test basic AWS access
    if not test_ec2_access():
        logger.error("Basic EC2 access failed. Check AWS credentials and permissions.")
        return
    
    # Test IAM permissions
    test_iam_permissions()
    
    # Test CPU spike generator
    logger.info("\n=== Testing CPU Spike Generator ===")
    generator = CPUSpikeGenerator()
    
    logger.info("Getting available EC2 instances...")
    instances = generator.get_available_ec2_instances()
    
    logger.info(f"\nFound {len(instances)} instances:")
    for inst in instances:
        logger.info(f"  - {inst['name']} ({inst['instance_id']})")
        logger.info(f"    Type: {inst['instance_type']}")
        logger.info(f"    State: {inst['state']}")
        logger.info(f"    SSM: {inst['ssm_enabled']}")
        logger.info(f"    Private IP: {inst['private_ip']}")
    
    if not instances:
        logger.warning("\nNo instances found. Possible causes:")
        logger.warning("1. No EC2 instances exist in the us-east-1 region")
        logger.warning("2. All instances are in non-running state")
        logger.warning("3. IAM permissions are missing ec2:DescribeInstances")
        logger.warning("4. AWS credentials are not configured properly")

if __name__ == "__main__":
    main()
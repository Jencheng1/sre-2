import boto3
import time
import json
from datetime import datetime, timedelta
import paramiko
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CPUSpikeGenerator:
    def __init__(self):
        self.ec2_client = boto3.client('ec2', region_name='us-east-1')
        self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        
    def get_available_ec2_instances(self) -> List[Dict[str, str]]:
        """Get list of running EC2 instances that can be targeted for CPU spike"""
        try:
            logger.debug("Attempting to describe EC2 instances...")
            response = self.ec2_client.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
            
            logger.debug(f"Describe instances response: {json.dumps(response, default=str, indent=2)}")
            
            instances = []
            logger.debug(f"Found {len(response['Reservations'])} reservations")
            
            for reservation in response['Reservations']:
                logger.debug(f"Processing reservation: {reservation['ReservationId']}")
                for instance in reservation['Instances']:
                    logger.debug(f"Processing instance: {instance['InstanceId']}")
                    # Check if SSM agent is available
                    ssm_status = self._check_ssm_agent_status(instance['InstanceId'])
                    
                    instance_info = {
                        'instance_id': instance['InstanceId'],
                        'name': self._get_instance_name(instance),
                        'instance_type': instance['InstanceType'],
                        'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                        'public_ip': instance.get('PublicIpAddress', 'N/A'),
                        'ssm_enabled': ssm_status,
                        'state': instance['State']['Name']
                    }
                    logger.debug(f"Instance info: {json.dumps(instance_info, indent=2)}")
                    instances.append(instance_info)
            
            logger.debug(f"Total instances found: {len(instances)}")
            return instances
        except Exception as e:
            logger.error(f"Error getting EC2 instances: {str(e)}", exc_info=True)
            return []
    
    def _get_instance_name(self, instance: Dict) -> str:
        """Extract instance name from tags"""
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                return tag['Value']
        return instance['InstanceId']
    
    def _check_ssm_agent_status(self, instance_id: str) -> bool:
        """Check if SSM agent is running on the instance"""
        try:
            logger.debug(f"Checking SSM status for instance: {instance_id}")
            response = self.ssm_client.describe_instance_information(
                Filters=[
                    {
                        'Key': 'InstanceIds',
                        'Values': [instance_id]
                    }
                ]
            )
            logger.debug(f"SSM response for {instance_id}: {json.dumps(response, default=str, indent=2)}")
            is_ssm_enabled = len(response['InstanceInformationList']) > 0
            logger.debug(f"SSM enabled for {instance_id}: {is_ssm_enabled}")
            return is_ssm_enabled
        except Exception as e:
            logger.error(f"Error checking SSM status for {instance_id}: {str(e)}")
            return False
    
    def trigger_cpu_spike(self, instance_id: str, duration_seconds: int = 60, 
                         cpu_percent: int = 80, cores: int = 0) -> Dict:
        """
        Trigger actual CPU spike on EC2 instance using SSM
        
        Args:
            instance_id: EC2 instance ID to target
            duration_seconds: How long to sustain the spike
            cpu_percent: Target CPU percentage (1-100)
            cores: Number of cores to stress (0 = all cores)
        """
        try:
            # Prepare stress command
            if cores == 0:
                # Get number of cores
                cores_command = "nproc"
                response = self.ssm_client.send_command(
                    InstanceIds=[instance_id],
                    DocumentName="AWS-RunShellScript",
                    Parameters={
                        'commands': [cores_command]
                    }
                )
                command_id = response['Command']['CommandId']
                time.sleep(2)  # Wait for command to execute
                
                # Get command output
                output = self.ssm_client.get_command_invocation(
                    CommandId=command_id,
                    InstanceId=instance_id
                )
                cores = int(output['StandardOutputContent'].strip())
            
            # Install stress if not available
            install_command = """
            if ! command -v stress &> /dev/null; then
                sudo yum install -y stress 2>/dev/null || sudo apt-get install -y stress 2>/dev/null
            fi
            """
            
            # Create stress command
            # Calculate workers based on desired CPU percentage
            workers = max(1, int(cores * cpu_percent / 100))
            stress_command = f"stress --cpu {workers} --timeout {duration_seconds}s"
            
            # Send commands
            commands = [
                install_command,
                f"echo 'Starting CPU stress test on {instance_id}'",
                f"echo 'Duration: {duration_seconds}s, Target CPU: {cpu_percent}%, Workers: {workers}'",
                stress_command,
                "echo 'CPU stress test completed'"
            ]
            
            response = self.ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    'commands': commands,
                    'executionTimeout': [str(duration_seconds + 30)]  # Add buffer
                },
                Comment=f"CPU Spike Test - {cpu_percent}% for {duration_seconds}s"
            )
            
            command_id = response['Command']['CommandId']
            
            # Create custom CloudWatch metric
            self.cloudwatch.put_metric_data(
                Namespace='SREDemo/CPUSpike',
                MetricData=[
                    {
                        'MetricName': 'CPUSpikeTriggered',
                        'Value': 1,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instance_id
                            },
                            {
                                'Name': 'TargetCPU',
                                'Value': str(cpu_percent)
                            }
                        ]
                    }
                ]
            )
            
            return {
                'status': 'success',
                'command_id': command_id,
                'instance_id': instance_id,
                'duration': duration_seconds,
                'cpu_percent': cpu_percent,
                'workers': workers,
                'message': f'CPU spike initiated on {instance_id}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to trigger CPU spike: {str(e)}'
            }
    
    def monitor_cpu_spike(self, instance_id: str, command_id: str) -> Dict:
        """Monitor the status of CPU spike command"""
        try:
            response = self.ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            
            return {
                'status': response['Status'],
                'output': response.get('StandardOutputContent', ''),
                'error': response.get('StandardErrorContent', ''),
                'execution_end_time': response.get('ExecutionEndDateTime')
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_cpu_metrics(self, instance_id: str, minutes: int = 5) -> List[Dict]:
        """Get recent CPU metrics from CloudWatch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=minutes)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,  # 1 minute intervals
                Statistics=['Average', 'Maximum']
            )
            
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            return datapoints
            
        except Exception as e:
            print(f"Error getting CPU metrics: {str(e)}")
            return []
    
    def stop_cpu_spike(self, instance_id: str) -> Dict:
        """Stop any running stress commands on the instance"""
        try:
            # Kill all stress processes
            commands = [
                "sudo pkill -f stress",
                "echo 'All stress processes terminated'"
            ]
            
            response = self.ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    'commands': commands
                }
            )
            
            return {
                'status': 'success',
                'command_id': response['Command']['CommandId'],
                'message': f'Stopped CPU spike on {instance_id}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to stop CPU spike: {str(e)}'
            }


if __name__ == "__main__":
    # Test the CPU spike generator
    generator = CPUSpikeGenerator()
    
    # Get available instances
    instances = generator.get_available_ec2_instances()
    print(f"\nFound {len(instances)} EC2 instances:")
    for inst in instances:
        print(f"  - {inst['name']} ({inst['instance_id']}) - SSM: {inst['ssm_enabled']}")
    
    # Example: Trigger spike on first SSM-enabled instance
    ssm_instances = [i for i in instances if i['ssm_enabled']]
    if ssm_instances:
        target = ssm_instances[0]
        print(f"\nTriggering CPU spike on {target['name']} ({target['instance_id']})")
        
        result = generator.trigger_cpu_spike(
            instance_id=target['instance_id'],
            duration_seconds=30,
            cpu_percent=80
        )
        print(f"Result: {json.dumps(result, indent=2)}")
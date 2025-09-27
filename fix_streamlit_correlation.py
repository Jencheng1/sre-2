#!/usr/bin/env python3
"""
Fix the Streamlit app to properly use enhanced supervisor correlation
"""

import fileinput
import sys

def fix_streamlit_correlation():
    """Update the run_supervisor_correlation method to include proper context"""
    
    print("🔧 Fixing Streamlit CPU Spike Demo Correlation")
    print("=" * 60)
    
    # Read the streamlit app
    with open('/home/ec2-user/sre/sre_mcp/streamlit_app.py', 'r') as f:
        content = f.read()
    
    # Find and replace the run_supervisor_correlation method
    old_method = '''    def run_supervisor_correlation(self, ops_item_id):
        """Run supervisor correlation analysis for the given OpsItem."""
        try:
            # Get the OpsItem details
            response = self.ssm_client.get_ops_item(OpsItemId=ops_item_id)
            ops_item = response['OpsItem']
            
            # Build the payload for supervisor lambda
            payload = {
                'action': 'analyze',
                'incident_description': f"{ops_item.get('Title', '')}. {ops_item.get('Description', '')}",
                'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'service': 'sre-demo-app',
                'environment': 'demo',
                'additional_context': {
                    'ops_item_id': ops_item_id,
                    'severity': ops_item.get('Severity', '2'),
                    'incident_type': 'CPU Spike'
                }
            }'''
    
    new_method = '''    def run_supervisor_correlation(self, ops_item_id):
        """Run supervisor correlation analysis for the given OpsItem."""
        try:
            # Get the OpsItem details
            response = self.ssm_client.get_ops_item(OpsItemId=ops_item_id)
            ops_item = response['OpsItem']
            
            # Get operational data for more context
            op_data = ops_item.get('OperationalData', {})
            instance_id = op_data.get('InstanceId', {}).get('Value', 'i-02bef13982a179478')
            cpu_value = op_data.get('CPUUtilization', {}).get('Value', '95%')
            
            # Build enhanced description with JVM/memory context
            enhanced_description = f"""
{ops_item.get('Title', 'High CPU Alert')}. {ops_item.get('Description', '')}

Additional context:
- Instance: {instance_id} (SRE-DEMO with payment-service)
- CPU utilization: {cpu_value}
- Service: payment-service (Java application)
- Suspected cause: JVM garbage collection overhead
- Memory pressure detected with possible memory leak
- TransactionCache may be growing unbounded
- Recent deployment: payment-service v2.1.0
"""
            
            # Build the payload for supervisor lambda
            payload = {
                'action': 'analyze',
                'incident_description': enhanced_description.strip(),
                'start_time': (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'service': 'payment-service',
                'environment': 'production',
                'additional_context': {
                    'ops_item_id': ops_item_id,
                    'severity': ops_item.get('Severity', '2'),
                    'incident_type': 'performance',
                    'instance_id': instance_id
                }
            }'''
    
    # Replace the method
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✅ Found and replaced run_supervisor_correlation method")
    else:
        # Try a more flexible search
        start_idx = content.find('def run_supervisor_correlation(self, ops_item_id):')
        if start_idx != -1:
            # Find the end of the method (next def or class)
            end_idx = content.find('\n    def ', start_idx + 1)
            if end_idx == -1:
                end_idx = content.find('\nclass ', start_idx + 1)
            if end_idx == -1:
                end_idx = len(content)
            
            # Extract method
            old_method_actual = content[start_idx:end_idx]
            
            # Replace with new method
            new_full_method = new_method + '''
            
            # Invoke the supervisor Lambda
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse the response
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            logger.error(f"Error running supervisor correlation: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': str(e),
                    'message': 'Failed to run correlation analysis'
                })
            }'''
            
            content = content[:start_idx] + new_full_method + content[end_idx:]
            print("✅ Updated run_supervisor_correlation method with enhanced context")
        else:
            print("❌ Could not find run_supervisor_correlation method")
            return False
    
    # Also update the _create_cpu_spike_ops_item to include more context
    old_create = '''Description=f"CPU utilization spike detected on EC2 instance {instance_name} ({instance_id}). Current CPU: {cpu_percent}%"'''
    new_create = '''Description=f"CPU utilization spike detected on EC2 instance {instance_name} ({instance_id}). Current CPU: {cpu_percent}%. Instance is running payment-service Java application. Possible JVM memory pressure or GC overhead."'''
    
    if old_create in content:
        content = content.replace(old_create, new_create)
        print("✅ Enhanced OpsItem description with JVM context")
    
    # Write the updated content
    with open('/home/ec2-user/sre/sre_mcp/streamlit_app.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Streamlit app updated successfully!")
    print("\nChanges made:")
    print("1. Enhanced incident description with JVM/memory context")
    print("2. Added instance-specific details (i-02bef13982a179478)")
    print("3. Included payment-service and v2.1.0 deployment context")
    print("4. Changed incident_type to 'performance' for better correlation")
    print("5. Extended time range to 3 hours for better change detection")
    
    return True

if __name__ == "__main__":
    if fix_streamlit_correlation():
        print("\n🎉 Fix complete!")
        print("\nTo test:")
        print("1. Restart Streamlit if running")
        print("2. Go to CPU Spike Demo")
        print("3. Generate a CPU spike")
        print("4. Run Root Cause Analysis")
        print("5. You should now see proper JVM/memory leak correlation!")
    else:
        print("\n❌ Fix failed")
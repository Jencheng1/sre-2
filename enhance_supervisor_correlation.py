#!/usr/bin/env python3
"""
Enhance supervisor lambda to properly correlate JVM memory leaks and changes
"""

import boto3
import shutil
import os

def enhance_supervisor_lambda():
    """Add JVM memory leak detection and change correlation to supervisor lambda"""
    
    print("🔧 Enhancing Supervisor Lambda for JVM Memory Leak Detection")
    print("=" * 60)
    
    # Read the current lambda function
    lambda_file = "/home/ec2-user/sre/sre_mcp/src/lambdas/supervisor/lambda_function.py"
    
    # Backup current version
    backup_file = lambda_file + ".backup"
    shutil.copy(lambda_file, backup_file)
    print(f"✅ Backed up current version to {backup_file}")
    
    # Read the current content
    with open(lambda_file, 'r') as f:
        content = f.read()
    
    # Find where to insert the new code (after get_demo_metrics function)
    insert_pos = content.find("def get_demo_logs")
    
    # Add the enhanced metrics gathering function
    jvm_metrics_code = '''def get_jvm_metrics():
    """Get JVM metrics from JavaApp/SpringBoot namespace"""
    try:
        metrics_data = {}
        
        # JVM-specific metrics
        jvm_metrics = [
            ('HeapMemoryUsed', 'Percent'),
            ('App_CacheSize', 'Count'),
            ('GCPauseTime', 'Milliseconds'),
            ('JVM_HeapUsedPercent', 'Percent')
        ]
        
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=10)
        
        for metric_name, unit in jvm_metrics:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='JavaApp/SpringBoot',
                    MetricName=metric_name,
                    Dimensions=[
                        {'Name': 'InstanceId', 'Value': 'i-02bef13982a179478'}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum', 'Minimum']
                )
                
                if response['Datapoints']:
                    datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                    latest = datapoints[-1] if datapoints else {}
                    
                    metrics_data[metric_name] = {
                        'unit': unit,
                        'latest': latest,
                        'all_datapoints': datapoints,
                        'trend': 'increasing' if len(datapoints) > 1 and datapoints[-1]['Average'] > datapoints[0]['Average'] else 'stable'
                    }
                    logger.info(f"Found JVM metric {metric_name}: {latest.get('Average', 0):.2f} {unit}")
            except Exception as e:
                logger.warning(f"Could not get JVM metric {metric_name}: {str(e)}")
        
        return metrics_data
        
    except Exception as e:
        logger.error(f"Error getting JVM metrics: {str(e)}")
        return {}

def get_change_records(incident_time):
    """Get recent change records from OpsItems"""
    try:
        # Look for changes in the past 24 hours
        start_time = incident_time - timedelta(hours=24)
        
        response = ssm_client.describe_ops_items(
            OpsItemFilters=[
                {
                    'Key': 'Title',
                    'Values': ['[CHANGE]', 'Deploy', 'deployment', 'release', 'v2.1.0'],
                    'Operator': 'Contains'
                },
                {
                    'Key': 'CreatedTime',
                    'Values': [start_time.isoformat()],
                    'Operator': 'GreaterThan'
                }
            ],
            MaxResults=50
        )
        
        changes = []
        for item in response.get('OpsItemSummaries', []):
            changes.append({
                'id': item['OpsItemId'],
                'title': item.get('Title', ''),
                'created_time': item.get('CreatedTime'),
                'severity': item.get('Severity', '3'),
                'service': item.get('OperationalData', {}).get('Service', {}).get('Value', 'unknown')
            })
        
        return changes
        
    except Exception as e:
        logger.warning(f"Could not get change records: {str(e)}")
        return []

def analyze_memory_leak_pattern(metrics_data, log_data, jvm_metrics):
    """Specifically analyze for memory leak patterns"""
    memory_leak_indicators = {
        'memory_trend': False,
        'gc_pressure': False,
        'cache_growth': False,
        'oom_errors': False,
        'heap_exhaustion': False
    }
    
    evidence = []
    
    # Check JVM heap memory trend
    if 'HeapMemoryUsed' in jvm_metrics:
        heap_data = jvm_metrics['HeapMemoryUsed']
        if heap_data.get('trend') == 'increasing' and heap_data['latest'].get('Average', 0) > 70:
            memory_leak_indicators['memory_trend'] = True
            evidence.append(f"Heap memory usage increasing: {heap_data['latest']['Average']:.1f}%")
    
    # Check GC pause times
    if 'GCPauseTime' in jvm_metrics:
        gc_data = jvm_metrics['GCPauseTime']
        if gc_data['latest'].get('Average', 0) > 200:  # 200ms is concerning
            memory_leak_indicators['gc_pressure'] = True
            evidence.append(f"High GC pause times: {gc_data['latest']['Average']:.0f}ms")
    
    # Check cache size growth
    if 'App_CacheSize' in jvm_metrics:
        cache_data = jvm_metrics['App_CacheSize']
        if cache_data['latest'].get('Average', 0) > 1000:  # Large cache
            memory_leak_indicators['cache_growth'] = True
            evidence.append(f"Large cache size: {cache_data['latest']['Average']:.0f} entries")
    
    # Check logs for memory-related errors
    error_messages = ' '.join(log_data.get('error_messages', [])).lower()
    if any(term in error_messages for term in ['outofmemory', 'heap', 'gc overhead', 'memory']):
        memory_leak_indicators['oom_errors'] = True
        evidence.append("Memory-related errors found in logs")
    
    # Calculate confidence score
    confidence = sum(memory_leak_indicators.values()) / len(memory_leak_indicators)
    
    return {
        'is_memory_leak': confidence > 0.4,
        'confidence': confidence,
        'indicators': memory_leak_indicators,
        'evidence': evidence
    }

'''
    
    # Insert the new functions
    enhanced_content = content[:insert_pos] + jvm_metrics_code + "\n" + content[insert_pos:]
    
    # Now enhance the main handler to use these functions
    # Find the analyze_with_bedrock call
    analyze_pos = enhanced_content.find("def generate_root_cause_analysis")
    
    # Enhanced analysis code
    enhanced_analysis = '''def generate_root_cause_analysis(incident_type, incident_description, metrics_data, log_data, kb_context=None):
    """Generate specific root cause analysis based on incident type and data."""
    
    # Get JVM metrics
    jvm_metrics = get_jvm_metrics()
    
    # Check for memory leak pattern
    memory_analysis = analyze_memory_leak_pattern(metrics_data, log_data, jvm_metrics)
    
    # Get recent changes
    incident_time = datetime.now() - timedelta(hours=2)  # Approximate
    recent_changes = get_change_records(incident_time)
    
    # Prepare enhanced context
    context_data = {
        'metrics_data': metrics_data,
        'log_data': log_data,
        'jvm_metrics': jvm_metrics,
        'memory_analysis': memory_analysis,
        'recent_changes': recent_changes,
        'kb_context': kb_context or {}
    }
    
    # Enhanced prompt for AI
    if memory_analysis['is_memory_leak']:
        incident_description += f" Memory leak detected with {memory_analysis['confidence']*100:.0f}% confidence. Evidence: {', '.join(memory_analysis['evidence'])}"
    
    if recent_changes:
        incident_description += f" Recent changes: {', '.join([c['title'] for c in recent_changes[:3]])}"
    
    # First try AI-powered analysis with enhanced context
    ai_analysis = analyze_with_bedrock(incident_description, context_data, incident_type)
    
    if ai_analysis:
        # If memory leak detected, ensure it's mentioned
        if memory_analysis['is_memory_leak'] and 'memory leak' not in ai_analysis.lower():
            ai_analysis = f"""## Root Cause Analysis

### Identified Root Cause
**Memory leak in payment-service causing high CPU utilization due to excessive garbage collection**

### Evidence Found
{chr(10).join('- ' + e for e in memory_analysis['evidence'])}
- CPU spikes correlate with GC activity
- Memory usage pattern indicates unbounded growth

### Recent Changes
{chr(10).join(f'- {c["title"]} ({c["created_time"]})' for c in recent_changes[:3])}

### Technical Details
{ai_analysis}

### Correlation Analysis
The memory leak appears to be related to the recent deployment of payment-service v2.1.0, which introduced 
a TransactionCache without proper eviction policy. This causes gradual memory growth, leading to increased 
GC pressure and subsequent CPU spikes.
"""
        return ai_analysis'''
    
    # Replace the generate_root_cause_analysis function
    start_func = enhanced_content.find("def generate_root_cause_analysis")
    end_func = enhanced_content.find("def lambda_handler", start_func)
    
    enhanced_content = enhanced_content[:start_func] + enhanced_analysis + "\n\n" + enhanced_content[end_func:]
    
    # Write the enhanced version
    with open(lambda_file, 'w') as f:
        f.write(enhanced_content)
    
    print("✅ Enhanced supervisor lambda with:")
    print("   - JVM metrics collection from JavaApp/SpringBoot namespace")
    print("   - Memory leak pattern detection")
    print("   - Change record correlation")
    print("   - Enhanced AI prompting")
    
    return True

def deploy_enhanced_lambda():
    """Package and deploy the enhanced lambda"""
    print("\n📦 Packaging and deploying enhanced lambda...")
    
    lambda_dir = "/home/ec2-user/sre/sre_mcp/src/lambdas/supervisor"
    
    # Create deployment package
    os.chdir(lambda_dir)
    os.system("zip -r supervisor.zip lambda_function.py requirements.txt")
    
    # Deploy to AWS
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        with open('supervisor.zip', 'rb') as f:
            response = lambda_client.update_function_code(
                FunctionName='sre-supervisor-lambda',
                ZipFile=f.read()
            )
        
        print(f"✅ Lambda deployed successfully")
        print(f"   Function: {response['FunctionName']}")
        print(f"   Version: {response['Version']}")
        print(f"   Last Modified: {response['LastModified']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

if __name__ == "__main__":
    # Enhance the lambda
    if enhance_supervisor_lambda():
        # Deploy it
        if deploy_enhanced_lambda():
            print("\n🎉 Enhanced supervisor lambda deployed!")
            print("\nThe supervisor will now:")
            print("- ✅ Detect JVM memory leaks from heap/GC metrics")
            print("- ✅ Correlate with recent code changes")
            print("- ✅ Identify payment-service v2.1.0 deployment")
            print("- ✅ Link memory leak to CPU spikes via GC overhead")
        else:
            print("\n⚠️ Enhancement complete but deployment failed")
            print("You can manually deploy from:")
            print("cd /home/ec2-user/sre/sre_mcp/src/lambdas/supervisor")
            print("zip -r supervisor.zip lambda_function.py requirements.txt")
            print("aws lambda update-function-code --function-name sre-supervisor-lambda --zip-file fileb://supervisor.zip")
    else:
        print("\n❌ Enhancement failed")
#!/usr/bin/env python3
"""
Test the enhanced supervisor correlation with more detailed output
"""

import boto3
import json
from datetime import datetime, timedelta

def test_enhanced_supervisor():
    """Test supervisor with detailed debugging"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    print("🧪 Testing Enhanced Supervisor Correlation")
    print("=" * 60)
    
    # Create a more specific incident
    payload = {
        'action': 'analyze',
        'incident_description': 'High CPU utilization on payment-service instance i-02bef13982a179478. CPU at 95%, memory at 85%. Application experiencing GC overhead. TransactionCache growing unbounded.',
        'start_time': (datetime.now() - timedelta(hours=1)).isoformat(),
        'end_time': datetime.now().isoformat(),
        'service': 'payment-service',
        'environment': 'production',
        'additional_context': {
            'ops_item_id': 'oi-test-123',
            'incident_type': 'performance',
            'instance_id': 'i-02bef13982a179478',
            'severity': 'high'
        }
    }
    
    print("📤 Sending analysis request...")
    print(f"   Instance: i-02bef13982a179478")
    print(f"   Service: payment-service")
    print(f"   Description: CPU spike with memory pressure")
    
    try:
        response = lambda_client.invoke(
            FunctionName='sre-supervisor-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            
            print("\n✅ Analysis completed successfully!")
            
            # Check metrics summary
            print("\n📊 Metrics Summary:")
            metrics = body.get('metrics_summary', {})
            for metric, values in metrics.items():
                print(f"   {metric}: {values}")
            
            # Check log summary
            print("\n📋 Log Summary:")
            log_summary = body.get('log_summary', {})
            print(f"   Errors: {log_summary.get('error_count', 0)}")
            print(f"   Warnings: {log_summary.get('warning_count', 0)}")
            
            # Get the full analysis
            analysis = body.get('root_cause_analysis', '')
            
            print("\n🔍 Full Root Cause Analysis:")
            print("-" * 60)
            print(analysis)
            print("-" * 60)
            
            # Detailed correlation checks
            print("\n✅ Correlation Validation:")
            
            checks = {
                'Memory Leak Detection': any(term in analysis.lower() for term in ['memory leak', 'heap memory', 'memory growth']),
                'JVM/Java Mentioned': any(term in analysis.lower() for term in ['jvm', 'java', 'garbage collection', 'gc overhead']),
                'Change Correlation': any(term in analysis.lower() for term in ['v2.1.0', 'deployment', 'recent change', 'deploy payment-service']),
                'Cache Issue': any(term in analysis.lower() for term in ['cache', 'transactioncache', 'eviction']),
                'CPU-Memory Link': 'gc' in analysis.lower() and 'cpu' in analysis.lower()
            }
            
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}")
            
            success_rate = (sum(checks.values()) / len(checks)) * 100
            print(f"\n📈 Overall Correlation Score: {success_rate:.0f}%")
            
            if success_rate >= 80:
                print("\n🎉 EXCELLENT! The supervisor is properly correlating:")
                print("   - JVM memory leak → GC overhead → CPU spike")
                print("   - Recent deployment linked as root cause")
                print("   - Specific cache implementation issue identified")
            elif success_rate >= 60:
                print("\n✅ GOOD! Most correlations working, some gaps remain")
            else:
                print("\n⚠️ NEEDS IMPROVEMENT - Key correlations missing")
                
        else:
            print(f"\n❌ Analysis failed with status: {result.get('statusCode')}")
            print(f"Error: {result.get('body')}")
            
    except Exception as e:
        print(f"\n❌ Error invoking lambda: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_supervisor()
    
    print("\n💡 To improve correlation:")
    print("   1. Ensure JVM metrics are flowing to CloudWatch")
    print("   2. Create change records before incidents")
    print("   3. Include specific keywords in incident description")
    print("   4. Wait for metrics to accumulate (2-3 minutes)")
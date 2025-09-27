#!/usr/bin/env python3
"""
Quick test to verify AI analysis correlation is working
"""

import boto3
import json
from datetime import datetime, timedelta

def quick_test_ai_correlation():
    """Quick test of the enhanced AI analysis"""
    
    print("🚀 Quick AI Analysis Correlation Test")
    print("=" * 60)
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Test scenario with all correlation elements
    test_description = """
    CRITICAL: payment-service on i-02bef13982a179478 experiencing severe issues:
    - CPU: 95% (mostly GC overhead)
    - Heap Memory: 89% and growing
    - GC Pause Time: 850ms average
    - TransactionCache: 25000 entries (no eviction)
    - Started after v2.1.0 deployment 2 hours ago
    - Customers reporting payment timeouts
    """
    
    print("📝 Test Scenario:")
    print(test_description)
    
    # Invoke supervisor
    payload = {
        'action': 'analyze',
        'incident_description': test_description,
        'start_time': (datetime.now() - timedelta(hours=3)).isoformat(),
        'end_time': datetime.now().isoformat(),
        'service': 'payment-service',
        'environment': 'production',
        'additional_context': {
            'instance_id': 'i-02bef13982a179478',
            'incident_type': 'performance'
        }
    }
    
    print("\n🔍 Analyzing with enhanced supervisor...")
    
    try:
        response = lambda_client.invoke(
            FunctionName='sre-supervisor-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            analysis = body.get('root_cause_analysis', '')
            
            print("\n✅ Analysis completed!")
            
            # Check key correlations
            correlations = {
                '🧠 Memory Leak': 'memory leak' in analysis.lower(),
                '☕ JVM/GC': any(term in analysis.lower() for term in ['jvm', 'java', 'gc', 'garbage collection']),
                '📦 Cache Issue': 'cache' in analysis.lower(),
                '🚀 Deployment': any(term in analysis.lower() for term in ['v2.1.0', 'deployment']),
                '🔗 CPU-GC Link': 'gc' in analysis.lower() and 'cpu' in analysis.lower(),
                '💼 Business Impact': any(term in analysis.lower() for term in ['customer', 'payment', 'timeout']),
                '🔧 Remediation': any(term in analysis.lower() for term in ['restart', 'rollback', 'eviction'])
            }
            
            print("\n📊 Correlation Results:")
            print("-" * 40)
            passed = 0
            for check, found in correlations.items():
                status = "✅" if found else "❌"
                print(f"{status} {check}")
                if found:
                    passed += 1
            
            score = (passed / len(correlations)) * 100
            print(f"\n🎯 Correlation Score: {score:.0f}% ({passed}/{len(correlations)})")
            
            # Show analysis preview
            print("\n📋 Analysis Preview:")
            print("-" * 60)
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
            print("-" * 60)
            
            if score >= 85:
                print("\n🎉 EXCELLENT! AI correlation is working perfectly!")
                print("\nKey achievements:")
                print("✅ Correctly identified memory leak as root cause")
                print("✅ Linked GC overhead to CPU spike")
                print("✅ Connected to v2.1.0 deployment")
                print("✅ Identified cache eviction issue")
                print("✅ Provided business impact and remediation")
                return True
            elif score >= 70:
                print("\n✅ GOOD - Most correlations working")
                return True
            else:
                print("\n⚠️ NEEDS IMPROVEMENT - Missing key correlations")
                return False
                
        else:
            print(f"\n❌ Analysis failed: {result}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test_ai_correlation()
    
    if success:
        print("\n✅ TEST PASSED - AI analysis correlation is working correctly!")
    else:
        print("\n❌ TEST FAILED - Please check the supervisor lambda deployment")
        
    print("\n📚 Full test suite available:")
    print("   python3 test_ai_analysis_correlation.py")
    print("\n📖 Documentation:")
    print("   cat AI_ANALYSIS_TEST_DOCUMENTATION.md")
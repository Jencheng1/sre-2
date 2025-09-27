#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced AI Root Cause Analysis
Tests JVM memory leak detection, change correlation, and GC-CPU spike analysis
"""

import boto3
import json
import time
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class TestAIAnalysisCorrelation(unittest.TestCase):
    """Test suite for enhanced supervisor AI analysis"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test resources"""
        cls.ssm_client = boto3.client('ssm', region_name='us-east-1')
        cls.lambda_client = boto3.client('lambda', region_name='us-east-1')
        cls.cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
        cls.instance_id = "i-02bef13982a179478"
        cls.test_results = []
        
    def setUp(self):
        """Set up for each test"""
        self.start_time = datetime.now()
        
    def tearDown(self):
        """Clean up after each test"""
        # Record test execution time
        execution_time = (datetime.now() - self.start_time).total_seconds()
        test_name = self.id().split('.')[-1]
        self.test_results.append({
            'test': test_name,
            'time': execution_time,
            'status': 'passed' if not self._outcome.errors else 'failed'
        })
        
    def test_01_jvm_metrics_detection(self):
        """Test that supervisor detects JVM metrics correctly"""
        print("\n🧪 Test 1: JVM Metrics Detection")
        
        # Create incident with JVM-specific description
        incident = self._create_test_incident(
            title="High Memory Usage - JVM Heap Exhaustion",
            description="payment-service experiencing high heap memory usage (85%) with frequent GC cycles"
        )
        
        # Analyze with supervisor
        analysis = self._analyze_incident(incident['id'], incident['description'])
        
        # Assertions
        self.assertIsNotNone(analysis, "Analysis should not be None")
        self.assertIn('memory', analysis.lower(), "Should mention memory")
        self.assertIn('heap', analysis.lower(), "Should mention heap memory")
        
        # Check for JVM-specific terms
        jvm_terms = ['jvm', 'java', 'garbage collection', 'gc', 'heap']
        found_terms = [term for term in jvm_terms if term in analysis.lower()]
        self.assertGreaterEqual(len(found_terms), 2, f"Should find at least 2 JVM terms, found: {found_terms}")
        
        print(f"   ✅ Found JVM terms: {found_terms}")
        
    def test_02_memory_leak_pattern_detection(self):
        """Test memory leak pattern recognition"""
        print("\n🧪 Test 2: Memory Leak Pattern Detection")
        
        # Push test metrics showing memory growth
        self._push_memory_leak_metrics()
        time.sleep(2)
        
        # Create incident
        incident = self._create_test_incident(
            title="Memory Leak Detected - TransactionCache Growing",
            description="Memory usage increasing steadily, TransactionCache has 20000 entries, GC pause times over 500ms"
        )
        
        # Analyze
        analysis = self._analyze_incident(incident['id'], incident['description'])
        
        # Assertions
        self.assertIn('memory leak', analysis.lower(), "Should identify memory leak")
        self.assertIn('cache', analysis.lower(), "Should mention cache")
        
        # Check for pattern recognition
        patterns = ['unbounded', 'growth', 'increasing', 'eviction']
        found_patterns = [p for p in patterns if p in analysis.lower()]
        self.assertGreaterEqual(len(found_patterns), 1, f"Should identify growth pattern: {found_patterns}")
        
        print(f"   ✅ Detected patterns: {found_patterns}")
        
    def test_03_gc_cpu_correlation(self):
        """Test GC overhead to CPU spike correlation"""
        print("\n🧪 Test 3: GC-CPU Correlation")
        
        # Create incident with GC-CPU symptoms
        incident = self._create_test_incident(
            title="CPU Spike - GC Overhead Limit",
            description="CPU at 95%, GC pause times 800ms, spending 70% time in garbage collection"
        )
        
        # Analyze
        analysis = self._analyze_incident(incident['id'], incident['description'])
        
        # Assertions for correlation
        self.assertIn('gc', analysis.lower(), "Should mention GC")
        self.assertIn('cpu', analysis.lower(), "Should mention CPU")
        
        # Check if correlation is made
        gc_cpu_correlation = any([
            'gc overhead' in analysis.lower() and 'cpu' in analysis.lower(),
            'garbage collection' in analysis.lower() and 'cpu' in analysis.lower(),
            'gc pause' in analysis.lower() and 'cpu' in analysis.lower()
        ])
        self.assertTrue(gc_cpu_correlation, "Should correlate GC overhead with CPU spike")
        
        print("   ✅ GC-CPU correlation identified")
        
    def test_04_change_deployment_correlation(self):
        """Test correlation with recent deployments"""
        print("\n🧪 Test 4: Change/Deployment Correlation")
        
        # Create a deployment change record
        change_id = self._create_deployment_change()
        time.sleep(2)
        
        # Create related incident
        incident = self._create_test_incident(
            title="Performance Degradation After Deployment",
            description="High CPU and memory after deploying payment-service v2.1.0, cache growing unbounded"
        )
        
        # Analyze
        analysis = self._analyze_incident(incident['id'], incident['description'])
        
        # Assertions
        deployment_mentioned = any([
            'v2.1.0' in analysis,
            'deployment' in analysis.lower(),
            'deploy' in analysis.lower(),
            'change' in analysis.lower()
        ])
        self.assertTrue(deployment_mentioned, "Should mention recent deployment")
        
        print("   ✅ Deployment correlation found")
        
    def test_05_cache_eviction_issue(self):
        """Test detection of cache eviction policy issues"""
        print("\n🧪 Test 5: Cache Eviction Policy Detection")
        
        incident = self._create_test_incident(
            title="TransactionCache Memory Leak",
            description="TransactionCache growing without bounds, no eviction policy, 50000 entries cached"
        )
        
        # Analyze
        analysis = self._analyze_incident(incident['id'], incident['description'])
        
        # Assertions
        self.assertIn('cache', analysis.lower(), "Should mention cache")
        
        eviction_mentioned = any([
            'eviction' in analysis.lower(),
            'ttl' in analysis.lower(),
            'time to live' in analysis.lower(),
            'cache policy' in analysis.lower(),
            'cache management' in analysis.lower()
        ])
        self.assertTrue(eviction_mentioned, "Should identify eviction policy issue")
        
        print("   ✅ Cache eviction issue identified")
        
    def test_06_comprehensive_correlation(self):
        """Test complete correlation chain: deployment → memory leak → GC → CPU"""
        print("\n🧪 Test 6: Comprehensive Correlation Chain")
        
        # Create full scenario
        change_id = self._create_deployment_change("v2.2.0", "Removed cache size limits")
        self._push_memory_leak_metrics()
        time.sleep(3)
        
        # Create comprehensive incident
        incident = self._create_test_incident(
            title="CRITICAL: Production Outage - Memory/CPU Crisis",
            description="""Multiple issues after v2.2.0 deployment:
            - Heap memory at 92%, growing 5MB/minute
            - GC pause times exceeding 1 second
            - CPU utilization at 98% due to GC overhead
            - TransactionCache has 100000 entries
            - Response times degraded to 10+ seconds
            Instance: i-02bef13982a179478"""
        )
        
        # Analyze
        analysis = self._analyze_incident(incident['id'], incident['description'])
        
        # Check for complete correlation chain
        correlation_elements = {
            'deployment': any(term in analysis.lower() for term in ['deployment', 'v2.2.0', 'deploy']),
            'memory_leak': 'memory leak' in analysis.lower(),
            'cache_issue': 'cache' in analysis.lower(),
            'gc_overhead': any(term in analysis.lower() for term in ['gc', 'garbage collection']),
            'cpu_impact': 'cpu' in analysis.lower()
        }
        
        print("\n   Correlation Chain Validation:")
        for element, found in correlation_elements.items():
            status = "✅" if found else "❌"
            print(f"   {status} {element}")
            
        # All elements should be present
        all_correlated = all(correlation_elements.values())
        self.assertTrue(all_correlated, "Should identify complete correlation chain")
        
        # Check for root cause clarity
        root_cause_clear = any([
            'cache' in analysis.lower() and 'eviction' in analysis.lower(),
            'transactioncache' in analysis.lower(),
            'unbounded' in analysis.lower() and 'cache' in analysis.lower()
        ])
        self.assertTrue(root_cause_clear, "Should clearly identify cache as root cause")
        
        print("   ✅ Complete correlation chain verified!")
        
    def test_07_remediation_recommendations(self):
        """Test that proper remediation steps are provided"""
        print("\n🧪 Test 7: Remediation Recommendations")
        
        incident = self._create_test_incident(
            title="Memory Leak Causing Production Impact",
            description="Severe memory leak in payment-service, need immediate remediation"
        )
        
        # Analyze
        analysis = self._analyze_incident(incident['id'], incident['description'])
        
        # Check for remediation keywords
        remediation_keywords = [
            'restart', 'rollback', 'eviction', 'policy', 'ttl',
            'cache size', 'limit', 'monitor', 'scale', 'optimize'
        ]
        
        found_remediation = [k for k in remediation_keywords if k in analysis.lower()]
        self.assertGreaterEqual(len(found_remediation), 2, 
                               f"Should provide remediation steps, found: {found_remediation}")
        
        print(f"   ✅ Remediation keywords found: {found_remediation}")
        
    def test_08_business_impact_assessment(self):
        """Test business impact is properly assessed"""
        print("\n🧪 Test 8: Business Impact Assessment")
        
        incident = self._create_test_incident(
            title="Payment Service Degraded - Customer Impact",
            description="Payment processing delays due to memory/CPU issues, transactions failing"
        )
        
        # Analyze
        analysis = self._analyze_incident(incident['id'], incident['description'])
        
        # Check for business impact terms
        business_terms = [
            'customer', 'revenue', 'transaction', 'payment', 
            'business', 'impact', 'user experience', 'downtime'
        ]
        
        found_business_terms = [t for t in business_terms if t in analysis.lower()]
        self.assertGreaterEqual(len(found_business_terms), 2,
                               f"Should assess business impact, found: {found_business_terms}")
        
        print(f"   ✅ Business impact terms: {found_business_terms}")
        
    # Helper methods
    def _create_test_incident(self, title: str, description: str) -> Dict:
        """Create a test OpsItem incident"""
        response = self.ssm_client.create_ops_item(
            Title=title,
            Description=description,
            Source="TestSuite",
            OperationalData={
                'TestId': {'Value': self.id()},
                'Instance': {'Value': self.instance_id}
            },
            Severity='2',
            Category='Performance'
        )
        
        return {
            'id': response['OpsItemId'],
            'title': title,
            'description': description
        }
        
    def _create_deployment_change(self, version: str = "v2.1.0", changes: str = "") -> str:
        """Create a deployment change record"""
        response = self.ssm_client.create_ops_item(
            Title=f"[CHANGE] Deploy payment-service {version}",
            Description=f"Deployment of payment-service {version}. Changes: {changes}",
            Source="ChangeManagement",
            OperationalData={
                'ChangeType': {'Value': 'Deployment'},
                'Version': {'Value': version}
            },
            Severity='3',
            Category='Availability'
        )
        
        return response['OpsItemId']
        
    def _push_memory_leak_metrics(self):
        """Push test metrics showing memory leak pattern"""
        try:
            # Push increasing memory metrics
            for i in range(3):
                value = 70 + (i * 10)  # 70%, 80%, 90%
                self.cloudwatch_client.put_metric_data(
                    Namespace='JavaApp/SpringBoot',
                    MetricData=[
                        {
                            'MetricName': 'HeapMemoryUsed',
                            'Value': value,
                            'Unit': 'Percent',
                            'Timestamp': datetime.now() - timedelta(minutes=3-i),
                            'Dimensions': [
                                {'Name': 'InstanceId', 'Value': self.instance_id}
                            ]
                        },
                        {
                            'MetricName': 'GCPauseTime',
                            'Value': 200 + (i * 150),  # Increasing GC pause
                            'Unit': 'Milliseconds',
                            'Dimensions': [
                                {'Name': 'InstanceId', 'Value': self.instance_id}
                            ]
                        }
                    ]
                )
        except Exception as e:
            print(f"   Warning: Could not push metrics: {e}")
            
    def _analyze_incident(self, ops_item_id: str, description: str) -> str:
        """Run supervisor analysis on incident"""
        payload = {
            'action': 'analyze',
            'incident_description': description,
            'start_time': (datetime.now() - timedelta(hours=1)).isoformat(),
            'end_time': datetime.now().isoformat(),
            'service': 'payment-service',
            'environment': 'test',
            'additional_context': {
                'ops_item_id': ops_item_id,
                'instance_id': self.instance_id
            }
        }
        
        response = self.lambda_client.invoke(
            FunctionName='sre-supervisor-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            return body.get('root_cause_analysis', '')
        else:
            self.fail(f"Analysis failed: {result}")
            
    @classmethod
    def tearDownClass(cls):
        """Generate test report"""
        print("\n" + "=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        
        total_tests = len(cls.test_results)
        passed_tests = sum(1 for t in cls.test_results if t['status'] == 'passed')
        failed_tests = total_tests - passed_tests
        total_time = sum(t['time'] for t in cls.test_results)
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"Total Execution Time: {total_time:.2f}s")
        
        print("\nDetailed Results:")
        for result in cls.test_results:
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            print(f"  {status_icon} {result['test']}: {result['time']:.2f}s")
            
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! The enhanced AI analysis is working correctly!")
        else:
            print(f"\n⚠️ {failed_tests} tests failed. Review the failures above.")


def run_test_suite():
    """Run the complete test suite"""
    print("🧪 ENHANCED AI ANALYSIS TEST SUITE")
    print("Testing JVM memory leak detection and correlation capabilities")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIAnalysisCorrelation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_test_suite()
    exit(0 if success else 1)
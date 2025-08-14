"""
Final validation of Problem Management features
"""

import json
import os
from datetime import datetime
from servicenow_problem_manager import ServiceNowProblemManager
from synthetic_transaction_generator import SyntheticTransactionGenerator


def validate_problem_management():
    """Validate problem management functionality"""
    print("=" * 60)
    print("PROBLEM MANAGEMENT VALIDATION")
    print("=" * 60)
    
    # Initialize managers
    problem_manager = ServiceNowProblemManager()
    transaction_generator = SyntheticTransactionGenerator()
    
    # Test 1: Create a problem from incident
    print("\n1. Testing Problem Creation from Incident...")
    test_incident = {
        'id': 'INC-VAL-001',
        'title': 'Validation Test - High CPU Usage',
        'description': 'Application servers experiencing high CPU usage during peak hours',
        'service': 'web-application',
        'impact': 'High',
        'type': 'performance'
    }
    
    try:
        result = problem_manager.create_problem_from_incident(test_incident)
        problem_id = result['problem_id']
        print(f"✅ Problem created successfully: {problem_id}")
        print(f"   - Category: {result['ai_analysis']['category']}")
        print(f"   - Priority: {result['ai_analysis']['priority']}")
        print(f"   - Root Cause: {result['ai_analysis']['root_cause'][:50]}...")
    except Exception as e:
        print(f"❌ Failed to create problem: {e}")
        return False
    
    # Test 2: Generate synthetic transactions
    print("\n2. Testing Synthetic Transaction Generation...")
    try:
        trans_result = transaction_generator.generate_transactions_for_incident(test_incident)
        print(f"✅ Generated {trans_result['summary']['total_transactions']} transactions")
        print(f"   - Failed: {trans_result['summary']['failed_transactions']}")
        print(f"   - Avg Duration: {trans_result['summary']['average_duration_ms']:.0f}ms")
        print(f"   - CloudWatch Logs: {trans_result['logs']['events_count']} events")
        print(f"   - CloudWatch Metrics: {trans_result['metrics']['metrics_count']} metrics")
        print(f"   - VPC Flow Logs: {trans_result['vpc_flow_logs']['logs_count']} logs")
        print(f"   - CloudTrail Events: {trans_result['cloudtrail_events']['events_count']} events")
    except Exception as e:
        print(f"❌ Failed to generate transactions: {e}")
        return False
    
    # Test 3: Correlate another incident
    print("\n3. Testing Incident-to-Problem Correlation...")
    test_incident2 = {
        'id': 'INC-VAL-002',
        'title': 'Related Issue - Memory Exhaustion',
        'description': 'Same application servers running out of memory',
        'service': 'web-application',
        'impact': 'High'
    }
    
    try:
        # Get correlation suggestions
        correlations = problem_manager.get_problems_for_correlation(test_incident2)
        if correlations:
            print(f"✅ Found {len(correlations)} potential correlations")
            best_match = correlations[0]
            print(f"   - Best match: {best_match['id']} (Confidence: {best_match.get('correlation_confidence', 0)}%)")
            
            # Correlate the incident
            corr_result = problem_manager.correlate_incident_to_problem(test_incident2['id'], best_match['id'])
            if corr_result['success']:
                print(f"✅ Successfully correlated incident to problem")
                print(f"   - Total related incidents: {len(corr_result['related_incidents'])}")
            else:
                print(f"❌ Failed to correlate: {corr_result['error']}")
        else:
            print("⚠️ No correlations found")
    except Exception as e:
        print(f"❌ Failed to correlate incident: {e}")
    
    # Test 4: Verify data persistence
    print("\n4. Testing Data Persistence...")
    all_problems = problem_manager.get_all_problems()
    print(f"✅ Found {len(all_problems)} problems in the system")
    
    # Clean up generated files
    print("\n5. Cleaning up test data...")
    cleanup_files = []
    
    # Find VPC flow log files
    for file in os.listdir('.'):
        if file.startswith('vpc_flow_logs_') and file.endswith('.json'):
            cleanup_files.append(file)
        elif file.startswith('cloudtrail_events_') and file.endswith('.json'):
            cleanup_files.append(file)
    
    for file in cleanup_files:
        try:
            os.remove(file)
            print(f"   - Removed {file}")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("✅ PROBLEM MANAGEMENT VALIDATION COMPLETE")
    print("=" * 60)
    return True


def display_feature_summary():
    """Display summary of new features"""
    print("\n" + "=" * 60)
    print("PROBLEM MANAGEMENT FEATURES SUMMARY")
    print("=" * 60)
    
    features = [
        ("ServiceNow Problem Management", [
            "AI-powered problem creation from incidents",
            "Incident-to-problem correlation with confidence scoring",
            "Problem state and priority management",
            "Root cause analysis and workaround documentation"
        ]),
        ("Synthetic Transaction Generator", [
            "Generate transactions based on incident patterns",
            "Create CloudWatch logs with error patterns",
            "Generate CloudWatch metrics",
            "Create VPC Flow Logs and CloudTrail events"
        ]),
        ("Enhanced Streamlit UI", [
            "Problem Management tab with 4 sub-tabs",
            "Synthetic Transactions tab with visualization",
            "Incident dropdown selection",
            "Problem analytics and metrics"
        ])
    ]
    
    for feature_name, capabilities in features:
        print(f"\n{feature_name}:")
        for capability in capabilities:
            print(f"  ✓ {capability}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    # Clean up any existing problems for fresh start
    problems_file = '/home/ec2-user/sre/sre_mcp/servicenow_problems.json'
    if os.path.exists(problems_file):
        os.remove(problems_file)
    
    # Run validation
    if validate_problem_management():
        display_feature_summary()
        
        print("\n🚀 READY TO USE!")
        print("Run the following command to start the enhanced Streamlit app:")
        print("\nexport AWS_DEFAULT_REGION=us-east-1 && python3 -m streamlit run streamlit_app_problem_management.py --server.port 8501 --server.address 0.0.0.0")
        print("\nThen navigate to:")
        print("- Advanced Tools > Problem Management")
        print("- Advanced Tools > Synthetic Transactions")
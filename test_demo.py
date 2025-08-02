#!/usr/bin/env python3
"""Test the demo from the usage guide documentation."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.incident_analyzer import SRECopilotAnalyzer

def test_basic_demo():
    """Test the basic demo from the usage guide."""
    print("Testing SRE Copilot Demo from Usage Guide")
    print("="*60)
    
    try:
        # Initialize the analyzer
        print("\n1. Initializing SRE Copilot Analyzer...")
        analyzer = SRECopilotAnalyzer()
        print("✓ Analyzer initialized successfully")
        
        # Test the demo incident from the usage guide
        print("\n2. Testing incident analysis...")
        result = analyzer.analyze_incident(
            "Our e-commerce website is experiencing high latency (>2s) for product page loads since 2:00 PM today.",
            log_data="2025-04-06 14:02:17 WARN [DatabaseConnector] Connection pool reaching capacity (85%)",
            metrics_data="Database connection pool utilization increased from 60% to 95%",
            dashboard_data="The CloudWatch dashboard shows a spike in database CPU utilization at 2:00 PM"
        )
        
        print("✓ Analysis completed successfully")
        print("\n3. Analysis Result:")
        print("-"*60)
        print(result)
        print("-"*60)
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_with_files():
    """Test the file-based demo from the usage guide."""
    print("\n\nTesting File-Based Demo")
    print("="*60)
    
    # Create sample files as shown in the documentation
    print("\n1. Creating sample data files...")
    
    # Create logs.txt
    with open('logs.txt', 'w') as f:
        f.write("""2025-04-06 13:55:23 INFO  [ProductService] Average response time: 120ms
2025-04-06 14:02:17 WARN  [DatabaseConnector] Connection pool reaching capacity (85%)
2025-04-06 14:05:42 ERROR [DatabaseConnector] Connection timeout after 3000ms
2025-04-06 14:06:13 ERROR [ProductService] Failed to retrieve product data: Database connection timeout""")
    print("✓ Created logs.txt")
    
    # Create metrics.txt
    with open('metrics.txt', 'w') as f:
        f.write("""Database connection pool utilization increased from 60% to 95%
Database query latency increased from 50ms to 500ms
Product service error rate increased from 0.1% to 5%""")
    print("✓ Created metrics.txt")
    
    # Create dashboard.txt
    with open('dashboard.txt', 'w') as f:
        f.write("""The CloudWatch dashboard shows:
- A spike in database CPU utilization at 2:00 PM
- Increased memory usage on the application servers
- Correlation between database connections and latency""")
    print("✓ Created dashboard.txt")
    
    try:
        # Initialize analyzer
        print("\n2. Analyzing incident with file data...")
        analyzer = SRECopilotAnalyzer()
        
        # Read file contents
        with open('logs.txt', 'r') as f:
            log_data = f.read()
        with open('metrics.txt', 'r') as f:
            metrics_data = f.read()
        with open('dashboard.txt', 'r') as f:
            dashboard_data = f.read()
        
        # Analyze incident
        result = analyzer.analyze_incident(
            "High latency on product pages",
            log_data=log_data,
            metrics_data=metrics_data,
            dashboard_data=dashboard_data
        )
        
        print("✓ Analysis completed successfully")
        print("\n3. Analysis Result:")
        print("-"*60)
        print(result)
        print("-"*60)
        
        # Clean up files
        import os
        os.remove('logs.txt')
        os.remove('metrics.txt')
        os.remove('dashboard.txt')
        print("\n✓ Cleaned up sample files")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all demo tests."""
    print("SRE Copilot Demo Testing")
    print("========================\n")
    
    results = []
    
    # Test basic demo
    results.append(("Basic Demo", test_basic_demo()))
    
    # Test file-based demo
    results.append(("File-Based Demo", test_with_files()))
    
    # Summary
    print("\n\nTest Summary")
    print("="*60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All demos are working!")
    else:
        print("\n❌ Some demos failed. Please check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
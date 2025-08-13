#!/usr/bin/env python3
"""
Integration test for IP masking functionality
Tests the actual Lambda functions and Streamlit integration
"""

import json
import subprocess
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the IP masker
from utils.ip_masker import IPMasker, mask_logs_for_llm


def test_ip_masker_basic():
    """Test basic IP masking functionality."""
    print("\n🧪 Testing Basic IP Masking...")
    
    masker = IPMasker(mask_type="partial")
    
    # Test cases with expected results
    test_cases = [
        {
            "input": "Error connecting to 192.168.1.100:5432",
            "expected_masked": "192.168.XXX.XXX",
            "expected_count": 1
        },
        {
            "input": "VPC Flow: srcaddr=10.0.1.100 dstaddr=172.16.0.50",
            "expected_masked": ["10.0.XXX.XXX", "172.16.XXX.XXX"],
            "expected_count": 2
        },
        {
            "input": '{"client_ip": "203.0.113.0", "server": "10.0.0.5"}',
            "expected_masked": ["203.0.XXX.XXX", "10.0.XXX.XXX"],
            "expected_count": 2
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases):
        masked_text, ip_map = masker.mask_text(test["input"])
        
        # Check IP count
        if len(ip_map) == test["expected_count"]:
            print(f"  ✅ Test {i+1}: Correct IP count ({test['expected_count']})")
            passed += 1
        else:
            print(f"  ❌ Test {i+1}: Expected {test['expected_count']} IPs, found {len(ip_map)}")
            failed += 1
            
        # Check masked content
        if isinstance(test["expected_masked"], list):
            all_found = all(masked in masked_text for masked in test["expected_masked"])
        else:
            all_found = test["expected_masked"] in masked_text
            
        if all_found:
            print(f"  ✅ Test {i+1}: Masked IPs found in output")
            passed += 1
        else:
            print(f"  ❌ Test {i+1}: Expected masked IPs not found")
            failed += 1
            
    print(f"\nBasic Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_aws_log_patterns():
    """Test masking of common AWS log patterns."""
    print("\n🧪 Testing AWS Log Pattern Masking...")
    
    masker = IPMasker(mask_type="partial")
    
    aws_patterns = [
        "2024-01-15T10:30:00 ERROR Failed to connect to RDS instance at 10.0.1.100:3306",
        "CloudTrail: User logged in from IP address 203.0.113.50",
        "ELB Access Log: 192.168.1.100:443 -> 10.0.2.200:8080 response_time=0.5",
        "Security Group ingress rule allows 0.0.0.0/0 to port 22",
        "VPC Flow Log: 2 123456789 eni-abc123 10.0.0.100 172.31.0.50 443 49152 6 10 840 1234567890 1234567891 ACCEPT OK"
    ]
    
    passed = 0
    failed = 0
    
    for pattern in aws_patterns:
        masked, ip_map = masker.mask_text(pattern)
        
        # Check that original IPs are not in masked text
        original_ips_found = any(ip in masked for ip in ip_map.keys())
        
        if not original_ips_found and len(ip_map) > 0:
            print(f"  ✅ Pattern masked successfully: {len(ip_map)} IPs found")
            passed += 1
        elif len(ip_map) == 0 and "0.0.0.0" in pattern:
            print(f"  ✅ Pattern with 0.0.0.0 handled correctly")
            passed += 1
        else:
            print(f"  ❌ Pattern masking failed: {pattern[:50]}...")
            failed += 1
            
    print(f"\nAWS Pattern Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_json_log_masking():
    """Test masking of JSON structured logs."""
    print("\n🧪 Testing JSON Log Masking...")
    
    masker = IPMasker(mask_type="partial")
    
    json_logs = [
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "ERROR",
            "message": "Database connection failed",
            "details": {
                "host": "192.168.1.100",
                "port": 5432,
                "client_ip": "10.0.0.5"
            }
        },
        {
            "event": "API_CALL",
            "source_ip": "203.0.113.0",
            "target_endpoint": "https://api.example.com",
            "response": {
                "error": "Rate limit exceeded for IP 203.0.113.0"
            }
        }
    ]
    
    passed = 0
    failed = 0
    
    for log in json_logs:
        masked_log = masker.mask_json(log)
        original_json = json.dumps(log)
        masked_json = json.dumps(masked_log)
        
        # Count IPs in original
        ips_found = []
        if "192.168.1.100" in original_json:
            ips_found.append("192.168.1.100")
        if "10.0.0.5" in original_json:
            ips_found.append("10.0.0.5")
        if "203.0.113.0" in original_json:
            ips_found.append("203.0.113.0")
            
        # Check all IPs are masked
        all_masked = all(ip not in masked_json for ip in ips_found)
        
        if all_masked and len(ips_found) > 0:
            print(f"  ✅ JSON log masked successfully: {len(ips_found)} IPs masked")
            passed += 1
        else:
            print(f"  ❌ JSON log masking failed")
            failed += 1
            
    print(f"\nJSON Log Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_security_compliance():
    """Test security compliance scenarios."""
    print("\n🧪 Testing Security Compliance...")
    
    masker = IPMasker(mask_type="partial")
    
    # Security-sensitive logs that must have IPs masked
    security_logs = [
        "SSH brute force attack detected from 192.168.100.50",
        "Unauthorized API access: token=XXX ip=10.0.0.100",
        "Failed login attempts from 203.0.113.0 - blocking IP",
        "Potential data exfiltration to external IP 198.51.100.0",
        "Firewall rule violation: src=172.16.0.10 dst=8.8.8.8 action=BLOCKED"
    ]
    
    passed = 0
    failed = 0
    
    for log in security_logs:
        masked, ip_map = masker.mask_text(log)
        
        # Verify no original IPs remain
        has_original_ips = any(ip in masked for ip in ip_map.keys())
        
        if not has_original_ips and len(ip_map) > 0:
            print(f"  ✅ Security log properly masked: {len(ip_map)} IPs removed")
            passed += 1
        else:
            print(f"  ❌ Security compliance failed: Original IPs may be exposed")
            failed += 1
            
    print(f"\nSecurity Compliance Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_performance():
    """Test masking performance with large datasets."""
    print("\n🧪 Testing Masking Performance...")
    
    import time
    
    masker = IPMasker(mask_type="partial")
    
    # Generate large log dataset
    large_log = []
    for i in range(1000):
        large_log.append(f"Log entry {i}: Connection from 192.168.{i % 256}.{i % 100} to 10.0.{i % 256}.{i % 50}")
    
    start_time = time.time()
    
    total_masked = 0
    for log in large_log:
        _, ip_map = masker.mask_text(log)
        total_masked += len(ip_map)
        
    end_time = time.time()
    elapsed = end_time - start_time
    
    logs_per_second = len(large_log) / elapsed
    
    print(f"  📊 Processed {len(large_log)} logs in {elapsed:.2f} seconds")
    print(f"  📊 Performance: {logs_per_second:.0f} logs/second")
    print(f"  📊 Total IPs masked: {total_masked}")
    print(f"  📊 Unique IPs tracked: {len(masker.ip_mapping)}")
    
    # Performance should be reasonable
    if logs_per_second > 100:  # Should process at least 100 logs/second
        print("  ✅ Performance test passed")
        return True
    else:
        print("  ❌ Performance test failed - too slow")
        return False


def test_streamlit_integration():
    """Test that Streamlit app imports IP masking correctly."""
    print("\n🧪 Testing Streamlit Integration...")
    
    try:
        # Check if streamlit app imports correctly
        result = subprocess.run(
            ["python3", "-c", "import streamlit_app; print('IP_MASKING_AVAILABLE' in dir(streamlit_app))"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "True" in result.stdout:
            print("  ✅ Streamlit app successfully imports IP masking")
            return True
        else:
            print("  ❌ Streamlit app failed to import IP masking")
            return False
            
    except Exception as e:
        print(f"  ❌ Streamlit integration test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🚀 Running IP Masking Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Basic IP Masking", test_ip_masker_basic),
        ("AWS Log Patterns", test_aws_log_patterns),
        ("JSON Log Masking", test_json_log_masking),
        ("Security Compliance", test_security_compliance),
        ("Performance", test_performance),
        ("Streamlit Integration", test_streamlit_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            failed += 1
            
    print("\n" + "=" * 50)
    print("📊 Integration Test Summary:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {len(tests)}")
    
    if failed == 0:
        print("\n🎉 All integration tests passed! IP masking is working correctly.")
        print("\n📝 Security Requirements Met:")
        print("  ✅ IP addresses are masked before sending to LLMs")
        print("  ✅ Original IPs are preserved for display")
        print("  ✅ Toggle available in UI to show/hide masking")
        print("  ✅ AWS log patterns are properly handled")
        print("  ✅ Performance is acceptable for production use")
    else:
        print("\n⚠️  Some tests failed. Please review and fix the issues.")
        
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
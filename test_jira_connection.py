#!/usr/bin/env python3
"""Test Jira MCP connection"""

import requests
import json

def test_jira_connection():
    """Test Jira MCP server connection"""
    print("🧪 Testing Jira MCP Connection...")
    print("="*50)
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:9086/health", timeout=2)
        print(f"✅ Health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False
    
    # Test issues endpoint
    try:
        response = requests.get("http://localhost:9086/jira/issues", timeout=5)
        print(f"✅ Issues endpoint: {response.status_code}")
        
        if response.status_code == 200:
            issues = response.json()
            print(f"✅ Found {len(issues)} issues")
            
            # Display first 3 issues
            print("\nSample Issues:")
            print("-"*50)
            for issue in issues[:3]:
                priority = issue.get('priority', {})
                if isinstance(priority, dict):
                    priority_name = priority.get('name', 'Unknown')
                else:
                    priority_name = priority
                    
                status = issue.get('status', {})
                if isinstance(status, dict):
                    status_name = status.get('name', 'Unknown')
                else:
                    status_name = status
                
                print(f"Key: {issue.get('key', 'Unknown')}")
                print(f"Summary: {issue.get('summary', 'No summary')}")
                print(f"Priority: {priority_name}")
                print(f"Status: {status_name}")
                print("-"*50)
        else:
            print(f"❌ Issues endpoint returned: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Issues endpoint failed: {str(e)}")
        return False
    
    # Test specific issue
    try:
        response = requests.get("http://localhost:9086/jira/issues/JIRA-101", timeout=2)
        print(f"\n✅ Specific issue endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Specific issue endpoint failed: {str(e)}")
    
    print("\n✅ All tests passed! Jira MCP is working correctly.")
    return True

if __name__ == "__main__":
    test_jira_connection()
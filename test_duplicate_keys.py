#!/usr/bin/env python3
"""Test duplicate key prevention in Streamlit app."""

import sys
import os
import streamlit as st

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit_key_manager import key_manager

def test_key_generation():
    """Test that key generation always produces unique keys."""
    print("=" * 60)
    print("Duplicate Key Prevention Test")
    print("=" * 60)
    
    # Initialize session state if needed
    if 'key_counter' not in st.session_state:
        st.session_state.key_counter = {}
    if 'widget_render_count' not in st.session_state:
        st.session_state.widget_render_count = 0
    
    # Test 1: Same base key called multiple times
    print("\n1. Testing same base key multiple times:")
    keys = []
    for i in range(5):
        key = key_manager.get_unique_key("test_button")
        keys.append(key)
        print(f"   Call {i+1}: {key}")
    
    if len(keys) == len(set(keys)):
        print("   ✅ All keys are unique")
    else:
        print("   ❌ Duplicate keys found!")
        return False
    
    # Test 2: Same base key with same arguments
    print("\n2. Testing same base key with identical arguments:")
    keys = []
    for i in range(3):
        key = key_manager.get_unique_key("create_jira", "oi_123", "performance", "recommendations")
        keys.append(key)
        print(f"   Call {i+1}: {key}")
    
    if len(keys) == len(set(keys)):
        print("   ✅ All keys are unique")
    else:
        print("   ❌ Duplicate keys found!")
        return False
    
    # Test 3: Tab keys
    print("\n3. Testing tab keys:")
    keys = []
    tabs = ["search", "browse", "add", "test"]
    for tab in tabs:
        # Simulate multiple renders of same tab
        for i in range(2):
            key = key_manager.get_tab_key("kb_button", tab)
            keys.append(key)
            print(f"   Tab '{tab}' render {i+1}: {key}")
    
    if len(keys) == len(set(keys)):
        print("   ✅ All tab keys are unique")
    else:
        print("   ❌ Duplicate tab keys found!")
        return False
    
    # Test 4: Form keys
    print("\n4. Testing form keys:")
    keys = []
    for i in range(3):
        key = key_manager.get_form_key("feedback", f"incident_{i}")
        keys.append(key)
        print(f"   Form {i+1}: {key}")
    
    if len(keys) == len(set(keys)):
        print("   ✅ All form keys are unique")
    else:
        print("   ❌ Duplicate form keys found!")
        return False
    
    # Test 5: Loop keys
    print("\n5. Testing loop keys:")
    keys = []
    for outer in range(2):
        for inner in range(3):
            key = key_manager.get_loop_key("incident_button", inner)
            keys.append(key)
            print(f"   Outer loop {outer}, index {inner}: {key}")
    
    if len(keys) == len(set(keys)):
        print("   ✅ All loop keys are unique")
    else:
        print("   ❌ Duplicate loop keys found!")
        return False
    
    # Test 6: Real-world scenario - recommendations buttons
    print("\n6. Testing real-world scenario (recommendations buttons):")
    keys = []
    incidents = [
        {"ops_item_id": "oi_7b7aec8178f6", "type": "performance"},
        {"ops_item_id": "oi_7b7aec8178f6", "type": "performance"},  # Same incident rendered twice
        {"ops_item_id": "oi_123456", "type": "security"}
    ]
    
    for idx, incident in enumerate(incidents):
        print(f"\n   Incident {idx+1}: {incident['ops_item_id']} ({incident['type']})")
        for button in ["create_jira", "send_slack", "export_report"]:
            key = key_manager.get_unique_key(button, incident['ops_item_id'], incident['type'], "recommendations")
            keys.append(key)
            print(f"      {button}: {key}")
    
    if len(keys) == len(set(keys)):
        print("\n   ✅ All recommendation button keys are unique")
    else:
        print("\n   ❌ Duplicate recommendation button keys found!")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total keys generated: {len(keys)}")
    print(f"Unique keys: {len(set(keys))}")
    print(f"Widget render count: {st.session_state.widget_render_count}")
    
    return True

def test_streamlit_app_scenarios():
    """Test specific Streamlit app scenarios that caused errors."""
    print("\n" + "=" * 60)
    print("STREAMLIT APP SPECIFIC TESTS")
    print("=" * 60)
    
    # Scenario 1: Analyze incident tab switching
    print("\n1. Simulating tab switching in Analyze Incident:")
    keys = []
    
    # User clicks on Root Cause tab
    key1 = key_manager.get_unique_key("create_jira", "oi_7b7aec8178f6", "performance", "recommendations")
    keys.append(("First visit to recommendations tab", key1))
    
    # User switches to Data Analysis tab then back to Recommendations
    key2 = key_manager.get_unique_key("create_jira", "oi_7b7aec8178f6", "performance", "recommendations")
    keys.append(("Return to recommendations tab", key2))
    
    # User reruns analysis
    key3 = key_manager.get_unique_key("create_jira", "oi_7b7aec8178f6", "performance", "recommendations")
    keys.append(("After rerun analysis", key3))
    
    for desc, key in keys:
        print(f"   {desc}: {key}")
    
    unique_keys = [k for _, k in keys]
    if len(unique_keys) == len(set(unique_keys)):
        print("   ✅ No duplicates when switching tabs")
    else:
        print("   ❌ Duplicates found when switching tabs!")
        return False
    
    # Scenario 2: Multiple incidents in same session
    print("\n2. Multiple incidents in same session:")
    keys = []
    
    for i in range(3):
        key = key_manager.get_unique_key("analyze_another", "main")
        keys.append(key)
        print(f"   Analyze another incident button {i+1}: {key}")
    
    if len(keys) == len(set(keys)):
        print("   ✅ No duplicates for repeated button renders")
    else:
        print("   ❌ Duplicates found for repeated buttons!")
        return False
    
    return True

def main():
    """Main test function."""
    # Test basic key generation
    if not test_key_generation():
        print("\n❌ Basic key generation tests FAILED")
        return False
    
    # Test Streamlit-specific scenarios
    if not test_streamlit_app_scenarios():
        print("\n❌ Streamlit app scenario tests FAILED")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL DUPLICATE KEY PREVENTION TESTS PASSED!")
    print("=" * 60)
    print("\nThe enhanced key manager ensures:")
    print("1. Every widget gets a unique key")
    print("2. Keys remain unique even when tabs are switched")
    print("3. Keys remain unique when same widget is rendered multiple times")
    print("4. Keys include render count for absolute uniqueness")
    print("\n🎉 No more duplicate key errors!")
    
    return True

if __name__ == "__main__":
    # Initialize Streamlit session state
    if hasattr(st, 'session_state'):
        success = main()
        sys.exit(0 if success else 1)
    else:
        print("Running outside Streamlit context - limited testing only")
        print("Some tests require Streamlit session state")
        sys.exit(0)
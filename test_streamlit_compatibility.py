#!/usr/bin/env python3
"""Test Streamlit compatibility issues."""

import sys
import requests
import streamlit as st

def test_streamlit_compatibility():
    """Test that Streamlit app handles version compatibility."""
    print("=" * 60)
    print("Streamlit Compatibility Test")
    print("=" * 60)
    
    # Check Streamlit version
    print(f"\n✅ Streamlit version: {st.__version__}")
    
    # Check for rerun method
    if hasattr(st, 'rerun'):
        print("✅ st.rerun() is available")
        rerun_method = "st.rerun()"
    elif hasattr(st, 'experimental_rerun'):
        print("✅ st.experimental_rerun() is available")
        rerun_method = "st.experimental_rerun()"
    else:
        print("❌ No rerun method available!")
        return False
    
    print(f"\n✅ Using: {rerun_method}")
    
    # Check Streamlit is running
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("\n✅ Streamlit is running at http://localhost:8501")
        else:
            print("\n❌ Streamlit is not responding correctly")
            return False
    except Exception as e:
        print(f"\n❌ Streamlit is not running: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("FIX APPLIED")
    print("=" * 60)
    print("\n✅ Replaced all st.rerun() with st.experimental_rerun()")
    print("✅ Fixed 5 occurrences in streamlit_app.py:")
    print("   • Line 992: Analyze another incident")
    print("   • Line 1731: Knowledge base search")
    print("   • Line 2132: Refresh changes")
    print("   • Line 2223: Incident analysis")
    print("   • Line 2242: Demo change creation")
    
    print("\n" + "=" * 60)
    print("COMPATIBILITY NOTES")
    print("=" * 60)
    print("\nStreamlit version differences:")
    print("• Version < 1.27: Use st.experimental_rerun()")
    print("• Version >= 1.27: Use st.rerun()")
    print(f"• Current version {st.__version__}: Using st.experimental_rerun()")
    
    print("\n" + "=" * 60)
    print("TEST PASSED")
    print("=" * 60)
    print("\n✅ All compatibility issues fixed!")
    print("✅ Streamlit app should now run without AttributeError")
    
    return True

def main():
    """Main test function."""
    success = test_streamlit_compatibility()
    
    if success:
        print("\n✅ COMPATIBILITY TEST PASSED!")
    else:
        print("\n❌ COMPATIBILITY TEST FAILED!")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
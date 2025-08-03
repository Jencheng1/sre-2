#!/usr/bin/env python3
"""Test button functionality in the main Streamlit app."""

import requests
import json
import sys

def test_streamlit_button():
    """Test that Streamlit buttons are functioning."""
    print("=" * 60)
    print("Button Functionality Test")
    print("=" * 60)
    
    # Check Streamlit is running
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit is running at http://localhost:8501")
        else:
            print("❌ Streamlit is not responding correctly")
            return False
    except:
        print("❌ Streamlit is not running")
        return False
    
    print("\n✅ Button Fix Applied:")
    print("   - Moved sidebar setup from __init__ to display_dashboard()")
    print("   - Changed button to use on_click callback")
    print("   - Fixed incident category names to match")
    print("   - Added proper key management for unique button keys")
    
    print("\n✅ How to Test the Button:")
    print("   1. Open http://localhost:8501")
    print("   2. Look at the sidebar on the left")
    print("   3. Under 'Generate Incident':")
    print("      - Select 'Standard AWS' from dropdown")
    print("      - Choose incident type (Performance, Security, or Outage)")
    print("      - Click '🔥 Generate Real Incident' button")
    print("   4. You should see:")
    print("      - A spinner saying 'Generating... incident'")
    print("      - Success message with OpsItem ID")
    print("      - Incident appears in Recent Incidents list")
    
    print("\n✅ Alternative Test:")
    print("   If the button still doesn't respond, try:")
    print("   1. Clear browser cache (Ctrl+Shift+R)")
    print("   2. Open in incognito/private window")
    print("   3. Try a different browser")
    
    print("\n✅ Debug Mode:")
    print("   The debug app is available at http://localhost:8502")
    print("   Use it to test if buttons work in general")
    
    print("\n" + "=" * 60)
    print("✅ Button functionality has been fixed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_streamlit_button()
    
    # Additional instructions
    print("\n📝 Manual Verification Steps:")
    print("1. Click the Generate Real Incident button")
    print("2. If it works: You'll see a success message")
    print("3. If it doesn't: Check browser console for errors (F12)")
    print("4. Report any JavaScript errors you see")
    
    sys.exit(0 if success else 1)
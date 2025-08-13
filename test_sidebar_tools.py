#!/usr/bin/env python3
"""
Test script to verify sidebar tools are properly implemented
"""
import sys
sys.path.insert(0, '.')

def test_render_methods():
    """Test that all render methods exist"""
    print("Testing render methods...")
    
    try:
        # Import the main app module
        from streamlit_app import EnhancedSREDashboard
        
        # Create instance
        dashboard = EnhancedSREDashboard()
        
        # Check if methods exist
        methods = [
            'render_postmortem_analysis',
            'render_ip_masking', 
            'render_test_scenarios'
        ]
        
        missing = []
        for method in methods:
            if hasattr(dashboard, method):
                print(f"✓ Method '{method}' exists")
            else:
                print(f"✗ Method '{method}' missing")
                missing.append(method)
        
        if missing:
            print(f"\nMissing methods: {missing}")
            return False
        
        print("\n✅ All render methods found!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_sidebar_features():
    """Test sidebar feature implementation"""
    print("\nTesting sidebar implementation...")
    
    try:
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for sidebar tool section
        checks = [
            ("Additional Tools section", "### 🛠️ Additional Tools"),
            ("Tool selection dropdown", "Select Tool"),
            ("Post-Mortem in dropdown", "📋 Post-Mortem Analysis"),
            ("IP Masking in dropdown", "🔐 IP Masking"),
            ("Test Scenarios in dropdown", "🧪 Test Scenarios"),
            ("Tool display logic", "if st.session_state.selected_tool ==")
        ]
        
        for name, pattern in checks:
            if pattern in content:
                print(f"✓ {name} found")
            else:
                print(f"✗ {name} missing")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SIDEBAR TOOLS VERIFICATION")
    print("=" * 60)
    
    test_render_methods()
    test_sidebar_features()
    
    print("\n" + "=" * 60)
    print("INSTRUCTIONS TO TEST IN BROWSER:")
    print("=" * 60)
    print("1. Go to http://localhost:8501")
    print("2. Look at LEFT SIDEBAR (scroll down)")
    print("3. Find '🛠️ Additional Tools' section")
    print("4. Select a tool from dropdown")
    print("5. Tool content should appear BELOW the main tabs")
    print("=" * 60)
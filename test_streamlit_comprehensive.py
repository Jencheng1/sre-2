#!/usr/bin/env python3
"""Comprehensive test for Streamlit app functionality."""

import streamlit as st
import sys
import time
from streamlit_key_manager import key_manager

# Configure page
st.set_page_config(
    page_title="Streamlit Key Test",
    page_icon="🧪",
    layout="wide"
)

def test_duplicate_forms():
    """Test form key duplication issues."""
    st.header("🧪 Form Key Test")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Form 1")
        with st.form(key_manager.get_form_key("test_form", "col1")):
            name1 = st.text_input("Name")
            age1 = st.number_input("Age", min_value=0, max_value=120)
            submit1 = st.form_submit_button("Submit Form 1")
            
        if submit1:
            st.success(f"Form 1 submitted: {name1}, {age1}")
    
    with col2:
        st.subheader("Form 2")
        with st.form(key_manager.get_form_key("test_form", "col2")):
            name2 = st.text_input("Name")
            age2 = st.number_input("Age", min_value=0, max_value=120)
            submit2 = st.form_submit_button("Submit Form 2")
            
        if submit2:
            st.success(f"Form 2 submitted: {name2}, {age2}")

def test_loop_widgets():
    """Test widgets in loops."""
    st.header("🔁 Loop Widget Test")
    
    items = ["Item A", "Item B", "Item C"]
    
    for i, item in enumerate(items):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{item}**")
        
        with col2:
            if st.button("Edit", key=key_manager.get_loop_key("edit_btn", i)):
                st.info(f"Editing {item}")
        
        with col3:
            if st.button("Delete", key=key_manager.get_loop_key("delete_btn", i)):
                st.warning(f"Deleting {item}")

def test_tab_widgets():
    """Test widgets in tabs."""
    st.header("📑 Tab Widget Test")
    
    tabs = st.tabs(["Tab 1", "Tab 2", "Tab 3"])
    
    for i, tab in enumerate(tabs):
        with tab:
            st.subheader(f"Content for Tab {i+1}")
            
            # Text input with tab-specific key
            text_value = st.text_input(
                "Enter text:",
                key=key_manager.get_tab_key("text_input", f"tab{i+1}")
            )
            
            # Button with tab-specific key
            if st.button("Process", key=key_manager.get_tab_key("process_btn", f"tab{i+1}")):
                st.success(f"Processing: {text_value}")
            
            # Selectbox with tab-specific key
            option = st.selectbox(
                "Choose option:",
                ["Option A", "Option B", "Option C"],
                key=key_manager.get_tab_key("selectbox", f"tab{i+1}")
            )
            st.write(f"Selected: {option}")

def test_conditional_rendering():
    """Test conditional widget rendering."""
    st.header("🔀 Conditional Rendering Test")
    
    show_advanced = st.checkbox("Show advanced options")
    
    if show_advanced:
        col1, col2 = st.columns(2)
        
        with col1:
            # Use unique keys for conditionally rendered widgets
            param1 = st.slider(
                "Parameter 1",
                0, 100, 50,
                key=key_manager.get_unique_key("param1_slider", "advanced")
            )
        
        with col2:
            param2 = st.slider(
                "Parameter 2",
                0, 100, 50,
                key=key_manager.get_unique_key("param2_slider", "advanced")
            )
        
        if st.button("Apply", key=key_manager.get_unique_key("apply_btn", "advanced")):
            st.info(f"Applied: param1={param1}, param2={param2}")

def test_session_state_persistence():
    """Test session state persistence."""
    st.header("💾 Session State Test")
    
    # Initialize session state
    if 'counter' not in st.session_state:
        st.session_state.counter = 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Increment", key="increment_btn"):
            st.session_state.counter += 1
    
    with col2:
        if st.button("Decrement", key="decrement_btn"):
            st.session_state.counter -= 1
    
    with col3:
        if st.button("Reset", key="reset_btn"):
            st.session_state.counter = 0
    
    st.metric("Counter Value", st.session_state.counter)

def run_all_tests():
    """Run all tests."""
    st.title("🧪 Streamlit Widget Key Testing Suite")
    
    st.info("""
    This test suite verifies that all Streamlit widgets have unique keys
    and work correctly without duplication errors.
    """)
    
    # Reset keys for fresh test
    key_manager.reset_keys()
    
    # Run tests
    test_duplicate_forms()
    st.divider()
    
    test_loop_widgets()
    st.divider()
    
    test_tab_widgets()
    st.divider()
    
    test_conditional_rendering()
    st.divider()
    
    test_session_state_persistence()
    
    # Summary
    st.divider()
    st.success("✅ All tests completed! If you see this without errors, the key management is working correctly.")

def main():
    """Main function."""
    try:
        run_all_tests()
    except st.errors.DuplicateWidgetID as e:
        st.error(f"❌ Duplicate Widget ID Error: {e}")
        st.error("This indicates a key management issue that needs to be fixed.")
        return 1
    except Exception as e:
        st.error(f"❌ Unexpected Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Run the test app
    main()
#!/usr/bin/env python3
"""Debug button click issue in Streamlit."""

import streamlit as st
from streamlit_key_manager import key_manager
import time

# Test button with different configurations
st.set_page_config(page_title="Button Debug Test", layout="wide")

st.title("🔍 Button Click Debug Test")

# Test 1: Simple button
st.header("Test 1: Simple Button")
if st.button("Simple Test Button"):
    st.success("✅ Simple button clicked!")
    st.balloons()

# Test 2: Button with key
st.header("Test 2: Button with Static Key")
if st.button("Button with Key", key="test_button_2"):
    st.success("✅ Button with static key clicked!")

# Test 3: Button with dynamic key
st.header("Test 3: Button with Dynamic Key")
category = st.selectbox("Select Category", ["Category A", "Category B"])
button_type = st.selectbox("Select Type", ["Type 1", "Type 2", "Type 3"])

dynamic_key = key_manager.get_unique_key("dynamic_button", category, button_type)
st.write(f"Generated key: `{dynamic_key}`")

if st.button("Dynamic Key Button", key=dynamic_key):
    st.success(f"✅ Dynamic button clicked! Category: {category}, Type: {button_type}")

# Test 4: Button in sidebar
with st.sidebar:
    st.header("Sidebar Button Test")
    if st.button("Sidebar Button", key="sidebar_test"):
        st.success("✅ Sidebar button clicked!")

# Test 5: Button with spinner
st.header("Test 5: Button with Spinner")
if st.button("Button with Spinner", key="spinner_test"):
    with st.spinner("Processing..."):
        time.sleep(2)
    st.success("✅ Spinner button completed!")

# Test 6: Multiple buttons
st.header("Test 6: Multiple Buttons")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Button 1", key="multi_1"):
        st.success("Button 1 clicked!")

with col2:
    if st.button("Button 2", key="multi_2"):
        st.success("Button 2 clicked!")

with col3:
    if st.button("Button 3", key="multi_3"):
        st.success("Button 3 clicked!")

# Session state info
st.header("Session State Debug Info")
st.write("Session state keys:", list(st.session_state.keys()))

# Test the actual generate incident logic
st.header("Test 7: Incident Generation Logic")

incident_type = st.selectbox("Incident Type", ["Performance Degradation", "Security Alert", "Service Outage"])

if st.button("Test Generate Incident", type="primary", use_container_width=True, key="test_generate"):
    with st.spinner(f"Generating {incident_type} incident..."):
        time.sleep(1)
        
        # Simulate incident data
        incident_data = {
            'type': incident_type.lower().replace(' ', '_'),
            'ops_item_id': f'TEST-{int(time.time())}',
            'description': f'Test incident of type {incident_type}',
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        st.success(f"✅ Test incident generated! ID: {incident_data['ops_item_id']}")
        st.json(incident_data)

st.divider()
st.info("""
**Debug Instructions:**
1. Test each button above to see which ones work
2. Check if any error messages appear
3. Note which button configurations work vs don't work
4. The actual issue might be in the generate_incident method implementation
""")
#!/usr/bin/env python3
"""Minimal test to verify CPU spike functionality"""

import streamlit as st
import os
import sys

# Set environment
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import CPU spike generator
from cpu_spike_generator import CPUSpikeGenerator

# Create a minimal Streamlit app
st.title("CPU Spike Test")

# Initialize generator
if 'cpu_spike_gen' not in st.session_state:
    st.session_state.cpu_spike_gen = CPUSpikeGenerator()

cpu_spike_gen = st.session_state.cpu_spike_gen

# Get instances
with st.spinner("Fetching EC2 instances..."):
    try:
        instances = cpu_spike_gen.get_available_ec2_instances()
        st.success(f"✓ Found {len(instances)} EC2 instances")
    except Exception as e:
        st.error(f"Error: {str(e)}")
        instances = []

# Display results
if instances:
    st.write("EC2 Instances:")
    for inst in instances:
        st.write(f"- {inst['name']} ({inst['instance_id']}): SSM={inst['ssm_enabled']}")
    
    # Filter SSM instances
    ssm_instances = [i for i in instances if i['ssm_enabled']]
    st.info(f"SSM-enabled instances: {len(ssm_instances)}")
else:
    st.error("No EC2 instances found!")
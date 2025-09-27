#!/usr/bin/env python3
"""
SRE Copilot - Enhanced Root Cause Analysis Dashboard with CPU Spike Demo
"""

import streamlit as st
import boto3
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
import sys
import random
import requests
from botocore.exceptions import ClientError
from user_guide_content import get_all_guides, get_guide_titles
from streamlit_key_manager import key_manager
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)

# Add path for modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import CPU spike generator
from cpu_spike_generator import CPUSpikeGenerator

# Try importing existing modules
try:
    from feedback.feedback_system import FeedbackSystem
    from config.mcp_config import MCPConfigManager
    from enhanced_incident_scenarios import EnhancedIncidentScenarios
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP modules not available - running in standard mode")

# Import IP masking utility
try:
    from utils.ip_masker import IPMasker, mask_logs_for_llm
    IP_MASKING_AVAILABLE = True
except ImportError:
    IP_MASKING_AVAILABLE = False
    print("IP masking utility not available")

# Import post-mortem agent
try:
    from postmortem.postmortem_agent import PostMortemAgent, PostMortemReport
    from dataclasses import asdict
    POST_MORTEM_AVAILABLE = True
except ImportError:
    POST_MORTEM_AVAILABLE = False
    print("Post-mortem agent not available")

# Import existing streamlit app functionality
from streamlit_app import (
    IncidentGenerator, check_aws_credentials, get_correlation_data,
    run_supervisor_correlation, generate_timeline_chart, generate_metrics_chart,
    CUSTOM_CSS, init_session_state, display_incident_details, 
    display_correlation_results, get_related_components, get_knowledge_base_content,
    query_knowledge_base, add_to_knowledge_base
)

def render_cpu_spike_demo():
    """Render the CPU Spike Demo tab"""
    st.header("🚨 CPU Spike Demo")
    
    # Initialize CPU spike generator in session state to maintain persistence
    if 'cpu_spike_gen' not in st.session_state:
        st.session_state.cpu_spike_gen = CPUSpikeGenerator()
    
    cpu_spike_gen = st.session_state.cpu_spike_gen
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Real EC2 CPU Spike Generator
        
        This tool triggers **actual CPU spikes** on EC2 instances using AWS Systems Manager.
        - Select a target EC2 instance
        - Configure spike parameters
        - Monitor real-time metrics in Grafana
        - Automatically create OpsItem incidents
        - Trigger AI root cause analysis
        """)
    
    with col2:
        # Grafana link
        st.info("📊 **Grafana Dashboard**")
        st.markdown("[Open Grafana](http://localhost:3000) (admin/admin123)")
    
    # Get available EC2 instances
    with st.spinner("Fetching EC2 instances..."):
        try:
            instances = cpu_spike_gen.get_available_ec2_instances()
            if instances:
                st.success(f"Found {len(instances)} EC2 instances")
        except Exception as e:
            st.error(f"Error fetching EC2 instances: {str(e)}")
            logger.error(f"EC2 fetch error: {str(e)}", exc_info=True)
            return
    
    if not instances:
        st.error("No EC2 instances found or accessible")
        st.info("Please check:")
        st.info("• AWS credentials are configured")
        st.info("• You have ec2:DescribeInstances permission")
        st.info("• There are EC2 instances in us-east-1 region")
        return
    
    # Filter SSM-enabled instances
    ssm_instances = [i for i in instances if i['ssm_enabled']]
    
    if not ssm_instances:
        st.warning("No EC2 instances with SSM agent available")
        st.info("Please ensure SSM agent is installed and running on your EC2 instances")
        
        # Show all instances for reference
        st.subheader("Available EC2 Instances")
        df = pd.DataFrame(instances)
        st.dataframe(df)
        return
    
    # Instance selection
    st.subheader("🎯 Target Selection")
    
    instance_options = {f"{i['name']} ({i['instance_id']})": i for i in ssm_instances}
    selected_instance_key = st.selectbox(
        "Select EC2 Instance",
        options=list(instance_options.keys()),
        help="Only instances with SSM agent enabled are shown"
    )
    
    selected_instance = instance_options[selected_instance_key]
    
    # Show instance details
    with st.expander("Instance Details", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Instance Type", selected_instance['instance_type'])
        with col2:
            st.metric("Private IP", selected_instance['private_ip'])
        with col3:
            st.metric("State", selected_instance['state'])
    
    # CPU spike configuration
    st.subheader("⚡ Spike Configuration")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        cpu_percent = st.slider(
            "Target CPU %",
            min_value=10,
            max_value=100,
            value=80,
            step=10,
            help="Target CPU utilization percentage"
        )
    
    with col2:
        duration = st.slider(
            "Duration (seconds)",
            min_value=30,
            max_value=300,
            value=60,
            step=30,
            help="How long to sustain the spike"
        )
    
    with col3:
        cores = st.number_input(
            "CPU Cores",
            min_value=0,
            max_value=16,
            value=0,
            help="0 = all cores"
        )
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Trigger CPU Spike", type="primary", key="trigger_spike"):
            with st.spinner("Triggering CPU spike..."):
                result = cpu_spike_gen.trigger_cpu_spike(
                    instance_id=selected_instance['instance_id'],
                    duration_seconds=duration,
                    cpu_percent=cpu_percent,
                    cores=cores
                )
                
                if result['status'] == 'success':
                    st.success(f"✅ {result['message']}")
                    st.session_state['active_spike'] = {
                        'instance_id': selected_instance['instance_id'],
                        'command_id': result['command_id'],
                        'start_time': datetime.now(),
                        'duration': duration,
                        'cpu_percent': cpu_percent
                    }
                    
                    # Create OpsItem
                    with st.spinner("Creating OpsItem incident..."):
                        ops_item = create_cpu_spike_ops_item(
                            selected_instance['instance_id'],
                            selected_instance['name'],
                            cpu_percent
                        )
                        if ops_item:
                            st.session_state['spike_ops_item_id'] = ops_item['OpsItemId']
                            st.success(f"📋 Created OpsItem: {ops_item['OpsItemId']}")
                else:
                    st.error(f"❌ {result['message']}")
    
    with col2:
        if st.button("🛑 Stop CPU Spike", key="stop_spike"):
            if 'active_spike' in st.session_state:
                result = cpu_spike_gen.stop_cpu_spike(
                    instance_id=st.session_state['active_spike']['instance_id']
                )
                if result['status'] == 'success':
                    st.success("✅ CPU spike stopped")
                    del st.session_state['active_spike']
                else:
                    st.error(f"❌ {result['message']}")
            else:
                st.info("No active spike to stop")
    
    with col3:
        if st.button("🔍 Run Root Cause Analysis", key="run_rca"):
            if 'spike_ops_item_id' in st.session_state:
                with st.spinner("Running AI root cause analysis..."):
                    # Trigger supervisor lambda
                    correlation_data = run_supervisor_correlation(
                        st.session_state['spike_ops_item_id']
                    )
                    
                    if correlation_data and correlation_data.get('statusCode') == 200:
                        st.session_state['spike_correlation_data'] = correlation_data
                        st.success("✅ Root cause analysis complete")
                    else:
                        st.error("Failed to run root cause analysis")
            else:
                st.warning("Please trigger a CPU spike first")
    
    # Monitor active spike
    if 'active_spike' in st.session_state:
        st.subheader("📊 Active Spike Monitoring")
        
        spike_info = st.session_state['active_spike']
        elapsed = (datetime.now() - spike_info['start_time']).total_seconds()
        remaining = max(0, spike_info['duration'] - elapsed)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Target CPU", f"{spike_info['cpu_percent']}%")
        with col2:
            st.metric("Elapsed Time", f"{int(elapsed)}s")
        with col3:
            st.metric("Remaining", f"{int(remaining)}s")
        
        # Progress bar
        progress = min(1.0, elapsed / spike_info['duration'])
        st.progress(progress)
        
        # Get command status
        if st.button("🔄 Check Status"):
            status = cpu_spike_gen.monitor_cpu_spike(
                instance_id=spike_info['instance_id'],
                command_id=spike_info['command_id']
            )
            
            st.json(status)
    
    # Display metrics
    st.subheader("📈 CPU Metrics")
    
    # Refresh metrics button
    if st.button("🔄 Refresh Metrics"):
        st.rerun()
    
    # Get recent CPU metrics
    with st.spinner("Loading CPU metrics..."):
        metrics = cpu_spike_gen.get_cpu_metrics(
            instance_id=selected_instance['instance_id'],
            minutes=15
        )
    
    if metrics:
        # Create metrics chart
        df = pd.DataFrame(metrics)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['Average'],
            mode='lines+markers',
            name='Average CPU',
            line=dict(color='blue', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['Maximum'],
            mode='lines+markers',
            name='Max CPU',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # Add threshold line
        fig.add_hline(y=80, line_dash="dot", line_color="orange",
                     annotation_text="Alert Threshold (80%)")
        
        fig.update_layout(
            title="EC2 CPU Utilization",
            xaxis_title="Time",
            yaxis_title="CPU %",
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Metrics table
        with st.expander("Raw Metrics Data"):
            st.dataframe(df)
    
    # Display correlation results if available
    if 'spike_correlation_data' in st.session_state:
        st.subheader("🤖 AI Root Cause Analysis Results")
        
        correlation_data = st.session_state['spike_correlation_data']
        body = json.loads(correlation_data.get('body', '{}'))
        
        if 'analysis' in body:
            analysis = body['analysis']
            
            # Root cause
            st.markdown("### 🎯 Root Cause")
            st.info(analysis.get('root_cause', 'Unknown'))
            
            # Impact
            st.markdown("### 💥 Impact")
            st.warning(analysis.get('impact', 'Unknown'))
            
            # Recommendations
            st.markdown("### 💡 Recommendations")
            for rec in analysis.get('recommendations', []):
                st.markdown(f"- {rec}")
            
            # Knowledge base results
            if 'knowledge_base_results' in body:
                st.markdown("### 📚 Related Knowledge Base Articles")
                kb_results = body['knowledge_base_results']
                
                if kb_results:
                    for kb in kb_results[:3]:
                        with st.expander(f"{kb.get('title', 'Article')} (Score: {kb.get('score', 0):.2f})"):
                            st.markdown(kb.get('content', 'No content'))
                            if 'resolution' in kb:
                                st.markdown("**Resolution:**")
                                st.code(kb['resolution'])
                else:
                    st.info("No related articles found")
    
    # Historical incidents
    st.subheader("📜 Historical CPU Spike Incidents")
    
    if st.button("🔍 Search Similar Incidents"):
        with st.spinner("Searching knowledge base..."):
            similar_incidents = query_knowledge_base(
                f"CPU spike high utilization {selected_instance['instance_type']}"
            )
            
            if similar_incidents:
                for incident in similar_incidents[:5]:
                    with st.expander(f"{incident.get('title', 'Incident')} - {incident.get('date', 'Unknown')}"):
                        st.markdown(f"**Description:** {incident.get('description', 'N/A')}")
                        st.markdown(f"**Root Cause:** {incident.get('root_cause', 'N/A')}")
                        if 'resolution' in incident:
                            st.markdown("**Resolution:**")
                            st.code(incident['resolution'])
            else:
                st.info("No similar incidents found")


def create_cpu_spike_ops_item(instance_id, instance_name, cpu_percent):
    """Create an OpsItem for CPU spike incident"""
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        
        response = ssm.create_ops_item(
            Title=f"High CPU Alert - {instance_name}",
            Description=f"CPU utilization spike detected on EC2 instance {instance_name} ({instance_id}). Current CPU: {cpu_percent}%",
            Source="SRE-Copilot-CPU-Demo",
            Severity="2",  # High severity
            Category="Performance",
            OperationalData={
                "/aws/resources": {
                    "Value": json.dumps([{
                        "arn": f"arn:aws:ec2:us-east-1::{instance_id}"
                    }])
                },
                "InstanceId": {"Value": instance_id},
                "InstanceName": {"Value": instance_name},
                "CPUPercent": {"Value": str(cpu_percent)},
                "IncidentType": {"Value": "cpu-spike"},
                "GeneratedBy": {"Value": "CPU-Spike-Demo"}
            }
        )
        
        return response
        
    except Exception as e:
        st.error(f"Failed to create OpsItem: {str(e)}")
        return None


def main():
    st.set_page_config(
        page_title="SRE Copilot - CPU Spike Demo",
        page_icon="🚨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Initialize session state
    init_session_state()
    
    # Check AWS credentials
    if not check_aws_credentials():
        st.error("AWS credentials not found. Please configure AWS credentials.")
        return
    
    # Sidebar
    with st.sidebar:
        st.title("🚨 SRE Copilot")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["Incident Management", "CPU Spike Demo", "Knowledge Base", "Analytics", "User Guide"]
        )
        
        # AWS Region
        st.markdown("---")
        st.info(f"🌎 Region: us-east-1")
    
    # Main content based on selection
    if page == "CPU Spike Demo":
        render_cpu_spike_demo()
    elif page == "Incident Management":
        # Import and render existing incident management
        from streamlit_app import main as original_main
        # This would need refactoring to extract the incident management logic
        st.info("Please use the original streamlit_app.py for full incident management")
    elif page == "Knowledge Base":
        # Knowledge base functionality
        st.header("📚 Knowledge Base")
        st.info("Knowledge base functionality available in main app")
    elif page == "Analytics":
        # Analytics functionality
        st.header("📊 Analytics")
        st.info("Analytics functionality available in main app")
    elif page == "User Guide":
        # User guide
        st.header("📖 User Guide")
        st.info("User guide available in main app")


if __name__ == "__main__":
    main()
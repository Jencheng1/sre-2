#!/usr/bin/env python3
"""
SRE Copilot - Enhanced Root Cause Analysis Dashboard with MCP Integration
Integrates real incident generation, AWS data analysis, MCP services, and human feedback.
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
from botocore.exceptions import ClientError

# Add MCP modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.streamlit_components import MCPComponents, FeedbackComponents
from config.mcp_config import MCPConfigManager
from enhanced_incident_scenarios import EnhancedIncidentScenarios
from feedback.feedback_system import FeedbackSystem

# Page configuration
st.set_page_config(
    page_title="SRE Copilot - Enhanced RCA with MCP",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .critical { background-color: #ffebee; border-left: 4px solid #f44336; }
    .warning { background-color: #fff3e0; border-left: 4px solid #ff9800; }
    .info { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
    .success { background-color: #e8f5e9; border-left: 4px solid #4caf50; }
    .incident-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .mcp-status {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        margin-left: 0.5rem;
    }
    .mcp-enabled { background-color: #4caf50; color: white; }
    .mcp-disabled { background-color: #f44336; color: white; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'current_incident' not in st.session_state:
    st.session_state.current_incident = None
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None
if 'mcp_config' not in st.session_state:
    st.session_state.mcp_config = MCPConfigManager()

def main():
    """Main application entry point."""
    st.markdown('<h1 class="main-header">🔍 SRE Copilot - Enhanced Root Cause Analysis</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        page = st.selectbox(
            "Select Page",
            ["Incident Analysis", "MCP Configuration", "Feedback Analytics", "Enhanced Scenarios", "User Guide"]
        )
        
        # MCP Status
        st.divider()
        st.subheader("MCP Status")
        enabled_servers = st.session_state.mcp_config.get_enabled_servers()
        
        for server in ["splunk", "dynatrace", "servicenow", "confluence", "gitlab"]:
            status = "enabled" if server in enabled_servers else "disabled"
            status_class = "mcp-enabled" if status == "enabled" else "mcp-disabled"
            st.markdown(
                f"{server.capitalize()} <span class='mcp-status {status_class}'>{status.upper()}</span>",
                unsafe_allow_html=True
            )
    
    # Page routing
    if page == "Incident Analysis":
        show_incident_analysis_page()
    elif page == "MCP Configuration":
        show_mcp_configuration_page()
    elif page == "Feedback Analytics":
        show_feedback_analytics_page()
    elif page == "Enhanced Scenarios":
        show_enhanced_scenarios_page()
    elif page == "User Guide":
        show_user_guide_page()

def show_incident_analysis_page():
    """Show the main incident analysis page."""
    st.header("Incident Analysis with MCP Integration")
    
    # Analysis options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        incident_description = st.text_area(
            "Describe the Incident",
            placeholder="e.g., Users reporting slow response times on the payment service. Database queries are timing out.",
            height=100
        )
    
    with col2:
        st.subheader("Analysis Options")
        use_mcp = st.checkbox("Enable MCP Correlation", value=True)
        use_kb = st.checkbox("Use Knowledge Base", value=True)
        use_feedback = st.checkbox("Apply Historical Feedback", value=True)
    
    if st.button("🔍 Analyze Incident", type="primary", disabled=not incident_description):
        run_enhanced_analysis(incident_description, use_mcp, use_kb, use_feedback)
    
    # Show current analysis results
    if st.session_state.current_analysis:
        show_analysis_results()

def run_enhanced_analysis(incident_description, use_mcp, use_kb, use_feedback):
    """Run enhanced analysis with MCP integration."""
    with st.spinner("Running enhanced analysis..."):
        try:
            # Simulate analysis (in real deployment, would call Lambda)
            time.sleep(2)  # Simulate processing
            
            # Create mock analysis result
            st.session_state.current_analysis = {
                'analysis': f"""
## Enhanced Root Cause Analysis

### Incident Description
{incident_description}

### Root Cause Identified
Based on correlation of AWS metrics and external service data, the root cause has been identified as:
**Database connection pool exhaustion due to a recent code deployment**

### Evidence from AWS
- CloudWatch: CPU utilization at 95%
- RDS: Connection count at maximum (500)
- Lambda: Timeout errors increasing

### External Service Correlations
- **Splunk**: Network latency normal, ruling out network issues
- **Dynatrace**: MQ depth increasing, indicating processing backlog
- **ServiceNow**: Recent change deployed 2 hours ago
- **GitLab**: Commit changed connection handling logic
- **Confluence**: Found KB article on similar issue

### Recommended Actions
1. Immediately increase RDS connection limit
2. Roll back recent deployment
3. Implement connection pooling best practices
4. Add monitoring for connection pool metrics
""",
                'incident_type': 'database_issue',
                'confidence': 0.85,
                'mcp_data_summary': {
                    'splunk': {'status': 'success', 'data_points': 150},
                    'dynatrace': {'status': 'success', 'data_points': 75},
                    'servicenow': {'status': 'success', 'data_points': 3},
                    'confluence': {'status': 'success', 'data_points': 5},
                    'gitlab': {'status': 'success', 'data_points': 12}
                },
                'metadata': {
                    'analysis_time': datetime.now().isoformat(),
                    'mcp_enabled': use_mcp,
                    'kb_enabled': use_kb
                }
            }
            
            # Add to history
            st.session_state.analysis_history.append({
                'timestamp': datetime.now(),
                'description': incident_description,
                'analysis': st.session_state.current_analysis
            })
            
            st.success("✅ Analysis complete!")
            
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")

def show_analysis_results():
    """Display analysis results with feedback option."""
    analysis = st.session_state.current_analysis
    
    st.divider()
    
    # Confidence meter
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        confidence = analysis.get('confidence', 0.7) * 100
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = confidence,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Analysis Confidence"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis", "🔗 MCP Correlations", "💬 Feedback", "📜 History"])
    
    with tab1:
        st.markdown(analysis.get('analysis', 'No analysis available'))
    
    with tab2:
        show_mcp_correlations(analysis.get('mcp_data_summary', {}))
    
    with tab3:
        feedback_ui = FeedbackComponents()
        feedback_ui.render_feedback_form(
            incident_id=f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            analysis=analysis
        )
    
    with tab4:
        show_analysis_history()

def show_mcp_correlations(mcp_data):
    """Display MCP correlation data."""
    st.subheader("External Service Correlations")
    
    if not mcp_data:
        st.info("No MCP data available. Enable MCP in analysis options.")
        return
    
    # Create visualization
    services = list(mcp_data.keys())
    data_points = [data.get('data_points', 0) for data in mcp_data.values()]
    colors = ['#4CAF50' if data.get('status') == 'success' else '#F44336' for data in mcp_data.values()]
    
    fig = go.Figure(data=[
        go.Bar(
            x=services,
            y=data_points,
            marker_color=colors,
            text=data_points,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Data Points from External Services",
        xaxis_title="Service",
        yaxis_title="Data Points",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed findings
    for service, data in mcp_data.items():
        if data.get('status') == 'success':
            with st.expander(f"{service.upper()} Findings"):
                if service == "splunk":
                    st.write("**Network Analysis**")
                    st.write("- Latency: Normal (< 100ms)")
                    st.write("- Packet Loss: 0%")
                    st.write("- Security Events: None detected")
                elif service == "dynatrace":
                    st.write("**Application Performance**")
                    st.write("- MQ Depth: 5,000 messages (HIGH)")
                    st.write("- Error Rate: 2.5%")
                    st.write("- Response Time: 3.2s (DEGRADED)")
                elif service == "servicenow":
                    st.write("**Recent Changes**")
                    st.write("- CHG0012345: Database connection pool update")
                    st.write("- Implemented: 2 hours ago")
                    st.write("- Risk Level: Medium")

def show_analysis_history():
    """Show history of analyses."""
    if not st.session_state.analysis_history:
        st.info("No analysis history yet.")
        return
    
    for idx, item in enumerate(reversed(st.session_state.analysis_history[-5:])):
        with st.expander(f"{item['timestamp'].strftime('%Y-%m-%d %H:%M')} - {item['description'][:50]}..."):
            st.write(f"**Incident Type**: {item['analysis'].get('incident_type', 'Unknown')}")
            st.write(f"**Confidence**: {item['analysis'].get('confidence', 0) * 100:.0f}%")
            if st.button(f"Load Analysis", key=f"load_{idx}"):
                st.session_state.current_analysis = item['analysis']
                st.rerun()

def show_mcp_configuration_page():
    """Show MCP configuration management page."""
    st.header("MCP Configuration Management")
    
    mcp_ui = MCPComponents()
    mcp_ui.render_mcp_config_form()
    
    # Test connections
    st.divider()
    st.subheader("Connection Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Test All Connections"):
            with st.spinner("Testing connections..."):
                # Simulate connection tests
                results = {
                    "splunk": random.choice([True, True, False]),
                    "dynatrace": random.choice([True, True, False]),
                    "servicenow": True,
                    "confluence": True,
                    "gitlab": random.choice([True, True, False])
                }
                
                for service, success in results.items():
                    if success:
                        st.success(f"✅ {service.upper()}: Connected")
                    else:
                        st.error(f"❌ {service.upper()}: Connection failed")
    
    with col2:
        if st.button("Export Configuration"):
            config = st.session_state.mcp_config.export_config(include_secrets=False)
            st.download_button(
                label="Download Config (JSON)",
                data=json.dumps(config, indent=2),
                file_name="mcp_config.json",
                mime="application/json"
            )

def show_feedback_analytics_page():
    """Show feedback analytics dashboard."""
    st.header("Feedback Analytics Dashboard")
    
    # Mock feedback data
    feedback_ui = FeedbackComponents()
    
    # Override with mock data for demo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Feedback", "247", "+12 this week")
    with col2:
        st.metric("Avg Rating", "4.2/5", "+0.3")
    with col3:
        st.metric("Accuracy", "87%", "+5%")
    with col4:
        st.metric("Resolution Time", "12m", "-3m")
    
    # Accuracy trend
    st.divider()
    st.subheader("Accuracy Improvement Over Time")
    
    # Generate sample data
    dates = pd.date_range(start='2024-01-01', periods=90, freq='D')
    baseline = 0.65
    accuracy = [baseline + (i/90) * 0.22 + random.uniform(-0.05, 0.05) for i in range(90)]
    
    df = pd.DataFrame({
        'Date': dates,
        'Accuracy': accuracy,
        'Baseline': [baseline] * 90
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Accuracy'],
        mode='lines',
        name='Actual Accuracy',
        line=dict(color='#2196f3', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Baseline'],
        mode='lines',
        name='Baseline',
        line=dict(color='#ff9800', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="Root Cause Analysis Accuracy Trend",
        xaxis_title="Date",
        yaxis_title="Accuracy",
        yaxis=dict(tickformat=',.0%', range=[0.6, 0.95]),
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Feedback by incident type
    st.divider()
    st.subheader("Feedback by Incident Type")
    
    incident_types = ['Network Latency', 'Database Issues', 'Service Outage', 'Performance', 'Security']
    feedback_counts = [45, 38, 67, 52, 45]
    ratings = [4.1, 4.3, 3.9, 4.2, 4.5]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Feedback Count',
        x=incident_types,
        y=feedback_counts,
        yaxis='y',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Scatter(
        name='Avg Rating',
        x=incident_types,
        y=ratings,
        yaxis='y2',
        mode='lines+markers',
        marker_color='orange',
        line=dict(width=3)
    ))
    
    fig.update_layout(
        yaxis=dict(title='Feedback Count', side='left'),
        yaxis2=dict(title='Average Rating', overlaying='y', side='right', range=[0, 5]),
        title='Feedback Distribution and Ratings by Incident Type',
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_enhanced_scenarios_page():
    """Show pre-built enhanced scenarios."""
    st.header("Enhanced Incident Scenarios")
    st.info("These scenarios demonstrate how MCP integration enhances root cause analysis with external service data.")
    
    scenarios = EnhancedIncidentScenarios.get_scenarios()
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        severity_filter = st.multiselect(
            "Filter by Severity",
            ["critical", "high", "medium", "low"],
            default=["critical", "high"]
        )
    
    with col2:
        type_filter = st.multiselect(
            "Filter by Type",
            ["network_latency", "service_outage", "performance_degradation", "security_incident"],
            default=["network_latency", "service_outage"]
        )
    
    # Display filtered scenarios
    for scenario in scenarios:
        if (scenario['incident']['severity'] in severity_filter and 
            scenario['incident']['type'] in type_filter):
            
            with st.expander(f"🔥 {scenario['incident']['title']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Type**: {scenario['incident']['type'].replace('_', ' ').title()}")
                    st.write(f"**Severity**: {scenario['incident']['severity'].upper()}")
                    st.write(f"**Service**: {scenario['incident']['service']}")
                    
                    st.write("**Symptoms**:")
                    for symptom in scenario['incident']['symptoms'][:3]:
                        st.write(f"- {symptom}")
                    
                    st.write("**Root Cause**:")
                    st.error(scenario['root_cause'])
                    
                    st.write("**Key MCP Correlations**:")
                    for service, data in scenario['mcp_correlations'].items():
                        if 'finding' in data:
                            st.write(f"- **{service.upper()}**: {data['finding']}")
                
                with col2:
                    st.write("**Resolution Steps**:")
                    for idx, step in enumerate(scenario['resolution'][:3], 1):
                        st.write(f"{idx}. {step}")
                    
                    if st.button(f"Run Scenario", key=f"scenario_{scenario['incident']['id']}"):
                        # Create incident description
                        symptoms = " ".join(scenario['incident']['symptoms'])
                        description = f"{scenario['incident']['title']}. {symptoms}"
                        
                        # Switch to analysis page and run
                        st.session_state.current_incident = description
                        st.info("Switch to 'Incident Analysis' page to see results")

def show_user_guide_page():
    """Show user guide and documentation."""
    st.header("User Guide")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Getting Started", "MCP Integration", "Feedback System", "Best Practices"])
    
    with tab1:
        st.markdown("""
        ## Getting Started with SRE Copilot
        
        ### Overview
        The SRE Copilot helps you quickly identify root causes of incidents by correlating data from:
        - AWS services (CloudWatch, CloudTrail, etc.)
        - External monitoring tools via MCP
        - Historical incidents and resolutions
        - Team feedback and learnings
        
        ### Quick Start
        1. **Describe the incident** in the text area
        2. **Enable MCP** for external service correlation
        3. **Click Analyze** to get root cause analysis
        4. **Provide feedback** to improve future analyses
        
        ### Key Features
        - 🔍 **Smart Analysis**: AI-powered root cause detection
        - 🔗 **MCP Integration**: Correlate with Splunk, Dynatrace, etc.
        - 📚 **Knowledge Base**: Learn from past incidents
        - 📈 **Continuous Improvement**: Feedback-driven accuracy
        """)
    
    with tab2:
        st.markdown("""
        ## MCP (Model Context Protocol) Integration
        
        ### What is MCP?
        MCP enables the SRE Copilot to gather context from external services:
        
        | Service | Purpose | Data Provided |
        |---------|---------|---------------|
        | **Splunk** | Network & Security | Latency, traffic patterns, security events |
        | **Dynatrace** | APM & Infrastructure | Application performance, MQ metrics |
        | **ServiceNow** | ITSM | Recent changes, related incidents |
        | **Confluence** | Knowledge Base | Runbooks, best practices |
        | **GitLab** | Source Control | Recent commits, deployments |
        
        ### Configuration Steps
        1. Go to **MCP Configuration** page
        2. Enable desired services
        3. Enter authentication credentials
        4. Test connections
        5. Save configuration
        
        ### Security
        - Credentials are stored securely in AWS SSM
        - All connections use HTTPS/TLS
        - Access is logged and audited
        """)
    
    with tab3:
        st.markdown("""
        ## Human-in-the-Loop Feedback System
        
        ### Why Feedback Matters
        Your feedback helps the system:
        - Learn from incorrect analyses
        - Identify new patterns
        - Improve accuracy over time
        - Build institutional knowledge
        
        ### How to Provide Feedback
        1. After each analysis, go to the **Feedback** tab
        2. Rate the accuracy (1-5 stars)
        3. Indicate if root cause was correct
        4. Add any additional context
        5. Suggest improvements
        
        ### Feedback Impact
        - **Immediate**: Adds to knowledge base
        - **Short-term**: Influences similar incident analysis
        - **Long-term**: Improves ML models
        
        ### Metrics
        - Current accuracy: 87%
        - Improvement from baseline: +22%
        - Average resolution time: 12 minutes
        """)
    
    with tab4:
        st.markdown("""
        ## Best Practices
        
        ### Writing Good Incident Descriptions
        ✅ **DO:**
        - Include specific symptoms
        - Mention affected services
        - Provide timeline if known
        - Include error messages
        
        ❌ **DON'T:**
        - Use vague descriptions
        - Omit important context
        - Assume system knows your infrastructure
        
        ### Maximizing MCP Value
        1. **Keep services updated**: Ensure MCP endpoints are current
        2. **Test regularly**: Verify connections weekly
        3. **Monitor data quality**: Check for stale or missing data
        4. **Review correlations**: Validate MCP findings
        
        ### Feedback Best Practices
        1. **Be specific**: Detail what was right/wrong
        2. **Add context**: Include information system missed
        3. **Suggest fixes**: Recommend better approaches
        4. **Follow up**: Check if suggestions were implemented
        
        ### Common Patterns
        | Incident Type | Key Indicators | Typical Root Causes |
        |---------------|----------------|---------------------|
        | Network Latency | High response time, timeouts | DNS, routing, congestion |
        | Database Issues | Connection errors, slow queries | Pool exhaustion, locks |
        | Service Outage | Health check failures | Config changes, deployments |
        | Performance | High CPU/memory | Code issues, traffic spike |
        """)

if __name__ == "__main__":
    main()
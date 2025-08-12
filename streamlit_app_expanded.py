#!/usr/bin/env python3
"""
SRE Copilot - Expanded Root Cause Analysis Dashboard with Defect Management Integration
Preserves all original functionality and adds comprehensive defect management capabilities.
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

# Add path for modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import original modules
try:
    from user_guide_content import get_all_guides, get_guide_titles
    from streamlit_key_manager import key_manager
    ORIGINAL_MODULES_AVAILABLE = True
except ImportError:
    ORIGINAL_MODULES_AVAILABLE = False

# Import MCP modules 
try:
    from feedback.feedback_system import FeedbackSystem
    from config.mcp_config import MCPConfigManager
    from enhanced_incident_scenarios import EnhancedIncidentScenarios
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP modules not available - running in standard mode")

# Import defect management modules
try:
    from defect_driven_incident_scenarios import DefectDrivenIncidentScenarios
    from defect_incident_correlator import DefectIncidentCorrelator
    from defect_management_ui import DefectManagementUI
    DEFECT_MANAGEMENT_AVAILABLE = True
except ImportError:
    DEFECT_MANAGEMENT_AVAILABLE = False
    print("Defect management modules not available")

# Load MCP ports configuration (expanded with defect management)
try:
    with open('mcp_ports.json', 'r') as f:
        MCP_PORTS = json.load(f)
except:
    MCP_PORTS = {
        'splunk': 9080,
        'dynatrace': 9081,
        'servicenow': 9082,
        'confluence': 9083,
        'gitlab': 9084,
        'alm_octane': 9085,  # NEW
        'jira': 9086         # NEW
    }

# Page configuration
st.set_page_config(
    page_title="SRE Copilot - Expanded Root Cause Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS (preserves original + adds defect management styles)
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
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .mcp-online { background-color: #4caf50; }
    .mcp-offline { background-color: #f44336; }
    .mcp-warning { background-color: #ff9800; }
    .feedback-section {
        background-color: #f5f5f5;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    /* NEW: Defect Management Styles */
    .defect-card {
        background-color: #fff9c4;
        border: 1px solid #f57f17;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .correlation-gauge {
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .correlation-high { background-color: #c8e6c9; }
    .correlation-medium { background-color: #fff3e0; }
    .correlation-low { background-color: #ffcdd2; }
    .causation-type {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.2rem;
    }
    .causation-defect { background-color: #ffecb3; color: #e65100; }
    .causation-change { background-color: #e1bee7; color: #4a148c; }
    .causation-system { background-color: #ffcdd2; color: #c62828; }
    .causation-infra { background-color: #c8e6c9; color: #2e7d32; }
    .defect-status {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 0.3rem;
        font-size: 0.7rem;
        font-weight: bold;
    }
    .status-open { background-color: #ffcdd2; color: #d32f2f; }
    .status-progress { background-color: #fff3e0; color: #f57c00; }
    .status-resolved { background-color: #c8e6c9; color: #388e3c; }
</style>
""", unsafe_allow_html=True)

def init_aws_clients():
    """Initialize AWS clients with region"""
    try:
        region = 'us-east-1'
        return {
            'lambda': boto3.client('lambda', region_name=region),
            'cloudwatch': boto3.client('cloudwatch', region_name=region),
            'logs': boto3.client('logs', region_name=region),
            'ssm': boto3.client('ssm', region_name=region),
            'vpc': boto3.client('ec2', region_name=region),
            'bedrock': boto3.client('bedrock-runtime', region_name=region)
        }
    except Exception as e:
        st.error(f"Failed to initialize AWS clients: {str(e)}")
        st.info("Note: AWS clients are optional for some functionality")
        return None

def check_defect_management_status():
    """Check status of defect management MCP servers"""
    status = {}
    
    # Check ALM Octane
    try:
        response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects", timeout=2)
        status['alm_octane'] = {
            'status': 'online' if response.status_code == 200 else 'offline',
            'defect_count': len(response.json()) if response.status_code == 200 else 0
        }
    except:
        status['alm_octane'] = {'status': 'offline', 'defect_count': 0}
    
    # Check Jira
    try:
        response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/issues", timeout=2)
        status['jira'] = {
            'status': 'online' if response.status_code == 200 else 'offline',
            'issue_count': len(response.json()) if response.status_code == 200 else 0
        }
    except:
        status['jira'] = {'status': 'offline', 'issue_count': 0}
    
    return status

def get_defect_correlation_data(incident_description, incident_type="general"):
    """Get defect correlation analysis for an incident"""
    if not DEFECT_MANAGEMENT_AVAILABLE:
        return {'error': 'Defect management not available'}
    
    try:
        # Initialize correlator with MCP endpoints
        mcp_endpoints = {
            'alm_octane': f"http://localhost:{MCP_PORTS['alm_octane']}",
            'jira': f"http://localhost:{MCP_PORTS['jira']}"
        }
        
        correlator = DefectIncidentCorrelator(mcp_endpoints)
        
        # Create incident data
        incident_data = {
            'incident_id': f"INC-{int(time.time())}",
            'title': incident_description[:100],
            'description': incident_description,
            'severity': 'High',
            'affected_services': ['general'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Run correlation analysis
        correlation_results = correlator.correlate_incident_with_defects(incident_data)
        summary = correlator.generate_correlation_summary(correlation_results)
        
        return {
            'correlation_results': correlation_results,
            'summary': summary,
            'total_correlations': summary.get('total_correlations', 0),
            'highest_correlation': summary.get('highest_correlation', 0.0),
            'defect_likelihood': summary.get('defect_likelihood', 'Low'),
            'recommended_actions': summary.get('recommended_actions', [])
        }
        
    except Exception as e:
        return {'error': str(e)}

def render_defect_correlation_section(incident_description):
    """Render defect correlation analysis section"""
    st.subheader("🔗 Defect Correlation Analysis")
    
    if not DEFECT_MANAGEMENT_AVAILABLE:
        st.warning("Defect management modules not available")
        return
    
    # Get correlation data
    with st.spinner("Analyzing incident for defect correlations..."):
        correlation_data = get_defect_correlation_data(incident_description)
    
    if 'error' in correlation_data:
        st.error(f"Correlation analysis failed: {correlation_data['error']}")
        return
    
    # Display correlation summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Correlations", correlation_data.get('total_correlations', 0))
    
    with col2:
        correlation_score = correlation_data.get('highest_correlation', 0.0)
        score_color = "🟢" if correlation_score >= 0.7 else "🟡" if correlation_score >= 0.4 else "🔴"
        st.metric("Highest Correlation", f"{score_color} {correlation_score:.1%}")
    
    with col3:
        likelihood = correlation_data.get('defect_likelihood', 'Low')
        st.metric("Defect Likelihood", likelihood)
    
    # Display correlation gauge
    if correlation_score > 0:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = correlation_score * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Correlation Strength"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgray"},
                    {'range': [30, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Display recommendations
    if correlation_data.get('recommended_actions'):
        st.subheader("💡 Recommendations")
        for action in correlation_data['recommended_actions'][:5]:
            st.markdown(f"• {action}")

def render_causation_analysis(incident_description):
    """Render multi-factor causation analysis"""
    st.subheader("🎯 Root Cause Categorization")
    
    # Analyze incident for different causation types
    causation_types = analyze_incident_causation(incident_description)
    
    # Display causation types as badges
    st.markdown("**Probable Causation Types:**")
    causation_html = ""
    for causation, probability in causation_types.items():
        if probability > 0.3:  # Show only likely causations
            css_class = f"causation-{causation.lower().replace(' ', '-').replace('_', '-')}"
            causation_html += f'<span class="causation-type {css_class}">{causation}: {probability:.1%}</span>'
    
    st.markdown(causation_html, unsafe_allow_html=True)
    
    # Detailed analysis tabs
    causation_tabs = st.tabs(["🐛 Defect-Caused", "🔧 Change-Caused", "🏗️ System Issues", "📊 Analysis Summary"])
    
    with causation_tabs[0]:
        render_defect_caused_analysis(incident_description, causation_types)
    
    with causation_tabs[1]:
        render_change_caused_analysis(incident_description, causation_types)
    
    with causation_tabs[2]:
        render_system_issues_analysis(incident_description, causation_types)
    
    with causation_tabs[3]:
        render_causation_summary(causation_types)

def analyze_incident_causation(incident_description):
    """Analyze incident for different causation types"""
    causation_keywords = {
        'Defect': ['bug', 'defect', 'error', 'exception', 'crash', 'failure', 'regression', 'broken'],
        'Change': ['deployment', 'release', 'update', 'configuration', 'change', 'migrate', 'upgrade'],
        'System': ['outage', 'down', 'unavailable', 'timeout', 'performance', 'slow', 'capacity'],
        'Infrastructure': ['network', 'server', 'hardware', 'disk', 'memory', 'cpu', 'storage'],
        'Security': ['breach', 'attack', 'unauthorized', 'security', 'vulnerability', 'exploit']
    }
    
    causation_scores = {}
    total_words = len(incident_description.lower().split())
    
    for causation, keywords in causation_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in incident_description.lower():
                score += 1
        causation_scores[causation] = min(score / len(keywords) * 2, 1.0)  # Normalize to 0-1
    
    return causation_scores

def render_defect_caused_analysis(incident_description, causation_types):
    """Render defect-caused incident analysis"""
    st.markdown("### 🐛 Defect-Related Root Cause Analysis")
    
    defect_probability = causation_types.get('Defect', 0.0)
    
    if defect_probability > 0.5:
        st.success(f"High probability ({defect_probability:.1%}) this incident is defect-related")
        render_defect_correlation_section(incident_description)
    elif defect_probability > 0.2:
        st.warning(f"Moderate probability ({defect_probability:.1%}) this incident is defect-related")
        render_defect_correlation_section(incident_description)
    else:
        st.info(f"Low probability ({defect_probability:.1%}) this incident is defect-related")
        st.markdown("**Consider checking:**")
        st.markdown("- Recent code deployments")
        st.markdown("- Application error logs")
        st.markdown("- Known defects in affected components")

def render_change_caused_analysis(incident_description, causation_types):
    """Render change-caused incident analysis"""
    st.markdown("### 🔧 Change-Related Root Cause Analysis")
    
    change_probability = causation_types.get('Change', 0.0)
    
    if change_probability > 0.5:
        st.success(f"High probability ({change_probability:.1%}) this incident is change-related")
        render_recent_changes_analysis()
    elif change_probability > 0.2:
        st.warning(f"Moderate probability ({change_probability:.1%}) this incident is change-related")
        render_recent_changes_analysis()
    else:
        st.info(f"Low probability ({change_probability:.1%}) this incident is change-related")
        st.markdown("**Consider checking:**")
        st.markdown("- Recent deployments or releases")
        st.markdown("- Configuration changes")
        st.markdown("- Infrastructure modifications")

def render_recent_changes_analysis():
    """Render recent changes analysis"""
    st.markdown("**Recent Changes Analysis:**")
    
    # Mock recent changes data
    recent_changes = [
        {
            "time": "2 hours ago",
            "type": "Deployment",
            "component": "API Gateway",
            "change": "Updated connection timeout from 30s to 60s",
            "risk": "Medium"
        },
        {
            "time": "6 hours ago", 
            "type": "Configuration",
            "component": "Database",
            "change": "Modified connection pool size from 10 to 20",
            "risk": "Low"
        },
        {
            "time": "1 day ago",
            "type": "Code Release",
            "component": "User Service",
            "change": "v2.1.4 - Bug fixes and performance improvements",
            "risk": "High"
        }
    ]
    
    for change in recent_changes:
        risk_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[change["risk"]]
        st.markdown(f"**{change['time']}** - {change['type']} ({change['component']})")
        st.markdown(f"{risk_color} Risk: {change['risk']} - {change['change']}")
        st.markdown("---")

def render_system_issues_analysis(incident_description, causation_types):
    """Render system issues analysis"""
    st.markdown("### 🏗️ System-Related Root Cause Analysis")
    
    system_probability = causation_types.get('System', 0.0)
    infra_probability = causation_types.get('Infrastructure', 0.0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("System Issues Probability", f"{system_probability:.1%}")
    
    with col2:
        st.metric("Infrastructure Issues Probability", f"{infra_probability:.1%}")
    
    if max(system_probability, infra_probability) > 0.5:
        st.success("High probability of system/infrastructure issues")
        
        # Display system metrics
        st.markdown("**System Health Indicators:**")
        
        # Mock system metrics
        metrics_data = {
            "CPU Usage": 85.2,
            "Memory Usage": 92.1,
            "Disk I/O": 73.5,
            "Network Latency": 245.8
        }
        
        cols = st.columns(4)
        for i, (metric, value) in enumerate(metrics_data.items()):
            with cols[i]:
                color = "🔴" if value > 90 else "🟡" if value > 75 else "🟢"
                if "Latency" in metric:
                    st.metric(metric, f"{value}ms", delta=f"{color}")
                else:
                    st.metric(metric, f"{value}%", delta=f"{color}")

def render_causation_summary(causation_types):
    """Render causation analysis summary"""
    st.markdown("### 📊 Causation Analysis Summary")
    
    # Create causation probability chart
    causation_df = pd.DataFrame(
        list(causation_types.items()),
        columns=['Causation Type', 'Probability']
    )
    causation_df['Probability'] = causation_df['Probability'] * 100
    
    fig = px.bar(
        causation_df,
        x='Causation Type',
        y='Probability',
        title='Incident Causation Probability Analysis',
        color='Probability',
        color_continuous_scale='RdYlGn'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations based on top causation
    top_causation = max(causation_types, key=causation_types.get)
    top_probability = causation_types[top_causation]
    
    st.markdown(f"**Primary Causation**: {top_causation} ({top_probability:.1%} probability)")
    
    recommendations = {
        'Defect': [
            "Check recent defect reports in ALM Octane",
            "Review code changes in affected components",
            "Search for similar incidents in Jira",
            "Analyze application error logs"
        ],
        'Change': [
            "Review recent deployments and releases",
            "Check configuration changes",
            "Analyze rollback options",
            "Review change management records"
        ],
        'System': [
            "Monitor system resource utilization",
            "Check for capacity issues",
            "Review system performance metrics",
            "Analyze infrastructure health"
        ],
        'Infrastructure': [
            "Check network connectivity",
            "Review server hardware status",
            "Monitor storage capacity",
            "Analyze infrastructure logs"
        ],
        'Security': [
            "Review security logs and alerts",
            "Check for unauthorized access",
            "Analyze threat detection systems",
            "Review recent security events"
        ]
    }
    
    if top_causation in recommendations:
        st.markdown("**Recommended Investigation Steps:**")
        for rec in recommendations[top_causation]:
            st.markdown(f"• {rec}")

def render_defect_management_tab():
    """Render the defect management tab"""
    st.header("🐛 Defect Management Dashboard")
    
    if not DEFECT_MANAGEMENT_AVAILABLE:
        st.warning("Defect management modules not available")
        return
    
    # Check defect management status
    defect_status = check_defect_management_status()
    
    # Status indicators
    col1, col2 = st.columns(2)
    
    with col1:
        alm_status = defect_status.get('alm_octane', {})
        status_icon = "🟢" if alm_status.get('status') == 'online' else "🔴"
        st.markdown(f"### {status_icon} ALM Octane")
        st.metric("Status", alm_status.get('status', 'offline').title())
        st.metric("Defects Available", alm_status.get('defect_count', 0))
    
    with col2:
        jira_status = defect_status.get('jira', {})
        status_icon = "🟢" if jira_status.get('status') == 'online' else "🔴"
        st.markdown(f"### {status_icon} Jira")
        st.metric("Status", jira_status.get('status', 'offline').title())
        st.metric("Issues Available", jira_status.get('issue_count', 0))
    
    # Defect management tabs
    defect_tabs = st.tabs(["📋 Defect Overview", "🔍 Search & Filter", "➕ Create Defect", "📊 Analytics"])
    
    with defect_tabs[0]:
        render_defect_overview()
    
    with defect_tabs[1]:
        render_defect_search()
    
    with defect_tabs[2]:
        render_defect_creation()
    
    with defect_tabs[3]:
        render_defect_analytics()

def render_defect_overview():
    """Render defect overview"""
    st.subheader("📋 Defect Overview")
    
    # Get defects from both systems
    try:
        # ALM Octane defects
        alm_response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects", timeout=5)
        alm_defects = alm_response.json()[:10] if alm_response.status_code == 200 else []
        
        # Jira issues
        jira_response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/issues", timeout=5)
        jira_issues = jira_response.json()[:10] if jira_response.status_code == 200 else []
        
        # Display side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ALM Octane Defects")
            for defect in alm_defects:
                severity_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(defect.get('severity', 'Low'), "⚪")
                status_class = f"status-{defect.get('status', 'open').lower().replace(' ', '')}"
                st.markdown(f"""
                <div class="defect-card">
                    <strong>{severity_icon} {defect.get('name', 'Unknown')}</strong><br>
                    <span class="defect-status {status_class}">{defect.get('status', 'Open')}</span><br>
                    <small>{defect.get('description', '')[:100]}...</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Jira Issues")
            for issue in jira_issues:
                priority_icon = {"Blocker": "🔴", "Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(issue.get('priority', 'Low'), "⚪")
                status_class = f"status-{issue.get('status', 'open').lower().replace(' ', '')}"
                st.markdown(f"""
                <div class="defect-card">
                    <strong>{priority_icon} {issue.get('key', 'Unknown')} - {issue.get('summary', 'Unknown')}</strong><br>
                    <span class="defect-status {status_class}">{issue.get('status', 'Open')}</span><br>
                    <small>{issue.get('description', '')[:100]}...</small>
                </div>
                """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Failed to load defects: {str(e)}")

def render_defect_search():
    """Render defect search interface"""
    st.subheader("🔍 Search & Filter Defects")
    
    # Search inputs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_text = st.text_input("Search Text", placeholder="Enter keywords...")
    
    with col2:
        severity_filter = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"])
    
    with col3:
        status_filter = st.selectbox("Status", ["All", "Open", "In Progress", "Resolved", "Closed"])
    
    if st.button("🔍 Search Defects"):
        # Perform search (mock implementation)
        st.info("Search functionality would query both ALM Octane and Jira with the specified filters")
        
        # Mock search results
        st.markdown("**Search Results:**")
        mock_results = [
            {"id": "ALM-001", "title": "API timeout issue", "severity": "High", "status": "In Progress"},
            {"id": "JIRA-123", "title": "Database connection pool", "severity": "Critical", "status": "Open"},
            {"id": "ALM-002", "title": "Memory leak in service", "severity": "Medium", "status": "Resolved"}
        ]
        
        for result in mock_results:
            severity_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(result['severity'], "⚪")
            st.markdown(f"**{severity_icon} {result['id']}** - {result['title']} ({result['status']})")

def render_defect_creation():
    """Render defect creation interface"""
    st.subheader("➕ Create New Defect")
    
    # Creation form
    with st.form("defect_creation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Defect Title*", placeholder="Brief description of the defect")
            severity = st.selectbox("Severity*", ["Low", "Medium", "High", "Critical"])
            component = st.text_input("Component", placeholder="Affected component/service")
        
        with col2:
            description = st.text_area("Description*", placeholder="Detailed description of the defect")
            target_system = st.selectbox("Target System*", ["ALM Octane", "Jira", "Both"])
            environment = st.selectbox("Environment", ["Development", "Test", "Staging", "Production"])
        
        # Additional fields for incident correlation
        st.markdown("#### Incident Correlation (Optional)")
        incident_id = st.text_input("Related Incident ID", placeholder="INC-12345")
        root_cause = st.text_area("Root Cause Analysis", placeholder="Analysis of the underlying cause")
        
        submitted = st.form_submit_button("Create Defect")
        
        if submitted:
            if not all([title, severity, description, target_system]):
                st.error("Please fill in all required fields marked with *")
            else:
                # Create defect (mock implementation)
                st.success(f"Defect created successfully in {target_system}!")
                
                # Show mock defect ID
                if target_system in ["ALM Octane", "Both"]:
                    st.info(f"ALM Octane Defect ID: ALM-{random.randint(1000, 9999)}")
                
                if target_system in ["Jira", "Both"]:
                    st.info(f"Jira Issue Key: BUG-{random.randint(100, 999)}")

def render_defect_analytics():
    """Render defect analytics"""
    st.subheader("📊 Defect Analytics Dashboard")
    
    # Mock analytics data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Open Defects", "127", "-8")
    
    with col2:
        st.metric("Critical Issues", "23", "+3")
    
    with col3:
        st.metric("Avg Resolution Time", "4.2 days", "-0.5 days")
    
    with col4:
        st.metric("Defect Detection Rate", "92%", "+2%")
    
    # Charts
    analytics_tabs = st.tabs(["📈 Trends", "🎯 Severity Distribution", "⚡ Resolution Times"])
    
    with analytics_tabs[0]:
        # Defect trend chart
        dates = pd.date_range(start='2025-07-01', end='2025-08-12', freq='D')
        defect_counts = [random.randint(5, 25) for _ in dates]
        
        fig = px.line(x=dates, y=defect_counts, title="Defect Creation Trend")
        fig.update_layout(xaxis_title="Date", yaxis_title="Defects Created")
        st.plotly_chart(fig, use_container_width=True)
    
    with analytics_tabs[1]:
        # Severity distribution
        severities = ['Critical', 'High', 'Medium', 'Low']
        counts = [23, 45, 67, 34]
        
        fig = px.pie(values=counts, names=severities, title="Defects by Severity")
        st.plotly_chart(fig, use_container_width=True)
    
    with analytics_tabs[2]:
        # Resolution times by severity
        resolution_data = pd.DataFrame({
            'Severity': ['Critical', 'High', 'Medium', 'Low'],
            'Avg Resolution (days)': [1.2, 2.8, 4.1, 6.5]
        })
        
        fig = px.bar(resolution_data, x='Severity', y='Avg Resolution (days)',
                    title="Average Resolution Time by Severity")
        st.plotly_chart(fig, use_container_width=True)

# Import the original SRE dashboard class and enhance it
try:
    from streamlit_app import SREDashboard as OriginalSREDashboard
    
    class ExpandedSREDashboard(OriginalSREDashboard):
        """Enhanced SRE Dashboard with defect management capabilities"""
        
        def __init__(self):
            super().__init__()
            # Initialize defect management components
            if DEFECT_MANAGEMENT_AVAILABLE:
                self.defect_scenarios = DefectDrivenIncidentScenarios()
                self.defect_ui = DefectManagementUI()
        
        def display_dashboard(self):
            """Display the expanded dashboard with defect management"""
            # Setup sidebar first
            self.setup_sidebar()
            
            st.markdown('<h1 class="main-header">🔍 SRE Copilot - Enhanced Root Cause Analysis</h1>', 
                       unsafe_allow_html=True)
            
            # Enhanced navigation tabs (preserves original + adds new)
            tab_names = [
                "🚨 Incident Management",      # Original
                "🔍 Analyze Incident",         # Original  
                "🔧 Recent Changes",           # Original
                "📚 Knowledge Base",           # Original
                "📊 Analytics",                # Original
                "🐛 Defect Management",        # NEW
                "🔗 Correlation Analysis"      # NEW
            ]
            
            if MCP_AVAILABLE and st.session_state.get('mcp_enabled', False):
                tab_names.extend(["🌐 MCP Status", "📈 Feedback Analytics"])
            
            tab_names.append("❓ User Guide")
            
            main_tabs = st.tabs(tab_names)
            
            # Original tabs (preserved functionality)
            with main_tabs[0]:  # Incident Management
                if st.session_state.current_incident:
                    self.display_incident_details()
                else:
                    self.display_welcome()
            
            with main_tabs[1]:  # Analyze Incident
                self.render_enhanced_analyze_tab()  # Enhanced version
            
            with main_tabs[2]:  # Recent Changes
                self.render_changes_tab()
            
            with main_tabs[3]:  # Knowledge Base
                self.render_knowledge_base_tab()
            
            with main_tabs[4]:  # Analytics
                self.render_analytics_tab()
            
            # New tabs (defect management)
            with main_tabs[5]:  # Defect Management
                render_defect_management_tab()
            
            with main_tabs[6]:  # Correlation Analysis
                self.render_correlation_analysis_tab()
            
            # Continue with original MCP and User Guide tabs
            tab_index = 7
            if MCP_AVAILABLE and st.session_state.get('mcp_enabled', False):
                with main_tabs[tab_index]:  # MCP Status
                    self.render_mcp_status_tab()
                
                with main_tabs[tab_index + 1]:  # Feedback Analytics
                    self.render_feedback_analytics_tab()
                
                tab_index += 2
            
            with main_tabs[tab_index]:  # User Guide
                self.render_user_guide_tab()
        
        def render_enhanced_analyze_tab(self):
            """Enhanced analyze tab with defect correlation and causation analysis"""
            st.header("🔍 Enhanced Incident Analysis")
            
            # Original incident analysis form
            with st.expander("📝 Incident Details", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    incident_title = st.text_input("Incident Title", 
                                                 value=st.session_state.get('incident_title', ''))
                    severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"],
                                          index=2)
                
                with col2:
                    incident_type = st.selectbox("Incident Type", 
                                               ["Performance", "Outage", "Security", "Data", "Network"],
                                               index=0)
                    affected_services = st.multiselect("Affected Services",
                                                     ["API Gateway", "User Service", "Database", 
                                                      "Payment Service", "Auth Service"])
                
                incident_description = st.text_area("Incident Description",
                                                  value=st.session_state.get('incident_description', ''),
                                                  placeholder="Describe the incident symptoms, timeline, and impact...")
                
                if st.button("🔍 Analyze Incident"):
                    if incident_description:
                        st.session_state.incident_title = incident_title
                        st.session_state.incident_description = incident_description
                        st.session_state.incident_severity = severity
                        st.session_state.incident_type = incident_type
                        st.session_state.affected_services = affected_services
                        
                        # Run enhanced analysis
                        self.run_enhanced_analysis(incident_description, incident_title, severity, incident_type)
                    else:
                        st.error("Please provide an incident description")
        
        def run_enhanced_analysis(self, incident_description, incident_title, severity, incident_type):
            """Run enhanced analysis with multiple causation types"""
            st.markdown("---")
            
            # Multi-factor causation analysis
            render_causation_analysis(incident_description)
            
            # Original AWS analysis (preserved)
            st.markdown("---")
            st.subheader("☁️ AWS Infrastructure Analysis")
            
            # Call original analysis methods
            if hasattr(self, 'analyze_aws_metrics'):
                self.analyze_aws_metrics(incident_description)
            
            # AWS clients initialization
            aws_clients = init_aws_clients()
            if aws_clients:
                self.display_aws_analysis(aws_clients, incident_description)
        
        def render_correlation_analysis_tab(self):
            """Render the correlation analysis tab"""
            st.header("🔗 Advanced Correlation Analysis")
            
            st.markdown("""
            This section provides comprehensive correlation analysis across multiple data sources
            to identify potential root causes and relationships between incidents, defects, and changes.
            """)
            
            # Correlation analysis tabs
            correlation_tabs = st.tabs(["🎯 Incident Correlation", "📈 Trend Analysis", "🔍 Pattern Detection"])
            
            with correlation_tabs[0]:
                st.subheader("🎯 Cross-System Incident Correlation")
                
                # Input for correlation analysis
                with st.form("correlation_analysis"):
                    analysis_incident = st.text_area("Incident Description for Correlation",
                                                   placeholder="Enter incident description to find correlations...")
                    
                    correlation_scope = st.multiselect("Correlation Scope",
                                                     ["Defects (ALM Octane)", "Issues (Jira)", 
                                                      "Changes (ServiceNow)", "Logs (Splunk)"],
                                                     default=["Defects (ALM Octane)", "Issues (Jira)"])
                    
                    time_range = st.selectbox("Time Range", ["Last 24 hours", "Last 7 days", "Last 30 days"],
                                            index=1)
                    
                    submitted = st.form_submit_button("🔍 Find Correlations")
                
                if submitted and analysis_incident:
                    st.markdown("### Correlation Results")
                    
                    # Run defect correlation if selected
                    if "Defects (ALM Octane)" in correlation_scope or "Issues (Jira)" in correlation_scope:
                        render_defect_correlation_section(analysis_incident)
                    
                    # Mock additional correlations
                    if "Changes (ServiceNow)" in correlation_scope:
                        st.markdown("#### 🔧 Recent Changes Correlation")
                        st.info("Found 3 potentially related changes in the specified time range")
                    
                    if "Logs (Splunk)" in correlation_scope:
                        st.markdown("#### 📊 Log Pattern Correlation")
                        st.info("Identified similar error patterns in application logs")
            
            with correlation_tabs[1]:
                st.subheader("📈 Trend Analysis")
                st.info("Trend analysis across incidents, defects, and system metrics")
                
                # Mock trend data
                dates = pd.date_range(start='2025-07-01', end='2025-08-12', freq='D')
                incidents = [random.randint(2, 12) for _ in dates]
                defects = [random.randint(5, 25) for _ in dates]
                
                trend_df = pd.DataFrame({
                    'Date': dates,
                    'Incidents': incidents,
                    'Defects': defects
                })
                
                fig = px.line(trend_df, x='Date', y=['Incidents', 'Defects'], 
                             title="Incident vs Defect Trends")
                st.plotly_chart(fig, use_container_width=True)
            
            with correlation_tabs[2]:
                st.subheader("🔍 Pattern Detection")
                st.info("AI-powered pattern detection across historical incidents and defects")
                
                # Mock pattern detection results
                patterns = [
                    {"pattern": "API timeout incidents", "frequency": "Weekly", "correlation": "Database defects", "confidence": 85},
                    {"pattern": "Memory leak symptoms", "frequency": "Bi-weekly", "correlation": "Code deployment", "confidence": 72},
                    {"pattern": "Authentication failures", "frequency": "Monthly", "correlation": "Configuration changes", "confidence": 68}
                ]
                
                for pattern in patterns:
                    confidence_color = "🟢" if pattern["confidence"] > 80 else "🟡" if pattern["confidence"] > 65 else "🔴"
                    st.markdown(f"""
                    **{pattern['pattern']}** ({pattern['frequency']})  
                    Correlation: {pattern['correlation']} {confidence_color} Confidence: {pattern['confidence']}%
                    """)
    
    # Use the expanded dashboard
    dashboard_class = ExpandedSREDashboard
    
except ImportError:
    st.error("Could not import original SRE Dashboard. Please ensure streamlit_app.py is available.")
    
    # Fallback minimal dashboard
    class MinimalExpandedDashboard:
        def display_dashboard(self):
            st.title("🔍 SRE Copilot - Expanded Dashboard")
            st.error("Original dashboard not available. Running in minimal mode.")
            render_defect_management_tab()
    
    dashboard_class = MinimalExpandedDashboard

def main():
    """Main application entry point"""
    try:
        # Initialize session state
        if 'aws_clients' not in st.session_state:
            st.session_state.aws_clients = init_aws_clients()
        
        if 'current_incident' not in st.session_state:
            st.session_state.current_incident = None
        
        if 'defect_management_status' not in st.session_state:
            st.session_state.defect_management_status = check_defect_management_status()
        
        # Initialize and display dashboard
        dashboard = dashboard_class()
        dashboard.display_dashboard()
        
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please check that all required modules and services are available.")

if __name__ == "__main__":
    main()
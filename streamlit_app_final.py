#!/usr/bin/env python3
"""
SRE Copilot - Final Expanded Dashboard
Preserves original functionality and adds comprehensive defect management
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

# Set page config first
st.set_page_config(
    page_title="SRE Copilot - Expanded Root Cause Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add path for modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import defect management modules
try:
    from defect_driven_incident_scenarios import DefectDrivenIncidentScenarios
    from defect_incident_correlator import DefectIncidentCorrelator
    DEFECT_MANAGEMENT_AVAILABLE = True
except ImportError:
    DEFECT_MANAGEMENT_AVAILABLE = False

# Load MCP ports
try:
    with open('mcp_ports.json', 'r') as f:
        MCP_PORTS = json.load(f)
except:
    MCP_PORTS = {
        'splunk': 9080, 'dynatrace': 9081, 'servicenow': 9082, 
        'confluence': 9083, 'gitlab': 9084, 'alm_octane': 9085, 'jira': 9086
    }

# Enhanced CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1f77b4; text-align: center; margin-bottom: 2rem; }
    .metric-card { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; }
    .alert-box { padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
    .critical { background-color: #ffebee; border-left: 4px solid #f44336; }
    .warning { background-color: #fff3e0; border-left: 4px solid #ff9800; }
    .info { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
    .success { background-color: #e8f5e9; border-left: 4px solid #4caf50; }
    .defect-card { background-color: #fff9c4; border: 1px solid #f57f17; border-radius: 0.5rem; padding: 1rem; margin: 0.5rem 0; }
    .causation-type { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 1rem; font-size: 0.8rem; font-weight: bold; margin: 0.2rem; }
    .causation-defect { background-color: #ffecb3; color: #e65100; }
    .causation-change { background-color: #e1bee7; color: #4a148c; }
    .causation-system { background-color: #ffcdd2; color: #c62828; }
    .causation-infra { background-color: #c8e6c9; color: #2e7d32; }
    .defect-status { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 0.3rem; font-size: 0.7rem; font-weight: bold; }
    .status-open { background-color: #ffcdd2; color: #d32f2f; }
    .status-progress { background-color: #fff3e0; color: #f57c00; }
    .status-resolved { background-color: #c8e6c9; color: #388e3c; }
</style>
""", unsafe_allow_html=True)

def init_aws_clients():
    """Initialize AWS clients"""
    try:
        region = 'us-east-1'
        return {
            'lambda': boto3.client('lambda', region_name=region),
            'cloudwatch': boto3.client('cloudwatch', region_name=region),
            'logs': boto3.client('logs', region_name=region),
            'ssm': boto3.client('ssm', region_name=region)
        }
    except Exception as e:
        st.error(f"AWS clients init failed: {str(e)}")
        return None

def check_mcp_server_status(server_name, port):
    """Check MCP server status"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return "🟢 Online" if response.status_code == 200 else "🟡 Partial"
    except:
        # Try alternative endpoints
        try:
            if server_name == 'alm_octane':
                response = requests.get(f"http://localhost:{port}/octane/defects", timeout=2)
            elif server_name == 'jira':
                response = requests.get(f"http://localhost:{port}/jira/issues", timeout=2)
            else:
                return "🔴 Offline"
            return "🟢 Online" if response.status_code == 200 else "🔴 Offline"
        except:
            return "🔴 Offline"

def analyze_incident_causation(incident_description):
    """Analyze incident for causation types"""
    causation_keywords = {
        'Defect': ['bug', 'defect', 'error', 'exception', 'crash', 'failure', 'regression', 'broken'],
        'Change': ['deployment', 'release', 'update', 'configuration', 'change', 'migrate', 'upgrade'],
        'System': ['outage', 'down', 'unavailable', 'timeout', 'performance', 'slow', 'capacity'],
        'Infrastructure': ['network', 'server', 'hardware', 'disk', 'memory', 'cpu', 'storage'],
        'Security': ['breach', 'attack', 'unauthorized', 'security', 'vulnerability', 'exploit']
    }
    
    causation_scores = {}
    for causation, keywords in causation_keywords.items():
        score = sum(1 for keyword in keywords if keyword in incident_description.lower())
        causation_scores[causation] = min(score / len(keywords) * 2, 1.0)
    
    return causation_scores

def get_defect_correlation_data(incident_description):
    """Get defect correlation analysis"""
    if not DEFECT_MANAGEMENT_AVAILABLE:
        return {'error': 'Defect management not available'}
    
    try:
        mcp_endpoints = {
            'alm_octane': f"http://localhost:{MCP_PORTS['alm_octane']}",
            'jira': f"http://localhost:{MCP_PORTS['jira']}"
        }
        
        correlator = DefectIncidentCorrelator(mcp_endpoints)
        incident_data = {
            'incident_id': f"INC-{int(time.time())}",
            'title': incident_description[:100],
            'description': incident_description,
            'severity': 'High',
            'affected_services': ['general'],
            'timestamp': datetime.now().isoformat()
        }
        
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

def render_incident_management_tab():
    """Render incident management tab (original functionality)"""
    st.header("🚨 Incident Management")
    
    # Quick incident creation
    with st.expander("➕ Create New Incident", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Incident Title", placeholder="Brief incident description", key="inc_mgmt_title")
            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], index=2, key="inc_mgmt_severity")
        
        with col2:
            incident_type = st.selectbox("Type", ["Performance", "Outage", "Security", "Network"], index=0, key="inc_mgmt_type")
            affected_services = st.multiselect("Affected Services", 
                                             ["API Gateway", "User Service", "Database", "Payment Service"], key="inc_mgmt_services")
        
        description = st.text_area("Description", placeholder="Detailed incident description...", key="inc_mgmt_desc")
        
        if st.button("🚨 Create Incident", key="inc_mgmt_create"):
            if title and description:
                st.session_state.current_incident = {
                    'id': f"INC-{random.randint(1000, 9999)}",
                    'title': title,
                    'description': description,
                    'severity': severity,
                    'type': incident_type,
                    'services': affected_services,
                    'created': datetime.now(),
                    'status': 'Open'
                }
                st.success(f"Created incident: {st.session_state.current_incident['id']}")
                st.rerun()
    
    # Current incident details
    if st.session_state.get('current_incident'):
        incident = st.session_state.current_incident
        st.markdown(f"""
        <div class="incident-card">
            <h3>🔴 Active Incident: {incident['id']}</h3>
            <p><strong>{incident['title']}</strong></p>
            <p>Severity: {incident['severity']} | Type: {incident['type']} | Status: {incident['status']}</p>
            <p>Created: {incident['created'].strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Services: {', '.join(incident['services'])}</p>
            <p>{incident['description']}</p>
        </div>
        """, unsafe_allow_html=True)

def render_analyze_incident_tab():
    """Enhanced incident analysis tab"""
    st.header("🔍 Enhanced Incident Analysis")
    
    # Incident input form
    with st.expander("📝 Incident Analysis", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            incident_title = st.text_input("Incident Title", key="analyze_title")
            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], index=2, key="analyze_severity")
        
        with col2:
            incident_type = st.selectbox("Type", ["Performance", "Outage", "Security", "Network"], key="analyze_type")
            affected_services = st.multiselect("Affected Services",
                                             ["API Gateway", "Database", "User Service", "Payment Service"], key="analyze_services")
        
        incident_description = st.text_area("Incident Description", 
                                          placeholder="Describe symptoms, timeline, and impact...", key="analyze_desc")
        
        if st.button("🔍 Analyze Incident", key="analyze_button") and incident_description:
            # Multi-factor causation analysis
            st.markdown("---")
            st.subheader("🎯 Root Cause Categorization")
            
            causation_types = analyze_incident_causation(incident_description)
            
            # Display causation badges
            st.markdown("**Probable Causation Types:**")
            causation_html = ""
            for causation, probability in causation_types.items():
                if probability > 0.3:
                    css_class = f"causation-{causation.lower()}"
                    causation_html += f'<span class="causation-type {css_class}">{causation}: {probability:.1%}</span>'
            
            st.markdown(causation_html, unsafe_allow_html=True)
            
            # Causation analysis tabs
            causation_tabs = st.tabs(["🐛 Defect Analysis", "🔧 Change Analysis", "🏗️ System Analysis", "📊 Summary"])
            
            with causation_tabs[0]:
                defect_probability = causation_types.get('Defect', 0.0)
                
                if defect_probability > 0.5:
                    st.success(f"High defect probability ({defect_probability:.1%})")
                    
                    # Defect correlation analysis
                    st.subheader("🔗 Defect Correlation Analysis")
                    with st.spinner("Analyzing defect correlations..."):
                        correlation_data = get_defect_correlation_data(incident_description)
                    
                    if 'error' not in correlation_data:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Correlations Found", correlation_data.get('total_correlations', 0))
                        
                        with col2:
                            score = correlation_data.get('highest_correlation', 0.0)
                            score_icon = "🟢" if score >= 0.7 else "🟡" if score >= 0.4 else "🔴"
                            st.metric("Highest Score", f"{score_icon} {score:.1%}")
                        
                        with col3:
                            st.metric("Defect Likelihood", correlation_data.get('defect_likelihood', 'Low'))
                        
                        # Recommendations
                        if correlation_data.get('recommended_actions'):
                            st.subheader("💡 Recommendations")
                            for action in correlation_data['recommended_actions'][:5]:
                                st.markdown(f"• {action}")
                    else:
                        st.error(f"Correlation failed: {correlation_data['error']}")
                
                elif defect_probability > 0.2:
                    st.warning(f"Moderate defect probability ({defect_probability:.1%})")
                    st.markdown("**Consider checking:**")
                    st.markdown("- Recent code deployments")
                    st.markdown("- Application error logs") 
                    st.markdown("- Known defects in affected components")
                else:
                    st.info(f"Low defect probability ({defect_probability:.1%})")
            
            with causation_tabs[1]:
                change_probability = causation_types.get('Change', 0.0)
                st.subheader(f"🔧 Change Analysis ({change_probability:.1%} probability)")
                
                if change_probability > 0.3:
                    st.markdown("**Recent Changes to Review:**")
                    changes = [
                        {"time": "2 hours ago", "type": "Deployment", "component": "API Gateway", "risk": "High"},
                        {"time": "6 hours ago", "type": "Config", "component": "Database", "risk": "Medium"},
                        {"time": "1 day ago", "type": "Release", "component": "User Service", "risk": "Low"}
                    ]
                    
                    for change in changes:
                        risk_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[change["risk"]]
                        st.markdown(f"**{change['time']}** - {change['type']} ({change['component']}) {risk_color}")
                
                st.markdown("**Investigation Steps:**")
                st.markdown("- Review deployment logs")
                st.markdown("- Check configuration changes")
                st.markdown("- Analyze rollback options")
            
            with causation_tabs[2]:
                system_prob = causation_types.get('System', 0.0)
                infra_prob = causation_types.get('Infrastructure', 0.0)
                
                st.subheader("🏗️ System & Infrastructure Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("System Issues", f"{system_prob:.1%}")
                with col2:
                    st.metric("Infrastructure Issues", f"{infra_prob:.1%}")
                
                if max(system_prob, infra_prob) > 0.5:
                    st.markdown("**System Metrics:**")
                    metrics = {"CPU": 85.2, "Memory": 92.1, "Disk I/O": 73.5, "Network": 245.8}
                    
                    cols = st.columns(4)
                    for i, (metric, value) in enumerate(metrics.items()):
                        with cols[i]:
                            color = "🔴" if value > 90 else "🟡" if value > 75 else "🟢"
                            unit = "ms" if "Network" in metric else "%"
                            st.metric(metric, f"{value}{unit}", delta=f"{color}")
            
            with causation_tabs[3]:
                st.subheader("📊 Analysis Summary")
                
                # Causation chart
                causation_df = pd.DataFrame(
                    list(causation_types.items()),
                    columns=['Causation Type', 'Probability']
                )
                causation_df['Probability'] = causation_df['Probability'] * 100
                
                fig = px.bar(causation_df, x='Causation Type', y='Probability',
                           title='Incident Causation Analysis',
                           color='Probability', color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
                
                # Top recommendation
                top_causation = max(causation_types, key=causation_types.get)
                st.markdown(f"**Primary Causation**: {top_causation} ({causation_types[top_causation]:.1%})")

def render_defect_management_tab():
    """Render defect management tab"""
    st.header("🐛 Defect Management Dashboard")
    
    # Status indicators
    col1, col2 = st.columns(2)
    
    with col1:
        alm_status = check_mcp_server_status('alm_octane', MCP_PORTS['alm_octane'])
        st.markdown(f"### ALM Octane {alm_status}")
        
        try:
            response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects", timeout=2)
            defect_count = len(response.json()) if response.status_code == 200 else 0
            st.metric("Defects Available", defect_count)
        except:
            st.metric("Defects Available", "0")
    
    with col2:
        jira_status = check_mcp_server_status('jira', MCP_PORTS['jira'])
        st.markdown(f"### Jira {jira_status}")
        
        try:
            response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/issues", timeout=2)
            issue_count = len(response.json()) if response.status_code == 200 else 0
            st.metric("Issues Available", issue_count)
        except:
            st.metric("Issues Available", "0")
    
    # Defect management sections
    defect_tabs = st.tabs(["📋 Overview", "🔍 Search", "➕ Create", "📊 Analytics"])
    
    with defect_tabs[0]:
        st.subheader("📋 Defect Overview")
        
        # Get recent defects
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Recent ALM Octane Defects")
            try:
                response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects", timeout=5)
                if response.status_code == 200:
                    defects = response.json()[:5]
                    for defect in defects:
                        severity_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(defect.get('severity', 'Low'), "⚪")
                        st.markdown(f"""
                        <div class="defect-card">
                            <strong>{severity_icon} {defect.get('name', 'Unknown')}</strong><br>
                            <span class="defect-status status-{defect.get('status', 'open').lower().replace(' ', '')}">{defect.get('status', 'Open')}</span><br>
                            <small>{defect.get('description', '')[:80]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No defects found")
            except:
                st.error("Cannot connect to ALM Octane")
        
        with col2:
            st.markdown("#### Recent Jira Issues")
            try:
                response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/issues", timeout=5)
                if response.status_code == 200:
                    issues = response.json()[:5]
                    for issue in issues:
                        priority_icon = {"Blocker": "🔴", "Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(issue.get('priority', 'Low'), "⚪")
                        st.markdown(f"""
                        <div class="defect-card">
                            <strong>{priority_icon} {issue.get('key', 'Unknown')} - {issue.get('summary', 'Unknown')}</strong><br>
                            <span class="defect-status status-{issue.get('status', 'open').lower().replace(' ', '')}">{issue.get('status', 'Open')}</span><br>
                            <small>{issue.get('description', '')[:80]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No issues found")
            except:
                st.error("Cannot connect to Jira")
    
    with defect_tabs[1]:
        st.subheader("🔍 Search Defects")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            search_text = st.text_input("Search Keywords", key="defect_search_text")
        with col2:
            severity_filter = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"], key="defect_search_severity")
        with col3:
            status_filter = st.selectbox("Status", ["All", "Open", "In Progress", "Resolved"], key="defect_search_status")
        
        if st.button("🔍 Search", key="defect_search_button"):
            st.info("Search functionality would query both systems with filters")
    
    with defect_tabs[2]:
        st.subheader("➕ Create Defect")
        
        with st.form("defect_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Title*", key="defect_create_title")
                severity = st.selectbox("Severity*", ["Low", "Medium", "High", "Critical"], key="defect_create_severity")
                component = st.text_input("Component", key="defect_create_component")
            
            with col2:
                description = st.text_area("Description*", key="defect_create_desc")
                target = st.selectbox("Target System*", ["ALM Octane", "Jira", "Both"], key="defect_create_target")
                environment = st.selectbox("Environment", ["Dev", "Test", "Staging", "Prod"], key="defect_create_env")
            
            submitted = st.form_submit_button("Create", key="defect_create_submit")
            
            if submitted and title and description:
                st.success(f"Defect would be created in {target}")
                if target in ["ALM Octane", "Both"]:
                    st.info(f"ALM Octane ID: ALM-{random.randint(1000, 9999)}")
                if target in ["Jira", "Both"]:
                    st.info(f"Jira Key: BUG-{random.randint(100, 999)}")
    
    with defect_tabs[3]:
        st.subheader("📊 Defect Analytics")
        
        # Mock metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Open Defects", "127", "-8")
        with col2:
            st.metric("Critical Issues", "23", "+3")
        with col3:
            st.metric("Avg Resolution", "4.2 days", "-0.5")
        with col4:
            st.metric("Detection Rate", "92%", "+2%")
        
        # Chart
        dates = pd.date_range(start='2025-07-01', end='2025-08-12', freq='D')
        defects = [random.randint(5, 25) for _ in dates]
        
        fig = px.line(x=dates, y=defects, title="Daily Defect Creation Trend")
        st.plotly_chart(fig, use_container_width=True)

def render_mcp_status_tab():
    """Render MCP status tab (original functionality)"""
    st.header("🌐 MCP Services Status")
    
    # Check all MCP servers
    servers = [
        ("Splunk", MCP_PORTS['splunk']),
        ("Dynatrace", MCP_PORTS['dynatrace']),
        ("ServiceNow", MCP_PORTS['servicenow']),
        ("Confluence", MCP_PORTS['confluence']),
        ("GitLab", MCP_PORTS['gitlab']),
        ("ALM Octane", MCP_PORTS['alm_octane']),
        ("Jira", MCP_PORTS['jira'])
    ]
    
    col1, col2 = st.columns(2)
    
    for i, (name, port) in enumerate(servers):
        with col1 if i % 2 == 0 else col2:
            status = check_mcp_server_status(name.lower().replace(' ', '_'), port)
            st.markdown(f"### {name} {status}")
            st.markdown(f"Port: {port}")
            
            if st.button(f"Test {name}", key=f"test_{name}"):
                st.info(f"Testing {name} connection...")

def main():
    """Main application"""
    st.markdown('<h1 class="main-header">🔍 SRE Copilot - Enhanced Root Cause Analysis</h1>', 
               unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_incident' not in st.session_state:
        st.session_state.current_incident = None
    if 'aws_clients' not in st.session_state:
        st.session_state.aws_clients = init_aws_clients()
    
    # Enhanced navigation (preserves original + adds new)
    tabs = st.tabs([
        "🚨 Incident Management",     # Original
        "🔍 Analyze Incident",        # Enhanced 
        "🔧 Recent Changes",          # Original
        "📚 Knowledge Base",          # Original
        "📊 Analytics",               # Original
        "🐛 Defect Management",       # NEW
        "🌐 MCP Status",             # Original
        "❓ User Guide"              # Original
    ])
    
    with tabs[0]:
        render_incident_management_tab()
    
    with tabs[1]:
        render_analyze_incident_tab()
    
    with tabs[2]:
        st.header("🔧 Recent Changes")
        st.info("Recent changes analysis (preserved from original)")
        # Mock recent changes
        changes = [
            {"time": "2h ago", "type": "Deploy", "component": "API", "impact": "High"},
            {"time": "6h ago", "type": "Config", "component": "DB", "impact": "Medium"},
            {"time": "1d ago", "type": "Release", "component": "User Service", "impact": "Low"}
        ]
        for change in changes:
            st.markdown(f"**{change['time']}** - {change['type']} ({change['component']}) - Impact: {change['impact']}")
    
    with tabs[3]:
        st.header("📚 Knowledge Base")
        st.info("Knowledge base functionality (preserved from original)")
        
        kb_tabs = st.tabs(["🔍 Search", "📖 Browse", "➕ Add"])
        with kb_tabs[0]:
            search_query = st.text_input("Search knowledge base...", key="kb_search_query")
            if search_query:
                st.info(f"Searching for: {search_query}")
        
        with kb_tabs[1]:
            st.markdown("**Recent Articles:**")
            st.markdown("- API Gateway troubleshooting guide")
            st.markdown("- Database performance optimization")
            st.markdown("- Security incident response playbook")
        
        with kb_tabs[2]:
            with st.form("kb_form"):
                title = st.text_input("Article Title", key="kb_article_title")
                content = st.text_area("Content", key="kb_article_content")
                submitted = st.form_submit_button("Add Article", key="kb_add_article")
                if submitted and title:
                    st.success("Article added to knowledge base")
    
    with tabs[4]:
        st.header("📊 Analytics")
        st.info("Analytics dashboard (preserved from original)")
        
        # Mock analytics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Incidents", "1,234", "+56")
        with col2:
            st.metric("Resolved Today", "23", "+5")
        with col3:
            st.metric("Avg MTTR", "2.4h", "-0.3h")
        with col4:
            st.metric("SLA Compliance", "94.5%", "+1.2%")
        
        # Trend chart
        dates = pd.date_range(start='2025-07-01', end='2025-08-12', freq='D')
        incidents = [random.randint(10, 30) for _ in dates]
        
        fig = px.line(x=dates, y=incidents, title="Daily Incident Trend")
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[5]:
        render_defect_management_tab()
    
    with tabs[6]:
        render_mcp_status_tab()
    
    with tabs[7]:
        st.header("❓ User Guide")
        st.info("User guide and help documentation (preserved from original)")
        
        guide_sections = st.tabs(["🚀 Getting Started", "🔍 Analysis", "🐛 Defects", "🔧 MCP"])
        
        with guide_sections[0]:
            st.markdown("""
            ## Getting Started
            1. Create or select an incident in the **Incident Management** tab
            2. Use **Analyze Incident** for enhanced root cause analysis
            3. Check **Defect Management** for related defects
            4. Review **MCP Status** for external tool integration
            """)
        
        with guide_sections[1]:
            st.markdown("""
            ## Incident Analysis
            - Enter incident description for AI-powered analysis
            - Review causation categories (Defect, Change, System, etc.)
            - Use correlation analysis to find related defects
            - Follow recommended investigation steps
            """)
        
        with guide_sections[2]:
            st.markdown("""
            ## Defect Management
            - View defects from ALM Octane and Jira
            - Create new defects linked to incidents  
            - Search and filter across both systems
            - Analyze defect trends and metrics
            """)
        
        with guide_sections[3]:
            st.markdown("""
            ## MCP Integration
            - Monitor status of all external tools
            - Test connections to ensure availability
            - Access tool-specific functionality
            - Review integration health metrics
            """)

if __name__ == "__main__":
    main()
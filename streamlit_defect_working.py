#!/usr/bin/env python3
"""
SRE Copilot - Working Defect Management Integration
Focus on defect management tabs and correlation scenarios
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

# Set page config
st.set_page_config(
    page_title="SRE Copilot - Defect Management",
    page_icon="🔍",
    layout="wide"
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

# MCP ports
MCP_PORTS = {
    'alm_octane': 9085,
    'jira': 9086
}

# CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1f77b4; text-align: center; margin-bottom: 2rem; }
    .defect-card { background-color: #fff9c4; border: 1px solid #f57f17; border-radius: 0.5rem; padding: 1rem; margin: 0.5rem 0; }
    .correlation-high { background-color: #c8e6c9; padding: 1rem; border-radius: 0.5rem; }
    .correlation-medium { background-color: #fff3e0; padding: 1rem; border-radius: 0.5rem; }
    .correlation-low { background-color: #ffcdd2; padding: 1rem; border-radius: 0.5rem; }
    .causation-badge { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 1rem; font-size: 0.8rem; font-weight: bold; margin: 0.2rem; }
    .causation-defect { background-color: #ffecb3; color: #e65100; }
    .causation-change { background-color: #e1bee7; color: #4a148c; }
    .causation-system { background-color: #ffcdd2; color: #c62828; }
</style>
""", unsafe_allow_html=True)

def check_defect_servers():
    """Check defect management server status"""
    status = {}
    
    try:
        response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects", timeout=2)
        status['alm_octane'] = {
            'online': response.status_code == 200,
            'defects': len(response.json()) if response.status_code == 200 else 0
        }
    except:
        status['alm_octane'] = {'online': False, 'defects': 0}
    
    try:
        response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/issues", timeout=2)
        status['jira'] = {
            'online': response.status_code == 200,
            'issues': len(response.json()) if response.status_code == 200 else 0
        }
    except:
        status['jira'] = {'online': False, 'issues': 0}
    
    return status

def get_correlation_analysis(incident_description):
    """Get defect correlation analysis"""
    if not DEFECT_MANAGEMENT_AVAILABLE:
        return None
    
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
            'total_correlations': summary.get('total_correlations', 0),
            'highest_correlation': summary.get('highest_correlation', 0.0),
            'defect_likelihood': summary.get('defect_likelihood', 'Low'),
            'recommended_actions': summary.get('recommended_actions', []),
            'correlation_results': correlation_results
        }
        
    except Exception as e:
        st.error(f"Correlation analysis failed: {str(e)}")
        return None

def render_incident_analysis():
    """Render enhanced incident analysis with defect correlation"""
    st.header("🔍 Enhanced Root Cause Analysis")
    
    with st.form("incident_analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            incident_title = st.text_input("Incident Title", placeholder="Brief description...")
            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], index=2)
        
        with col2:
            incident_type = st.selectbox("Incident Type", ["Performance", "Outage", "Security", "Network"])
            services = st.multiselect("Affected Services", ["API Gateway", "Database", "User Service", "Payment"])
        
        incident_description = st.text_area("Incident Description", 
                                          placeholder="Describe the incident symptoms, timeline, and impact...",
                                          height=150)
        
        analyze_button = st.form_submit_button("🔍 Analyze with Defect Correlation")
    
    if analyze_button and incident_description:
        # Show analysis results
        st.markdown("---")
        st.subheader("🎯 Multi-Factor Root Cause Analysis")
        
        # Analyze causation types
        causation_scores = analyze_causation(incident_description)
        
        # Display causation badges
        st.markdown("**Probable Causation Types:**")
        badges_html = ""
        for causation, score in causation_scores.items():
            if score > 0.3:
                css_class = f"causation-{causation.lower()}"
                badges_html += f'<span class="causation-badge {css_class}">{causation}: {score:.1%}</span>'
        
        if badges_html:
            st.markdown(badges_html, unsafe_allow_html=True)
        
        # Defect correlation analysis
        st.markdown("---")
        st.subheader("🔗 Defect Correlation Analysis")
        
        with st.spinner("Analyzing defect correlations..."):
            correlation_data = get_correlation_analysis(incident_description)
        
        if correlation_data:
            # Display correlation metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Correlations Found", correlation_data['total_correlations'])
            
            with col2:
                score = correlation_data['highest_correlation']
                score_icon = "🟢" if score >= 0.7 else "🟡" if score >= 0.4 else "🔴"
                st.metric("Highest Correlation", f"{score_icon} {score:.1%}")
            
            with col3:
                likelihood = correlation_data['defect_likelihood']
                st.metric("Defect Likelihood", likelihood)
            
            # Correlation gauge
            if score > 0:
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = score * 100,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Correlation Strength"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 40], 'color': "lightgray"},
                            {'range': [40, 70], 'color': "yellow"},
                            {'range': [70, 100], 'color': "green"}
                        ]
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            # Recommendations
            if correlation_data['recommended_actions']:
                st.subheader("💡 AI Recommendations")
                for i, action in enumerate(correlation_data['recommended_actions'][:5], 1):
                    st.markdown(f"{i}. {action}")
        
        # Causation-specific analysis
        st.markdown("---")
        render_causation_analysis(causation_scores, incident_description)

def analyze_causation(incident_description):
    """Analyze incident for different causation types"""
    keywords = {
        'Defect': ['bug', 'defect', 'error', 'exception', 'crash', 'failure', 'regression'],
        'Change': ['deployment', 'release', 'update', 'configuration', 'change', 'upgrade'],
        'System': ['outage', 'down', 'timeout', 'performance', 'slow', 'capacity'],
        'Infrastructure': ['network', 'server', 'hardware', 'disk', 'memory'],
        'Security': ['breach', 'attack', 'unauthorized', 'security', 'vulnerability']
    }
    
    scores = {}
    text = incident_description.lower()
    
    for category, words in keywords.items():
        score = sum(1 for word in words if word in text)
        scores[category] = min(score / len(words) * 2, 1.0)
    
    return scores

def render_causation_analysis(causation_scores, incident_description):
    """Render detailed causation analysis"""
    st.subheader("📊 Causation Analysis Details")
    
    tabs = st.tabs(["🐛 Defect-Caused", "🔧 Change-Caused", "🏗️ System Issues", "📈 Summary"])
    
    with tabs[0]:
        defect_prob = causation_scores.get('Defect', 0.0)
        
        if defect_prob > 0.5:
            st.markdown('<div class="correlation-high">', unsafe_allow_html=True)
            st.success(f"High defect probability: {defect_prob:.1%}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("**Investigation Steps:**")
            st.markdown("- Check ALM Octane for recent defects in affected components")
            st.markdown("- Review Jira issues related to similar symptoms")
            st.markdown("- Analyze application error logs for exceptions")
            st.markdown("- Check recent code deployments for regression issues")
            
        elif defect_prob > 0.2:
            st.markdown('<div class="correlation-medium">', unsafe_allow_html=True)
            st.warning(f"Moderate defect probability: {defect_prob:.1%}")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="correlation-low">', unsafe_allow_html=True)
            st.info(f"Low defect probability: {defect_prob:.1%}")
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tabs[1]:
        change_prob = causation_scores.get('Change', 0.0)
        
        st.markdown(f"### Change-Caused Analysis ({change_prob:.1%} probability)")
        
        if change_prob > 0.3:
            st.markdown("**Recent Changes to Review:**")
            
            # Mock recent changes
            changes = [
                {"time": "2 hours ago", "type": "Deployment", "component": "API Gateway", "risk": "High"},
                {"time": "6 hours ago", "type": "Configuration", "component": "Database", "risk": "Medium"},
                {"time": "1 day ago", "type": "Code Release", "component": "User Service", "risk": "Low"}
            ]
            
            for change in changes:
                risk_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[change["risk"]]
                st.markdown(f"**{change['time']}** - {change['type']} ({change['component']}) {risk_color} {change['risk']} Risk")
    
    with tabs[2]:
        system_prob = causation_scores.get('System', 0.0)
        infra_prob = causation_scores.get('Infrastructure', 0.0)
        
        st.markdown("### System & Infrastructure Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("System Issues", f"{system_prob:.1%}")
        with col2:
            st.metric("Infrastructure Issues", f"{infra_prob:.1%}")
        
        if max(system_prob, infra_prob) > 0.5:
            st.markdown("**Current System Metrics:**")
            
            # Mock system metrics
            metrics_cols = st.columns(4)
            metrics = [("CPU Usage", "85.2%", "🟡"), ("Memory", "92.1%", "🔴"), ("Disk I/O", "73.5%", "🟢"), ("Network", "245ms", "🟡")]
            
            for i, (name, value, status) in enumerate(metrics):
                with metrics_cols[i]:
                    st.metric(name, value, delta=status)
    
    with tabs[3]:
        # Summary chart
        causation_df = pd.DataFrame(
            list(causation_scores.items()),
            columns=['Causation Type', 'Probability']
        )
        causation_df['Probability'] = causation_df['Probability'] * 100
        
        fig = px.bar(causation_df, x='Causation Type', y='Probability',
                    title='Incident Causation Probability Analysis',
                    color='Probability', color_continuous_scale='RdYlGn')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def render_defect_management():
    """Render defect management dashboard"""
    st.header("🐛 Defect Management Dashboard")
    
    # Check server status
    status = check_defect_servers()
    
    # Status indicators
    col1, col2 = st.columns(2)
    
    with col1:
        alm_online = status['alm_octane']['online']
        status_icon = "🟢" if alm_online else "🔴"
        st.markdown(f"### {status_icon} ALM Octane")
        st.metric("Status", "Online" if alm_online else "Offline")
        st.metric("Defects Available", status['alm_octane']['defects'])
    
    with col2:
        jira_online = status['jira']['online']
        status_icon = "🟢" if jira_online else "🔴"
        st.markdown(f"### {status_icon} Jira")
        st.metric("Status", "Online" if jira_online else "Offline")
        st.metric("Issues Available", status['jira']['issues'])
    
    # Defect management tabs
    defect_tabs = st.tabs(["📋 Overview", "🔍 Search", "➕ Create", "📊 Analytics"])
    
    with defect_tabs[0]:
        render_defect_overview(status)
    
    with defect_tabs[1]:
        render_defect_search()
    
    with defect_tabs[2]:
        render_defect_creation()
    
    with defect_tabs[3]:
        render_defect_analytics()

def render_defect_overview(status):
    """Render defect overview"""
    st.subheader("📋 Recent Defects & Issues")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ALM Octane Defects")
        if status['alm_octane']['online']:
            try:
                response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects", timeout=5)
                if response.status_code == 200:
                    defects = response.json()[:5]
                    for defect in defects:
                        severity_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(defect.get('severity', 'Low'), "⚪")
                        st.markdown(f"""
                        <div class="defect-card">
                            <strong>{severity_icon} {defect.get('name', 'Unknown Defect')}</strong><br>
                            Status: {defect.get('status', 'Open')}<br>
                            <small>{defect.get('description', 'No description')[:100]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("Could not load defects")
            except:
                st.error("Connection to ALM Octane failed")
        else:
            st.warning("ALM Octane server offline")
    
    with col2:
        st.markdown("#### Jira Issues")
        if status['jira']['online']:
            try:
                response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/issues", timeout=5)
                if response.status_code == 200:
                    issues = response.json()[:5]
                    for issue in issues:
                        priority_icon = {"Blocker": "🔴", "Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(issue.get('priority', 'Low'), "⚪")
                        st.markdown(f"""
                        <div class="defect-card">
                            <strong>{priority_icon} {issue.get('key', 'Unknown')} - {issue.get('summary', 'Unknown Issue')}</strong><br>
                            Status: {issue.get('status', 'Open')}<br>
                            <small>{issue.get('description', 'No description')[:100]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("Could not load issues")
            except:
                st.error("Connection to Jira failed")
        else:
            st.warning("Jira server offline")

def render_defect_search():
    """Render defect search"""
    st.subheader("🔍 Search Defects & Issues")
    
    with st.form("search_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_text = st.text_input("Search Keywords")
        with col2:
            severity = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"])
        with col3:
            status_filter = st.selectbox("Status", ["All", "Open", "In Progress", "Resolved"])
        
        search_submitted = st.form_submit_button("🔍 Search")
    
    if search_submitted:
        st.info("Search would query both ALM Octane and Jira with the specified filters")
        
        if search_text:
            st.markdown(f"**Searching for:** {search_text}")
            st.markdown(f"**Filters:** Severity: {severity}, Status: {status_filter}")

def render_defect_creation():
    """Render defect creation"""
    st.subheader("➕ Create New Defect")
    
    with st.form("create_defect_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Defect Title*")
            severity = st.selectbox("Severity*", ["Low", "Medium", "High", "Critical"])
            component = st.text_input("Component/Service")
        
        with col2:
            description = st.text_area("Description*", height=100)
            target = st.selectbox("Create In*", ["ALM Octane", "Jira", "Both"])
            environment = st.selectbox("Environment", ["Development", "Test", "Staging", "Production"])
        
        # Incident correlation
        st.markdown("#### Link to Incident (Optional)")
        incident_id = st.text_input("Related Incident ID")
        
        create_submitted = st.form_submit_button("Create Defect")
    
    if create_submitted:
        if title and description:
            st.success(f"✅ Defect would be created in {target}")
            
            if target in ["ALM Octane", "Both"]:
                defect_id = f"ALM-{random.randint(1000, 9999)}"
                st.info(f"🔗 ALM Octane Defect ID: {defect_id}")
            
            if target in ["Jira", "Both"]:
                issue_key = f"BUG-{random.randint(100, 999)}"
                st.info(f"🔗 Jira Issue Key: {issue_key}")
        else:
            st.error("Please fill in required fields (Title and Description)")

def render_defect_analytics():
    """Render defect analytics"""
    st.subheader("📊 Defect Analytics")
    
    # Mock metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Open", "127", "-8")
    with col2:
        st.metric("Critical", "23", "+3")
    with col3:
        st.metric("Avg Resolution", "4.2 days", "-0.5")
    with col4:
        st.metric("Quality Score", "87%", "+2%")
    
    # Charts
    chart_tabs = st.tabs(["📈 Trends", "🎯 Severity", "⚡ Resolution Times"])
    
    with chart_tabs[0]:
        # Defect trend
        dates = pd.date_range(start='2025-07-01', end='2025-08-12', freq='D')
        defects = [random.randint(5, 25) for _ in dates]
        
        fig = px.line(x=dates, y=defects, title="Daily Defect Creation Trend")
        fig.update_layout(xaxis_title="Date", yaxis_title="Defects Created")
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_tabs[1]:
        # Severity distribution
        severities = ['Critical', 'High', 'Medium', 'Low']
        counts = [23, 45, 67, 34]
        
        fig = px.pie(values=counts, names=severities, title="Defects by Severity")
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_tabs[2]:
        # Resolution times
        resolution_data = pd.DataFrame({
            'Severity': ['Critical', 'High', 'Medium', 'Low'],
            'Avg Resolution (days)': [1.2, 2.8, 4.1, 6.5]
        })
        
        fig = px.bar(resolution_data, x='Severity', y='Avg Resolution (days)',
                    title="Resolution Time by Severity")
        st.plotly_chart(fig, use_container_width=True)

def render_correlation_scenarios():
    """Render defect correlation test scenarios"""
    st.header("🧪 Defect Correlation Test Scenarios")
    
    if not DEFECT_MANAGEMENT_AVAILABLE:
        st.warning("Defect correlation scenarios not available - modules not loaded")
        return
    
    st.markdown("""
    Test the defect correlation engine with realistic incident scenarios.
    Each scenario has been designed with known defect correlations to validate the analysis.
    """)
    
    try:
        scenarios_generator = DefectDrivenIncidentScenarios()
        scenarios = scenarios_generator.get_all_scenarios()
        
        scenario_names = [f"{s['scenario_id']}: {s['incident_title']}" for s in scenarios]
        selected_scenario = st.selectbox("Select Test Scenario", scenario_names)
        
        if selected_scenario:
            scenario_id = selected_scenario.split(':')[0]
            scenario = scenarios_generator.get_scenario(scenario_id)
            
            if scenario:
                # Display scenario details
                st.subheader(f"📋 Scenario: {scenario['incident_title']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Incident Details:**")
                    st.markdown(f"- **Severity:** {scenario['incident_severity']}")
                    st.markdown(f"- **Type:** {scenario['incident_type']}")
                    st.markdown(f"- **Services:** {', '.join(scenario['affected_services'])}")
                    st.markdown(f"- **Detection:** {scenario['detection_time']}")
                
                with col2:
                    st.markdown("**Expected Correlation:**")
                    st.markdown(f"- **Score:** {scenario['expected_correlation_score']:.1%}")
                    st.markdown(f"- **Confidence:** {scenario['confidence_level']}")
                    st.markdown(f"- **Root Cause:** {scenario['root_cause_type']}")
                
                # Scenario description
                st.markdown("**Incident Description:**")
                st.info(scenario['incident_description'])
                
                # Test correlation button
                if st.button("🔍 Test Correlation Analysis", key=f"test_{scenario_id}"):
                    st.markdown("---")
                    
                    with st.spinner("Running correlation analysis..."):
                        correlation_data = get_correlation_analysis(scenario['incident_description'])
                    
                    if correlation_data:
                        st.subheader("📊 Correlation Results")
                        
                        # Compare expected vs actual
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            expected = scenario['expected_correlation_score']
                            st.metric("Expected Score", f"{expected:.1%}")
                        
                        with col2:
                            actual = correlation_data['highest_correlation']
                            st.metric("Actual Score", f"{actual:.1%}")
                        
                        with col3:
                            accuracy = abs(expected - actual)
                            accuracy_color = "🟢" if accuracy < 0.1 else "🟡" if accuracy < 0.2 else "🔴"
                            st.metric("Accuracy", f"{accuracy_color} {(1-accuracy):.1%}")
                        
                        # Detailed results
                        st.markdown("**Analysis Results:**")
                        st.markdown(f"- **Correlations Found:** {correlation_data['total_correlations']}")
                        st.markdown(f"- **Defect Likelihood:** {correlation_data['defect_likelihood']}")
                        
                        if correlation_data['recommended_actions']:
                            st.markdown("**Recommendations:**")
                            for action in correlation_data['recommended_actions'][:3]:
                                st.markdown(f"- {action}")
    
    except Exception as e:
        st.error(f"Error loading scenarios: {str(e)}")

def main():
    """Main application"""
    st.markdown('<h1 class="main-header">🔍 SRE Copilot - Defect Management Integration</h1>', 
               unsafe_allow_html=True)
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'incident_analysis'
    
    # Navigation
    tabs = st.tabs([
        "🔍 Enhanced Root Cause Analysis",
        "🐛 Defect Management", 
        "🧪 Correlation Scenarios",
        "🌐 System Status"
    ])
    
    with tabs[0]:
        render_incident_analysis()
    
    with tabs[1]:
        render_defect_management()
    
    with tabs[2]:
        render_correlation_scenarios()
    
    with tabs[3]:
        st.header("🌐 System Status")
        
        st.subheader("Defect Management Servers")
        status = check_defect_servers()
        
        col1, col2 = st.columns(2)
        
        with col1:
            alm_status = "🟢 Online" if status['alm_octane']['online'] else "🔴 Offline"
            st.markdown(f"**ALM Octane**: {alm_status} (Port {MCP_PORTS['alm_octane']})")
            if status['alm_octane']['online']:
                st.markdown(f"Defects: {status['alm_octane']['defects']}")
        
        with col2:
            jira_status = "🟢 Online" if status['jira']['online'] else "🔴 Offline"
            st.markdown(f"**Jira**: {jira_status} (Port {MCP_PORTS['jira']})")
            if status['jira']['online']:
                st.markdown(f"Issues: {status['jira']['issues']}")
        
        st.subheader("Quick Tests")
        
        if st.button("🧪 Run System Test"):
            st.info("Running system readiness test...")
            
            # Run the test
            try:
                import subprocess
                result = subprocess.run(['python3', 'test_system_ready.py'], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    st.success("✅ All system tests passed!")
                    st.text(result.stdout)
                else:
                    st.error("❌ Some tests failed")
                    st.text(result.stderr)
            except Exception as e:
                st.error(f"Test execution failed: {str(e)}")

if __name__ == "__main__":
    main()
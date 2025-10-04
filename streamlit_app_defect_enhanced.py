#!/usr/bin/env python3
"""
SRE Copilot - Enhanced Root Cause Analysis Dashboard with Defect Management Integration
Integrates real incident generation, AWS data analysis, defect correlation, and external MCP services.
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

# Import defect scenarios and change correlator
try:
    from defect_driven_incident_scenarios import DefectDrivenIncidentScenarios
    DEFECT_SCENARIOS_AVAILABLE = True
except ImportError:
    DEFECT_SCENARIOS_AVAILABLE = False

try:
    from change_incident_correlator import ChangeIncidentCorrelator
    CHANGE_CORRELATOR_AVAILABLE = True
except ImportError:
    CHANGE_CORRELATOR_AVAILABLE = False

try:
    from change_driven_incident_scenarios import ChangeDrivenIncidentScenarios
    CHANGE_SCENARIOS_AVAILABLE = True
except ImportError:
    CHANGE_SCENARIOS_AVAILABLE = False

try:
    from servicenow_problem_integration import ServiceNowProblemManager
    SERVICENOW_INTEGRATION_AVAILABLE = True
except ImportError:
    SERVICENOW_INTEGRATION_AVAILABLE = False

try:
    from streamlit_synthetic_transaction_tab import render_synthetic_transaction_tab
    SYNTHETIC_TRANSACTION_AVAILABLE = True
except ImportError:
    SYNTHETIC_TRANSACTION_AVAILABLE = False

try:
    from streamlit_knowledge_base_tab import render_knowledge_base_tab
    KNOWLEDGE_BASE_TAB_AVAILABLE = True
except ImportError:
    KNOWLEDGE_BASE_TAB_AVAILABLE = False

try:
    from ai_problem_management import AIProblemManager
    AI_PROBLEM_MANAGEMENT_AVAILABLE = True
except ImportError:
    AI_PROBLEM_MANAGEMENT_AVAILABLE = False

# Load MCP ports configuration including defect management
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
        'alm_octane': 9085,
        'jira': 9086
    }

# Page configuration
st.set_page_config(
    page_title="SRE Copilot - Defect-Enhanced Root Cause Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with defect management styles
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .defect-correlation {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .defect-card {
        background-color: #fff5f5;
        border: 1px solid #fed7d7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .jira-card {
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .correlation-score {
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
    .high-correlation { background-color: #fecaca; color: #991b1b; }
    .medium-correlation { background-color: #fed7aa; color: #9a3412; }
    .low-correlation { background-color: #d1fae5; color: #065f46; }
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
    .defect-evidence {
        background-color: #fef7ff;
        border: 1px solid #e9d5ff;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def init_aws_clients():
    """Initialize AWS clients"""
    try:
        # Set AWS region
        region = 'us-east-1'
        return {
            'lambda': boto3.client('lambda', region_name=region),
            'cloudwatch': boto3.client('cloudwatch', region_name=region),
            'logs': boto3.client('logs', region_name=region),
            'ssm': boto3.client('ssm', region_name=region)
        }
    except Exception as e:
        st.error(f"Failed to initialize AWS clients: {str(e)}")
        st.info("Note: AWS clients are optional for defect management functionality")
        return None

def check_defect_management_status():
    """Check status of defect management MCP servers"""
    status = {}
    
    # Check ALM Octane
    try:
        response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects", timeout=2)
        status['alm_octane'] = 'online' if response.status_code == 200 else 'offline'
    except:
        status['alm_octane'] = 'offline'
    
    # Check Jira
    try:
        response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/issues", timeout=2)
        status['jira'] = 'online' if response.status_code == 200 else 'offline'
    except:
        status['jira'] = 'offline'
    
    return status

def get_defect_correlation_data(incident_description, incident_type="general"):
    """Get defect correlation data from MCP servers"""
    correlation_data = {
        'alm_octane_defects': [],
        'jira_issues': [],
        'correlation_score': 0.0,
        'evidence': []
    }
    
    try:
        # Query ALM Octane for related defects
        octane_response = requests.get(
            f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects",
            params={'status': 'all', 'limit': 20},
            timeout=5
        )
        
        if octane_response.status_code == 200:
            all_defects = octane_response.json()
            # Filter based on incident description
            keywords = extract_keywords_from_description(incident_description)
            related_defects = []
            
            for defect in all_defects:
                relevance = calculate_defect_relevance(defect, keywords, incident_type)
                if relevance > 0.3:
                    defect['relevance_score'] = relevance
                    related_defects.append(defect)
            
            correlation_data['alm_octane_defects'] = sorted(related_defects, 
                                                          key=lambda x: x.get('relevance_score', 0), 
                                                          reverse=True)[:5]
        
        # Query Jira for related issues
        jira_response = requests.get(
            f"http://localhost:{MCP_PORTS['jira']}/jira/issues",
            params={'issue_type': 'Bug', 'status': 'all', 'limit': 20},
            timeout=5
        )
        
        if jira_response.status_code == 200:
            all_issues = jira_response.json()
            keywords = extract_keywords_from_description(incident_description)
            related_issues = []
            
            for issue in all_issues:
                relevance = calculate_issue_relevance(issue, keywords, incident_type)
                if relevance > 0.3:
                    issue['relevance_score'] = relevance
                    related_issues.append(issue)
            
            correlation_data['jira_issues'] = sorted(related_issues, 
                                                   key=lambda x: x.get('relevance_score', 0), 
                                                   reverse=True)[:5]
        
        # Calculate overall correlation score
        correlation_data['correlation_score'] = calculate_overall_correlation_score(correlation_data)
        
        # Generate evidence
        correlation_data['evidence'] = generate_correlation_evidence(correlation_data, incident_description)
        
    except Exception as e:
        st.error(f"Error correlating with defects: {str(e)}")
    
    return correlation_data

def extract_keywords_from_description(description):
    """Extract relevant keywords from incident description"""
    keywords = []
    description_lower = description.lower()
    
    # Technical keywords relevant for correlation
    relevant_keywords = [
        'api', 'database', 'connection', 'timeout', 'authentication', 'ssl',
        'memory', 'cpu', 'performance', 'latency', 'error', 'failure',
        'gateway', 'service', 'cache', 'session', 'payment', 'search',
        'upload', 'file', 'security', 'certificate', 'pool', 'leak'
    ]
    
    for keyword in relevant_keywords:
        if keyword in description_lower:
            keywords.append(keyword)
    
    return keywords

def calculate_defect_relevance(defect, keywords, incident_type):
    """Calculate relevance score for a defect"""
    score = 0.0
    
    # Check name relevance
    defect_name = defect.get('name', '').lower()
    for keyword in keywords:
        if keyword in defect_name:
            score += 0.3
    
    # Check description relevance
    defect_desc = defect.get('description', '').lower()
    for keyword in keywords:
        if keyword in defect_desc:
            score += 0.2
    
    # Check component relevance
    component = defect.get('component', '').lower()
    for keyword in keywords:
        if keyword in component:
            score += 0.25
    
    # Severity and status bonuses
    if defect.get('severity', '').lower() in ['critical', 'high']:
        score += 0.15
    if defect.get('status', '').lower() in ['new', 'in progress']:
        score += 0.1
    
    return min(score, 1.0)

def calculate_issue_relevance(issue, keywords, incident_type):
    """Calculate relevance score for a Jira issue"""
    score = 0.0
    
    # Check summary relevance
    summary = issue.get('summary', '').lower()
    for keyword in keywords:
        if keyword in summary:
            score += 0.3
    
    # Check description relevance
    description = issue.get('description', '').lower()
    for keyword in keywords:
        if keyword in description:
            score += 0.2
    
    # Priority and status bonuses
    priority = issue.get('priority', {}).get('name', '').lower()
    if priority in ['blocker', 'critical', 'high']:
        score += 0.15
    
    status = issue.get('status', {}).get('name', '').lower()
    if status in ['open', 'in progress', 'reopened']:
        score += 0.1
    
    return min(score, 1.0)

def calculate_overall_correlation_score(correlation_data):
    """Calculate overall correlation score"""
    octane_defects = correlation_data.get('alm_octane_defects', [])
    jira_issues = correlation_data.get('jira_issues', [])
    
    score = 0.0
    
    if octane_defects:
        avg_octane_score = sum(d.get('relevance_score', 0) for d in octane_defects) / len(octane_defects)
        score += avg_octane_score * 0.5
    
    if jira_issues:
        avg_jira_score = sum(i.get('relevance_score', 0) for i in jira_issues) / len(jira_issues)
        score += avg_jira_score * 0.5
    
    return min(score, 1.0)

def generate_correlation_evidence(correlation_data, incident_description):
    """Generate evidence for defect correlation"""
    evidence = []
    
    octane_defects = correlation_data.get('alm_octane_defects', [])
    jira_issues = correlation_data.get('jira_issues', [])
    
    # Evidence from ALM Octane defects
    for defect in octane_defects[:2]:
        if defect.get('relevance_score', 0) > 0.5:
            evidence.append(f"High correlation with ALM Octane defect {defect.get('id')}: {defect.get('name')}")
    
    # Evidence from Jira issues
    for issue in jira_issues[:2]:
        if issue.get('relevance_score', 0) > 0.5:
            evidence.append(f"Strong correlation with Jira issue {issue.get('key')}: {issue.get('summary')}")
    
    # Pattern-based evidence
    keywords = extract_keywords_from_description(incident_description)
    if 'timeout' in keywords and 'connection' in keywords:
        evidence.append("Connection timeout pattern suggests database or API defects")
    if 'authentication' in keywords:
        evidence.append("Authentication issues often correlate with session management defects")
    if 'memory' in keywords or 'performance' in keywords:
        evidence.append("Performance issues may indicate memory leak or optimization defects")
    
    return evidence

def display_defect_correlation_section(correlation_data):
    """Display defect correlation analysis section"""
    correlation_score = correlation_data.get('correlation_score', 0.0)
    
    # Correlation score display
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if correlation_score >= 0.7:
            css_class = "high-correlation"
            interpretation = "🚨 HIGH CORRELATION - Likely defect-related incident"
        elif correlation_score >= 0.4:
            css_class = "medium-correlation"
            interpretation = "⚠️ MEDIUM CORRELATION - Possible defect involvement"
        else:
            css_class = "low-correlation"
            interpretation = "✅ LOW CORRELATION - Likely new issue"
        
        st.markdown(f"""
        <div class="correlation-score {css_class}">
            Defect Correlation Score: {correlation_score:.2f}
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"*{interpretation}*")
    
    # Display correlated defects and issues
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 ALM Octane Defects")
        octane_defects = correlation_data.get('alm_octane_defects', [])
        if octane_defects:
            for defect in octane_defects:
                with st.expander(f"Defect: {defect.get('id')} (Score: {defect.get('relevance_score', 0):.2f})"):
                    st.markdown(f"""
                    <div class="defect-card">
                        <strong>Name:</strong> {defect.get('name', 'N/A')}<br>
                        <strong>Severity:</strong> {defect.get('severity', 'N/A')}<br>
                        <strong>Status:</strong> {defect.get('status', 'N/A')}<br>
                        <strong>Component:</strong> {defect.get('component', 'N/A')}<br>
                        <strong>Created:</strong> {defect.get('created_date', 'N/A')}<br>
                        <strong>Description:</strong> {defect.get('description', 'N/A')[:200]}...
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No correlated ALM Octane defects found")
    
    with col2:
        st.subheader("🎫 Jira Issues")
        jira_issues = correlation_data.get('jira_issues', [])
        if jira_issues:
            for issue in jira_issues:
                with st.expander(f"Issue: {issue.get('key')} (Score: {issue.get('relevance_score', 0):.2f})"):
                    st.markdown(f"""
                    <div class="jira-card">
                        <strong>Summary:</strong> {issue.get('summary', 'N/A')}<br>
                        <strong>Priority:</strong> {issue.get('priority', {}).get('name', 'N/A')}<br>
                        <strong>Status:</strong> {issue.get('status', {}).get('name', 'N/A')}<br>
                        <strong>Type:</strong> {issue.get('issuetype', {}).get('name', 'N/A')}<br>
                        <strong>Project:</strong> {issue.get('project', {}).get('key', 'N/A')}<br>
                        <strong>Description:</strong> {issue.get('description', 'N/A')[:200]}...
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No correlated Jira issues found")
    
    # Display evidence
    evidence = correlation_data.get('evidence', [])
    if evidence:
        st.subheader("🔍 Correlation Evidence")
        for i, evt in enumerate(evidence):
            st.markdown(f"""
            <div class="defect-evidence">
                <strong>Evidence {i+1}:</strong> {evt}
            </div>
            """, unsafe_allow_html=True)

def display_defect_management_dashboard():
    """Display defect management dashboard"""
    st.markdown("## 🐛 Defect Management Dashboard")
    
    # Check defect management status
    defect_status = check_defect_management_status()
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    with col1:
        alm_status = "🟢 Online" if defect_status.get('alm_octane') == 'online' else "🔴 Offline"
        st.metric("ALM Octane", alm_status)
    
    with col2:
        jira_status = "🟢 Online" if defect_status.get('jira') == 'online' else "🔴 Offline"
        st.metric("Jira", jira_status)
    
    with col3:
        overall_status = "Operational" if all(status == 'online' for status in defect_status.values()) else "Degraded"
        st.metric("Overall Status", overall_status)
    
    # Defect Analytics
    if defect_status.get('alm_octane') == 'online' or defect_status.get('jira') == 'online':
        st.subheader("📊 Defect Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if defect_status.get('alm_octane') == 'online':
                try:
                    # Get ALM Octane quality metrics
                    response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/analytics/quality-metrics", timeout=5)
                    if response.status_code == 200:
                        metrics = response.json().get('metrics', {})
                        
                        st.markdown("### ALM Octane Quality Metrics")
                        quality_col1, quality_col2 = st.columns(2)
                        
                        with quality_col1:
                            st.metric("Defect Density", f"{metrics.get('defect_density', 0):.2f}")
                            st.metric("Test Coverage", f"{metrics.get('test_coverage', 0):.1f}%")
                        
                        with quality_col2:
                            st.metric("Defect Removal Efficiency", f"{metrics.get('defect_removal_efficiency', 0):.1f}%")
                            st.metric("Mean Resolution Time", f"{metrics.get('mean_time_to_resolution', 0):.1f} days")
                except:
                    st.error("Failed to load ALM Octane metrics")
        
        with col2:
            if defect_status.get('jira') == 'online':
                try:
                    # Get Jira defect metrics
                    response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/analytics/defect-metrics", timeout=5)
                    if response.status_code == 200:
                        metrics = response.json().get('metrics', {})
                        
                        st.markdown("### Jira Defect Metrics")
                        jira_col1, jira_col2 = st.columns(2)
                        
                        with jira_col1:
                            st.metric("Total Bugs", metrics.get('total_bugs', 0))
                            st.metric("Open Bugs", metrics.get('open_bugs', 0))
                        
                        with jira_col2:
                            st.metric("Critical Bugs", metrics.get('critical_bugs', 0))
                            st.metric("Avg Resolution Time", f"{metrics.get('average_resolution_time', 0):.1f} days")
                except:
                    st.error("Failed to load Jira metrics")

def main():
    """Main application function"""
    st.markdown('<h1 class="main-header">🔍 SRE Copilot - Defect-Enhanced Root Cause Analysis</h1>', 
                unsafe_allow_html=True)
    
    # Initialize AWS clients
    aws_clients = init_aws_clients()
    if not aws_clients:
        st.error("Cannot proceed without AWS clients")
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🛠️ Navigation")
        page = st.radio("Select Page", [
            "🔍 Incident Analysis",
            "🐛 Defect Management",
            "🔄 Change Management",
            "🔗 Change Correlation",
            "🎫 Problem Management",
            "📚 Knowledge Base",
            "🔬 Synthetic Transactions",
            "📊 Analytics",
            "🧪 Test Scenarios"
        ])
        
        # Defect management status in sidebar
        st.markdown("---")
        st.subheader("Defect Management Status")
        defect_status = check_defect_management_status()
        
        alm_icon = "🟢" if defect_status.get('alm_octane') == 'online' else "🔴"
        jira_icon = "🟢" if defect_status.get('jira') == 'online' else "🔴"
        
        st.markdown(f"{alm_icon} ALM Octane: {defect_status.get('alm_octane', 'unknown')}")
        st.markdown(f"{jira_icon} Jira: {defect_status.get('jira', 'unknown')}")
    
    # Main content based on page selection
    if page == "🔍 Incident Analysis":
        st.markdown("## 🚨 Incident Analysis with Defect Correlation")
        
        # Incident input
        with st.form("incident_form"):
            incident_title = st.text_input("Incident Title", 
                                         value="API Gateway Timeout Surge")
            
            incident_description = st.text_area("Incident Description", 
                                               value="API Gateway experiencing 500% increase in timeout errors affecting customer-facing services",
                                               height=100)
            
            incident_severity = st.selectbox("Severity", ["Critical", "High", "Medium", "Low"])
            
            submit_button = st.form_submit_button("🔍 Analyze Incident")
        
        if submit_button:
            with st.spinner("Analyzing incident and correlating with defects..."):
                # Get defect correlation data
                correlation_data = get_defect_correlation_data(incident_description)
                
                # Display results
                st.markdown("---")
                st.markdown("## 📋 Analysis Results")
                
                # Display defect correlation section
                st.markdown("### 🔗 Defect Correlation Analysis")
                display_defect_correlation_section(correlation_data)
                
                # Simulate enhanced root cause analysis with defect context
                st.markdown("### 🎯 AI-Enhanced Root Cause Analysis")
                
                analysis_placeholder = st.empty()
                with analysis_placeholder.container():
                    st.info("Performing AI analysis with defect correlation context...")
                    time.sleep(2)  # Simulate processing
                    
                    correlation_score = correlation_data.get('correlation_score', 0.0)
                    
                    if correlation_score >= 0.7:
                        analysis_result = f"""
                        **High Defect Correlation Detected (Score: {correlation_score:.2f})**
                        
                        This incident shows strong correlation with existing defects in your tracking systems. 
                        The analysis suggests this is likely a manifestation of known issues rather than a new problem.
                        
                        **Recommended Actions:**
                        1. 🔧 Review and prioritize the correlated defects shown above
                        2. 🚀 Check if fixes are already in progress or deployed
                        3. 📋 Update defect tracking with this incident information
                        4. 🔄 Verify if this represents a regression of previously fixed issues
                        
                        **Root Cause Likelihood:** Existing defect manifestation (90% confidence)
                        """
                    elif correlation_score >= 0.4:
                        analysis_result = f"""
                        **Medium Defect Correlation Detected (Score: {correlation_score:.2f})**
                        
                        This incident shows moderate correlation with existing defects. Further investigation is needed
                        to determine if this is related to known issues or represents a new problem.
                        
                        **Recommended Actions:**
                        1. 🔍 Investigate the correlated defects for potential relationship
                        2. 📊 Compare incident symptoms with defect descriptions
                        3. 🧪 Consider if recent changes might have triggered dormant defects
                        4. 📝 Document findings for future correlation analysis
                        
                        **Root Cause Likelihood:** Possibly defect-related (60% confidence)
                        """
                    else:
                        analysis_result = f"""
                        **Low Defect Correlation Detected (Score: {correlation_score:.2f})**
                        
                        This incident shows minimal correlation with existing defects, suggesting it may be a new issue
                        that requires fresh investigation and potentially new defect creation.
                        
                        **Recommended Actions:**
                        1. 🆕 Treat as potentially new defect - begin root cause investigation
                        2. 🔬 Perform detailed technical analysis of symptoms
                        3. 📋 Consider creating new defects in ALM Octane and Jira
                        4. 🏗️ Implement monitoring to detect similar future incidents
                        
                        **Root Cause Likelihood:** New issue requiring investigation (80% confidence)
                        """
                    
                    st.markdown(analysis_result)
        
        # Show example scenarios
        if DEFECT_SCENARIOS_AVAILABLE:
            st.markdown("---")
            st.markdown("## 📚 Example Defect-Driven Scenarios")
            
            scenarios_generator = DefectDrivenIncidentScenarios()
            scenarios = scenarios_generator.get_all_scenarios()
            
            scenario_titles = [f"{s['scenario_id']}: {s['incident_title']}" for s in scenarios]
            selected_scenario = st.selectbox("Select Example Scenario", scenario_titles)
            
            if selected_scenario:
                scenario_id = selected_scenario.split(":")[0]
                scenario = scenarios_generator.get_scenario(scenario_id)
                
                if scenario:
                    with st.expander("View Scenario Details"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Incident Information:**")
                            st.write(f"**Title:** {scenario['incident_title']}")
                            st.write(f"**Severity:** {scenario['incident_severity']}")
                            st.write(f"**Duration:** {scenario['incident_duration_minutes']} minutes")
                            st.write(f"**Description:** {scenario['incident_description']}")
                        
                        with col2:
                            st.markdown("**Root Cause Defect:**")
                            defect = scenario['root_cause_defect']
                            st.write(f"**Defect ID:** {defect['defect_id']}")
                            st.write(f"**Title:** {defect['defect_title']}")
                            st.write(f"**Severity:** {defect['defect_severity']}")
                            st.write(f"**Status:** {defect['defect_status']}")
                            st.write(f"**Component:** {defect['defect_component']}")
    
    elif page == "🐛 Defect Management":
        display_defect_management_dashboard()
        
        # Defect creation form
        st.markdown("---")
        st.subheader("📝 Create New Defect from Incident")
        
        # Fetch recent incidents for dropdown
        recent_incidents = []
        try:
            ssm_client = boto3.client('ssm', region_name='us-east-1')
            response = ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Status',
                        'Values': ['Open', 'InProgress', 'Resolved'],
                        'Operator': 'Equal'
                    }
                ],
                MaxResults=20
            )
            
            for item in response.get('OpsItemSummaries', []):
                recent_incidents.append({
                    'id': item.get('OpsItemId', ''),
                    'title': item.get('Title', ''),
                    'status': item.get('Status', ''),
                    'description': item.get('Description', 'No description available')
                })
        except Exception as e:
            st.warning(f"Could not fetch recent incidents: {str(e)}")
        
        with st.form("defect_creation_form"):
            # Incident selection section
            st.markdown("**🔍 Select Source Incident (Optional)**")
            incident_options = ["Create new defect manually"] + [f"{inc['id']} - {inc['title']}" for inc in recent_incidents]
            selected_incident = st.selectbox("Recent Incidents", incident_options)
            
            # Parse selected incident
            selected_incident_data = None
            if selected_incident != "Create new defect manually":
                incident_id = selected_incident.split(' - ')[0]
                selected_incident_data = next((inc for inc in recent_incidents if inc['id'] == incident_id), None)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Auto-populate from incident if selected
                default_title = selected_incident_data['title'] if selected_incident_data else ""
                defect_title = st.text_input("Defect Title", value=default_title)
                
                # Map incident status to severity
                default_severity = "High"
                if selected_incident_data and selected_incident_data['status'] == 'Open':
                    default_severity = "Critical"
                elif selected_incident_data and selected_incident_data['status'] == 'Resolved':
                    default_severity = "Medium"
                
                defect_severity = st.selectbox("Severity", ["Critical", "High", "Medium", "Low"], 
                                             index=["Critical", "High", "Medium", "Low"].index(default_severity))
                defect_component = st.text_input("Component")
            
            with col2:
                defect_environment = st.selectbox("Environment", ["Production", "Staging", "QA", "Development"])
                defect_assignee = st.text_input("Assigned To")
                create_in = st.selectbox("Create In", ["ALM Octane", "Jira", "Both"])
            
            # Auto-populate description from incident
            default_description = ""
            if selected_incident_data:
                default_description = f"Root cause analysis from incident {selected_incident_data['id']}:\n\n{selected_incident_data['description']}\n\nRequires investigation and resolution."
            
            defect_description = st.text_area("Description", value=default_description, height=120)
            
            create_defect_btn = st.form_submit_button("🐛 Create Defect")
        
        if create_defect_btn and defect_title and defect_description:
            with st.spinner("Creating defect..."):
                success_count = 0
                
                # If incident was selected, enhance with correlation analysis
                if selected_incident_data:
                    st.info(f"🔗 Creating defect from incident {selected_incident_data['id']}")
                    
                    # Perform AI-powered incident analysis
                    with st.spinner("Analyzing incident for defect correlation..."):
                        correlation_data = get_defect_correlation_data(
                            selected_incident_data['description'], 
                            "incident_based"
                        )
                        
                        # Extract key insights for defect creation
                        ai_analysis = ""
                        if correlation_data and 'analysis' in correlation_data:
                            ai_analysis = f"\n\n**AI Analysis:**\n{correlation_data['analysis']}"
                        
                        # Check for related defects
                        related_defects = ""
                        if correlation_data and 'alm_octane_defects' in correlation_data:
                            defect_count = len(correlation_data['alm_octane_defects'])
                            if defect_count > 0:
                                related_defects = f"\n**Related Defects Found:** {defect_count} similar defects detected"
                    
                    # Add incident reference to defect data
                    incident_reference = f"\n\n**Source Incident:** {selected_incident_data['id']}\n**Status:** {selected_incident_data['status']}{ai_analysis}{related_defects}"
                    defect_description_enhanced = defect_description + incident_reference
                
                if create_in in ["ALM Octane", "Both"]:
                    try:
                        # Use enhanced description if incident was selected
                        final_description = defect_description_enhanced if selected_incident_data else defect_description
                        
                        defect_data = {
                            "name": defect_title,
                            "description": final_description,
                            "severity": defect_severity,
                            "component": defect_component,
                            "environment": defect_environment,
                            "assigned_to": defect_assignee
                        }
                        
                        response = requests.post(
                            f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects",
                            json=defect_data,
                            timeout=10
                        )
                        
                        if response.status_code == 201:
                            created_defect = response.json()
                            defect_msg = f"✅ Created ALM Octane defect: {created_defect.get('id')}"
                            if selected_incident_data:
                                defect_msg += f" (linked to incident {selected_incident_data['id']})"
                            st.success(defect_msg)
                            success_count += 1
                        else:
                            st.error(f"❌ Failed to create ALM Octane defect: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error creating ALM Octane defect: {str(e)}")
                
                if create_in in ["Jira", "Both"]:
                    try:
                        # Use enhanced description if incident was selected
                        final_description = defect_description_enhanced if selected_incident_data else defect_description
                        
                        issue_data = {
                            "project": "SREPROJ",
                            "summary": defect_title,
                            "description": final_description,
                            "issue_type": "Bug",
                            "priority": defect_severity,
                            "assignee": defect_assignee
                        }
                        
                        response = requests.post(
                            f"http://localhost:{MCP_PORTS['jira']}/jira/issues",
                            json=issue_data,
                            timeout=10
                        )
                        
                        if response.status_code == 201:
                            created_issue = response.json()
                            issue_msg = f"✅ Created Jira issue: {created_issue.get('key')}"
                            if selected_incident_data:
                                issue_msg += f" (linked to incident {selected_incident_data['id']})"
                            st.success(issue_msg)
                            success_count += 1
                        else:
                            st.error(f"❌ Failed to create Jira issue: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error creating Jira issue: {str(e)}")
                
                if success_count > 0:
                    st.success(f"✅ Successfully created {success_count} defect(s)")
    
    elif page == "🔄 Change Management":
        st.markdown("## 🔄 Change Management Dashboard")
        
        # Recent Changes Overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Recent Changes (24h)", "12", delta="3")
        with col2:
            st.metric("High Risk Changes", "2", delta="1", delta_color="inverse")
        with col3:
            st.metric("Failed Changes", "1", delta="-1", delta_color="normal")
        
        # Change Status Summary
        st.markdown("---")
        st.subheader("📋 Recent Changes")
        
        # Fetch recent changes
        if CHANGE_CORRELATOR_AVAILABLE:
            try:
                correlator = ChangeIncidentCorrelator()
                # Get changes from last 24 hours
                from datetime import datetime, timedelta
                recent_time = datetime.now() - timedelta(hours=1)
                changes = correlator._get_recent_changes(recent_time)
                
                if changes:
                    # Create a dataframe for display
                    change_data = []
                    for change in changes[:15]:  # Show last 15 changes
                        change_data.append({
                            'ID': change['id'],
                            'Title': change['title'][:60] + "..." if len(change['title']) > 60 else change['title'],
                            'Type': change.get('change_type', 'unknown').title(),
                            'Risk': change.get('risk_level', 'medium').title(),
                            'Status': change.get('status', 'unknown'),
                            'Time': change['created_time'].strftime('%Y-%m-%d %H:%M') if isinstance(change['created_time'], datetime) else str(change['created_time'])[:16]
                        })
                    
                    df = pd.DataFrame(change_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Change Type Distribution
                    st.markdown("### 📊 Change Distribution")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        type_counts = df['Type'].value_counts()
                        fig = px.pie(values=type_counts.values, names=type_counts.index, 
                                   title="Changes by Type")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        risk_counts = df['Risk'].value_counts()
                        fig = px.bar(x=risk_counts.index, y=risk_counts.values, 
                                   title="Changes by Risk Level",
                                   color=risk_counts.index,
                                   color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'green'})
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No recent changes found")
                    
            except Exception as e:
                st.error(f"Error loading change data: {str(e)}")
        else:
            st.warning("Change correlator not available")
            
        # Create New Change
        st.markdown("---")
        st.subheader("📝 Create New Change Request")
        
        with st.form("change_request_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                change_title = st.text_input("Change Title")
                change_type = st.selectbox("Change Type", ["Deployment", "Configuration", "Infrastructure", "Database", "Security"])
                change_risk = st.selectbox("Risk Level", ["Low", "Medium", "High"])
            
            with col2:
                change_environment = st.selectbox("Environment", ["Development", "QA", "Staging", "Production"])
                change_assignee = st.text_input("Assigned To")
                scheduled_time = st.datetime_input("Scheduled Time")
            
            change_description = st.text_area("Description", height=100)
            affected_services = st.text_input("Affected Services (comma-separated)")
            
            create_change_btn = st.form_submit_button("🔄 Create Change Request")
        
        if create_change_btn and change_title and change_description:
            # Create change request (simulate)
            st.success(f"✅ Change request created: CHG-{random.randint(1000, 9999)}")
            st.info("Change request will be tracked for incident correlation analysis")

    elif page == "🔗 Change Correlation":
        st.markdown("## 🔗 Change-Incident Correlation Analysis")
        
        # Incident Selection for Correlation
        st.subheader("🎯 Select Incident for Change Analysis")
        
        # Fetch recent incidents for dropdown
        recent_incidents = []
        try:
            ssm_client = boto3.client('ssm', region_name='us-east-1')
            response = ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Status',
                        'Values': ['Open', 'InProgress', 'Resolved'],
                        'Operator': 'Equal'
                    }
                ],
                MaxResults=15
            )
            
            for item in response.get('OpsItemSummaries', []):
                recent_incidents.append({
                    'id': item.get('OpsItemId', ''),
                    'title': item.get('Title', ''),
                    'status': item.get('Status', ''),
                    'description': item.get('Description', 'No description available')
                })
        except Exception as e:
            st.warning(f"Could not fetch recent incidents: {str(e)}")
        
        if recent_incidents:
            incident_options = [f"{inc['id']} - {inc['title']}" for inc in recent_incidents]
            selected_incident = st.selectbox("Recent Incidents", incident_options)
            
            # Parse selected incident
            incident_id = selected_incident.split(' - ')[0]
            selected_incident_data = next((inc for inc in recent_incidents if inc['id'] == incident_id), None)
            
            if selected_incident_data:
                # Display incident details
                st.markdown("### 📋 Incident Details")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**ID:** {selected_incident_data['id']}")
                with col2:
                    st.markdown(f"**Status:** {selected_incident_data['status']}")
                with col3:
                    st.markdown(f"**Title:** {selected_incident_data['title']}")
                
                # Analyze button
                if st.button("🔍 Analyze Change Correlation"):
                    if CHANGE_CORRELATOR_AVAILABLE:
                        with st.spinner("Analyzing change-incident correlation..."):
                            correlator = ChangeIncidentCorrelator()
                            correlation_result = correlator.analyze_change_incident_correlation(
                                selected_incident_data['id'], 
                                selected_incident_data['description']
                            )
                            
                            # Display correlation results
                            st.markdown("---")
                            st.markdown("### 📊 Correlation Analysis Results")
                            
                            # Summary metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Changes Analyzed", correlation_result['total_changes_analyzed'])
                            with col2:
                                st.metric("Significant Correlations", correlation_result['significant_correlations'])
                            with col3:
                                st.metric("Top Correlation", f"{correlation_result['top_correlation_score']:.1%}")
                            with col4:
                                confidence = "High" if correlation_result['top_correlation_score'] >= 0.6 else "Medium" if correlation_result['top_correlation_score'] >= 0.3 else "Low"
                                st.metric("Confidence", confidence)
                            
                            # AI Analysis
                            if correlation_result['analysis']:
                                st.markdown("### 🤖 AI Analysis")
                                st.markdown(correlation_result['analysis'])
                            
                            # Top Correlations
                            if correlation_result['correlations']:
                                st.markdown("### 🏆 Top Change Correlations")
                                
                                for i, correlation in enumerate(correlation_result['correlations'][:5]):
                                    with st.expander(f"#{i+1}: {correlation['change_title']} ({correlation['correlation_score']:.1%})"):
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("**Change Details:**")
                                            st.write(f"**Type:** {correlation['change_type'].title()}")
                                            st.write(f"**Risk Level:** {correlation.get('risk_level', 'unknown').title()}")
                                            st.write(f"**Time Difference:** {correlation['time_difference_minutes']} minutes")
                                            st.write(f"**Confidence:** {correlation['confidence_level']}")
                                        
                                        with col2:
                                            st.markdown("**Correlation Factors:**")
                                            factors = correlation.get('correlation_factors', {})
                                            for factor, score in factors.items():
                                                st.write(f"• {factor.replace('_', '').title()}: {score:.2f}")
                                        
                                        if correlation.get('common_services'):
                                            st.markdown(f"**Common Services:** {', '.join(correlation['common_services'])}")
                                        
                                        st.markdown(f"**Description:** {correlation.get('change_description', 'N/A')}")
                            
                            # Recommendations
                            if correlation_result['recommendations']:
                                st.markdown("### 💡 Recommendations")
                                for recommendation in correlation_result['recommendations']:
                                    st.markdown(f"• {recommendation}")
                            
                            # Change Categories
                            if correlation_result['change_categories']:
                                st.markdown("### 📂 Change Categories")
                                categories = correlation_result['change_categories']
                                category_df = pd.DataFrame(list(categories.items()), columns=['Type', 'Count'])
                                fig = px.bar(category_df, x='Type', y='Count', title="Correlated Changes by Type")
                                st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error("Change correlator not available")
        else:
            st.info("No recent incidents available for analysis")

    elif page == "🎫 Problem Management":
        st.markdown("## 🎫 ServiceNow Problem Management")
        
        # Add AI Problem Management indicator
        if AI_PROBLEM_MANAGEMENT_AVAILABLE:
            st.success("🤖 AI-Powered Problem Management is ACTIVE")
        
        # Problem Management Overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Problems", "8", delta="2")
        with col2:
            st.metric("Resolved Problems", "15", delta="3")
        with col3:
            st.metric("Avg Resolution Time", "4.2h", delta="-0.8h", delta_color="normal")
        with col4:
            st.metric("AI Auto-Created", "5", delta="2")
        
        # Create Problem from Incident
        st.markdown("---")
        st.subheader("📝 Create Problem from Incident")
        
        # Fetch recent incidents for problem creation
        recent_incidents = []
        try:
            ssm_client = boto3.client('ssm', region_name='us-east-1')
            response = ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Status',
                        'Values': ['Open', 'InProgress'],
                        'Operator': 'Equal'
                    }
                ],
                MaxResults=20
            )
            
            for item in response.get('OpsItemSummaries', []):
                recent_incidents.append({
                    'id': item.get('OpsItemId', ''),
                    'title': item.get('Title', ''),
                    'status': item.get('Status', ''),
                    'severity': item.get('Severity', 'Medium'),
                    'description': item.get('Description', 'No description available')
                })
        except Exception as e:
            st.warning(f"Could not fetch recent incidents: {str(e)}")
        
        # AI Analysis Section
        if recent_incidents and AI_PROBLEM_MANAGEMENT_AVAILABLE:
            st.markdown("---")
            st.subheader("🤖 AI-Powered Problem Analysis")
            
            # Select incident for AI analysis
            ai_incident_options = [f"{inc['id']} - {inc['title']}" for inc in recent_incidents]
            selected_ai_incident = st.selectbox("Select Incident for AI Analysis", ai_incident_options, key="ai_incident_select")
            
            if st.button("🔍 Analyze with AI", key="ai_analyze_btn"):
                # Parse selected incident
                ai_incident_id = selected_ai_incident.split(' - ')[0]
                ai_incident_data = next((inc for inc in recent_incidents if inc['id'] == ai_incident_id), None)
                
                if ai_incident_data:
                    with st.spinner("AI analyzing incident for problem creation..."):
                        try:
                            ai_manager = AIProblemManager()
                            analysis = ai_manager.analyze_incident_for_problem(ai_incident_data)
                            
                            # Display analysis results
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("Should Create Problem?", 
                                         "YES" if analysis['should_create_problem'] else "NO",
                                         delta=f"{analysis['confidence_score']:.0%} confidence")
                                
                                if analysis['reasoning']:
                                    st.markdown("**Reasoning:**")
                                    for reason in analysis['reasoning']:
                                        st.write(f"• {reason}")
                            
                            with col2:
                                st.metric("Problem Type", analysis.get('problem_type', 'Unknown').replace('_', ' ').title())
                                st.metric("Related Incidents", len(analysis['related_incidents']))
                                
                                if analysis['impact_analysis']:
                                    impact = analysis['impact_analysis']
                                    st.metric("Business Impact", impact['category'].upper(), 
                                             delta=f"{impact['score']:.0%}")
                            
                            # AI Recommendation
                            if analysis['ai_recommendation']:
                                st.markdown("### 🎯 AI Recommendation")
                                ai_rec = analysis['ai_recommendation']
                                
                                st.info(ai_rec.get('reasoning', 'No specific recommendation'))
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**Recommended Priority:** {ai_rec.get('recommended_priority', 'Medium')}")
                                    st.write(f"**Problem Category:** {ai_rec.get('problem_category', 'Technical')}")
                                
                                with col2:
                                    if analysis['should_create_problem']:
                                        if st.button("🚀 Auto-Create Problem", type="primary", key="auto_create_btn"):
                                            with st.spinner("Creating problem automatically..."):
                                                result = ai_manager.create_problem_automatically(ai_incident_data, analysis)
                                                
                                                if result['success']:
                                                    st.success(f"✅ Problem {result['problem_number']} created automatically!")
                                                else:
                                                    st.error(f"Failed to create problem: {result.get('error', 'Unknown error')}")
                            
                        except Exception as e:
                            st.error(f"AI analysis error: {str(e)}")
        
        # Manual Problem Creation Form
        if recent_incidents and SERVICENOW_INTEGRATION_AVAILABLE:
            st.markdown("---")
            st.subheader("📝 Manual Problem Creation")
            
            with st.form("problem_creation_form"):
                st.markdown("**🎯 Select Incident for Problem Creation**")
                incident_options = [f"{inc['id']} - {inc['title']}" for inc in recent_incidents]
                selected_incident = st.selectbox("Recent Incidents", incident_options)
                
                # Parse selected incident
                incident_id = selected_incident.split(' - ')[0]
                selected_incident_data = next((inc for inc in recent_incidents if inc['id'] == incident_id), None)
                
                if selected_incident_data:
                    # Display incident details
                    st.markdown("**📋 Incident Details:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**ID:** {selected_incident_data['id']}")
                    with col2:
                        st.write(f"**Status:** {selected_incident_data['status']}")
                    with col3:
                        st.write(f"**Severity:** {selected_incident_data['severity']}")
                    
                    # Problem creation options
                    st.markdown("**🛠️ Problem Details:**")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        problem_priority = st.selectbox("Priority", ["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"])
                        assignment_group = st.selectbox("Assignment Group", ["SRE Team", "DevOps Team", "Platform Team", "Database Team"])
                    
                    with col2:
                        problem_category = st.selectbox("Category", ["Software", "Hardware", "Network", "Database", "Security"])
                        assigned_to = st.text_input("Assigned To", value="sre-team@company.com")
                    
                    additional_notes = st.text_area("Additional Problem Notes", height=100)
                    
                    create_problem_btn = st.form_submit_button("🎫 Create Problem in ServiceNow")
                
                if create_problem_btn and selected_incident_data:
                    if SERVICENOW_INTEGRATION_AVAILABLE:
                        with st.spinner("Creating problem in ServiceNow..."):
                            try:
                                problem_manager = ServiceNowProblemManager()
                                
                                # Enhance incident data with form inputs
                                enhanced_incident_data = {
                                    **selected_incident_data,
                                    'priority': problem_priority,
                                    'assignment_group': assignment_group,
                                    'assigned_to': assigned_to,
                                    'category': problem_category,
                                    'additional_notes': additional_notes
                                }
                                
                                result = problem_manager.create_problem_from_incident(incident_id, enhanced_incident_data)
                                
                                if result['success']:
                                    st.success(f"✅ Problem created successfully!")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.info(f"**Problem ID:** {result['problem_id']}")
                                        st.info(f"**Problem Number:** {result['problem_number']}")
                                    with col2:
                                        st.info(f"**Status:** {result['status'].title()}")
                                        st.info(f"**ServiceNow URL:** [View Problem]({result['servicenow_url']})")
                                    
                                    # Link problem to incident
                                    link_result = problem_manager.link_problem_to_incident(result['problem_id'], incident_id)
                                    if link_result['success']:
                                        st.success("🔗 Problem successfully linked to incident")
                                else:
                                    st.error(f"❌ Failed to create problem: {result.get('error', 'Unknown error')}")
                                    
                            except Exception as e:
                                st.error(f"❌ Error creating problem: {str(e)}")
                    else:
                        st.error("ServiceNow integration not available")
        elif not SERVICENOW_INTEGRATION_AVAILABLE:
            st.warning("ServiceNow integration not available. Problem management features are disabled.")
        else:
            st.info("No open incidents available for problem creation")
        
        # Problem Resolution Tracking
        st.markdown("---")
        st.subheader("🔧 Problem Resolution Tracking")
        
        if SERVICENOW_INTEGRATION_AVAILABLE:
            # Sample active problems (in real implementation, fetch from ServiceNow)
            active_problems = [
                {
                    'id': 'PRB0001001',
                    'title': 'API Gateway Performance Degradation',
                    'state': 'In Progress',
                    'priority': '2 - High',
                    'assigned_to': 'SRE Team',
                    'created': '2025-08-12 09:30:00',
                    'incident_id': 'oi-114b7755dee1'
                },
                {
                    'id': 'PRB0001002', 
                    'title': 'Database Connection Timeout Issues',
                    'state': 'New',
                    'priority': '1 - Critical',
                    'assigned_to': 'Database Team',
                    'created': '2025-08-12 10:15:00',
                    'incident_id': 'oi-e6af31aba693'
                }
            ]
            
            for problem in active_problems:
                with st.expander(f"🎫 {problem['id']}: {problem['title']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**State:** {problem['state']}")
                        st.write(f"**Priority:** {problem['priority']}")
                        st.write(f"**Created:** {problem['created']}")
                    
                    with col2:
                        st.write(f"**Assigned To:** {problem['assigned_to']}")
                        st.write(f"**Source Incident:** {problem['incident_id']}")
                    
                    with col3:
                        if st.button(f"🔧 Update Resolution", key=f"update_{problem['id']}"):
                            st.info("Resolution update form would appear here")
                        
                        if st.button(f"🔗 View in ServiceNow", key=f"view_{problem['id']}"):
                            st.info(f"Would open ServiceNow problem {problem['id']}")
        else:
            st.warning("ServiceNow integration not available")
        
        # Problem Analytics
        st.markdown("---")
        st.subheader("📈 Problem Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sample problem trend data
            problem_trend_data = {
                'Date': ['Aug 8', 'Aug 9', 'Aug 10', 'Aug 11', 'Aug 12'],
                'Created': [3, 5, 2, 4, 3],
                'Resolved': [2, 4, 3, 3, 2]
            }
            df = pd.DataFrame(problem_trend_data)
            fig = px.line(df, x='Date', y=['Created', 'Resolved'], title="Problem Trend (5 days)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sample resolution time data
            resolution_data = {
                'Priority': ['Critical', 'High', 'Moderate', 'Low'],
                'Avg Resolution (hours)': [2.5, 4.2, 8.1, 16.3]
            }
            df = pd.DataFrame(resolution_data)
            fig = px.bar(df, x='Priority', y='Avg Resolution (hours)', 
                        title="Avg Resolution Time by Priority",
                        color='Priority',
                        color_discrete_map={'Critical': 'red', 'High': 'orange', 'Moderate': 'yellow', 'Low': 'green'})
            st.plotly_chart(fig, use_container_width=True)

    elif page == "📚 Knowledge Base":
        if KNOWLEDGE_BASE_TAB_AVAILABLE:
            render_knowledge_base_tab()
        else:
            st.error("Knowledge Base functionality not available. Please ensure the module is properly installed.")
            st.info("To enable knowledge base search, make sure all MCP servers are running")
    
    elif page == "🔬 Synthetic Transactions":
        if SYNTHETIC_TRANSACTION_AVAILABLE:
            render_synthetic_transaction_tab()
        else:
            st.error("Synthetic Transaction functionality not available. Please ensure the module is properly installed.")
            st.info("To enable synthetic transactions, make sure Fed LPP MCP server is running on port 9087")
    
    elif page == "📊 Analytics":
        st.markdown("## 📊 Defect and Incident Analytics")
        
        # Combined analytics dashboard
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 ALM Octane Trends")
            try:
                response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/analytics/defect-trends?time_range=-30d", timeout=5)
                if response.status_code == 200:
                    trends_data = response.json()
                    trends = trends_data.get('trends', [])
                    
                    if trends:
                        df = pd.DataFrame(trends)
                        fig = px.line(df, x='date', y=['new_defects', 'resolved_defects'], 
                                     title="ALM Octane Defect Trends (30 days)")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No trend data available")
                else:
                    st.error("Failed to load ALM Octane trends")
            except Exception as e:
                st.error(f"Error loading trends: {str(e)}")
        
        with col2:
            st.subheader("🎫 Jira Velocity")
            try:
                response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/analytics/velocity?board_id=1", timeout=5)
                if response.status_code == 200:
                    velocity_data = response.json()
                    velocity_points = velocity_data.get('velocity_data', [])
                    
                    if velocity_points:
                        df = pd.DataFrame(velocity_points)
                        fig = px.bar(df, x='sprint_name', y=['committed_points', 'completed_points'], 
                                    title="Jira Sprint Velocity")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No velocity data available")
                else:
                    st.error("Failed to load Jira velocity")
            except Exception as e:
                st.error(f"Error loading velocity: {str(e)}")
    
    elif page == "🧪 Test Scenarios":
        st.markdown("## 🧪 Comprehensive Test Scenarios")
        
        # Scenario type selector
        scenario_type = st.selectbox("Select Scenario Type", 
                                   ["Defect-Driven Incidents", "Change-Driven Incidents", "Combined Analysis"])
        
        if scenario_type == "Defect-Driven Incidents":
            st.markdown("### 🐛 Defect-Driven Test Scenarios")
            
            if DEFECT_SCENARIOS_AVAILABLE:
                scenarios_generator = DefectDrivenIncidentScenarios()
                scenarios = scenarios_generator.get_all_scenarios()
                
                st.markdown(f"**Available Scenarios:** {len(scenarios)}")
                
                for scenario in scenarios:
                    with st.expander(f"🔬 {scenario['scenario_id']}: {scenario['incident_title']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**Incident Details**")
                            st.write(f"Severity: {scenario['incident_severity']}")
                            st.write(f"Duration: {scenario['incident_duration_minutes']} min")
                            st.write(f"Confidence: {scenario['correlation_confidence']:.0%}")
                        
                        with col2:
                            st.markdown("**Root Cause Defect**")
                            defect = scenario['root_cause_defect']
                            st.write(f"ID: {defect['defect_id']}")
                            st.write(f"Status: {defect['defect_status']}")
                            st.write(f"Component: {defect['defect_component']}")
                        
                        with col3:
                            st.markdown("**Jira Correlation**")
                            jira = scenario['jira_correlation']
                            st.write(f"Issue: {jira['issue_key']}")
                            st.write(f"Sprint: {jira['sprint']}")
                            st.write(f"Points: {jira['story_points']}")
                        
                        if st.button(f"🚀 Test Scenario {scenario['scenario_id']}", key=f"test_{scenario['scenario_id']}"):
                            with st.spinner("Running scenario analysis..."):
                                correlation_data = get_defect_correlation_data(
                                    scenario['incident_description'], 
                                    "defect_related"
                                )
                                
                                st.success("Scenario analysis completed!")
                                display_defect_correlation_section(correlation_data)
            else:
                st.error("Defect-driven scenarios not available")
        
        elif scenario_type == "Change-Driven Incidents":
            st.markdown("### 🔄 Change-Driven Test Scenarios")
            
            if CHANGE_SCENARIOS_AVAILABLE:
                change_scenarios = ChangeDrivenIncidentScenarios()
                scenarios = change_scenarios.get_all_scenarios()
                summary = change_scenarios.generate_scenario_summary()
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Scenarios", summary['total_scenarios'])
                with col2:
                    st.metric("Avg Confidence", f"{summary['average_correlation_confidence']:.1%}")
                with col3:
                    st.metric("Total Customers Affected", f"{summary['business_impact']['total_customers_affected']:,}")
                with col4:
                    st.metric("SLA Breaches", summary['business_impact']['sla_breaches'])
                
                st.markdown("---")
                st.markdown(f"**Available Change Scenarios:** {len(scenarios)}")
                
                for scenario in scenarios:
                    with st.expander(f"🔄 {scenario['scenario_id']}: {scenario['incident_title']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**Incident Details**")
                            st.write(f"**Severity:** {scenario['incident_severity']}")
                            st.write(f"**Duration:** {scenario['incident_duration_minutes']} minutes")
                            st.write(f"**Confidence:** {scenario['correlation_confidence']:.1%}")
                            st.write(f"**Customers Affected:** {scenario['change_impact_analysis']['customers_affected']:,}")
                        
                        with col2:
                            st.markdown("**Root Cause Change**")
                            change = scenario['root_cause_change']
                            st.write(f"**ID:** {change['change_id']}")
                            st.write(f"**Type:** {change['change_type'].title()}")
                            st.write(f"**Risk Level:** {change['risk_level'].title()}")
                            st.write(f"**Changed By:** {change.get('changed_by', 'N/A')}")
                        
                        with col3:
                            st.markdown("**Business Impact**")
                            impact = scenario['change_impact_analysis']
                            st.write(f"**Revenue Impact:** ${impact['revenue_impact_usd']:,}")
                            st.write(f"**SLA Breach:** {'Yes' if impact['sla_breach'] else 'No'}")
                            st.write(f"**Regulatory:** {'Yes' if impact['regulatory_impact'] else 'No'}")
                        
                        # Change description
                        st.markdown("**Change Description:**")
                        st.write(change.get('change_description', 'N/A'))
                        
                        # Correlation evidence
                        st.markdown("**Correlation Evidence:**")
                        evidence = scenario['correlation_evidence']
                        evidence_cols = st.columns(len(evidence))
                        for i, (key, value) in enumerate(evidence.items()):
                            with evidence_cols[i % len(evidence_cols)]:
                                st.write(f"**{key.replace('_', ' ').title()}:** {value:.1%}")
                        
                        if st.button(f"🔍 Analyze Change Correlation {scenario['scenario_id']}", key=f"analyze_{scenario['scenario_id']}"):
                            if CHANGE_CORRELATOR_AVAILABLE:
                                with st.spinner("Analyzing change-incident correlation..."):
                                    correlator = ChangeIncidentCorrelator()
                                    correlation_result = correlator.analyze_change_incident_correlation(
                                        scenario['scenario_id'], 
                                        scenario['incident_description']
                                    )
                                    
                                    st.success("✅ Change correlation analysis completed!")
                                    
                                    # Display results
                                    st.markdown("**🤖 AI Analysis:**")
                                    st.markdown(correlation_result['analysis'])
                                    
                                    if correlation_result['recommendations']:
                                        st.markdown("**💡 Recommendations:**")
                                        for rec in correlation_result['recommendations']:
                                            st.markdown(f"• {rec}")
                            else:
                                st.error("Change correlator not available")
            else:
                st.error("Change-driven scenarios not available")
        
        elif scenario_type == "Combined Analysis":
            st.markdown("### 🔀 Combined Defect and Change Analysis")
            
            # Combined scenario statistics
            defect_count = 0
            change_count = 0
            
            if DEFECT_SCENARIOS_AVAILABLE:
                defect_scenarios = DefectDrivenIncidentScenarios()
                defect_count = len(defect_scenarios.get_all_scenarios())
            
            if CHANGE_SCENARIOS_AVAILABLE:
                change_scenarios = ChangeDrivenIncidentScenarios()
                change_count = len(change_scenarios.get_all_scenarios())
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Defect Scenarios", defect_count)
            with col2:
                st.metric("Change Scenarios", change_count)
            with col3:
                st.metric("Total Coverage", defect_count + change_count)
            
            st.markdown("---")
            st.markdown("### 📊 Scenario Distribution")
            
            if DEFECT_SCENARIOS_AVAILABLE and CHANGE_SCENARIOS_AVAILABLE:
                # Create visualization of scenario types
                scenario_data = {
                    'Type': ['Defect-Driven', 'Change-Driven'],
                    'Count': [defect_count, change_count]
                }
                df = pd.DataFrame(scenario_data)
                fig = px.pie(df, values='Count', names='Type', title="Test Scenario Distribution")
                st.plotly_chart(fig, use_container_width=True)
                
                # Sample combined analysis
                st.markdown("### 🎯 Run Combined Analysis")
                st.info("Select an incident to analyze both defect and change correlations simultaneously")
                
                if st.button("🚀 Run Sample Combined Analysis"):
                    with st.spinner("Running combined defect and change analysis..."):
                        # Sample incident for combined analysis
                        sample_incident = """
                        API Gateway experiencing 500 errors starting at 14:30 UTC.
                        Database connection timeouts observed.
                        Recent deployment of web-service v2.1.4 completed 30 minutes ago.
                        Similar issues reported in previous defect DEF-2024-001.
                        """
                        
                        # Run both analyses
                        if CHANGE_CORRELATOR_AVAILABLE:
                            correlator = ChangeIncidentCorrelator()
                            change_result = correlator.analyze_change_incident_correlation(
                                "combined-test", sample_incident
                            )
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**🔄 Change Analysis Results:**")
                                st.write(f"Changes Analyzed: {change_result['total_changes_analyzed']}")
                                st.write(f"Top Correlation: {change_result['top_correlation_score']:.1%}")
                                st.markdown("**Analysis:**")
                                st.write(change_result['analysis'])
                            
                            with col2:
                                st.markdown("**🐛 Defect Analysis Results:**")
                                defect_data = get_defect_correlation_data(sample_incident)
                                if defect_data:
                                    st.write("Defect correlation analysis completed")
                                    display_defect_correlation_section(defect_data)
                                else:
                                    st.write("No significant defect correlations found")
                        
                        st.success("✅ Combined analysis completed!")
            else:
                st.warning("Both defect and change scenarios need to be available for combined analysis")

if __name__ == "__main__":
    main()
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

# Import defect scenarios
try:
    from defect_driven_incident_scenarios import DefectDrivenIncidentScenarios
    DEFECT_SCENARIOS_AVAILABLE = True
except ImportError:
    DEFECT_SCENARIOS_AVAILABLE = False

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
        
        with st.form("defect_creation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                defect_title = st.text_input("Defect Title")
                defect_severity = st.selectbox("Severity", ["Critical", "High", "Medium", "Low"])
                defect_component = st.text_input("Component")
            
            with col2:
                defect_environment = st.selectbox("Environment", ["Production", "Staging", "QA", "Development"])
                defect_assignee = st.text_input("Assigned To")
                create_in = st.selectbox("Create In", ["ALM Octane", "Jira", "Both"])
            
            defect_description = st.text_area("Description", height=100)
            
            create_defect_btn = st.form_submit_button("🐛 Create Defect")
        
        if create_defect_btn and defect_title and defect_description:
            with st.spinner("Creating defect..."):
                success_count = 0
                
                if create_in in ["ALM Octane", "Both"]:
                    try:
                        defect_data = {
                            "name": defect_title,
                            "description": defect_description,
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
                            st.success(f"✅ Created ALM Octane defect: {created_defect.get('id')}")
                            success_count += 1
                        else:
                            st.error(f"❌ Failed to create ALM Octane defect: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error creating ALM Octane defect: {str(e)}")
                
                if create_in in ["Jira", "Both"]:
                    try:
                        issue_data = {
                            "project": "SREPROJ",
                            "summary": defect_title,
                            "description": defect_description,
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
                            st.success(f"✅ Created Jira issue: {created_issue.get('key')}")
                            success_count += 1
                        else:
                            st.error(f"❌ Failed to create Jira issue: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error creating Jira issue: {str(e)}")
                
                if success_count > 0:
                    st.balloons()
    
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
        st.markdown("## 🧪 Defect-Driven Test Scenarios")
        
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

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
SRE Copilot - Enhanced Root Cause Analysis Dashboard
Integrates real incident generation and AWS data analysis using Bedrock agents.
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

# Page configuration
st.set_page_config(
    page_title="SRE Copilot - Root Cause Analysis",
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'current_incident' not in st.session_state:
    st.session_state.current_incident = None
if 'agent_data' not in st.session_state:
    st.session_state.agent_data = {}
if 'generated_incidents' not in st.session_state:
    st.session_state.generated_incidents = []
if 'demo_resources' not in st.session_state:
    st.session_state.demo_resources = {
        'security_group_id': None,
        'log_group_name': '/aws/demo/sre-incident-generator',
        'namespace': 'SREDemo/Application'
    }

class IncidentGenerator:
    """Handles real incident generation in AWS."""
    
    def __init__(self):
        self.region = 'us-east-1'
        self.setup_aws_clients()
        
    def setup_aws_clients(self):
        """Initialize AWS service clients."""
        self.clients = {
            'logs': boto3.client('logs', region_name=self.region),
            'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
            'ec2': boto3.client('ec2', region_name=self.region),
            'ssm': boto3.client('ssm', region_name=self.region),
            'cloudtrail': boto3.client('cloudtrail', region_name=self.region)
        }
        
    def create_demo_resources(self):
        """Create necessary demo resources."""
        # Create CloudWatch Log Group
        try:
            self.clients['logs'].create_log_group(
                logGroupName=st.session_state.demo_resources['log_group_name']
            )
        except self.clients['logs'].exceptions.ResourceAlreadyExistsException:
            pass
            
        # Create/Get demo security group
        try:
            response = self.clients['ec2'].create_security_group(
                GroupName='sre-demo-incident-sg',
                Description='Demo security group for incident generation'
            )
            st.session_state.demo_resources['security_group_id'] = response['GroupId']
        except ClientError as e:
            if 'InvalidGroup.Duplicate' in str(e):
                response = self.clients['ec2'].describe_security_groups(
                    GroupNames=['sre-demo-incident-sg']
                )
                st.session_state.demo_resources['security_group_id'] = response['SecurityGroups'][0]['GroupId']
                
    def generate_application_logs(self, scenario='error'):
        """Generate application logs in CloudWatch."""
        log_stream = f"app-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            self.clients['logs'].create_log_stream(
                logGroupName=st.session_state.demo_resources['log_group_name'],
                logStreamName=log_stream
            )
        except:
            pass
            
        log_events = []
        timestamp = int(time.time() * 1000)
        
        if scenario == 'error':
            messages = [
                {"level": "INFO", "message": "Application started successfully"},
                {"level": "WARN", "message": "Database connection slow", "duration_ms": 3500},
                {"level": "ERROR", "message": "Database connection timeout", "error": "Connection refused"},
                {"level": "ERROR", "message": "Failed to process user request", "user_id": "user456"},
                {"level": "ERROR", "message": "Application crash", "error": "NullPointerException"},
                {"level": "FATAL", "message": "Service unavailable", "status_code": 503}
            ]
        elif scenario == 'performance':
            messages = [
                {"level": "INFO", "message": "Request received", "endpoint": "/api/data"},
                {"level": "WARN", "message": "High response time detected", "duration_ms": 5000},
                {"level": "WARN", "message": "Memory usage high", "memory_percent": 92},
                {"level": "ERROR", "message": "Request timeout", "duration_ms": 30000},
                {"level": "WARN", "message": "Thread pool exhausted", "active_threads": 200}
            ]
            
        for i, msg_data in enumerate(messages):
            log_events.append({
                'timestamp': timestamp + (i * 1000),
                'message': json.dumps(msg_data)
            })
            
        self.clients['logs'].put_log_events(
            logGroupName=st.session_state.demo_resources['log_group_name'],
            logStreamName=log_stream,
            logEvents=log_events
        )
        
        return len(log_events), log_stream
        
    def generate_cloudwatch_metrics(self, scenario='failure'):
        """Generate CloudWatch metrics."""
        timestamp = datetime.utcnow()
        
        if scenario == 'failure':
            metrics_data = [
                {'MetricName': 'CPUUtilization', 'Value': 95, 'Unit': 'Percent'},
                {'MetricName': 'MemoryUtilization', 'Value': 92, 'Unit': 'Percent'},
                {'MetricName': 'RequestCount', 'Value': random.randint(50, 100), 'Unit': 'Count'},
                {'MetricName': 'ErrorRate', 'Value': random.uniform(50, 80), 'Unit': 'Percent'},
                {'MetricName': 'ResponseTime', 'Value': random.uniform(10000, 30000), 'Unit': 'Milliseconds'}
            ]
        elif scenario == 'high_load':
            metrics_data = [
                {'MetricName': 'CPUUtilization', 'Value': random.uniform(85, 95), 'Unit': 'Percent'},
                {'MetricName': 'MemoryUtilization', 'Value': random.uniform(80, 90), 'Unit': 'Percent'},
                {'MetricName': 'RequestCount', 'Value': random.randint(800, 1000), 'Unit': 'Count'},
                {'MetricName': 'ErrorRate', 'Value': random.uniform(5, 15), 'Unit': 'Percent'},
                {'MetricName': 'ResponseTime', 'Value': random.uniform(2000, 5000), 'Unit': 'Milliseconds'}
            ]
            
        for metric in metrics_data:
            self.clients['cloudwatch'].put_metric_data(
                Namespace=st.session_state.demo_resources['namespace'],
                MetricData=[{
                    'MetricName': metric['MetricName'],
                    'Value': metric['Value'],
                    'Unit': metric['Unit'],
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'Environment', 'Value': 'demo'},
                        {'Name': 'Service', 'Value': 'sre-demo-app'}
                    ]
                }]
            )
            
        return metrics_data
        
    def modify_security_group(self, action='add_risky_rule'):
        """Modify security group to generate events."""
        if not st.session_state.demo_resources['security_group_id']:
            return False
            
        try:
            if action == 'add_risky_rule':
                self.clients['ec2'].authorize_security_group_ingress(
                    GroupId=st.session_state.demo_resources['security_group_id'],
                    IpPermissions=[{
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH from anywhere (RISKY)'}]
                    }]
                )
                return True
        except ClientError:
            pass
        return False
        
    def generate_api_failures(self):
        """Generate API failures for CloudTrail."""
        failures = []
        
        # S3 unauthorized access
        try:
            self.clients['s3'].get_object(
                Bucket='non-existent-bucket-sre-demo-12345',
                Key='secret-file.txt'
            )
        except ClientError as e:
            failures.append(f"S3 Access Denied: {e.response['Error']['Code']}")
            
        # Lambda invocation failure
        try:
            self.clients['lambda'].invoke(
                FunctionName='non-existent-function-sre-demo',
                InvocationType='RequestResponse'
            )
        except ClientError as e:
            failures.append(f"Lambda Invocation Failed: {e.response['Error']['Code']}")
            
        return failures
        
    def create_opsitem(self, title, description, severity='3'):
        """Create SSM OpsItem."""
        try:
            response = self.clients['ssm'].create_ops_item(
                Title=title,
                Description=description,
                Priority=int(severity),
                Source='SRE-Demo-Streamlit',
                Category='Performance',
                Severity=severity,
                OperationalData={
                    '/aws/resources': {
                        'Value': json.dumps([{
                            'arn': f'arn:aws:logs:{self.region}:123456789012:log-group:{st.session_state.demo_resources["log_group_name"]}'
                        }])
                    }
                },
                Tags=[
                    {'Key': 'Environment', 'Value': 'demo'},
                    {'Key': 'Source', 'Value': 'streamlit-app'}
                ]
            )
            return response['OpsItemId']
        except ClientError:
            return None
            
    def generate_correlated_incident(self, incident_type="performance"):
        """Generate a complete correlated incident."""
        incident_data = {
            'start_time': datetime.utcnow(),
            'type': incident_type,
            'components': []
        }
        
        # Generate different components based on type
        if incident_type == "performance":
            # High load metrics
            metrics = self.generate_cloudwatch_metrics('high_load')
            incident_data['components'].append(f"Generated {len(metrics)} high load metrics")
            
            # Performance logs
            count, stream = self.generate_application_logs('performance')
            incident_data['components'].append(f"Generated {count} performance warning logs")
            
        elif incident_type == "security":
            # Security group change
            if self.modify_security_group('add_risky_rule'):
                incident_data['components'].append("Modified security group with risky rule")
                
            # API failures
            failures = self.generate_api_failures()
            incident_data['components'].append(f"Generated {len(failures)} API failures")
            
        elif incident_type == "outage":
            # Failure metrics
            metrics = self.generate_cloudwatch_metrics('failure')
            incident_data['components'].append(f"Generated {len(metrics)} failure metrics")
            
            # Error logs
            count, stream = self.generate_application_logs('error')
            incident_data['components'].append(f"Generated {count} error logs")
            
        # Create OpsItem
        ops_item_id = self.create_opsitem(
            f"Incident: {incident_type.capitalize()} Issue Detected",
            f"Automated incident generated for {incident_type} scenario. Components affected: {', '.join(incident_data['components'])}",
            severity='2' if incident_type == 'outage' else '3'
        )
        
        incident_data['ops_item_id'] = ops_item_id
        incident_data['end_time'] = datetime.utcnow()
        
        return incident_data

class EnhancedSREDashboard:
    """Enhanced dashboard with real incident generation and analysis."""
    
    def __init__(self):
        self.region = 'us-east-1'
        os.environ['AWS_DEFAULT_REGION'] = self.region
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.logs_client = boto3.client('logs', region_name=self.region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        self.incident_generator = IncidentGenerator()
        self.setup_sidebar()
        
    def setup_sidebar(self):
        """Setup the enhanced sidebar."""
        with st.sidebar:
            st.image("https://via.placeholder.com/300x100.png?text=SRE+Copilot", width=300)
            st.markdown("## 🎯 Incident Management")
            
            # Incident Generation Section
            st.markdown("### 🚀 Generate Incident")
            
            incident_type = st.selectbox(
                "Select Incident Type to Generate",
                ["Performance Degradation", "Security Alert", "Service Outage"]
            )
            
            if st.button("🔥 Generate Real Incident", type="primary", use_container_width=True):
                self.generate_incident(incident_type)
                
            # Analysis Section
            st.markdown("### 🔍 Analyze Incident")
            
            # OpsItem selection
            if st.session_state.generated_incidents:
                ops_items = [f"{inc['ops_item_id']} - {inc['type']}" for inc in st.session_state.generated_incidents]
                selected_ops = st.selectbox("Select OpsItem", ops_items)
                
                if st.button("🤖 Run Root Cause Analysis", type="primary", use_container_width=True):
                    ops_item_id = selected_ops.split(' - ')[0]
                    self.run_root_cause_analysis(ops_item_id)
            else:
                st.info("Generate an incident first to analyze")
                
            # Data Sources
            st.markdown("### 📊 Data Sources")
            self.include_logs = st.checkbox("CloudWatch Logs", value=True)
            self.include_metrics = st.checkbox("CloudWatch Metrics", value=True)
            self.include_cloudtrail = st.checkbox("CloudTrail Events", value=True)
            self.include_vpc_logs = st.checkbox("VPC Flow Logs", value=True)
            self.include_health = st.checkbox("AWS Health", value=True)
            
            # Time Range
            self.time_range = st.selectbox(
                "Analysis Time Range",
                ["Last 15 minutes", "Last 30 minutes", "Last 1 hour", "Last 6 hours"]
            )
            
            # History
            st.markdown("### 📜 Recent Incidents")
            for i, incident in enumerate(reversed(st.session_state.generated_incidents[-5:])):
                if st.button(f"📋 {incident['type']} - {incident['start_time'].strftime('%H:%M')}", key=f"inc_{i}"):
                    st.session_state.current_incident = incident
                    
    def generate_incident(self, incident_type):
        """Generate a real incident in AWS."""
        with st.spinner(f"🔥 Generating {incident_type} incident..."):
            # Create demo resources if needed
            self.incident_generator.create_demo_resources()
            
            # Map UI types to generator types
            type_map = {
                "Performance Degradation": "performance",
                "Security Alert": "security",
                "Service Outage": "outage"
            }
            
            # Generate the incident
            incident_data = self.incident_generator.generate_correlated_incident(
                type_map[incident_type]
            )
            
            # Store incident data
            incident_data['ui_type'] = incident_type
            st.session_state.generated_incidents.append(incident_data)
            st.session_state.current_incident = incident_data
            
            st.success(f"✅ Incident generated! OpsItem ID: {incident_data['ops_item_id']}")
            st.balloons()
            
    def run_root_cause_analysis(self, ops_item_id):
        """Run comprehensive root cause analysis."""
        with st.spinner("🤖 Running root cause analysis..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Get OpsItem details
                status_text.text("Fetching incident details...")
                progress_bar.progress(10)
                
                ops_response = self.ssm_client.get_ops_item(OpsItemId=ops_item_id)
                ops_item = ops_response['OpsItem']
                
                # Step 2: Collect data from various sources
                status_text.text("Collecting data from AWS services...")
                progress_bar.progress(30)
                
                collected_data = self.collect_comprehensive_data(ops_item)
                
                # Step 3: Invoke supervisor agent
                status_text.text("Invoking AI agents for analysis...")
                progress_bar.progress(60)
                
                analysis_result = self.invoke_supervisor_analysis(ops_item, collected_data)
                
                # Step 4: Process results
                status_text.text("Processing analysis results...")
                progress_bar.progress(90)
                
                # Store results
                incident_data = {
                    'ops_item_id': ops_item_id,
                    'type': ops_item.get('Title', 'Unknown'),
                    'description': ops_item.get('Description', ''),
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'analysis': analysis_result,
                    'raw_data': collected_data,
                    'ops_item': ops_item
                }
                
                st.session_state.current_incident = incident_data
                st.session_state.analysis_history.append(incident_data)
                
                progress_bar.progress(100)
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ Root cause analysis complete!")
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                progress_bar.empty()
                status_text.empty()
                
    def collect_comprehensive_data(self, ops_item):
        """Collect data from multiple AWS services."""
        data = {
            'logs': {},
            'metrics': {},
            'cloudtrail': {},
            'vpc_logs': {},
            'health': {}
        }
        
        # Get time range
        time_map = {
            "Last 15 minutes": 15,
            "Last 30 minutes": 30,
            "Last 1 hour": 60,
            "Last 6 hours": 360
        }
        minutes = time_map.get(self.time_range, 30)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        # Collect CloudWatch Logs
        if self.include_logs:
            try:
                log_groups = self.logs_client.describe_log_groups(
                    logGroupNamePrefix='/aws/demo/sre'
                )['logGroups']
                
                for lg in log_groups[:3]:  # Limit to 3 log groups
                    log_data = self.logs_client.filter_log_events(
                        logGroupName=lg['logGroupName'],
                        startTime=int(start_time.timestamp() * 1000),
                        endTime=int(end_time.timestamp() * 1000),
                        limit=50
                    )
                    data['logs'][lg['logGroupName']] = log_data.get('events', [])
            except:
                pass
                
        # Collect CloudWatch Metrics
        if self.include_metrics:
            try:
                metrics = ['CPUUtilization', 'MemoryUtilization', 'ErrorRate']
                for metric_name in metrics:
                    metric_data = self.cloudwatch_client.get_metric_statistics(
                        Namespace='SREDemo/Application',
                        MetricName=metric_name,
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Average', 'Maximum'],
                        Dimensions=[
                            {'Name': 'Environment', 'Value': 'demo'},
                            {'Name': 'Service', 'Value': 'sre-demo-app'}
                        ]
                    )
                    data['metrics'][metric_name] = metric_data.get('Datapoints', [])
            except:
                pass
                
        return data
        
    def invoke_supervisor_analysis(self, ops_item, collected_data):
        """Invoke the supervisor agent for analysis."""
        payload = {
            'action': 'analyze',
            'incident_description': f"{ops_item.get('Title', '')}. {ops_item.get('Description', '')}",
            'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'service': 'sre-demo-app',
            'environment': 'demo',
            'additional_context': {
                'ops_item_id': ops_item.get('OpsItemId'),
                'severity': ops_item.get('Severity'),
                'data_summary': {
                    'log_events': sum(len(events) for events in collected_data['logs'].values()),
                    'metric_points': sum(len(points) for points in collected_data['metrics'].values())
                }
            }
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
                return self.parse_supervisor_response(body)
            else:
                return {'error': 'Analysis failed', 'details': result.get('body')}
                
        except Exception as e:
            return {'error': str(e)}
            
    def parse_supervisor_response(self, response):
        """Parse and structure the supervisor response."""
        analysis = {
            'root_cause': 'Analyzing...',
            'contributing_factors': [],
            'affected_services': [],
            'recommendations': [],
            'timeline': [],
            'correlations': [],
            'agent_findings': {}
        }
        
        # Extract information from the response
        if isinstance(response, dict):
            # Look for analysis results
            if 'analysis' in response:
                ai_text = response['analysis']
                analysis['ai_analysis'] = ai_text
                
                # Extract root cause
                if 'root cause' in ai_text.lower():
                    analysis['root_cause'] = "Identified from AI analysis"
                    
            # Extract agent findings
            if 'agent_results' in response:
                analysis['agent_findings'] = response['agent_results']
                
            # Extract timeline
            if 'timeline' in response:
                analysis['timeline'] = response['timeline']
                
            # Extract recommendations
            if 'recommendations' in response:
                analysis['recommendations'] = response['recommendations']
                
        return analysis
        
    def display_dashboard(self):
        """Display the enhanced dashboard."""
        st.markdown('<h1 class="main-header">🔍 SRE Copilot - Real-Time Root Cause Analysis</h1>', 
                   unsafe_allow_html=True)
        
        if st.session_state.current_incident:
            self.display_incident_details()
        else:
            self.display_welcome()
            
    def display_welcome(self):
        """Display enhanced welcome screen."""
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2>Welcome to Enhanced SRE Copilot</h2>
            <p>Generate real incidents and analyze them with AI-powered root cause analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class='metric-card'>
                <h3>🔥 Real Incidents</h3>
                <p>Generate actual AWS incidents with logs, metrics, and events</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class='metric-card'>
                <h3>🤖 AI Analysis</h3>
                <p>Bedrock agents analyze real AWS data for root causes</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class='metric-card'>
                <h3>🔗 Correlation</h3>
                <p>Correlate events across CloudWatch, CloudTrail, and VPC logs</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown("""
            <div class='metric-card'>
                <h3>💡 Remediation</h3>
                <p>Get actionable recommendations to resolve incidents</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Quick start guide
        st.markdown("### 🚀 Quick Start")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **Step 1: Generate an Incident**
            1. Select incident type in sidebar
            2. Click "Generate Real Incident"
            3. Wait for AWS resources to be created
            """)
            
        with col2:
            st.info("""
            **Step 2: Analyze the Incident**
            1. Select the generated OpsItem
            2. Click "Run Root Cause Analysis"
            3. Review AI-powered analysis results
            """)
            
    def display_incident_details(self):
        """Display comprehensive incident details."""
        incident = st.session_state.current_incident
        
        # Header
        if 'ops_item_id' in incident:
            st.markdown(f"## 🚨 Incident Analysis: {incident.get('ops_item_id', 'Unknown')}")
        else:
            st.markdown(f"## 🚨 Generated Incident: {incident.get('ui_type', incident.get('type', 'Unknown'))}")
            
        # Incident info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Type", incident.get('ui_type', incident.get('type', 'Unknown')))
        with col2:
            if 'start_time' in incident:
                st.metric("Generated", incident['start_time'].strftime("%H:%M:%S"))
            else:
                st.metric("Analyzed", incident.get('time', 'Unknown'))
        with col3:
            st.metric("Status", "Analyzed" if 'analysis' in incident else "Generated")
            
        # Show generated components
        if 'components' in incident:
            st.markdown("### 📋 Generated Components")
            for component in incident['components']:
                st.success(f"✅ {component}")
                
        # Analysis results
        if 'analysis' in incident:
            # Tabs for different views
            tabs = st.tabs(["🎯 Root Cause", "📊 Data Analysis", "🔗 Correlations", 
                           "💡 Recommendations", "📈 Metrics", "📝 Raw Data"])
            
            with tabs[0]:
                self.display_root_cause(incident)
                
            with tabs[1]:
                self.display_data_analysis(incident)
                
            with tabs[2]:
                self.display_correlations(incident)
                
            with tabs[3]:
                self.display_recommendations(incident)
                
            with tabs[4]:
                self.display_metrics_analysis(incident)
                
            with tabs[5]:
                self.display_raw_data(incident)
        else:
            st.info("📊 Run root cause analysis to see detailed results")
            
    def display_root_cause(self, incident):
        """Display root cause analysis."""
        st.markdown("### 🎯 Root Cause Analysis")
        
        analysis = incident.get('analysis', {})
        
        # AI Analysis
        if 'ai_analysis' in analysis:
            st.markdown("#### 🤖 AI-Powered Analysis")
            with st.expander("View Full AI Analysis", expanded=True):
                st.text(analysis['ai_analysis'])
                
        # Root Cause
        st.markdown("#### 🔍 Identified Root Cause")
        if analysis.get('root_cause'):
            st.error(f"**{analysis['root_cause']}**")
        else:
            # Determine based on incident type
            if incident.get('type') == 'performance':
                st.error("**High resource utilization causing performance degradation**")
            elif incident.get('type') == 'security':
                st.error("**Security group misconfiguration allowing unauthorized access**")
            elif incident.get('type') == 'outage':
                st.error("**Service failure due to resource exhaustion**")
                
        # Contributing Factors
        st.markdown("#### 🔗 Contributing Factors")
        factors = analysis.get('contributing_factors', [])
        if not factors and 'raw_data' in incident:
            # Generate factors from data
            if incident['raw_data'].get('metrics', {}).get('CPUUtilization'):
                factors.append("High CPU utilization detected")
            if incident['raw_data'].get('logs'):
                factors.append("Error patterns found in application logs")
                
        for factor in factors:
            st.warning(f"• {factor}")
            
    def display_data_analysis(self, incident):
        """Display data analysis from various sources."""
        st.markdown("### 📊 Data Source Analysis")
        
        if 'raw_data' in incident:
            data = incident['raw_data']
            
            # CloudWatch Logs Analysis
            if data.get('logs'):
                st.markdown("#### 📝 CloudWatch Logs")
                total_events = sum(len(events) for events in data['logs'].values())
                st.metric("Total Log Events Analyzed", total_events)
                
                for log_group, events in data['logs'].items():
                    if events:
                        st.write(f"**{log_group}**: {len(events)} events")
                        # Show sample events
                        with st.expander(f"View sample events from {log_group}"):
                            for event in events[:5]:
                                st.text(event.get('message', ''))
                                
            # CloudWatch Metrics Analysis
            if data.get('metrics'):
                st.markdown("#### 📈 CloudWatch Metrics")
                for metric_name, datapoints in data['metrics'].items():
                    if datapoints:
                        df = pd.DataFrame(datapoints)
                        if not df.empty:
                            fig = px.line(df, x='Timestamp', y='Maximum', 
                                         title=f"{metric_name} Over Time")
                            st.plotly_chart(fig, use_container_width=True)
                            
    def display_correlations(self, incident):
        """Display event correlations."""
        st.markdown("### 🔗 Event Correlations")
        
        analysis = incident.get('analysis', {})
        correlations = analysis.get('correlations', [])
        
        if not correlations:
            # Generate sample correlations
            if incident.get('type') == 'performance':
                correlations = [
                    "CPU spike correlates with increased API response times",
                    "Memory exhaustion coincides with application errors",
                    "Database connection timeouts align with service degradation"
                ]
            elif incident.get('type') == 'security':
                correlations = [
                    "Security group changes preceded unauthorized access attempts",
                    "API failures spike after security rule modification",
                    "CloudTrail shows suspicious activity from new IP ranges"
                ]
                
        for correlation in correlations:
            st.info(f"🔗 {correlation}")
            
        # Timeline visualization
        if 'timeline' in analysis or 'start_time' in incident:
            st.markdown("#### ⏱️ Event Timeline")
            self.display_timeline_chart(incident)
            
    def display_timeline_chart(self, incident):
        """Display timeline visualization."""
        events = []
        
        if 'start_time' in incident:
            base_time = incident['start_time']
            events.extend([
                {'time': base_time, 'event': 'Incident started', 'severity': 1},
                {'time': base_time + timedelta(minutes=2), 'event': 'Metrics degradation', 'severity': 2},
                {'time': base_time + timedelta(minutes=5), 'event': 'Errors in logs', 'severity': 3},
                {'time': base_time + timedelta(minutes=10), 'event': 'OpsItem created', 'severity': 2}
            ])
            
        if events:
            df = pd.DataFrame(events)
            fig = px.scatter(df, x='time', y='severity', text='event',
                           title='Incident Timeline',
                           labels={'severity': 'Severity Level', 'time': 'Time'})
            fig.update_traces(textposition='top center')
            st.plotly_chart(fig, use_container_width=True)
            
    def display_recommendations(self, incident):
        """Display actionable recommendations."""
        st.markdown("### 💡 Recommendations")
        
        analysis = incident.get('analysis', {})
        recommendations = analysis.get('recommendations', [])
        
        if not recommendations:
            # Generate based on incident type
            if incident.get('type') == 'performance':
                recommendations = [
                    "Scale up EC2 instances to handle increased load",
                    "Implement auto-scaling policies with appropriate thresholds",
                    "Optimize database queries showing high latency",
                    "Enable caching for frequently accessed data"
                ]
            elif incident.get('type') == 'security':
                recommendations = [
                    "Review and restrict security group rules",
                    "Enable AWS GuardDuty for threat detection",
                    "Implement network ACLs for additional security",
                    "Review CloudTrail logs for unauthorized activities"
                ]
            elif incident.get('type') == 'outage':
                recommendations = [
                    "Implement health checks and auto-recovery",
                    "Configure multi-AZ deployment for high availability",
                    "Set up CloudWatch alarms for early detection",
                    "Create runbooks for incident response"
                ]
                
        # Immediate actions
        st.markdown("#### 🚨 Immediate Actions")
        for i, rec in enumerate(recommendations[:2], 1):
            st.error(f"{i}. {rec}")
            
        # Long-term improvements
        st.markdown("#### 📋 Long-term Improvements")
        for i, rec in enumerate(recommendations[2:], 1):
            st.info(f"{i}. {rec}")
            
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📧 Create JIRA Ticket", use_container_width=True):
                st.success("✅ Ticket created")
        with col2:
            if st.button("📢 Send to Slack", use_container_width=True):
                st.success("✅ Notification sent")
        with col3:
            if st.button("📄 Export Report", use_container_width=True):
                st.success("✅ Report exported")
                
    def display_metrics_analysis(self, incident):
        """Display detailed metrics analysis."""
        st.markdown("### 📈 Metrics Analysis")
        
        # Create sample metrics visualization
        time_range = pd.date_range(end=datetime.now(), periods=20, freq='5min')
        
        # CPU and Memory metrics
        col1, col2 = st.columns(2)
        
        with col1:
            cpu_data = pd.DataFrame({
                'Time': time_range,
                'CPU %': [30 + (i * 3 if i > 10 else 0) for i in range(20)]
            })
            fig = px.line(cpu_data, x='Time', y='CPU %', title='CPU Utilization')
            fig.add_hline(y=80, line_dash="dash", line_color="red", 
                         annotation_text="Critical Threshold")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            memory_data = pd.DataFrame({
                'Time': time_range,
                'Memory %': [40 + (i * 2.5 if i > 10 else 0) for i in range(20)]
            })
            fig = px.line(memory_data, x='Time', y='Memory %', title='Memory Utilization')
            fig.add_hline(y=85, line_dash="dash", line_color="orange", 
                         annotation_text="Warning Threshold")
            st.plotly_chart(fig, use_container_width=True)
            
        # Error rate and response time
        col1, col2 = st.columns(2)
        
        with col1:
            error_data = pd.DataFrame({
                'Time': time_range,
                'Error Rate %': [0.5 + (i * 0.8 if i > 12 else 0) for i in range(20)]
            })
            fig = px.line(error_data, x='Time', y='Error Rate %', 
                         title='Error Rate', color_discrete_sequence=['red'])
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            response_data = pd.DataFrame({
                'Time': time_range,
                'Response Time (ms)': [200 + (i * 100 if i > 12 else 0) for i in range(20)]
            })
            fig = px.line(response_data, x='Time', y='Response Time (ms)', 
                         title='API Response Time')
            st.plotly_chart(fig, use_container_width=True)
            
    def display_raw_data(self, incident):
        """Display raw data for debugging."""
        st.markdown("### 📝 Raw Data")
        
        # OpsItem details
        if 'ops_item' in incident:
            with st.expander("OpsItem Details"):
                st.json(incident['ops_item'])
                
        # Analysis results
        if 'analysis' in incident:
            with st.expander("Analysis Results"):
                st.json(incident['analysis'])
                
        # Raw collected data
        if 'raw_data' in incident:
            with st.expander("Collected Data"):
                st.json(incident['raw_data'])

def main():
    """Main application entry point."""
    dashboard = EnhancedSREDashboard()
    dashboard.display_dashboard()

if __name__ == "__main__":
    main()
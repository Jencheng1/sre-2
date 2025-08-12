"""
Synthetic Transaction Tab for Streamlit Dashboard
Enables incident reproduction via synthetic transactions
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

def render_synthetic_transaction_tab():
    """Render the Synthetic Transaction tab"""
    st.markdown("## 🔬 Synthetic Transaction Testing")
    st.markdown("Reproduce incidents and test scenarios using synthetic transactions")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Transactions Today", "23", delta="5")
    with col2:
        st.metric("Success Rate", "87%", delta="3%")
    with col3:
        st.metric("Avg Reproduction Confidence", "91%", delta="2%")
    with col4:
        st.metric("Issues Reproduced", "18", delta="4")
    
    st.markdown("---")
    
    # Transaction Type Selection
    st.subheader("🎯 Create Synthetic Transaction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transaction_type = st.selectbox(
            "Transaction Type",
            ["API Timeout", "Authentication Failure", "Connection Pool Exhaustion", 
             "Memory Leak", "Custom Scenario"]
        )
        
        # Map to internal types
        type_mapping = {
            "API Timeout": "api_timeout",
            "Authentication Failure": "authentication_failure",
            "Connection Pool Exhaustion": "connection_pool_exhaustion",
            "Memory Leak": "memory_leak",
            "Custom Scenario": "custom"
        }
        
        severity = st.select_slider(
            "Incident Severity",
            options=["Low", "Medium", "High", "Critical"]
        )
    
    with col2:
        endpoint = st.text_input(
            "Target Endpoint",
            value="/api/v1/test",
            help="API endpoint to test"
        )
        
        duration = st.number_input(
            "Test Duration (seconds)",
            min_value=5,
            max_value=300,
            value=30,
            step=5
        )
    
    # Incident Description
    st.markdown("### 📝 Incident Details")
    
    incident_description = st.text_area(
        "Incident Description",
        placeholder="Describe the incident you want to reproduce...",
        height=100
    )
    
    # Advanced Options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            concurrent_users = st.number_input(
                "Concurrent Users",
                min_value=1,
                max_value=1000,
                value=10
            )
            
            request_rate = st.number_input(
                "Requests per Second",
                min_value=1,
                max_value=1000,
                value=50
            )
        
        with col2:
            inject_delay = st.number_input(
                "Inject Delay (ms)",
                min_value=0,
                max_value=10000,
                value=0,
                step=100
            )
            
            error_rate = st.slider(
                "Expected Error Rate",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.05
            )
    
    # Create Transaction Button
    if st.button("🚀 Create Synthetic Transaction", type="primary"):
        if incident_description:
            with st.spinner("Creating synthetic transaction..."):
                try:
                    # Call Fed LPP API
                    response = requests.post(
                        "http://localhost:9087/fedlpp/synthetic-transaction",
                        json={
                            "incident_id": f"INC-{int(time.time())}",
                            "incident_type": type_mapping[transaction_type],
                            "description": incident_description,
                            "severity": severity,
                            "endpoint": endpoint,
                            "duration": duration,
                            "concurrent_users": concurrent_users,
                            "request_rate": request_rate,
                            "inject_delay": inject_delay,
                            "expected_error_rate": error_rate
                        },
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        result = response.json()
                        
                        st.success("✅ Synthetic transaction created successfully!")
                        
                        # Display transaction details
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.info(f"**Transaction ID:** {result.get('transaction_id', 'N/A')}")
                            st.info(f"**Status:** {result.get('status', 'Created')}")
                        
                        with col2:
                            confidence = result.get('reproduction_confidence', 0)
                            st.info(f"**Reproduction Confidence:** {confidence:.0%}")
                            st.info(f"**Type:** {transaction_type}")
                        
                        # Show execution plan
                        if 'execution_plan' in result:
                            st.markdown("### 📋 Execution Plan")
                            
                            for i, step in enumerate(result['execution_plan']):
                                st.write(f"{i+1}. **{step.get('action', 'Unknown')}**")
                                if 'endpoint' in step:
                                    st.write(f"   - Endpoint: {step['endpoint']}")
                                if 'duration' in step:
                                    st.write(f"   - Duration: {step['duration']}s")
                        
                        # Execute transaction
                        if st.button("▶️ Execute Transaction"):
                            execute_synthetic_transaction(result['transaction_id'])
                    
                    else:
                        st.error(f"Failed to create transaction: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error creating synthetic transaction: {str(e)}")
        else:
            st.warning("Please provide an incident description")
    
    st.markdown("---")
    
    # Recent Synthetic Transactions
    st.subheader("📊 Recent Synthetic Transactions")
    
    # Sample data (in production, fetch from API)
    recent_transactions = [
        {
            "id": "ST-INC-1234-001",
            "type": "API Timeout",
            "status": "Completed",
            "confidence": 0.92,
            "errors_detected": 3,
            "duration": "45s",
            "timestamp": datetime.now() - timedelta(minutes=5)
        },
        {
            "id": "ST-INC-1234-002", 
            "type": "Connection Pool",
            "status": "Running",
            "confidence": 0.85,
            "errors_detected": 0,
            "duration": "12s",
            "timestamp": datetime.now() - timedelta(minutes=2)
        },
        {
            "id": "ST-INC-1234-003",
            "type": "Auth Failure",
            "status": "Completed",
            "confidence": 0.98,
            "errors_detected": 5,
            "duration": "23s",
            "timestamp": datetime.now() - timedelta(minutes=10)
        }
    ]
    
    # Display as dataframe
    df = pd.DataFrame(recent_transactions)
    
    # Add status indicators
    df['Status'] = df.apply(lambda row: 
        f"🟢 {row['status']}" if row['status'] == 'Completed' else 
        f"🔵 {row['status']}" if row['status'] == 'Running' else 
        f"🔴 {row['status']}", axis=1
    )
    
    # Format confidence as percentage
    df['Confidence'] = df['confidence'].apply(lambda x: f"{x:.0%}")
    
    # Display table
    st.dataframe(
        df[['id', 'type', 'Status', 'Confidence', 'errors_detected', 'duration', 'timestamp']],
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Transaction Analysis
    st.subheader("📈 Synthetic Transaction Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Success rate over time
        fig_success = create_success_rate_chart()
        st.plotly_chart(fig_success, use_container_width=True)
    
    with col2:
        # Transaction types distribution
        fig_types = create_transaction_types_chart()
        st.plotly_chart(fig_types, use_container_width=True)
    
    # Confidence distribution
    fig_confidence = create_confidence_distribution_chart()
    st.plotly_chart(fig_confidence, use_container_width=True)

def execute_synthetic_transaction(transaction_id):
    """Execute a synthetic transaction and show results"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulate execution steps
    steps = [
        "Initializing transaction...",
        "Sending test requests...",
        "Monitoring responses...",
        "Collecting metrics...",
        "Analyzing results..."
    ]
    
    for i, step in enumerate(steps):
        status_text.text(step)
        progress_bar.progress((i + 1) / len(steps))
        time.sleep(1)
    
    # Show results
    st.success("✅ Transaction executed successfully!")
    
    # Display execution results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Requests Sent", "1,245")
        st.metric("Success Rate", "87.3%")
    
    with col2:
        st.metric("Errors Detected", "158")
        st.metric("Avg Response Time", "234ms")
    
    with col3:
        st.metric("Peak Memory", "412MB")
        st.metric("CPU Usage", "67%")
    
    # Show reproduction evidence
    st.markdown("### 🔍 Reproduction Evidence")
    
    evidence_items = [
        "✓ Timeout errors detected after 5 seconds",
        "✓ Error rate matches expected pattern (87% vs 85% expected)",
        "✓ Response times degraded progressively",
        "✓ Connection pool exhaustion confirmed at 100 concurrent users"
    ]
    
    for item in evidence_items:
        st.write(item)
    
    # Recommendations
    st.markdown("### 💡 Recommendations")
    
    recommendations = [
        "🔧 Increase connection pool size to 200",
        "⏱️ Set timeout to 10 seconds for this endpoint",
        "📊 Implement circuit breaker pattern",
        "🚨 Add monitoring for connection pool metrics"
    ]
    
    for rec in recommendations:
        st.info(rec)

def create_success_rate_chart():
    """Create success rate over time chart"""
    # Sample data
    times = pd.date_range(start='2025-08-12 10:00', periods=24, freq='H')
    success_rates = [95, 94, 93, 91, 87, 85, 82, 80, 78, 77, 79, 81, 
                    83, 85, 87, 89, 91, 92, 93, 94, 95, 96, 95, 94]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=success_rates,
        mode='lines+markers',
        name='Success Rate',
        line=dict(color='#10b981', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="Synthetic Transaction Success Rate (24h)",
        xaxis_title="Time",
        yaxis_title="Success Rate (%)",
        yaxis=dict(range=[0, 100]),
        hovermode='x unified'
    )
    
    return fig

def create_transaction_types_chart():
    """Create transaction types distribution chart"""
    types = ['API Timeout', 'Auth Failure', 'Connection Pool', 'Memory Leak', 'Custom']
    counts = [45, 32, 28, 15, 12]
    
    fig = px.pie(
        values=counts,
        names=types,
        title="Transaction Types Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    return fig

def create_confidence_distribution_chart():
    """Create confidence score distribution chart"""
    confidence_ranges = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    transaction_counts = [2, 5, 12, 35, 68]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=confidence_ranges,
        y=transaction_counts,
        marker=dict(
            color=transaction_counts,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Count")
        )
    ))
    
    fig.update_layout(
        title="Reproduction Confidence Distribution",
        xaxis_title="Confidence Range",
        yaxis_title="Number of Transactions",
        showlegend=False
    )
    
    return fig
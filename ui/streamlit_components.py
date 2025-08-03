"""
Streamlit UI components for MCP configuration and feedback
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from config.mcp_config import MCPConfigManager
from feedback.feedback_system import FeedbackSystem

class MCPComponents:
    """UI components for MCP configuration"""
    
    def __init__(self):
        self.config_manager = MCPConfigManager()
        self.available_servers = ["splunk", "dynatrace", "servicenow", "confluence", "gitlab"]
        
    def render_mcp_config_form(self):
        """Render MCP configuration form"""
        st.subheader("MCP Server Configuration")
        
        # Get current configuration
        current_config = self.config_manager.config
        
        # Tabs for different servers
        tabs = st.tabs(self.available_servers + ["Add New"])
        
        # Render each server config
        for i, server_name in enumerate(self.available_servers):
            with tabs[i]:
                self._render_server_config(server_name)
        
        # Add new server tab
        with tabs[-1]:
            self._render_add_new_server()
        
        # Global settings
        st.divider()
        st.subheader("Global Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_timeout = st.number_input(
                "Default Timeout (seconds)",
                min_value=5,
                max_value=300,
                value=current_config.get("global_settings", {}).get("default_timeout", 30)
            )
            
            enable_caching = st.checkbox(
                "Enable Response Caching",
                value=current_config.get("global_settings", {}).get("enable_caching", True)
            )
        
        with col2:
            max_retry = st.number_input(
                "Max Retry Count",
                min_value=0,
                max_value=10,
                value=current_config.get("global_settings", {}).get("max_retry_count", 3)
            )
            
            cache_ttl = st.number_input(
                "Cache TTL (seconds)",
                min_value=60,
                max_value=3600,
                value=current_config.get("global_settings", {}).get("cache_ttl", 300),
                disabled=not enable_caching
            )
        
        if st.button("Save Global Settings"):
            global_settings = {
                "default_timeout": default_timeout,
                "max_retry_count": max_retry,
                "enable_caching": enable_caching,
                "cache_ttl": cache_ttl,
                "log_level": "INFO"
            }
            
            current_config["global_settings"] = global_settings
            self.config_manager.save_config(current_config)
            st.success("Global settings saved!")
        
        return self
    
    def _render_server_config(self, server_name: str):
        """Render configuration for a specific server"""
        server_config = self.config_manager.get_mcp_config(server_name) or {}
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{server_name.upper()} Configuration**")
        
        with col2:
            enabled = st.checkbox(
                "Enabled",
                value=server_config.get("enabled", True),
                key=f"{server_name}_enabled"
            )
        
        # Server settings
        endpoint = st.text_input(
            "Endpoint URL",
            value=server_config.get("endpoint", ""),
            key=f"{server_name}_endpoint"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            auth_type = st.selectbox(
                "Authentication Type",
                options=["bearer", "api_token", "basic", "private_token"],
                index=["bearer", "api_token", "basic", "private_token"].index(
                    server_config.get("auth", {}).get("type", "bearer")
                ),
                key=f"{server_name}_auth_type"
            )
        
        with col2:
            test_mode = st.checkbox(
                "Test Mode",
                value=server_config.get("test_mode", True),
                key=f"{server_name}_test_mode"
            )
        
        # Auth credentials
        if auth_type in ["bearer", "api_token", "private_token"]:
            token = st.text_input(
                "Token",
                type="password",
                value="",  # Don't show actual token
                placeholder="Enter token or leave blank to keep existing",
                key=f"{server_name}_token"
            )
        elif auth_type == "basic":
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input(
                    "Username",
                    value=server_config.get("auth", {}).get("username", ""),
                    key=f"{server_name}_username"
                )
            with col2:
                password = st.text_input(
                    "Password",
                    type="password",
                    value="",
                    placeholder="Enter password or leave blank",
                    key=f"{server_name}_password"
                )
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            timeout = st.number_input(
                "Timeout (seconds)",
                min_value=5,
                max_value=300,
                value=server_config.get("timeout", 30),
                key=f"{server_name}_timeout"
            )
            
            retry_count = st.number_input(
                "Retry Count",
                min_value=0,
                max_value=10,
                value=server_config.get("retry_count", 3),
                key=f"{server_name}_retry"
            )
        
        # Save button
        if st.button(f"Save {server_name.upper()} Configuration", key=f"{server_name}_save"):
            # Build new config
            new_config = {
                "name": server_name,
                "type": "rest_api",
                "endpoint": endpoint,
                "enabled": enabled,
                "test_mode": test_mode,
                "timeout": timeout,
                "retry_count": retry_count,
                "auth": {"type": auth_type}
            }
            
            # Handle auth based on type
            if auth_type in ["bearer", "api_token", "private_token"]:
                if token:  # Only update if new token provided
                    new_config["auth"]["token"] = token
                else:
                    # Keep existing token
                    new_config["auth"]["token"] = server_config.get("auth", {}).get("token", "")
            elif auth_type == "basic":
                new_config["auth"]["username"] = username
                if password:
                    new_config["auth"]["password"] = password
                else:
                    new_config["auth"]["password"] = server_config.get("auth", {}).get("password", "")
            
            # Save configuration
            result = self.config_manager.add_mcp_server(new_config)
            
            if result["success"]:
                st.success(f"{server_name.upper()} configuration saved!")
            else:
                st.error(f"Error: {result['error']}")
        
        # Test connection button
        if st.button(f"Test {server_name.upper()} Connection", key=f"{server_name}_test"):
            with st.spinner("Testing connection..."):
                # Here you would implement actual connection test
                st.info(f"Connection test for {server_name} would be performed here")
    
    def _render_add_new_server(self):
        """Render form to add new MCP server"""
        st.write("**Add New MCP Server**")
        
        server_name = st.text_input("Server Name", placeholder="e.g., custom_monitoring")
        endpoint = st.text_input("Endpoint URL", placeholder="https://api.example.com")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auth_type = st.selectbox(
                "Authentication Type",
                options=["bearer", "api_token", "basic", "oauth2"],
                key="new_auth_type"
            )
        
        with col2:
            server_type = st.selectbox(
                "Server Type",
                options=["rest_api", "graphql", "grpc"],
                key="new_server_type"
            )
        
        if st.button("Add Server"):
            if server_name and endpoint:
                new_config = {
                    "name": server_name,
                    "type": server_type,
                    "endpoint": endpoint,
                    "auth": {"type": auth_type},
                    "enabled": True,
                    "test_mode": False
                }
                
                result = self.config_manager.add_mcp_server(new_config)
                
                if result["success"]:
                    st.success("New server added successfully!")
                    st.experimental_rerun()
                else:
                    st.error(f"Error: {result['error']}")
            else:
                st.error("Please provide server name and endpoint")


class FeedbackComponents:
    """UI components for human-in-the-loop feedback"""
    
    def __init__(self):
        self.feedback_system = FeedbackSystem()
        self.fields = ["rating", "comments", "correct_root_cause", "additional_context"]
        
    def render_feedback_form(self, incident_id: str, analysis: Dict[str, Any] = None):
        """Render feedback form for incident analysis"""
        st.subheader("Analysis Feedback")
        
        # Display analysis summary if provided
        if analysis:
            with st.expander("View Analysis Details"):
                st.json(analysis)
        
        # Feedback form
        col1, col2 = st.columns([2, 1])
        
        with col1:
            rating = st.slider(
                "How accurate was this analysis?",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Very Inaccurate, 5 = Very Accurate"
            )
        
        with col2:
            correct_root_cause = st.checkbox(
                "Root cause was correct",
                value=True
            )
        
        # Additional feedback
        additional_context = st.text_area(
            "Additional Context",
            placeholder="Provide any additional information about the incident...",
            height=100
        )
        
        # Corrections
        st.write("**Corrections & Improvements**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            actual_root_cause = st.text_input(
                "Actual Root Cause (if different)",
                placeholder="e.g., DNS misconfiguration"
            )
        
        with col2:
            time_to_resolution = st.number_input(
                "Time to Resolution (minutes)",
                min_value=0,
                value=0
            )
        
        # Suggested actions
        suggested_actions = st.text_area(
            "Suggested Actions for Similar Incidents",
            placeholder="Enter actions separated by newlines...",
            height=100
        )
        
        # False positives
        false_positives = st.multiselect(
            "False Positive Findings",
            options=self._extract_findings(analysis) if analysis else [],
            help="Select any findings that were incorrect"
        )
        
        # Submit feedback
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Submit Feedback", type="primary"):
                feedback_data = {
                    "incident_id": incident_id,
                    "analysis_id": analysis.get("analysis_id", "") if analysis else "",
                    "rating": rating,
                    "correct_root_cause": correct_root_cause,
                    "additional_context": additional_context,
                    "suggested_actions": [a.strip() for a in suggested_actions.split("\n") if a.strip()],
                    "actual_root_cause": actual_root_cause,
                    "time_to_resolution": time_to_resolution,
                    "false_positives": false_positives,
                    "effectiveness": rating  # Use rating as effectiveness score
                }
                
                result = self.feedback_system.submit_feedback(feedback_data)
                
                if result["success"]:
                    st.success("Thank you for your feedback! It will help improve future analysis.")
                else:
                    st.error(f"Error submitting feedback: {result['error']}")
        
        with col2:
            if st.button("Skip"):
                st.info("Feedback skipped")
        
        # Show historical feedback
        with st.expander("View Historical Feedback"):
            historical = self.feedback_system.get_feedback(incident_id)
            
            if historical:
                for feedback in historical[:5]:  # Show last 5
                    st.write(f"**Rating:** {feedback.get('rating', 'N/A')}/5")
                    st.write(f"**Date:** {feedback.get('timestamp', 'N/A')}")
                    if feedback.get('additional_context'):
                        st.write(f"**Context:** {feedback['additional_context']}")
                    st.divider()
            else:
                st.write("No historical feedback for this incident")
        
        return self
    
    def render_feedback_analytics(self):
        """Render feedback analytics dashboard"""
        st.subheader("Feedback Analytics")
        
        stats = self.feedback_system.get_feedback_stats()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Feedback", stats["total_feedback"])
        
        with col2:
            st.metric("Average Rating", f"{stats['average_rating']:.1f}/5")
        
        with col3:
            st.metric("Accuracy Rate", f"{stats['accuracy_rate']*100:.0f}%")
        
        with col4:
            st.metric("Improvement Trend", stats["improvement_trend"])
        
        # Common issues
        st.write("**Most Common Issues**")
        for i, issue in enumerate(stats["most_common_issues"], 1):
            st.write(f"{i}. {issue}")
        
        # Feedback by type
        st.write("**Feedback by Incident Type**")
        feedback_data = stats["feedback_by_type"]
        
        # Simple bar chart representation
        for incident_type, count in feedback_data.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(count / max(feedback_data.values()))
            with col2:
                st.write(f"{incident_type}: {count}")
    
    def _extract_findings(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract findings from analysis for false positive selection"""
        findings = []
        
        if analysis and "evidence" in analysis:
            for evidence in analysis["evidence"]:
                if "finding" in evidence:
                    findings.append(evidence["finding"])
        
        return findings
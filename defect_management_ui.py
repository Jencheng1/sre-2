"""
Defect Management UI Components for Streamlit
Comprehensive UI components for defect tracking, correlation, and management
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import json

class DefectManagementUI:
    """UI components for defect management integration"""
    
    def __init__(self, mcp_endpoints: Dict[str, str]):
        self.mcp_endpoints = mcp_endpoints
    
    def render_defect_correlation_dashboard(self, correlation_data: Dict[str, Any]):
        """Render the main defect correlation dashboard"""
        st.markdown("### 🔗 Defect Correlation Analysis")
        
        # Correlation score visualization
        self._render_correlation_score_gauge(correlation_data.get('correlation_score', 0.0))
        
        # Split into columns for ALM Octane and Jira
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_alm_octane_section(correlation_data.get('alm_octane_defects', []))
        
        with col2:
            self._render_jira_section(correlation_data.get('jira_issues', []))
        
        # Evidence and recommendations
        self._render_evidence_section(correlation_data.get('evidence', []))
        self._render_recommendations_section(correlation_data.get('recommended_actions', []))
    
    def _render_correlation_score_gauge(self, correlation_score: float):
        """Render correlation score as a gauge chart"""
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=correlation_score * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Defect Correlation Score"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgray"},
                    {'range': [30, 50], 'color': "yellow"},
                    {'range': [50, 70], 'color': "orange"},
                    {'range': [70, 100], 'color': "red"}
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
        
        # Interpretation
        if correlation_score >= 0.7:
            st.error("🚨 HIGH CORRELATION - Likely defect-related incident")
        elif correlation_score >= 0.4:
            st.warning("⚠️ MEDIUM CORRELATION - Possible defect involvement")
        else:
            st.success("✅ LOW CORRELATION - Likely new issue")
    
    def _render_alm_octane_section(self, defects: List[Dict[str, Any]]):
        """Render ALM Octane defects section"""
        st.markdown("#### 🔧 ALM Octane Defects")
        
        if not defects:
            st.info("No correlated ALM Octane defects found")
            return
        
        for i, defect in enumerate(defects):
            relevance_score = defect.get('relevance_score', 0.0)
            
            # Color code based on relevance
            if relevance_score >= 0.7:
                border_color = "#dc3545"  # Red
            elif relevance_score >= 0.5:
                border_color = "#fd7e14"  # Orange
            else:
                border_color = "#6c757d"  # Gray
            
            with st.expander(
                f"🔧 Defect {defect.get('id', 'N/A')} (Relevance: {relevance_score:.2f})",
                expanded=(i == 0)  # Expand first item
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **Name:** {defect.get('name', 'N/A')}
                    
                    **Severity:** {defect.get('severity', 'N/A')}
                    
                    **Status:** {defect.get('status', 'N/A')}
                    
                    **Component:** {defect.get('component', 'N/A')}
                    """)
                
                with col2:
                    st.markdown(f"""
                    **Created:** {defect.get('created_date', 'N/A')}
                    
                    **Assigned To:** {defect.get('assigned_to', 'N/A')}
                    
                    **Environment:** {defect.get('environment', 'N/A')}
                    
                    **Project:** {defect.get('project', 'N/A')}
                    """)
                
                # Description
                st.markdown("**Description:**")
                st.markdown(f"{defect.get('description', 'No description available')[:300]}...")
                
                # Action buttons
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                with btn_col1:
                    if st.button(f"View Full Details", key=f"alm_view_{defect.get('id')}"):
                        self._show_defect_details_modal(defect, 'alm_octane')
                
                with btn_col2:
                    if st.button(f"Update Status", key=f"alm_update_{defect.get('id')}"):
                        self._show_update_defect_form(defect, 'alm_octane')
                
                with btn_col3:
                    if st.button(f"Add Comment", key=f"alm_comment_{defect.get('id')}"):
                        self._show_add_comment_form(defect, 'alm_octane')
    
    def _render_jira_section(self, issues: List[Dict[str, Any]]):
        """Render Jira issues section"""
        st.markdown("#### 🎫 Jira Issues")
        
        if not issues:
            st.info("No correlated Jira issues found")
            return
        
        for i, issue in enumerate(issues):
            relevance_score = issue.get('relevance_score', 0.0)
            
            with st.expander(
                f"🎫 Issue {issue.get('key', 'N/A')} (Relevance: {relevance_score:.2f})",
                expanded=(i == 0)  # Expand first item
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **Summary:** {issue.get('summary', 'N/A')}
                    
                    **Priority:** {issue.get('priority', {}).get('name', 'N/A')}
                    
                    **Status:** {issue.get('status', {}).get('name', 'N/A')}
                    
                    **Type:** {issue.get('issuetype', {}).get('name', 'N/A')}
                    """)
                
                with col2:
                    st.markdown(f"""
                    **Project:** {issue.get('project', {}).get('key', 'N/A')}
                    
                    **Assignee:** {issue.get('assignee', {}).get('displayName', 'Unassigned') if issue.get('assignee') else 'Unassigned'}
                    
                    **Created:** {issue.get('created', 'N/A')}
                    
                    **Updated:** {issue.get('updated', 'N/A')}
                    """)
                
                # Description
                st.markdown("**Description:**")
                st.markdown(f"{issue.get('description', 'No description available')[:300]}...")
                
                # Action buttons
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                with btn_col1:
                    if st.button(f"View in Jira", key=f"jira_view_{issue.get('key')}"):
                        st.info(f"Would open Jira issue {issue.get('key')} in new tab")
                
                with btn_col2:
                    if st.button(f"Transition", key=f"jira_transition_{issue.get('key')}"):
                        self._show_transition_issue_form(issue)
                
                with btn_col3:
                    if st.button(f"Add Comment", key=f"jira_comment_{issue.get('key')}"):
                        self._show_add_comment_form(issue, 'jira')
    
    def _render_evidence_section(self, evidence: List[str]):
        """Render correlation evidence section"""
        if not evidence:
            return
        
        st.markdown("#### 🔍 Correlation Evidence")
        
        for i, evidence_item in enumerate(evidence):
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border-left: 4px solid #007bff;">
                <strong>Evidence {i+1}:</strong> {evidence_item}
            </div>
            """, unsafe_allow_html=True)
    
    def _render_recommendations_section(self, recommendations: List[str]):
        """Render recommendations section"""
        if not recommendations:
            return
        
        st.markdown("#### 💡 Recommended Actions")
        
        for i, recommendation in enumerate(recommendations):
            # Determine icon and color based on recommendation content
            if "HIGH PRIORITY" in recommendation.upper() or "CRITICAL" in recommendation.upper():
                icon = "🚨"
                bg_color = "#fee"
                border_color = "#dc3545"
            elif "MEDIUM" in recommendation.upper() or "INVESTIGATE" in recommendation.upper():
                icon = "⚠️"
                bg_color = "#fff3cd"
                border_color = "#fd7e14"
            else:
                icon = "💡"
                bg_color = "#d1ecf1"
                border_color = "#17a2b8"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border-left: 4px solid {border_color};">
                {icon} {recommendation}
            </div>
            """, unsafe_allow_html=True)
    
    def render_defect_creation_form(self, incident_data: Dict[str, Any] = None):
        """Render form for creating new defects from incidents"""
        st.markdown("### 📝 Create Defect from Incident")
        
        with st.form("defect_creation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                defect_title = st.text_input(
                    "Defect Title",
                    value=f"Incident-derived: {incident_data.get('title', '')}" if incident_data else ""
                )
                
                defect_severity = st.selectbox(
                    "Severity",
                    ["Critical", "High", "Medium", "Low"],
                    index=0 if incident_data and incident_data.get('severity') == 'Critical' else 2
                )
                
                defect_component = st.text_input(
                    "Component",
                    value=self._suggest_component_from_incident(incident_data) if incident_data else ""
                )
                
                defect_environment = st.selectbox(
                    "Environment",
                    ["Production", "Staging", "QA", "Development"],
                    index=0
                )
            
            with col2:
                defect_assignee = st.text_input("Assigned To", value="SRE Team")
                
                create_in = st.multiselect(
                    "Create In",
                    ["ALM Octane", "Jira"],
                    default=["ALM Octane", "Jira"]
                )
                
                defect_priority = st.selectbox(
                    "Priority",
                    ["Critical", "High", "Medium", "Low"],
                    index=0 if incident_data and incident_data.get('severity') == 'Critical' else 1
                )
                
                fix_version = st.text_input("Target Fix Version", value="Next Release")
            
            # Pre-populate description from incident
            default_description = ""
            if incident_data:
                default_description = f"""Defect created from incident analysis.

**Incident Details:**
- Title: {incident_data.get('title', 'N/A')}
- Description: {incident_data.get('description', 'N/A')}
- Severity: {incident_data.get('severity', 'N/A')}
- Affected Services: {', '.join(incident_data.get('affected_services', []))}

**Recommended Investigation:**
- Review system logs for error patterns
- Check recent deployments and configuration changes
- Validate monitoring and alerting coverage
- Consider implementing additional safeguards
"""
            
            defect_description = st.text_area(
                "Description",
                value=default_description,
                height=200
            )
            
            steps_to_reproduce = st.text_area(
                "Steps to Reproduce",
                value=self._generate_reproduction_steps(incident_data) if incident_data else "",
                height=100
            )
            
            create_defect_btn = st.form_submit_button("🐛 Create Defect(s)")
        
        if create_defect_btn and defect_title and defect_description:
            self._create_defects(
                {
                    'title': defect_title,
                    'description': defect_description,
                    'severity': defect_severity,
                    'priority': defect_priority,
                    'component': defect_component,
                    'environment': defect_environment,
                    'assignee': defect_assignee,
                    'fix_version': fix_version,
                    'steps_to_reproduce': steps_to_reproduce
                },
                create_in
            )
    
    def render_defect_analytics_dashboard(self):
        """Render comprehensive defect analytics dashboard"""
        st.markdown("### 📊 Defect Analytics Dashboard")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        # Fetch metrics from both systems
        alm_metrics = self._fetch_alm_octane_metrics()
        jira_metrics = self._fetch_jira_metrics()
        
        with col1:
            total_defects = (alm_metrics.get('total_defects', 0) + 
                           jira_metrics.get('total_bugs', 0))
            st.metric("Total Defects", total_defects)
        
        with col2:
            open_defects = (alm_metrics.get('open_defects', 0) + 
                          jira_metrics.get('open_bugs', 0))
            st.metric("Open Defects", open_defects)
        
        with col3:
            critical_defects = (alm_metrics.get('critical_defects', 0) + 
                              jira_metrics.get('critical_bugs', 0))
            st.metric("Critical Defects", critical_defects)
        
        with col4:
            avg_resolution = (alm_metrics.get('avg_resolution_time', 0) + 
                            jira_metrics.get('average_resolution_time', 0)) / 2
            st.metric("Avg Resolution (days)", f"{avg_resolution:.1f}")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_defect_trends_chart()
        
        with col2:
            self._render_defect_severity_distribution()
        
        # Quality metrics
        st.markdown("#### 📈 Quality Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if alm_metrics:
                st.markdown("**ALM Octane Quality**")
                st.metric("Defect Density", f"{alm_metrics.get('defect_density', 0):.2f}")
                st.metric("Test Coverage", f"{alm_metrics.get('test_coverage', 0):.1f}%")
        
        with col2:
            if jira_metrics:
                st.markdown("**Jira Metrics**")
                st.metric("Bug Creation Rate", f"{jira_metrics.get('bug_creation_rate', 0):.1f}/day")
                st.metric("Escaped Bugs", jira_metrics.get('escaped_bugs', 0))
        
        with col3:
            # Combined metrics
            st.markdown("**Combined Health**")
            defect_health_score = self._calculate_defect_health_score(alm_metrics, jira_metrics)
            st.metric("Health Score", f"{defect_health_score:.0f}%")
    
    def _suggest_component_from_incident(self, incident_data: Dict[str, Any]) -> str:
        """Suggest component based on incident data"""
        if not incident_data:
            return "General"
        
        description = incident_data.get('description', '').lower()
        affected_services = incident_data.get('affected_services', [])
        
        # Service-based suggestions
        if any('api' in service for service in affected_services):
            return "API Gateway"
        elif any('database' in service or 'db' in service for service in affected_services):
            return "Database"
        elif any('auth' in service for service in affected_services):
            return "Authentication"
        elif any('payment' in service for service in affected_services):
            return "Payment System"
        
        # Description-based suggestions
        if 'api' in description or 'gateway' in description:
            return "API Gateway"
        elif 'database' in description or 'connection' in description:
            return "Database"
        elif 'auth' in description or 'login' in description:
            return "Authentication"
        elif 'payment' in description:
            return "Payment System"
        elif 'search' in description:
            return "Search Service"
        elif 'file' in description or 'upload' in description:
            return "File Management"
        else:
            return "General"
    
    def _generate_reproduction_steps(self, incident_data: Dict[str, Any]) -> str:
        """Generate reproduction steps from incident data"""
        if not incident_data:
            return ""
        
        steps = [
            "1. Set up test environment with similar configuration",
            f"2. Simulate conditions described in incident: {incident_data.get('description', '')[:100]}...",
            "3. Monitor system metrics and error logs",
            "4. Reproduce the failure scenario",
            "5. Document observed symptoms and error messages"
        ]
        
        # Add specific steps based on incident type
        affected_services = incident_data.get('affected_services', [])
        if 'api-gateway' in affected_services:
            steps.append("6. Test API endpoints with various load patterns")
        if 'database' in affected_services:
            steps.append("6. Check database connection pool and query performance")
        
        return "\n".join(steps)
    
    def _create_defects(self, defect_data: Dict[str, Any], create_in: List[str]):
        """Create defects in selected systems"""
        success_count = 0
        
        if "ALM Octane" in create_in:
            success = self._create_alm_octane_defect(defect_data)
            if success:
                success_count += 1
        
        if "Jira" in create_in:
            success = self._create_jira_issue(defect_data)
            if success:
                success_count += 1
        
        if success_count > 0:
            st.success(f"✅ Successfully created defect(s) in {success_count} system(s)")
            st.balloons()
        else:
            st.error("❌ Failed to create defects in any system")
    
    def _create_alm_octane_defect(self, defect_data: Dict[str, Any]) -> bool:
        """Create defect in ALM Octane"""
        try:
            payload = {
                "name": defect_data['title'],
                "description": defect_data['description'],
                "severity": defect_data['severity'],
                "priority": defect_data['priority'],
                "component": defect_data['component'],
                "environment": defect_data['environment'],
                "assigned_to": defect_data['assignee'],
                "steps_to_reproduce": defect_data['steps_to_reproduce'],
                "created_by": "SRE Copilot"
            }
            
            response = requests.post(
                f"{self.mcp_endpoints['alm_octane']}/octane/defects",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                created_defect = response.json()
                st.success(f"✅ Created ALM Octane defect: {created_defect.get('id')}")
                return True
            else:
                st.error(f"❌ Failed to create ALM Octane defect: {response.status_code}")
                return False
                
        except Exception as e:
            st.error(f"❌ Error creating ALM Octane defect: {str(e)}")
            return False
    
    def _create_jira_issue(self, defect_data: Dict[str, Any]) -> bool:
        """Create issue in Jira"""
        try:
            payload = {
                "project": "SREPROJ",
                "summary": defect_data['title'],
                "description": defect_data['description'],
                "issue_type": "Bug",
                "priority": defect_data['priority'],
                "assignee": defect_data['assignee'],
                "labels": ["sre-incident", "defect-management"]
            }
            
            response = requests.post(
                f"{self.mcp_endpoints['jira']}/jira/issues",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                created_issue = response.json()
                st.success(f"✅ Created Jira issue: {created_issue.get('key')}")
                return True
            else:
                st.error(f"❌ Failed to create Jira issue: {response.status_code}")
                return False
                
        except Exception as e:
            st.error(f"❌ Error creating Jira issue: {str(e)}")
            return False
    
    def _fetch_alm_octane_metrics(self) -> Dict[str, Any]:
        """Fetch metrics from ALM Octane"""
        try:
            response = requests.get(
                f"{self.mcp_endpoints['alm_octane']}/octane/analytics/quality-metrics",
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get('metrics', {})
        except:
            pass
        return {}
    
    def _fetch_jira_metrics(self) -> Dict[str, Any]:
        """Fetch metrics from Jira"""
        try:
            response = requests.get(
                f"{self.mcp_endpoints['jira']}/jira/analytics/defect-metrics",
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get('metrics', {})
        except:
            pass
        return {}
    
    def _render_defect_trends_chart(self):
        """Render defect trends chart"""
        try:
            response = requests.get(
                f"{self.mcp_endpoints['alm_octane']}/octane/analytics/defect-trends?time_range=-30d",
                timeout=5
            )
            if response.status_code == 200:
                trends_data = response.json()
                trends = trends_data.get('trends', [])
                
                if trends:
                    df = pd.DataFrame(trends)
                    fig = px.line(
                        df, 
                        x='date', 
                        y=['new_defects', 'resolved_defects'],
                        title="Defect Trends (30 days)",
                        labels={'value': 'Count', 'variable': 'Metric'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No trend data available")
            else:
                st.error("Failed to load trend data")
        except Exception as e:
            st.error(f"Error loading trends: {str(e)}")
    
    def _render_defect_severity_distribution(self):
        """Render defect severity distribution pie chart"""
        try:
            response = requests.get(
                f"{self.mcp_endpoints['alm_octane']}/octane/defects",
                timeout=5
            )
            if response.status_code == 200:
                defects = response.json()
                
                if defects:
                    severity_counts = {}
                    for defect in defects:
                        severity = defect.get('severity', 'Unknown')
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    
                    fig = px.pie(
                        values=list(severity_counts.values()),
                        names=list(severity_counts.keys()),
                        title="Defect Severity Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No defect data available")
            else:
                st.error("Failed to load defect data")
        except Exception as e:
            st.error(f"Error loading defects: {str(e)}")
    
    def _calculate_defect_health_score(self, alm_metrics: Dict[str, Any], 
                                     jira_metrics: Dict[str, Any]) -> float:
        """Calculate overall defect health score"""
        score = 50  # Base score
        
        # ALM Octane contributions
        if alm_metrics:
            test_coverage = alm_metrics.get('test_coverage', 0)
            defect_density = alm_metrics.get('defect_density', 1)
            
            if test_coverage >= 80:
                score += 15
            elif test_coverage >= 60:
                score += 10
            
            if defect_density <= 0.5:
                score += 15
            elif defect_density <= 1.0:
                score += 10
        
        # Jira contributions
        if jira_metrics:
            critical_bugs = jira_metrics.get('critical_bugs', 0)
            avg_resolution = jira_metrics.get('average_resolution_time', 0)
            
            if critical_bugs == 0:
                score += 10
            elif critical_bugs <= 2:
                score += 5
            
            if avg_resolution <= 3:
                score += 10
            elif avg_resolution <= 7:
                score += 5
        
        return min(score, 100)
    
    # Modal and form methods (placeholders for actual implementation)
    def _show_defect_details_modal(self, defect: Dict[str, Any], source: str):
        """Show detailed defect information in modal"""
        st.info(f"Would show detailed view for {source} defect: {defect.get('id')}")
    
    def _show_update_defect_form(self, defect: Dict[str, Any], source: str):
        """Show form to update defect status"""
        st.info(f"Would show update form for {source} defect: {defect.get('id')}")
    
    def _show_add_comment_form(self, item: Dict[str, Any], source: str):
        """Show form to add comment"""
        st.info(f"Would show comment form for {source} item: {item.get('id' if source == 'alm_octane' else 'key')}")
    
    def _show_transition_issue_form(self, issue: Dict[str, Any]):
        """Show form to transition Jira issue"""
        st.info(f"Would show transition form for Jira issue: {issue.get('key')}")


# Usage example
if __name__ == "__main__":
    # Example usage in Streamlit app
    mcp_endpoints = {
        'alm_octane': 'http://localhost:9085',
        'jira': 'http://localhost:9086'
    }
    
    ui = DefectManagementUI(mcp_endpoints)
    
    # Example correlation data
    correlation_data = {
        'correlation_score': 0.75,
        'alm_octane_defects': [
            {
                'id': 'ALM-001',
                'name': 'API Gateway timeout issue',
                'severity': 'High',
                'status': 'In Progress',
                'relevance_score': 0.8
            }
        ],
        'jira_issues': [
            {
                'key': 'PROJ-123',
                'summary': 'Connection timeout errors',
                'priority': {'name': 'High'},
                'status': {'name': 'Open'},
                'relevance_score': 0.7
            }
        ],
        'evidence': ['High textual similarity detected', 'Component overlap found'],
        'recommended_actions': ['Review ALM defect ALM-001', 'Escalate Jira issue PROJ-123']
    }
    
    ui.render_defect_correlation_dashboard(correlation_data)
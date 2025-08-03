#!/usr/bin/env python3
"""
Authenticated wrapper for SRE Copilot Streamlit application.
"""

import streamlit as st
from datetime import datetime
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our authentication module
from auth_config import authenticate, is_valid_session, create_session_token

# Import the main app
from streamlit_app import SRECopilotDashboard

# Page configuration
st.set_page_config(
    page_title="SRE Copilot - Login",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def show_login_page():
    """Display the login page."""
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            padding: 2rem;
            background-color: #f0f2f6;
            border-radius: 10px;
            margin-top: 5rem;
        }
        .login-header {
            text-align: center;
            color: #1f77b4;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<h1 class="login-header">🔐 SRE Copilot Login</h1>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submitted:
                if username and password:
                    success, role = authenticate(username, password)
                    if success:
                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = role
                        st.session_state.login_time = datetime.now().isoformat()
                        st.session_state.session_token = create_session_token(username)
                        st.success(f"Welcome, {username}!")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Login information
        st.info("""
        **Default Credentials:**
        - Admin: `admin` / `ChangeMeNow!`
        - Demo: `demo` / `DemoUser123!`
        
        ⚠️ **Please change default passwords after first login!**
        """)

def show_main_app():
    """Display the main application."""
    # Add logout button to sidebar
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.role}")
        
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()
        
        st.divider()
    
    # Run the main application
    dashboard = SRECopilotDashboard()
    dashboard.display_dashboard()

def main():
    """Main application entry point."""
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Check if user is authenticated
    if is_valid_session(st.session_state):
        show_main_app()
    else:
        show_login_page()

if __name__ == "__main__":
    main()
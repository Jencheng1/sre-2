#!/usr/bin/env python3
"""Script to fix duplicate key issues in Streamlit app."""

import re
import hashlib
import time

def generate_unique_suffix():
    """Generate a unique suffix based on timestamp."""
    return str(int(time.time() * 1000000))[-8:]

def fix_streamlit_keys(input_file, output_file):
    """Fix duplicate key issues in Streamlit app."""
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Key fixes mapping
    fixes = {
        # Fix form keys - make them unique per render
        'with st.form("feedback_form")': 'with st.form(form_key)',
        
        # Fix button keys that might be in loops or conditional renders
        'key="generate_incident"': 'key=f"generate_incident_{st.session_state.get(\'render_id\', \'default\')}"',
        'key="run_analysis_sidebar"': 'key=f"run_analysis_sidebar_{st.session_state.get(\'render_id\', \'default\')}"',
        'key="analyze_selected"': 'key=f"analyze_selected_{st.session_state.get(\'render_id\', \'default\')}"',
        'key="analyze_manual_no_items"': 'key=f"analyze_manual_no_items_{st.session_state.get(\'render_id\', \'default\')}"',
        'key="analyze_error"': 'key=f"analyze_error_{st.session_state.get(\'render_id\', \'default\')}"',
        'key="analyze_another"': 'key=f"analyze_another_{st.session_state.get(\'render_id\', \'default\')}"',
        
        # Fix text input keys
        'key="manual_opsitem_with_list"': 'key=f"manual_opsitem_with_list_{st.session_state.get(\'tab_id\', \'default\')}"',
        'key="manual_opsitem_no_items"': 'key=f"manual_opsitem_no_items_{st.session_state.get(\'tab_id\', \'default\')}"',
        'key="manual_opsitem_error"': 'key=f"manual_opsitem_error_{st.session_state.get(\'tab_id\', \'default\')}"',
        
        # Fix knowledge base keys
        'key="kb_search_button"': 'key=f"kb_search_button_{st.session_state.get(\'kb_tab\', \'default\')}"',
        'key="kb_browse_button"': 'key=f"kb_browse_button_{st.session_state.get(\'kb_tab\', \'default\')}"',
        'key="kb_add_document"': 'key=f"kb_add_document_{st.session_state.get(\'kb_tab\', \'default\')}"',
        'key="kb_test_analysis"': 'key=f"kb_test_analysis_{st.session_state.get(\'kb_tab\', \'default\')}"',
        
        # Fix recent changes keys
        'key="refresh_changes"': 'key=f"refresh_changes_{st.session_state.get(\'changes_render\', \'default\')}"',
        'key="create_demo_change"': 'key=f"create_demo_change_{st.session_state.get(\'changes_render\', \'default\')}"',
        
        # Fix guide keys
        'key="guide_gen_incident"': 'key=f"guide_gen_incident_{st.session_state.get(\'guide_render\', \'default\')}"',
        'key="guide_analyze"': 'key=f"guide_analyze_{st.session_state.get(\'guide_render\', \'default\')}"',
        'key="guide_kb"': 'key=f"guide_kb_{st.session_state.get(\'guide_render\', \'default\')}"',
        'key="guide_go_analyze"': 'key=f"guide_go_analyze_{st.session_state.get(\'guide_render\', \'default\')}"',
        'key="guide_go_kb"': 'key=f"guide_go_kb_{st.session_state.get(\'guide_render\', \'default\')}"',
        'key="guide_search"': 'key=f"guide_search_{st.session_state.get(\'guide_render\', \'default\')}"',
    }
    
    # Apply fixes
    fixed_content = content
    for old, new in fixes.items():
        fixed_content = fixed_content.replace(old, new)
    
    # Add render ID management at the beginning of display_dashboard
    dashboard_init = """    def display_dashboard(self):
        \"\"\"Main dashboard display method.\"\"\"
        # Initialize render IDs for unique keys
        if 'render_id' not in st.session_state:
            st.session_state.render_id = 'init'
        if 'tab_id' not in st.session_state:
            st.session_state.tab_id = 'default'
        if 'kb_tab' not in st.session_state:
            st.session_state.kb_tab = 'default'
        if 'changes_render' not in st.session_state:
            st.session_state.changes_render = 'default'
        if 'guide_render' not in st.session_state:
            st.session_state.guide_render = 'default'
            
        # Update render ID on each render
        st.session_state.render_id = generate_unique_suffix()"""
    
    # Find and replace the display_dashboard method start
    pattern = r'def display_dashboard\(self\):\s*\n\s*"""Main dashboard display method."""'
    replacement = dashboard_init
    fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # Add the generate_unique_suffix function before the class
    import_section = """import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import boto3
import time
import random
import os
import sys
import requests
from decimal import Decimal

def generate_unique_suffix():
    \"\"\"Generate a unique suffix based on timestamp.\"\"\"
    return str(int(time.time() * 1000000))[-8:]
"""
    
    # Replace imports section
    fixed_content = re.sub(r'import streamlit as st.*?from decimal import Decimal\n', import_section, fixed_content, flags=re.DOTALL)
    
    # Write fixed content
    with open(output_file, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed Streamlit app written to {output_file}")

if __name__ == "__main__":
    fix_streamlit_keys('/home/ec2-user/sre/sre_mcp/streamlit_app.py', 
                       '/home/ec2-user/sre/sre_mcp/streamlit_app_fixed.py')
#!/usr/bin/env python3
"""Minimal test to verify KB UI functionality."""

import streamlit as st
import json
import boto3
from datetime import datetime

st.set_page_config(page_title="KB UI Test", layout="wide")

st.title("Knowledge Base UI Minimal Test")

# Initialize session state
if 'test_results' not in st.session_state:
    st.session_state.test_results = None

# Simple search test
st.header("1. Direct Lambda Test")

query = st.text_input("Search Query", value="performance issue")

if st.button("Test Search"):
    with st.spinner("Searching..."):
        try:
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            response = lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'search_incidents',
                    'query': query,
                    'k': 5
                })
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                st.session_state.test_results = body
                st.success(f"✅ Search successful! Found {len(body.get('results', []))} results")
            else:
                st.error(f"Search failed: {result}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Display results
if st.session_state.test_results:
    st.header("2. Results Display")
    
    results = st.session_state.test_results.get('results', [])
    
    if results:
        st.write(f"**Displaying {len(results)} results:**")
        
        for idx, doc in enumerate(results, 1):
            with st.expander(f"{idx}. {doc.get('title', 'No title')} (Score: {doc.get('score', 0):.3f})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write("**Document ID:**", doc.get('document_id'))
                    st.write("**Category:**", doc.get('metadata', {}).get('category'))
                    st.write("**Type:**", doc.get('metadata', {}).get('type'))
                    if doc.get('metadata', {}).get('tags'):
                        st.write("**Tags:**", ', '.join(doc['metadata']['tags']))
                
                with col2:
                    if doc.get('metadata', {}).get('severity'):
                        st.write("**Severity:**", doc['metadata']['severity'])
                
                st.write("**Content:**")
                content = doc.get('content', 'No content')
                if len(content) > 500:
                    st.write(content[:500] + "...")
                else:
                    st.write(content)
                
                if doc.get('metadata', {}).get('root_cause'):
                    st.info(f"**Root Cause:** {doc['metadata']['root_cause']}")
    else:
        st.warning("No results to display")

# Test the main app's display function
st.header("3. Test Main App Display Function")

if st.button("Simulate Main App Display"):
    if st.session_state.test_results:
        # This simulates what should happen in the main app
        results = st.session_state.test_results.get('results', [])
        
        st.success(f"Found {len(results)} results")
        
        # Group by type
        incidents = [r for r in results if r.get('metadata', {}).get('type') == 'incident']
        best_practices = [r for r in results if r.get('metadata', {}).get('type') == 'best_practice']
        
        if incidents:
            st.markdown("### 🚨 Similar Incidents")
            for idx, doc in enumerate(incidents[:3], 1):
                with st.expander(f"{idx}. {doc['title']} (Similarity: {doc.get('score', 0):.2f})"):
                    st.markdown(f"**Category:** {doc['metadata'].get('category', 'N/A')}")
                    st.markdown("**Content Preview:**")
                    st.markdown(doc['content'][:300] + "...")
        
        if best_practices:
            st.markdown("### 📚 Best Practices")
            for idx, doc in enumerate(best_practices[:3], 1):
                with st.expander(f"{idx}. {doc['title']}"):
                    st.markdown(doc['content'][:300] + "...")
        
        if not incidents and not best_practices:
            st.info("No incidents or best practices found in results")
    else:
        st.warning("No test results available. Run the search test first.")

# Debug info
with st.sidebar:
    st.header("Debug Info")
    st.write("**Session State Keys:**")
    st.write(list(st.session_state.keys()))
    
    if st.button("Clear Session State"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()
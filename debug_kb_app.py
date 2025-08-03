#!/usr/bin/env python3
"""Debug version of KB to find the issue."""

import streamlit as st
import json
import boto3
from datetime import datetime

st.set_page_config(page_title="KB Debug", layout="wide")

# Add debug information
st.sidebar.header("🔍 Debug Info")
st.sidebar.write("**Session State:**")
st.sidebar.json(dict(st.session_state))

st.title("Knowledge Base Debug")

# Initialize session state
if 'kb_search_results' not in st.session_state:
    st.session_state.kb_search_results = None
if 'kb_browse_results' not in st.session_state:
    st.session_state.kb_browse_results = None
if 'debug_messages' not in st.session_state:
    st.session_state.debug_messages = []

def add_debug(message):
    """Add debug message."""
    st.session_state.debug_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - {message}")

# Test Search
st.header("1. Test Search")

query = st.text_input("Query", value="performance")

col1, col2 = st.columns(2)

with col1:
    if st.button("Search (Method 1 - Direct)"):
        add_debug("Search button clicked")
        with st.spinner("Searching..."):
            try:
                lambda_client = boto3.client('lambda', region_name='us-east-1')
                add_debug("Lambda client created")
                
                response = lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'search_incidents',
                        'query': query,
                        'k': 5
                    })
                )
                add_debug("Lambda invoked")
                
                result = json.loads(response['Payload'].read())
                add_debug(f"Lambda status: {result.get('statusCode')}")
                
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    results = body.get('results', [])
                    add_debug(f"Got {len(results)} results")
                    
                    # Display directly
                    st.success(f"Found {len(results)} results")
                    for idx, doc in enumerate(results, 1):
                        with st.expander(f"{idx}. {doc.get('title', 'No title')}"):
                            st.json(doc)
                else:
                    st.error(f"Failed: {result}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                add_debug(f"Error: {str(e)}")

with col2:
    if st.button("Search (Method 2 - Session State)"):
        add_debug("Search button clicked (session state method)")
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
                    st.session_state.kb_search_results = {
                        'type': 'search_incidents',
                        'body': body,
                        'timestamp': datetime.now()
                    }
                    add_debug(f"Stored in session state")
                else:
                    st.error(f"Failed: {result}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                add_debug(f"Error: {str(e)}")

# Display from session state
if st.session_state.kb_search_results:
    st.header("Search Results from Session State")
    data = st.session_state.kb_search_results
    st.write(f"**Type:** {data['type']}")
    st.write(f"**Timestamp:** {data['timestamp']}")
    
    results = data['body'].get('results', [])
    st.write(f"**Results count:** {len(results)}")
    
    if results:
        for idx, doc in enumerate(results, 1):
            with st.expander(f"{idx}. {doc.get('title', 'No title')} (Score: {doc.get('score', 0):.3f})"):
                st.json(doc)

# Test Browse
st.header("2. Test Browse")

category = st.selectbox("Category", ["All", "performance", "security", "outage"])

if st.button("Browse"):
    add_debug(f"Browse button clicked for category: {category}")
    with st.spinner("Browsing..."):
        try:
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            
            response = lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'browse_documents',
                    'category': None if category == "All" else category,
                    'limit': 20
                })
            )
            
            result = json.loads(response['Payload'].read())
            add_debug(f"Lambda status: {result.get('statusCode')}")
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                results = body.get('results', [])
                add_debug(f"Got {len(results)} documents")
                
                st.session_state.kb_browse_results = {
                    'results': results,
                    'category': category,
                    'timestamp': datetime.now()
                }
                
                # Display directly
                st.success(f"Found {len(results)} documents")
                for idx, doc in enumerate(results[:5], 1):
                    with st.expander(f"{idx}. {doc.get('title', 'No title')}"):
                        st.json(doc)
            else:
                st.error(f"Failed: {result}")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            add_debug(f"Error: {str(e)}")

# Debug messages
st.header("3. Debug Messages")
for msg in st.session_state.debug_messages[-10:]:
    st.code(msg)

# Clear buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Clear Session State"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

with col2:
    if st.button("Clear Debug Messages"):
        st.session_state.debug_messages = []
        st.experimental_rerun()
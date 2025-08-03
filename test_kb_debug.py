#!/usr/bin/env python3
"""Debug Knowledge Base functionality in detail."""

import streamlit as st
import json
import boto3
from datetime import datetime

# Initialize session state
if 'kb_search_results' not in st.session_state:
    st.session_state.kb_search_results = None
if 'kb_browse_results' not in st.session_state:
    st.session_state.kb_browse_results = None

st.title("Knowledge Base Debug Tool")

# Test Search
st.header("1. Test Search Directly")

search_type = st.selectbox("Search Type", ["Similar Incidents", "Best Practices", "Resolution Guides"])
query = st.text_input("Query", value="high CPU")

if st.button("Test Search Lambda"):
    with st.spinner("Testing..."):
        try:
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            
            # Prepare action
            if search_type == "Similar Incidents":
                action = "search_incidents"
                params = {'query': query, 'k': 3}
            elif search_type == "Best Practices":
                action = "search_best_practices"
                params = {'query': query, 'tags': []}
            else:
                action = "get_resolution"
                params = {'incident_type': 'performance'}
            
            # Call Lambda
            response = lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': action,
                    **params
                })
            )
            
            result = json.loads(response['Payload'].read())
            
            st.write("**Lambda Response Status:**", result.get('statusCode'))
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                st.write("**Response Body:**")
                st.json(body)
                
                # Store in session state
                st.session_state.kb_search_results = {
                    'type': action,
                    'body': body,
                    'timestamp': datetime.now()
                }
                st.success("✅ Stored in session state")
            else:
                st.error(f"Lambda error: {result}")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.exception(e)

# Display session state
st.header("2. Session State Contents")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Search Results")
    if st.session_state.kb_search_results:
        st.write("**Type:**", st.session_state.kb_search_results.get('type'))
        st.write("**Timestamp:**", st.session_state.kb_search_results.get('timestamp'))
        if 'body' in st.session_state.kb_search_results:
            body = st.session_state.kb_search_results['body']
            if 'results' in body:
                st.write(f"**Results Count:** {len(body['results'])}")
                for i, result in enumerate(body['results'][:3]):
                    st.write(f"{i+1}. {result.get('title', 'No title')}")
            else:
                st.write("**Body:**", body)
    else:
        st.info("No search results in session state")

with col2:
    st.subheader("Browse Results")
    if st.session_state.kb_browse_results:
        st.write("**Category:**", st.session_state.kb_browse_results.get('category'))
        st.write("**Results Count:**", len(st.session_state.kb_browse_results.get('results', [])))
    else:
        st.info("No browse results in session state")

# Test Display Function
st.header("3. Test Display Functions")

if st.button("Test Display Search Results"):
    if st.session_state.kb_search_results:
        results_data = st.session_state.kb_search_results
        action = results_data['type']
        body = results_data['body']
        
        if action == "get_resolution" and body.get('guide'):
            guide = body['guide']
            with st.expander(f"📋 {guide['title']}", expanded=True):
                st.markdown(guide['content'])
        else:
            results = body.get('results', [])
            st.success(f"Found {len(results)} results")
            
            if results:
                for idx, doc in enumerate(results, 1):
                    with st.expander(f"{idx}. {doc.get('title', 'Unknown')} (Score: {doc.get('score', 0):.2f})"):
                        st.write("**Category:**", doc.get('metadata', {}).get('category'))
                        st.write("**Content:**")
                        st.write(doc.get('content', '')[:500] + "...")
    else:
        st.warning("No results to display")

# Clear session state
st.header("4. Session State Management")
if st.button("Clear All Session State"):
    st.session_state.kb_search_results = None
    st.session_state.kb_browse_results = None
    st.success("Session state cleared")
    st.experimental_rerun()
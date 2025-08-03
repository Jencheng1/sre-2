"""Streamlit key management utilities."""

import streamlit as st
import hashlib
from datetime import datetime

class KeyManager:
    """Manages unique keys for Streamlit widgets to prevent duplicates."""
    
    @staticmethod
    def get_unique_key(base_key, *args):
        """
        Generate a unique key based on base key and additional context.
        
        Args:
            base_key: The base key name
            *args: Additional context to make the key unique
        
        Returns:
            A unique key string
        """
        # Combine all arguments
        parts = [str(base_key)]
        for arg in args:
            if arg is not None:
                parts.append(str(arg))
        
        # Add session-specific data if needed
        if 'key_counter' not in st.session_state:
            st.session_state.key_counter = {}
        
        # Add a timestamp-based suffix to ensure uniqueness
        if 'widget_render_count' not in st.session_state:
            st.session_state.widget_render_count = 0
        
        # Always increment the render count for true uniqueness
        st.session_state.widget_render_count += 1
        parts.append(str(st.session_state.widget_render_count))
        
        # If this exact key combination was used before in this session,
        # also add a counter
        key_combo = '_'.join(parts[:-1])  # Exclude the render count for checking
        if key_combo in st.session_state.key_counter:
            st.session_state.key_counter[key_combo] += 1
            parts.append(str(st.session_state.key_counter[key_combo]))
        else:
            st.session_state.key_counter[key_combo] = 0
        
        return '_'.join(parts)
    
    @staticmethod
    def reset_keys():
        """Reset key counter for a new render cycle."""
        if 'key_counter' in st.session_state:
            st.session_state.key_counter = {}
    
    @staticmethod
    def get_tab_key(base_key, tab_name):
        """Get a unique key for a widget in a specific tab."""
        # Use the get_unique_key method to ensure true uniqueness
        return KeyManager.get_unique_key(base_key, "tab", tab_name)
    
    @staticmethod
    def get_form_key(base_key, form_context):
        """Get a unique key for a form."""
        # Use the get_unique_key method to ensure true uniqueness
        return KeyManager.get_unique_key(base_key, "form", form_context)
    
    @staticmethod
    def get_loop_key(base_key, index):
        """Get a unique key for widgets in loops."""
        # Use the get_unique_key method to ensure true uniqueness
        return KeyManager.get_unique_key(base_key, "idx", index)

# Global instance
key_manager = KeyManager()
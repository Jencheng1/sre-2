"""
Simple authentication configuration for Streamlit app.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta

# Configuration file for storing users
AUTH_FILE = "/home/ec2-user/sre/sre_mcp/.auth_users.json"

# Default admin credentials (change these!)
DEFAULT_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("ChangeMeNow!".encode()).hexdigest(),
        "role": "admin",
        "created": datetime.now().isoformat()
    },
    "demo": {
        "password_hash": hashlib.sha256("DemoUser123!".encode()).hexdigest(),
        "role": "viewer",
        "created": datetime.now().isoformat()
    }
}

def hash_password(password):
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify a password against its hash."""
    return hash_password(password) == password_hash

def load_users():
    """Load users from the auth file."""
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Create default users if file doesn't exist
    save_users(DEFAULT_USERS)
    return DEFAULT_USERS

def save_users(users):
    """Save users to the auth file."""
    with open(AUTH_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def authenticate(username, password):
    """Authenticate a user."""
    users = load_users()
    
    if username in users:
        user = users[username]
        if verify_password(password, user['password_hash']):
            return True, user['role']
    
    return False, None

def add_user(username, password, role='viewer'):
    """Add a new user."""
    users = load_users()
    
    if username in users:
        return False, "User already exists"
    
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "created": datetime.now().isoformat()
    }
    
    save_users(users)
    return True, "User added successfully"

def change_password(username, old_password, new_password):
    """Change a user's password."""
    users = load_users()
    
    if username not in users:
        return False, "User not found"
    
    if not verify_password(old_password, users[username]['password_hash']):
        return False, "Invalid old password"
    
    users[username]['password_hash'] = hash_password(new_password)
    users[username]['last_password_change'] = datetime.now().isoformat()
    
    save_users(users)
    return True, "Password changed successfully"

def delete_user(username):
    """Delete a user."""
    users = load_users()
    
    if username not in users:
        return False, "User not found"
    
    if username == "admin":
        return False, "Cannot delete admin user"
    
    del users[username]
    save_users(users)
    return True, "User deleted successfully"

def list_users():
    """List all users."""
    users = load_users()
    return [(username, user['role'], user.get('created', 'Unknown')) 
            for username, user in users.items()]

# Session management
def create_session_token(username):
    """Create a simple session token."""
    timestamp = datetime.now().isoformat()
    token_data = f"{username}:{timestamp}"
    return hashlib.sha256(token_data.encode()).hexdigest()

def is_valid_session(session_state):
    """Check if the session is valid."""
    if 'authenticated' not in session_state:
        return False
    
    if not session_state.get('authenticated'):
        return False
    
    # Check session timeout (24 hours)
    if 'login_time' in session_state:
        login_time = datetime.fromisoformat(session_state['login_time'])
        if datetime.now() - login_time > timedelta(hours=24):
            return False
    
    return True
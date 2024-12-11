import streamlit as st
from models.user import User

def check_authentication():
    """Check if a user is authenticated."""
    return st.session_state.get('authenticated', False) and st.session_state.get('user') is not None

def login_user(email, password):
    """Log in a user and set up their session."""
    user_model = User()
    user = user_model.authenticate(email, password)
    if user:
        # Set all required session state variables
        st.session_state.authenticated = True
        st.session_state.user = user
        return True
    return False

def logout_user():
    """Clear all authentication-related session state."""
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'user' in st.session_state:
        del st.session_state.user
    # Clear any other auth-related session states
    for key in list(st.session_state.keys()):
        if key.startswith(('login_', 'register_', 'auth_')):
            del st.session_state[key]

def require_auth(role=None):
    """Require authentication and optionally a specific role."""
    if not check_authentication():
        logout_user()  # Ensure clean session state
        st.error("Please login to access this page")
        st.stop()
    if role and st.session_state.user['role'] != role:
        st.error("You don't have permission to access this page")
        st.stop()

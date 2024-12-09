import streamlit as st
from models.user import User

def check_authentication():
    if 'user' not in st.session_state:
        st.session_state.user = None
    return st.session_state.user is not None

def login_user(email, password):
    user_model = User()
    user = user_model.authenticate(email, password)
    if user:
        st.session_state.user = user
        return True
    return False

def logout_user():
    st.session_state.user = None

def require_auth(role=None):
    if not check_authentication():
        st.error("Please login to access this page")
        st.stop()
    if role and st.session_state.user['role'] != role:
        st.error("You don't have permission to access this page")
        st.stop()

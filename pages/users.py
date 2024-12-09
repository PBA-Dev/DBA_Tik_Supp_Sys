import streamlit as st
from utils.auth import require_auth
from models.user import User

def render_users():
    require_auth('admin')
    
    st.title("User Management")
    
    user_model = User()
    
    tab1, tab2 = st.tabs(["User List", "Create User"])
    
    with tab1:
        users = user_model.get_all_users()
        
        for user in users:
            with st.expander(f"{user['email']} - {user['role'].upper()}"):
                st.write(f"Created: {user['created_at']}")
                
    with tab2:
        st.subheader("Create New User")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["customer", "agent", "admin"])
        
        if st.button("Create User"):
            if not email or not password:
                st.error("Please fill in all required fields")
            else:
                user_model.create_user(email, password, role)
                st.success("User created successfully")
                st.rerun()

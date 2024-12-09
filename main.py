import streamlit as st
from utils.auth import check_authentication, login_user, logout_user
from models.user import User
from pages.dashboard import render_dashboard
from pages.tickets import render_tickets
from pages.users import render_users
from pages.settings import render_settings

st.set_page_config(
    page_title="Support Ticket System",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Hide all Streamlit elements except the sidebar toggle
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def main():
    if not check_authentication():
        st.title("Support Ticket System")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login"):
                if login_user(email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
                    
        with tab2:
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_role = "customer"  # Default role for new registrations
            
            if st.button("Register"):
                if not reg_email or not reg_password:
                    st.error("Please fill in all fields")
                else:
                    user_model = User()
                    try:
                        user_model.create_user(reg_email, reg_password, reg_role)
                        st.success("Registration successful! Please login.")
                    except Exception as e:
                        if "duplicate key" in str(e):
                            st.error("Email already registered")
                        else:
                            st.error("Registration failed")
    else:
        # Main title in sidebar (MAIN)
        st.sidebar.markdown("### MAIN")
        st.sidebar.markdown("---")
        
        # Navigation section
        st.sidebar.markdown("### Navigation")
        if 'navigation' not in st.session_state:
            st.session_state.navigation = "Dashboard"
            
        # Only show navigation options in the radio buttons
        page = st.sidebar.radio("Go to", 
            ["Dashboard", "Tickets", "Users", "Settings"],
            key="nav_radio",
            index=["Dashboard", "Tickets", "Users", "Settings"].index(st.session_state.navigation))
        
        st.sidebar.markdown("---")
        st.sidebar.write(f"Logged in as: {st.session_state.user['email']}")
        if st.sidebar.button("Logout"):
            logout_user()
            st.rerun()
            
        # Page routing
        if page == "Dashboard":
            render_dashboard()
        elif page == "Tickets":
            render_tickets()
        elif page == "Users":
            render_users()
        elif page == "Settings":
            render_settings()

if __name__ == "__main__":
    main()

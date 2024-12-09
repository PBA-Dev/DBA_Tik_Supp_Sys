import streamlit as st
from utils.auth import check_authentication, login_user, logout_user
from pages.dashboard import render_dashboard
from pages.tickets import render_tickets
from pages.users import render_users
from pages.settings import render_settings

st.set_page_config(
    page_title="Support Ticket System",
    page_icon="🎫",
    layout="wide"
)

def main():
    if not check_authentication():
        st.title("Login")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if login_user(email, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Dashboard", "Tickets", "Users", "Settings"])
        
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

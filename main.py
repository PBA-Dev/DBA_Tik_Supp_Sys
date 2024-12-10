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

def hide_streamlit_elements():
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    div[data-testid="stDecoration"] {visibility: hidden;}
    div[data-testid="stStatusWidget"] {visibility: hidden;}
    .st-emotion-cache-1q2d4ya {display: none !important;}
    .eczjsme13 {display: none !important;}
    .main {visibility: hidden;}
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

def hide_sidebar():
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

def style_sidebar():
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        width: 250px;
        background-color: #262730;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .st-emotion-cache-16idsys p,
    section[data-testid="stSidebar"] .st-emotion-cache-16idsys span,
    section[data-testid="stSidebar"] .st-emotion-cache-16idsys label,
    section[data-testid="stSidebar"] .st-emotion-cache-pkbazv,
    section[data-testid="stSidebar"] .st-emotion-cache-16txtl3,
    section[data-testid="stSidebar"] .st-emotion-cache-16idsys,
    section[data-testid="stSidebar"] .element-container div {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    section[data-testid="stSidebar"] .stButton button,
    section[data-testid="stSidebar"] button.st-emotion-cache-19rxjzo {
        color: #ffffff !important;
        background-color: #4a4a4a !important;
        border-color: #4a4a4a !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Hide all Streamlit elements except the sidebar toggle
hide_streamlit_elements()

def main():
    # Main content area
    if not check_authentication():
        hide_streamlit_elements()
        hide_sidebar()
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
        # Apply sidebar styling for authenticated users
        style_sidebar()
        # Configure the sidebar for authenticated users
        with st.sidebar:
            st.markdown("### MAIN")
            st.markdown("---")
            
            # Navigation section
            st.markdown("### Navigation")
            if 'navigation' not in st.session_state:
                st.session_state.navigation = "Dashboard"
                
            # Only show navigation options in the radio buttons
            page = st.radio("Go to", 
                ["Dashboard", "Tickets", "Users", "Settings"],
                key="nav_radio",
                index=["Dashboard", "Tickets", "Users", "Settings"].index(st.session_state.navigation))
            
            st.markdown("---")
            st.write(f"Logged in as: {st.session_state.user['email']}")
            if st.button("Logout"):
                logout_user()
                st.rerun()
        
        # Page routing for authenticated users
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

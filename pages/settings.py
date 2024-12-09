import streamlit as st
from utils.auth import require_auth

def render_settings():
    require_auth('admin')
    
    st.title("System Settings")
    
    st.subheader("Email Settings")
    smtp_server = st.text_input("SMTP Server", value="smtp.yourdomain.com")
    smtp_port = st.number_input("SMTP Port", value=587)
    smtp_user = st.text_input("SMTP Username")
    smtp_password = st.text_input("SMTP Password", type="password")
    
    st.subheader("File Upload Settings")
    max_file_size = st.number_input("Max File Size (MB)", value=5)
    allowed_extensions = st.multiselect(
        "Allowed File Extensions",
        [".txt", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"],
        default=[".txt", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"]
    )
    
    if st.button("Save Settings"):
        # In a real implementation, these would be saved to a configuration file or database
        st.success("Settings saved successfully")

import streamlit as st
from models.user import User
from utils.recaptcha import ReCaptcha
from utils.gdpr import GDPRCompliance
import json

def render_auth():
    if "user" in st.session_state:
        st.success("You are already logged in")
        return

    tab1, tab2 = st.tabs(["Login", "Register"])

    recaptcha = ReCaptcha()
    gdpr = GDPRCompliance()
    user_model = User()

    with tab1:
        st.subheader("Login")
        
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        # Add reCAPTCHA
        st.markdown(recaptcha.render(), unsafe_allow_html=True)
        
        if st.button("Login"):
            if not email or not password:
                st.error("Please fill in all fields")
                return
                
            # Verify reCAPTCHA
            recaptcha_response = st.query_params.get("g-recaptcha-response")
            if not recaptcha.verify(recaptcha_response):
                st.error("Please complete the reCAPTCHA verification")
                return
                
            user = user_model.authenticate(email, password)
            if user:
                st.session_state.user = user
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password")

    with tab2:
        st.subheader("Register")
        
        new_email = st.text_input("Email", key="register_email")
        new_password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        # GDPR Consent
        consents = gdpr.render_consent_form()
        
        # Add reCAPTCHA
        st.markdown(recaptcha.render(), unsafe_allow_html=True)
        
        if st.button("Register"):
            if not new_email or not new_password or not confirm_password:
                st.error("Please fill in all fields")
                return
                
            if new_password != confirm_password:
                st.error("Passwords do not match")
                return
                
            if not consents['essential']:
                st.error("You must agree to essential data processing to use this service")
                return
                
            # Verify reCAPTCHA
            recaptcha_response = st.query_params.get("g-recaptcha-response")
            if not recaptcha.verify(recaptcha_response):
                st.error("Please complete the reCAPTCHA verification")
                return
                
            try:
                result = user_model.create_user(new_email, new_password, "customer")
                if result:
                    # Save GDPR consent
                    gdpr.save_user_consent(
                        user_id=result[0]['id'],
                        consents=consents,
                        ip_address=st.experimental_get_query_params().get('client_ip', ['unknown'])[0]
                    )
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Failed to create account")
            except Exception as e:
                st.error(f"Registration failed: {str(e)}")

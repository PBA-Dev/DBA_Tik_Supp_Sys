import os
import requests
import streamlit as st

class ReCaptcha:
    def __init__(self):
        self.site_key = os.environ.get('RECAPTCHA_SITE_KEY')
        self.secret_key = os.environ.get('RECAPTCHA_SECRET_KEY')
        self.verify_url = "https://www.google.com/recaptcha/api/siteverify"

    def render(self):
        return f"""
            <div class="g-recaptcha" data-sitekey="{self.site_key}"></div>
            <script src="https://www.google.com/recaptcha/api.js" async defer></script>
            <br/>
        """

    def verify(self, response_token):
        if not response_token:
            return False

        try:
            r = requests.post(
                self.verify_url,
                data={
                    'secret': self.secret_key,
                    'response': response_token
                }
            )
            result = r.json()
            return result.get('success', False)
        except Exception as e:
            st.error(f"ReCaptcha verification failed: {str(e)}")
            return False

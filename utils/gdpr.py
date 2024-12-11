import streamlit as st
from db.database import Database
import json
from datetime import datetime

class GDPRCompliance:
    def __init__(self):
        self.db = Database()
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Ensure the GDPR consent table exists"""
        query = """
            CREATE TABLE IF NOT EXISTS gdpr_consents (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                consents JSONB,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
        """
        self.db.execute(query)

    def render_consent_form(self):
        """Render GDPR consent checkboxes"""
        st.markdown("### Data Processing Consent")
        
        consent_essential = st.checkbox(
            "I agree to the essential data processing required for the service to function (Required)",
            key="consent_essential"
        )
        
        consent_communications = st.checkbox(
            "I agree to receive service-related communications",
            key="consent_communications"
        )
        
        consent_analytics = st.checkbox(
            "I agree to the use of my data for service improvement analytics",
            key="consent_analytics"
        )
        
        if st.button("Privacy Policy"):
            st.markdown(self.get_privacy_policy())
            
        return {
            "essential": consent_essential,
            "communications": consent_communications,
            "analytics": consent_analytics
        }

    def save_user_consent(self, user_id, consents, ip_address):
        """Save user's GDPR consent"""
        query = """
            INSERT INTO gdpr_consents (user_id, consents, ip_address)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET consents = EXCLUDED.consents,
                         ip_address = EXCLUDED.ip_address,
                         created_at = CURRENT_TIMESTAMP
        """
        consent_data = {
            "consents": consents,
            "timestamp": datetime.now().isoformat(),
        }
        self.db.execute(query, (user_id, json.dumps(consent_data), ip_address))

    def get_user_consent(self, user_id):
        """Get user's GDPR consent status"""
        query = """
            SELECT consents, created_at
            FROM gdpr_consents
            WHERE user_id = %s
        """
        result = self.db.execute(query, (user_id,))
        return result[0] if result else None

    def get_privacy_policy(self):
        """Return the privacy policy text"""
        return """
        ## Privacy Policy

        ### 1. Data Collection
        We collect and process the following types of data:
        - Account information (email, encrypted password)
        - Support ticket data
        - Usage analytics
        - Communication preferences

        ### 2. Data Usage
        Your data is used to:
        - Provide support ticket services
        - Improve our service
        - Send service-related communications
        - Ensure security and prevent fraud

        ### 3. Data Protection
        We implement appropriate technical and organizational measures to protect your data.

        ### 4. Your Rights
        You have the right to:
        - Access your personal data
        - Correct inaccurate data
        - Request data deletion
        - Withdraw consent
        - Export your data

        ### 5. Contact
        For privacy-related inquiries, contact our Data Protection Officer.

        ### 6. Updates
        This privacy policy may be updated periodically.
        """

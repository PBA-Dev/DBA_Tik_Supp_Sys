import streamlit as st
from models.ticket import Ticket
import time

class CommentHandler:
    def __init__(self):
        self.ticket_model = Ticket()

    def render_comments(self, ticket_id, user_id, user_role):
        # Display existing comments
        comments = self.ticket_model.get_ticket_comments(ticket_id)
        visible_comments = [c for c in comments if not c['is_private'] or 
                          user_role in ['admin', 'agent']]
        
        if visible_comments:
            for comment in visible_comments:
                with st.container():
                    privacy_badge = " 🔒 Private" if comment['is_private'] else ""
                    st.markdown(f"**{comment['user_email']}**{privacy_badge} - {comment['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    st.markdown(comment['content'])
                    st.markdown("---")
        else:
            st.info("No comments yet")

    def render_comment_form(self, ticket_id, user_id):
        st.subheader("Add Comment")
        
        # Create unique keys for this form
        form_key = f"comment_form_{ticket_id}"
        text_key = f"comment_text_{ticket_id}"
        private_key = f"private_{ticket_id}"
        
        # Initialize the comment text in session state if it doesn't exist
        if text_key not in st.session_state:
            st.session_state[text_key] = ""
        
        with st.form(key=form_key):
            # Text area for comment
            comment_text = st.text_area(
                "Comment",
                key=text_key,
                height=100
            )
            
            # Checkbox for private comment
            is_private = st.checkbox("Private Comment", key=private_key)
            
            # Submit button
            submit_clicked = st.form_submit_button("Add Comment")
            
            if submit_clicked:
                # Check if comment is not empty or just whitespace
                if not comment_text or comment_text.strip() == "":
                    st.error("Please enter a comment")
                else:
                    try:
                        # Add the comment to the database
                        self.ticket_model.add_comment(
                            ticket_id=ticket_id,
                            user_id=user_id,
                            content=comment_text.strip(),
                            is_private=is_private
                        )
                        
                        # Clear the form
                        st.session_state[text_key] = ""
                        
                        # Show success message
                        st.success("Comment added successfully")
                        
                        # Rerun the app to refresh the comments
                        time.sleep(0.1)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Failed to add comment: {str(e)}")

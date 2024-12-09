import streamlit as st
from models.ticket import Ticket
import time

class CommentHandler:
    def __init__(self):
        self.ticket_model = Ticket()

    def render_comments(self, ticket_id, user_id, user_role):
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
        
        with st.form(key=f"comment_form_{ticket_id}"):
            comment_text = st.text_area("Comment", height=100)
            is_private = st.checkbox("Private Comment")
            submitted = st.form_submit_button("Add Comment")
            
            if submitted:
                if not comment_text or comment_text.strip() == "":
                    st.error("Please enter a comment")
                else:
                    try:
                        self.ticket_model.add_comment(
                            ticket_id=ticket_id,
                            user_id=user_id,
                            content=comment_text.strip(),
                            is_private=is_private
                        )
                        st.success("Comment added successfully")
                        time.sleep(0.1)  # Small delay for state update
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add comment: {str(e)}")
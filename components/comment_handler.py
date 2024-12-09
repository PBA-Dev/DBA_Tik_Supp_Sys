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
        
        # Initialize state for this comment form
        form_id = f"comment_form_{ticket_id}"
        comment_key = f"comment_{ticket_id}"
        processing_key = f"processing_{ticket_id}"
        
        # Initialize form state if not exists
        if comment_key not in st.session_state:
            st.session_state[comment_key] = ""
        if processing_key not in st.session_state:
            st.session_state[processing_key] = False
            
        # Create a form for the comment
        with st.form(key=form_id, clear_on_submit=True):
            comment_content = st.text_area(
                "Comment",
                key=comment_key
            )
            is_private = st.checkbox("Private Comment", key=f"private_{ticket_id}")
            submit_button = st.form_submit_button("Add Comment")
            
            if submit_button:
                if not comment_content.strip():
                    st.error("Please enter a comment")
                    return
                
                if st.session_state.get(processing_key, False):
                    st.warning("Comment is being processed...")
                    return
                
                try:
                    # Set processing flag
                    st.session_state[processing_key] = True
                    
                    # Add the comment
                    self.ticket_model.add_comment(
                        ticket_id=ticket_id,
                        user_id=user_id,
                        content=comment_content,
                        is_private=is_private
                    )
                    
                    # Show success and rerun
                    st.success("Comment added successfully")
                    time.sleep(0.1)  # Small delay for state update
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to add comment: {str(e)}")
                finally:
                    st.session_state[processing_key] = False

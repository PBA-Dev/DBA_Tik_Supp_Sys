import streamlit as st
import time
from utils.auth import require_auth
from models.ticket import Ticket
from models.user import User
from components.rich_text import create_rich_text_editor
from components.file_handler import FileHandler
from utils.email import EmailNotifier

def render_tickets():
    require_auth()
    
    st.title("Ticket Management")
    
    ticket_model = Ticket()
    user_model = User()
    file_handler = FileHandler()
    email_notifier = EmailNotifier()
    
    tab1, tab2 = st.tabs(["Ticket List", "Create Ticket"])
    
    with tab1:
        # Get tickets based on user role
        tickets = ticket_model.get_all_tickets(
            user_id=st.session_state.user['id'],
            user_role=st.session_state.user['role']
        )
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Status", ["All", "Open", "In Progress", "Closed"])
        with col2:
            priority_filter = st.selectbox("Priority", ["All", "Low", "Medium", "High"])
        with col3:
            search = st.text_input("Search tickets")
        
        filtered_tickets = tickets
        if status_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t['status'].lower() == status_filter.lower()]
        if priority_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t['priority'].lower() == priority_filter.lower()]
        if search:
            filtered_tickets = [t for t in filtered_tickets if search.lower() in t['title'].lower()]
        
        for ticket in filtered_tickets:
            with st.expander(f"{ticket['title']} - {ticket['status'].upper()}"):
                st.write(f"Priority: {ticket['priority']}")
                st.write(f"Category: {ticket['category']}")
                st.write(f"Created by: {ticket['creator_email']}")
                
                # Show attachments
                attachments = file_handler.get_ticket_attachments(ticket['id'])
                if attachments:
                    st.subheader("Attachments")
                    for attachment in attachments:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if file_handler.is_image_file(attachment['file_name']):
                                st.image(
                                    f"data:image/png;base64,{attachment['file_data_base64']}", 
                                    caption=attachment['file_name'],
                                    use_container_width=True
                                )
                            st.write(f"📎 {attachment['file_name']} (Uploaded: {attachment['uploaded_at'].strftime('%Y-%m-%d %H:%M')})")
                    
                    # Add file upload for existing tickets
                    upload_key = f"upload_{ticket['id']}"
                    file_key = f"attachment_{ticket['id']}"
                    
                    if upload_key not in st.session_state:
                        st.session_state[upload_key] = False
                        
                    new_file = st.file_uploader("Add Attachment", key=file_key)
                    
                    if new_file and not st.session_state[upload_key]:
                        if file_handler.save_file(ticket['id'], new_file):
                            st.session_state[upload_key] = True
                            st.success("File uploaded successfully")
                            # Clear the file uploader
                            st.session_state[file_key] = None
                            st.rerun()
                        else:
                            st.error("Invalid file. Please ensure the file is under 5MB and has a valid extension (.txt, .pdf, .doc, .docx, .png, .jpg, .jpeg)")
                    
                    # Reset upload state when no file is selected
                    if not new_file:
                        st.session_state[upload_key] = False
                        
                # Handle comments using the CommentHandler
                from components.comment_handler import CommentHandler
                comment_handler = CommentHandler()
                
                # Show existing comments
                comment_handler.render_comments(
                    ticket_id=ticket['id'],
                    user_id=st.session_state.user['id'],
                    user_role=st.session_state.user['role']
                )
                
                # Render comment form
                comment_handler.render_comment_form(
                    ticket_id=ticket['id'],
                    user_id=st.session_state.user['id']
                )
                
                st.markdown("---")
                
                # Update ticket
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_status = st.selectbox("Update Status", 
                        ["Open", "In Progress", "Closed"],
                        key=f"status_{ticket['id']}"
                    )
                with col2:
                    new_priority = st.selectbox("Update Priority",
                        ["Low", "Medium", "High"],
                        key=f"priority_{ticket['id']}"
                    )
                with col3:
                    if st.session_state.user['role'] in ['admin', 'agent']:
                        agents = [u for u in user_model.get_all_users() if u['role'] in ['admin', 'agent']]
                        agent_options = [(None, "Unassigned")] + [(str(a['id']), a['email']) for a in agents]
                        current_assigned = str(ticket['assigned_to']) if ticket['assigned_to'] else None
                        selected_agent = st.selectbox(
                            "Assign To",
                            options=[id for id, _ in agent_options],
                            format_func=lambda x: dict(agent_options)[x],
                            index=next((i for i, (id, _) in enumerate(agent_options) if id == current_assigned), 0),
                            key=f"assign_{ticket['id']}"
                        )
                        assigned_to = int(selected_agent) if selected_agent else None
                    else:
                        assigned_to = ticket['assigned_to']
                
                with st.form(key=f"update_form_{ticket['id']}"):
                    submitted = st.form_submit_button("Update")
                    if submitted:
                        try:
                            with st.spinner("Updating ticket..."):
                                # Update ticket first
                                ticket_model.update_ticket(
                                    ticket['id'],
                                    status=new_status,
                                    priority=new_priority,
                                    assigned_to=assigned_to
                                )
                                
                                # Handle notifications in try-except blocks to prevent blocking
                                try:
                                    email_notifier.notify_ticket_updated(ticket, ticket['creator_email'])
                                    if assigned_to and assigned_to != ticket['assigned_to']:
                                        assigned_user = user_model.get_user_by_id(assigned_to)
                                        if assigned_user:
                                            email_notifier.notify_ticket_assigned(ticket, assigned_user['email'])
                                except Exception as e:
                                    st.warning(f"Ticket updated but notification failed: {str(e)}")
                                
                                st.success("Ticket updated successfully")
                                # Redirect to dashboard
                                st.session_state['navigation'] = "Dashboard"
                                time.sleep(0.1)  # Small delay to ensure state updates
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update ticket: {str(e)}")
    
    with tab2:
        st.subheader("Create New Ticket")
        
        # Initialize form fields in session state if not exists
        if 'title' not in st.session_state:
            st.session_state.title = ""
        if 'description' not in st.session_state:
            st.session_state.description = ""
            
        title = st.text_input("Title", key="title")
        description = create_rich_text_editor("new_ticket_description", st.session_state.get('description', ''))
        category = st.selectbox("Category", ["Technical", "Billing", "General"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        # Allow admin/agents to assign tickets to users during creation
        assigned_to = None
        if st.session_state.user['role'] in ['admin', 'agent']:
            user_model = User()
            all_users = user_model.get_all_users()
            user_options = [(None, "Unassigned")] + [(str(u['id']), f"{u['email']} ({u['role']})") for u in all_users]
            selected_user = st.selectbox(
                "Assign To",
                options=[id for id, _ in user_options],
                format_func=lambda x: dict(user_options)[x]
            )
            assigned_to = int(selected_user) if selected_user else None
        
        uploaded_file = st.file_uploader("Attach File", key="new_ticket_file")
        
        # Initialize ticket creation state
        if 'creating_ticket' not in st.session_state:
            st.session_state.creating_ticket = False
            
        if st.button("Create Ticket") and not st.session_state.creating_ticket:
            if not title or not description:
                st.error("Please fill in all required fields")
            else:
                try:
                    # Set creating flag to prevent multiple submissions
                    st.session_state.creating_ticket = True
                    
                    new_ticket = ticket_model.create_ticket(
                        title=title,
                        description=description,
                        status="Open",
                        priority=priority,
                        category=category,
                        created_by=st.session_state.user['id'],
                        assigned_to=assigned_to
                    )
                    
                    if uploaded_file:
                        file_handler.save_file(new_ticket[0]['id'], uploaded_file)
                    
                    # Notify admin
                    admins = [u for u in user_model.get_all_users() if u['role'] == 'admin']
                    if admins:
                        try:
                            email_notifier.notify_ticket_created(
                                {'title': title, 'priority': priority, 'description': description},
                                admins[0]['email']
                            )
                        except Exception as e:
                            st.warning(f"Ticket created but notification failed: {str(e)}")
                    
                    # Clear the form
                    st.session_state.title = ""
                    st.session_state.description = ""
                    st.session_state.uploaded_file = None
                    
                    st.success("Ticket created successfully")
                    time.sleep(0.1)  # Small delay to ensure state is updated
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create ticket: {str(e)}")
                finally:
                    st.session_state.creating_ticket = False

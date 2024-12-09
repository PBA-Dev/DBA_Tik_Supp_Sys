import streamlit as st
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
        tickets = ticket_model.get_all_tickets()
        
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
                        st.write(f"📎 {attachment['file_name']} (Uploaded: {attachment['uploaded_at'].strftime('%Y-%m-%d %H:%M')})")
                        
                # Show comments
                st.subheader("Comments")
                comments = ticket_model.get_ticket_comments(ticket['id'])
                # Filter private comments for non-admin/agent users
                visible_comments = [c for c in comments if not c['is_private'] or 
                                 st.session_state.user['role'] in ['admin', 'agent']]
                for comment in visible_comments:
                    with st.container():
                        privacy_badge = " 🔒 Private" if comment['is_private'] else ""
                        st.markdown(f"**{comment['user_email']}**{privacy_badge} - {comment['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        st.markdown(comment['content'])
                        st.markdown("---")
                
                # Add new comment
                st.subheader("Add Comment")
                new_comment = create_rich_text_editor(f"comment_{ticket['id']}")
                is_private = st.checkbox("Private Comment", key=f"private_{ticket['id']}")
                if st.button("Add Comment", key=f"add_comment_{ticket['id']}"):
                    if new_comment:
                        ticket_model.add_comment(
                            ticket_id=ticket['id'],
                            user_id=st.session_state.user['id'],
                            content=new_comment,
                            is_private=is_private
                        )
                        st.success("Comment added successfully")
                        st.rerun()
                    else:
                        st.error("Please enter a comment")
                
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
                
                if st.button("Update", key=f"update_{ticket['id']}"):
                    ticket_model.update_ticket(
                        ticket['id'],
                        status=new_status,
                        priority=new_priority,
                        assigned_to=assigned_to
                    )
                    
                    # Notify ticket creator
                    email_notifier.notify_ticket_updated(ticket, ticket['creator_email'])
                    
                    # Notify assigned agent if changed
                    if assigned_to and assigned_to != ticket['assigned_to']:
                        assigned_user = user_model.get_user_by_id(assigned_to)
                        if assigned_user:
                            email_notifier.notify_ticket_assigned(ticket, assigned_user['email'])
                    
                    st.success("Ticket updated successfully")
                    st.rerun()
    
    with tab2:
        st.subheader("Create New Ticket")
        
        title = st.text_input("Title")
        description = create_rich_text_editor("new_ticket_description")
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
        
        if st.button("Create Ticket"):
            if not title or not description:
                st.error("Please fill in all required fields")
            else:
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
                    email_notifier.notify_ticket_created(
                        {'title': title, 'priority': priority, 'description': description},
                        admins[0]['email']
                    )
                
                st.success("Ticket created successfully")
                st.rerun()

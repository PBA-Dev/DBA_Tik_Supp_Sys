import streamlit as st
import time
from utils.auth import require_auth
from models.ticket import Ticket
from models.user import User
from models.custom_field import CustomField
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
    custom_field = CustomField()
    
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
                
                # Display custom field values
                field_values = custom_field.get_ticket_field_values(ticket['id'])
                if field_values:
                    st.subheader("Additional Information")
                    for field_value in field_values:
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.markdown(f"**{field_value['field_name']}:**")
                        with col2:
                            value = field_value['field_value']
                            if field_value['field_type'] == 'MultiSelect' and value:
                                value = ', '.join(value.split(','))
                            elif field_value['field_type'] == 'Checkbox':
                                value = '✓' if value.lower() == 'true' else '✗'
                            elif field_value['field_type'] == 'Date':
                                try:
                                    value = value.split()[0]  # Get only the date part
                                except:
                                    pass
                            st.write(value)
                
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
                    
                    if new_file:
                        if file_handler.save_file(ticket['id'], new_file):
                            st.success("File uploaded successfully")
                            st.session_state['navigation'] = "Dashboard"
                            time.sleep(0.1)  # Small delay to ensure state updates
                            st.rerun()
                        else:
                            st.error("Invalid file. Please ensure the file is under 5MB and has a valid extension (.txt, .pdf, .doc, .docx, .png, .jpg, .jpeg)")
                        
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
                            # Update ticket first
                            ticket_model.update_ticket(
                                ticket['id'],
                                status=new_status,
                                priority=new_priority,
                                assigned_to=assigned_to
                            )
                            
                            # Handle notifications asynchronously
                            try:
                                email_notifier.notify_ticket_updated(ticket, ticket['creator_email'])
                                if assigned_to and assigned_to != ticket['assigned_to']:
                                    assigned_user = user_model.get_user_by_id(assigned_to)
                                    if assigned_user:
                                        email_notifier.notify_ticket_assigned(ticket, assigned_user['email'])
                            except Exception:
                                pass  # Ignore notification errors to prevent blocking
                            
                            st.success(f"Ticket '{ticket['title']}' updated successfully")
                            st.session_state['navigation'] = "Dashboard"
                            time.sleep(0.5)  # Brief pause to show success message
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
        
        # Custom Fields
        st.subheader("Additional Information")
        custom_fields = custom_field.get_all_fields()
        custom_field_values = {}
        
        if custom_fields:
            # First, render fields without dependencies
            independent_fields = [f for f in custom_fields if not f.get('depends_on')]
            dependent_fields = [f for f in custom_fields if f.get('depends_on')]
            
            # Helper function to check if field should be shown based on dependencies
            def should_show_field(field):
                if not field.get('depends_on'):
                    return True
                    
                depends_on = field['depends_on']
                if not depends_on:
                    return True
                    
                parent_field_id = depends_on.get('field_id')
                if not parent_field_id:
                    return True
                    
                parent_value = custom_field_values.get(parent_field_id)
                if parent_value is None:
                    return False
                    
                if 'value' in depends_on:  # Checkbox dependency
                    expected_value = str(depends_on['value']).lower() == 'true'
                    actual_value = str(parent_value).lower() == 'true'
                    return expected_value == actual_value
                elif 'values' in depends_on:  # Dropdown/MultiSelect dependency
                    parent_values = parent_value.split(',') if isinstance(parent_value, str) else [parent_value]
                    return any(str(v) in map(str, depends_on['values']) for v in parent_values)
                return True
            
            # Helper function to render a single field
            def render_field(field):
                field_id = field['id']
                label = f"{field['field_name']}" + (" *" if field['is_required'] else "")
                help = field.get('help_text', '')
                
                validation = field.get('validation_rules', {}) or {}
                value = None
                
                if field['field_type'] == 'Text':
                    value = st.text_input(
                        label,
                        help=help,
                        key=f"custom_{field_id}"
                    )
                    # Validate text input
                    if value and validation:
                        if 'min_length' in validation and len(value) < validation['min_length']:
                            st.error(f"Minimum length is {validation['min_length']} characters")
                        if 'max_length' in validation and len(value) > validation['max_length']:
                            st.error(f"Maximum length is {validation['max_length']} characters")
                        if 'pattern' in validation:
                            import re
                            if not re.match(validation['pattern'], value):
                                st.error("Input format is invalid")
                
                elif field['field_type'] == 'Number':
                    min_val = validation.get('min_value', None)
                    max_val = validation.get('max_value', None)
                    value = st.number_input(
                        label,
                        min_value=min_val if min_val is not None else None,
                        max_value=max_val if max_val is not None else None,
                        help=help,
                        key=f"custom_{field_id}"
                    )
                
                elif field['field_type'] == 'Date':
                    value = st.date_input(
                        label,
                        help=help,
                        key=f"custom_{field_id}"
                    )
                
                elif field['field_type'] == 'Dropdown':
                    value = st.selectbox(
                        label,
                        options=field['field_options'] if field['field_options'] else [],
                        help=help,
                        key=f"custom_{field_id}"
                    )
                
                elif field['field_type'] == 'MultiSelect':
                    value = st.multiselect(
                        label,
                        options=field['field_options'] if field['field_options'] else [],
                        help=help,
                        key=f"custom_{field_id}"
                    )
                
                elif field['field_type'] == 'Checkbox':
                    value = st.checkbox(
                        label,
                        help=help,
                        key=f"custom_{field_id}"
                    )
                
                return value
            
            # Render independent fields first
            for field in independent_fields:
                custom_field_values[field['id']] = render_field(field)
            
            # Then render dependent fields if their conditions are met
            for field in dependent_fields:
                if should_show_field(field):
                    custom_field_values[field['id']] = render_field(field)
        
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
            validation_failed = False
            
            # Basic field validation
            if not title or not description:
                st.error("Please fill in all required fields")
                validation_failed = True
            
            # Custom fields validation
            if custom_fields:
                for field in custom_fields:
                    field_id = field['id']
                    value = custom_field_values.get(field_id)
                    
                    if field['is_required']:
                        if value is None or (isinstance(value, str) and not value.strip()):
                            st.error(f"{field['field_name']} is required")
                            validation_failed = True
                        elif isinstance(value, list) and not value:
                            st.error(f"Please select at least one option for {field['field_name']}")
                            validation_failed = True
            
            if not validation_failed:
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
                    
                    # Add initial comment with the description
                    if description:
                        try:
                            comment_result = ticket_model.add_comment(
                                ticket_id=new_ticket[0]['id'],
                                user_id=st.session_state.user['id'],
                                content=description,
                                is_private=False
                            )
                            if not comment_result:
                                st.warning("Initial comment was not saved properly")
                        except Exception as e:
                            st.error(f"Error saving initial comment: {str(e)}")
                    
                    # Save custom field values
                    for field in custom_fields:
                        field_id = field['id']
                        value = custom_field_values.get(field_id)
                        
                        # Only save fields that should be visible based on dependencies
                        if should_show_field(field):
                            if isinstance(value, (list, set)):
                                value = ','.join(map(str, value))
                            elif not isinstance(value, (str, int, float)):
                                value = str(value)
                            if value is not None:  # Only save non-None values
                                custom_field.save_field_value(new_ticket[0]['id'], field_id, value)
                    
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
                    
                    st.success(f"Ticket '{title}' created successfully with {priority} priority")
                    time.sleep(0.5)  # Brief pause to show success message
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create ticket: {str(e)}")
                finally:
                    st.session_state.creating_ticket = False

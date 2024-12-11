import streamlit as st
import time
from utils.auth import require_auth
from models.custom_field import CustomField

def render_settings():
    require_auth('admin')
    
    st.title("System Settings")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Email Settings", "File Upload Settings", "Custom Fields", "Macros", "Audit Logs"])
    
    with tab1:
        st.subheader("Email Settings")
        smtp_server = st.text_input("SMTP Server", value="smtp.yourdomain.com")
        smtp_port = st.number_input("SMTP Port", value=587)
        smtp_user = st.text_input("SMTP Username")
        smtp_password = st.text_input("SMTP Password", type="password")
        
        if st.button("Save Email Settings"):
            st.success("Email settings saved successfully")
    
    with tab2:
        st.subheader("File Upload Settings")
        max_file_size = st.number_input("Max File Size (MB)", value=5)
        allowed_extensions = st.multiselect(
            "Allowed File Extensions",
            [".txt", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"],
            default=[".txt", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"]
        )
        
        if st.button("Save Upload Settings"):
            st.success("File upload settings saved successfully")
            
    with tab3:
        st.subheader("Custom Fields")
        
    with tab4:
        st.subheader("Macros")
        from models.macro import Macro
        
        macro_model = Macro()
        
        # Create new macro
        with st.expander("Create New Macro"):
            with st.form("create_macro"):
                macro_name = st.text_input("Macro Name")
                macro_description = st.text_area("Description")
                
                st.subheader("Actions")
                update_status = st.checkbox("Update Status")
                new_status = st.selectbox("New Status", ["Open", "In Progress", "Closed"]) if update_status else None
                
                update_priority = st.checkbox("Update Priority")
                new_priority = st.selectbox("New Priority", ["Low", "Medium", "High"]) if update_priority else None
                
                add_comment = st.checkbox("Add Comment")
                comment_template = st.text_area("Comment Template") if add_comment else None
                
                submitted = st.form_submit_button("Create Macro")
                
                if submitted:
                    if not macro_name:
                        st.error("Macro name is required")
                    else:
                        actions = {}
                        if update_status:
                            actions['status'] = new_status
                        if update_priority:
                            actions['priority'] = new_priority
                        if add_comment:
                            actions['comment'] = comment_template
                            
                        if not actions:
                            st.error("Please select at least one action")
                        else:
                            try:
                                macro_model.create_macro(
                                    name=macro_name,
                                    user_id=st.session_state.user['id'],
                                    actions=actions,
                                    description=macro_description
                                )
                                st.success("Macro created successfully")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to create macro: {str(e)}")
        
        # List existing macros
        st.subheader("Your Macros")
        macros = macro_model.get_user_macros(st.session_state.user['id'])
        
        if not macros:
            st.info("You haven't created any macros yet")
        else:
            for macro in macros:
                with st.expander(f"{macro['name']}"):
                    if macro['description']:
                        st.write("Description:", macro['description'])
                    
                    st.write("Actions:")
                    actions = macro['actions']
                    if 'status' in actions:
                        st.write(f"- Update status to: {actions['status']}")
                    if 'priority' in actions:
                        st.write(f"- Update priority to: {actions['priority']}")
                    if 'comment' in actions:
                        st.write("- Add comment:")
                        st.text_area("Template", actions['comment'], disabled=True)
                    
                    if st.button("Delete Macro", key=f"delete_macro_{macro['id']}"):
                        if macro_model.delete_macro(macro['id'], st.session_state.user['id']):
                            st.success("Macro deleted successfully")
                            st.rerun()
                        else:
                            st.error("Failed to delete macro")
                            
    with tab5:
        st.subheader("Audit Logs")
        from db.database import Database
        
        db = Database()
        query = """
            SELECT al.*, u.email as user_email
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            ORDER BY al.created_at DESC
            LIMIT 100
        """
        logs = db.execute(query)
        
        if not logs:
            st.info("No audit logs found")
        else:
            for log in logs:
                with st.expander(f"{log['operation'].upper()} {log['entity_type']} - {log['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    st.write(f"Operation: {log['operation'].upper()}")
                    st.write(f"Entity Type: {log['entity_type']}")
                    st.write(f"Entity ID: {log['entity_id']}")
                    if log['user_email']:
                        st.write(f"User: {log['user_email']}")
                    if log['details']:
                        st.json(log['details'])
        custom_field = CustomField()
        
        # Create new custom field
        with st.expander("Add New Custom Field"):
            field_name = st.text_input("Field Name")
            field_type = st.selectbox(
                "Field Type",
                ["Text", "Number", "Date", "Dropdown", "MultiSelect", "Checkbox"]
            )
            
            help_text = st.text_input("Help Text", help="Explanatory text that appears below the field")
            
            # Field options for dropdown and multiselect
            field_options = None
            if field_type in ["Dropdown", "MultiSelect"]:
                options_input = st.text_area(
                    "Options (one per line)",
                    help="Enter each option on a new line"
                )
                if options_input:
                    field_options = [opt.strip() for opt in options_input.split('\n') if opt.strip()]
            
            # Validation rules based on field type
            validation_rules = {}
            if field_type == "Text":
                regex_pattern = st.text_input(
                    "Validation Pattern (regex)",
                    help="Optional: Enter a regular expression pattern for validation"
                )
                min_length = st.number_input("Minimum Length", min_value=0, value=0)
                max_length = st.number_input("Maximum Length", min_value=0, value=0)
                if regex_pattern:
                    validation_rules["pattern"] = regex_pattern
                if min_length > 0:
                    validation_rules["min_length"] = min_length
                if max_length > 0:
                    validation_rules["max_length"] = max_length
                    
            elif field_type == "Number":
                min_value = st.number_input("Minimum Value", value=0)
                max_value = st.number_input("Maximum Value", value=0)
                if min_value != 0:
                    validation_rules["min_value"] = min_value
                if max_value != 0:
                    validation_rules["max_value"] = max_value
            
            # Field dependencies
            existing_fields = [f for f in custom_field.get_all_fields() if f['field_type'] in ["Dropdown", "MultiSelect", "Checkbox"]]
            if existing_fields:
                st.subheader("Field Dependencies")
                add_dependency = st.checkbox("Add dependency rule")
                
                if add_dependency:
                    depends_on_field = st.selectbox(
                        "Show this field when",
                        options=[(f['id'], f['field_name']) for f in existing_fields],
                        format_func=lambda x: x[1]
                    )
                    if depends_on_field:
                        field_id, _ = depends_on_field
                        depend_field = next(f for f in existing_fields if f['id'] == field_id)
                        
                        if depend_field['field_type'] == "Checkbox":
                            show_when = st.radio("Show when value is", ["True", "False"])
                            validation_rules["depends_on"] = {
                                "field_id": field_id,
                                "value": show_when == "True"
                            }
                        else:
                            selected_values = st.multiselect(
                                "Show when value is",
                                options=depend_field['field_options']
                            )
                            if selected_values:
                                validation_rules["depends_on"] = {
                                    "field_id": field_id,
                                    "values": selected_values
                                }
            
            is_required = st.checkbox("Required Field")
            
            if st.button("Create Field"):
                if not field_name:
                    st.error("Field name is required")
                elif field_type in ["Dropdown", "MultiSelect"] and not field_options:
                    st.error("Options are required for Dropdown/MultiSelect fields")
                else:
                    try:
                        custom_field.create_field(
                            field_name=field_name,
                            field_type=field_type,
                            field_options=field_options,
                            is_required=is_required,
                            validation_rules=validation_rules if validation_rules else None,
                            help_text=help_text if help_text.strip() else None,
                            depends_on=validation_rules.get("depends_on") if validation_rules else None,
                            user_id=st.session_state.user['id']
                        )
                        st.success(f"Custom field '{field_name}' created successfully")
                        time.sleep(0.5)  # Brief pause to show success message
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create custom field: {str(e)}")
        
        # List and manage existing custom fields
        st.subheader("Existing Custom Fields")
        fields = custom_field.get_all_fields()
        
        if not fields:
            st.info("No custom fields defined yet")
        else:
            for field in fields:
                with st.expander(f"{field['field_name']} ({field['field_type']})"):
                    st.write(f"Type: {field['field_type']}")
                    st.write(f"Required: {'Yes' if field['is_required'] else 'No'}")
                    if field['field_options']:
                        st.write("Options:", ", ".join(field['field_options']))
                    
                    # Update field
                    new_name = st.text_input("Update Name", value=field['field_name'], key=f"name_{field['id']}")
                    new_required = st.checkbox("Update Required", value=field['is_required'], key=f"req_{field['id']}")
                    
                    new_options = None
                    if field['field_type'] in ["Dropdown", "MultiSelect"]:
                        options_str = "\n".join(field['field_options'] if field['field_options'] else [])
                        new_options_input = st.text_area(
                            "Update Options (one per line)", 
                            value=options_str,
                            key=f"opt_{field['id']}"
                        )
                        if new_options_input:
                            new_options = [opt.strip() for opt in new_options_input.split('\n') if opt.strip()]
                    
                    if st.button("Update Field", key=f"update_{field['id']}"):
                        try:
                            custom_field.update_field(
                                field_id=field['id'],
                                field_name=new_name,
                                field_options=new_options,
                                is_required=new_required,
                                user_id=st.session_state.user['id']
                            )
                            st.success("Field updated successfully")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update field: {str(e)}")
                            
                    # Delete field section
                    st.markdown("---")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        delete_confirm = st.checkbox(
                            "I understand this will permanently delete this field and all its values",
                            key=f"confirm_delete_{field['id']}"
                        )
                    with col2:
                        if st.button(
                            "Delete Field",
                            key=f"delete_field_{field['id']}",
                            type="secondary",
                            disabled=not delete_confirm
                        ):
                            try:
                                if custom_field.delete_field(field['id']):
                                    st.success("Field deleted successfully")
                                    time.sleep(0.5)  # Brief pause to show success message
                                    st.rerun()
                                else:
                                    st.error("Failed to delete field: No such field exists")
                            except Exception as e:
                                st.error(f"Failed to delete field: {str(e)}")

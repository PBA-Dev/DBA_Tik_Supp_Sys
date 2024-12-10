import streamlit as st
from utils.auth import require_auth
from models.custom_field import CustomField

def render_settings():
    require_auth('admin')
    
    st.title("System Settings")
    
    tabs = st.tabs(["Email Settings", "File Upload Settings", "Custom Fields"])
    
    with tabs[0]:
        st.subheader("Email Settings")
        smtp_server = st.text_input("SMTP Server", value="smtp.yourdomain.com")
        smtp_port = st.number_input("SMTP Port", value=587)
        smtp_user = st.text_input("SMTP Username")
        smtp_password = st.text_input("SMTP Password", type="password")
        
        if st.button("Save Email Settings"):
            st.success("Email settings saved successfully")
    
    with tabs[1]:
        st.subheader("File Upload Settings")
        max_file_size = st.number_input("Max File Size (MB)", value=5)
        allowed_extensions = st.multiselect(
            "Allowed File Extensions",
            [".txt", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"],
            default=[".txt", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"]
        )
        
        if st.button("Save Upload Settings"):
            st.success("File upload settings saved successfully")
            
    with tabs[2]:
        st.subheader("Custom Fields")
        custom_field = CustomField()
        
        # Create new custom field
        with st.expander("Add New Custom Field"):
            field_name = st.text_input("Field Name")
            field_type = st.selectbox(
                "Field Type",
                ["Text", "Number", "Date", "Dropdown", "MultiSelect", "Checkbox"]
            )
            
            field_options = None
            if field_type in ["Dropdown", "MultiSelect"]:
                options_input = st.text_area(
                    "Options (one per line)",
                    help="Enter each option on a new line"
                )
                if options_input:
                    field_options = [opt.strip() for opt in options_input.split('\n') if opt.strip()]
                    
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
                            is_required=is_required
                        )
                        st.success("Custom field created successfully")
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
                                is_required=new_required
                            )
                            st.success("Field updated successfully")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update field: {str(e)}")

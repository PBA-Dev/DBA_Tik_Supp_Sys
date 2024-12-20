import streamlit as st
from streamlit_quill import st_quill

def create_rich_text_editor(key, default_value=""):
    # Return empty string if the editor is cleared
    content = st_quill(
        value=default_value,
        key=key,
        html=True,
        toolbar=[
            ['bold', 'italic', 'underline', 'strike'],
            ['blockquote', 'code-block'],
            [{'list': 'ordered'}, {'list': 'bullet'}],
            ['link'],
            ['clean']
        ]
    )
    return content if content else ""

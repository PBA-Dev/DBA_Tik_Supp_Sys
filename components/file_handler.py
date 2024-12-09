import streamlit as st
import os
from db.database import Database

class FileHandler:
    def __init__(self):
        self.db = Database()
        self.allowed_extensions = {'.txt', '.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg'}
        self.max_file_size = 5 * 1024 * 1024  # 5MB limit
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.gif'}

    def is_valid_file(self, file):
        if file is None:
            return False
        
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in self.allowed_extensions:
            return False
            
        if file.size > self.max_file_size:
            return False
            
        return True

    def save_file(self, ticket_id, file):
        if not self.is_valid_file(file):
            return False
            
        query = """
            INSERT INTO attachments (ticket_id, file_name, file_data)
            VALUES (%s, %s, %s) RETURNING id
        """
        
        file_data = file.read()
        return self.db.execute(query, (ticket_id, file.name, file_data))

    def get_ticket_attachments(self, ticket_id):
        query = """
            SELECT id, file_name, uploaded_at, 
                   encode(file_data, 'base64') as file_data_base64
            FROM attachments
            WHERE ticket_id = %s
        """
        return self.db.execute(query, (ticket_id,))

    def is_image_file(self, filename):
        return os.path.splitext(filename)[1].lower() in self.image_extensions

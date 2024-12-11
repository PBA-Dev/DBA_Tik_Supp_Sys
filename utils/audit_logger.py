from db.database import Database
import json

class AuditLogger:
    def __init__(self):
        self.db = Database()
    
    def log_action(self, operation, entity_type, entity_id, user_id, details=None):
        """
        Log an action in the audit_logs table
        
        Args:
            operation (str): The type of operation (create, update, delete)
            entity_type (str): The type of entity (field, ticket)
            entity_id (int): The ID of the entity
            user_id (int): The ID of the user performing the action
            details (dict, optional): Additional details about the change
        """
        query = """
            INSERT INTO audit_logs (operation, entity_type, entity_id, user_id, details)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            details_json = json.dumps(details) if details else None
            self.db.execute(query, (operation, entity_type, entity_id, user_id, details_json))
        except Exception as e:
            print(f"Failed to log action: {str(e)}")

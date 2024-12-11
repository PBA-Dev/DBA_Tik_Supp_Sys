from db.database import Database
from psycopg2.extras import Json
import json

class Macro:
    def __init__(self):
        self.db = Database()
    
    def create_macro(self, name, user_id, actions, description=None):
        """Create a new macro"""
        query = """
            INSERT INTO macros (name, user_id, actions, description)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, actions
        """
        try:
            return self.db.execute(query, (name, user_id, Json(actions), description))
        except Exception as e:
            print(f"Error creating macro: {str(e)}")
            raise
    
    def get_user_macros(self, user_id):
        """Get all macros for a user"""
        query = """
            SELECT id, name, actions, description, created_at, updated_at
            FROM macros
            WHERE user_id = %s
            ORDER BY name
        """
        return self.db.execute(query, (user_id,))
    
    def get_macro_by_id(self, macro_id, user_id):
        """Get a specific macro by ID and user"""
        query = """
            SELECT id, name, actions, description
            FROM macros
            WHERE id = %s AND user_id = %s
        """
        result = self.db.execute(query, (macro_id, user_id))
        return result[0] if result else None
    
    def update_macro(self, macro_id, user_id, name=None, actions=None, description=None):
        """Update an existing macro"""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if actions is not None:
            updates.append("actions = %s")
            params.append(Json(actions))
        if description is not None:
            updates.append("description = %s")
            params.append(description)
            
        if not updates:
            return None
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([macro_id, user_id])
        
        query = f"""
            UPDATE macros 
            SET {', '.join(updates)}
            WHERE id = %s AND user_id = %s
            RETURNING id, name, actions
        """
        result = self.db.execute(query, tuple(params))
        return result[0] if result else None
    
    def delete_macro(self, macro_id, user_id):
        """Delete a macro"""
        query = """
            DELETE FROM macros 
            WHERE id = %s AND user_id = %s
            RETURNING id
        """
        result = self.db.execute(query, (macro_id, user_id))
        return bool(result)

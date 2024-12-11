from db.database import Database
from psycopg2.extras import Json
import json

class SavedFilter:
    def __init__(self):
        self.db = Database()
    
    def create_filter(self, name, user_id, filter_criteria, is_macro=False):
        """Create a new saved filter"""
        query = """
            INSERT INTO saved_filters (name, user_id, filter_criteria, is_macro)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, filter_criteria
        """
        try:
            return self.db.execute(query, (name, user_id, Json(filter_criteria), is_macro))
        except Exception as e:
            print(f"Error creating filter: {str(e)}")
            raise

    def get_user_filters(self, user_id, include_macros=True):
        """Get all filters for a user"""
        query = """
            SELECT id, name, filter_criteria, is_macro, created_at, updated_at
            FROM saved_filters
            WHERE user_id = %s
            AND (is_macro = %s OR %s = TRUE)
            ORDER BY name
        """
        return self.db.execute(query, (user_id, False, include_macros))

    def get_filter_by_id(self, filter_id, user_id):
        """Get a specific filter by ID and user"""
        query = """
            SELECT id, name, filter_criteria, is_macro
            FROM saved_filters
            WHERE id = %s AND user_id = %s
        """
        result = self.db.execute(query, (filter_id, user_id))
        return result[0] if result else None

    def update_filter(self, filter_id, user_id, name=None, filter_criteria=None):
        """Update an existing filter"""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if filter_criteria is not None:
            updates.append("filter_criteria = %s")
            params.append(Json(filter_criteria))
            
        if not updates:
            return None
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([filter_id, user_id])
        
        query = f"""
            UPDATE saved_filters 
            SET {', '.join(updates)}
            WHERE id = %s AND user_id = %s
            RETURNING id, name, filter_criteria
        """
        result = self.db.execute(query, tuple(params))
        return result[0] if result else None

    def delete_filter(self, filter_id, user_id):
        """Delete a saved filter"""
        query = """
            DELETE FROM saved_filters 
            WHERE id = %s AND user_id = %s
            RETURNING id
        """
        result = self.db.execute(query, (filter_id, user_id))
        return bool(result)

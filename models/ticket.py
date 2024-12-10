from db.database import Database

class Ticket:
    def __init__(self):
        self.db = Database()

    def create_ticket(self, title, description, status, priority, category, created_by, assigned_to=None):
        query = """
            INSERT INTO tickets (title, description, status, priority, category, created_by, assigned_to)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        return self.db.execute(query, (title, description, status, priority, category, created_by, assigned_to))

    def get_all_tickets(self, user_id=None, user_role=None):
        base_query = """
            SELECT t.*, u1.email as creator_email, u2.email as assignee_email
            FROM tickets t
            LEFT JOIN users u1 ON t.created_by = u1.id
            LEFT JOIN users u2 ON t.assigned_to = u2.id
        """
        
        if user_role == 'customer':
            base_query += " WHERE t.created_by = %s OR t.assigned_to = %s"
            return self.db.execute(base_query, (user_id, user_id))
        
        return self.db.execute(base_query)

    def get_ticket_by_id(self, ticket_id):
        query = """
            SELECT t.*, u1.email as creator_email, u2.email as assignee_email
            FROM tickets t
            LEFT JOIN users u1 ON t.created_by = u1.id
            LEFT JOIN users u2 ON t.assigned_to = u2.id
            WHERE t.id = %s
        """
        result = self.db.execute(query, (ticket_id,))
        return result[0] if result else None

    def update_ticket(self, ticket_id, status=None, priority=None, assigned_to=None):
        updates = []
        params = []
        
        if status:
            updates.append("status = %s")
            params.append(status)
        if priority:
            updates.append("priority = %s")
            params.append(priority)
        if assigned_to:
            updates.append("assigned_to = %s")
            params.append(assigned_to)
            
        params.append(ticket_id)
        
        query = f"""
            UPDATE tickets SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        return self.db.execute(query, tuple(params))

    def add_comment(self, ticket_id, user_id, content, is_private=False):
        if not content or not content.strip():
            return None
            
        query = """
            INSERT INTO comments (ticket_id, user_id, content, is_private)
            VALUES (%s, %s, %s, %s) RETURNING id, ticket_id, user_id, content, is_private
        """
        result = self.db.execute(query, (ticket_id, user_id, content.strip(), is_private))
        return result[0] if result else None

    def get_ticket_comments(self, ticket_id):
        query = """
            SELECT c.*, u.email as user_email
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.ticket_id = %s
            ORDER BY c.created_at DESC
        """
        return self.db.execute(query, (ticket_id,))

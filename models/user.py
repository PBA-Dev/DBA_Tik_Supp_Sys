import hashlib
import uuid
from db.database import Database

class User:
    def __init__(self):
        self.db = Database()

    def create_user(self, email, password, role):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        query = """
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, %s) RETURNING id
        """
        return self.db.execute(query, (email, password_hash, role))

    def authenticate(self, email, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        query = """
            SELECT * FROM users WHERE email = %s AND password_hash = %s
        """
        result = self.db.execute(query, (email, password_hash))
        return result[0] if result else None

    def get_all_users(self):
        query = "SELECT id, email, role, created_at FROM users"
        return self.db.execute(query)

    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id = %s"
        result = self.db.execute(query, (user_id,))
        return result[0] if result else None

import os
import psycopg2
from psycopg2.extras import RealDictCursor

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.conn = psycopg2.connect(
                os.environ['DATABASE_URL'],
                sslmode='require'
            )
            cls._instance.create_tables()
        return cls._instance

    def create_tables(self):
        with self.conn.cursor() as cur:
            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tickets table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    priority VARCHAR(20) NOT NULL,
                    category VARCHAR(50),
                    created_by INTEGER REFERENCES users(id),
                    assigned_to INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Attachments table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attachments (
                    id SERIAL PRIMARY KEY,
                    ticket_id INTEGER REFERENCES tickets(id),
                    file_name VARCHAR(255) NOT NULL,
                    file_data BYTEA NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Comments table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id SERIAL PRIMARY KEY,
                    ticket_id INTEGER REFERENCES tickets(id),
                    user_id INTEGER REFERENCES users(id),
                    content TEXT NOT NULL,
                    is_private BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.commit()

    def execute(self, query, params=None):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            self.conn.commit()
            try:
                return cur.fetchall()
            except:
                return None

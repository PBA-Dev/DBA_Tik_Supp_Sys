import os
import time
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

class Database:
    _instance = None
    _pool = None
    _max_retries = 3
    _retry_delay = 1  # seconds

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize_pool()
            cls._instance.create_tables()
        return cls._instance

    def _initialize_pool(self):
        """Initialize the connection pool with retry logic"""
        retry_count = 0
        while retry_count < self._max_retries:
            try:
                if self._pool is None or self._pool.closed:
                    self._pool = psycopg2.pool.SimpleConnectionPool(
                        minconn=1,
                        maxconn=10,
                        dsn=os.environ['DATABASE_URL'],
                        sslmode='require'
                    )
                break
            except (psycopg2.Error, Exception) as e:
                retry_count += 1
                if retry_count == self._max_retries:
                    raise Exception(f"Failed to initialize database pool after {self._max_retries} attempts: {str(e)}")
                time.sleep(self._retry_delay)

    def _get_connection(self):
        """Get a connection from the pool with retry logic"""
        retry_count = 0
        while retry_count < self._max_retries:
            try:
                conn = self._pool.getconn()
                if conn is None or conn.closed:
                    self._initialize_pool()
                    conn = self._pool.getconn()
                return conn
            except (psycopg2.Error, Exception) as e:
                retry_count += 1
                if retry_count == self._max_retries:
                    raise Exception(f"Failed to get database connection after {self._max_retries} attempts: {str(e)}")
                time.sleep(self._retry_delay)
                self._initialize_pool()

    def _return_connection(self, conn):
        """Return a connection to the pool"""
        try:
            self._pool.putconn(conn)
        except Exception:
            # If returning the connection fails, just close it
            try:
                conn.close()
            except Exception:
                pass

    def create_tables(self):
        """Create database tables with retry logic"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
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
                
                conn.commit()
        finally:
            self._return_connection(conn)

    def execute(self, query, params=None):
        """Execute a query with retry logic"""
        retry_count = 0
        last_error = None
        while retry_count < self._max_retries:
            conn = None
            try:
                conn = self._get_connection()
                if conn is None or conn.closed:
                    raise Exception("Failed to get valid database connection")
                    
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    conn.commit()
                    try:
                        result = cur.fetchall()
                        return result
                    except psycopg2.ProgrammingError:
                        return None
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                last_error = e
                retry_count += 1
                if retry_count < self._max_retries:
                    print(f"Database connection error (attempt {retry_count}): {str(e)}")
                    time.sleep(self._retry_delay * retry_count)  # Exponential backoff
                    self._initialize_pool()  # Reinitialize the pool on connection errors
            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count < self._max_retries:
                    print(f"Query execution error (attempt {retry_count}): {str(e)}")
                    time.sleep(self._retry_delay)
            finally:
                if conn:
                    try:
                        self._return_connection(conn)
                    except Exception as e:
                        print(f"Error returning connection to pool: {str(e)}")
        
        if last_error:
            raise Exception(f"Query execution failed after {self._max_retries} attempts. Last error: {str(last_error)}")
        raise Exception("Query execution failed with unknown error")

    def __del__(self):
        """Cleanup: close all connections in the pool"""
        if self._pool:
            self._pool.closeall()

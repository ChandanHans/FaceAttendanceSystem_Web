import mysql.connector
import logging
import json
import os

def get_config():
    # Get project root (FaceAttendanceSystem_Web directory)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(project_root, 'config', 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

db_connection = get_config()["db_connection"]

class Database:
    def __init__(
        self,
        host=db_connection["host"],
        user=db_connection["user"],
        passwd=db_connection["passwd"],
        database=db_connection["db"],
        wait_timeout=28800,
        interactive_timeout=28800,
    ):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.database = database
        self.wait_timeout = wait_timeout
        self.interactive_timeout = interactive_timeout
        self.conn = None
        self.connect()

    def connect(self):
        try:
            if not self.conn or not self.conn.is_connected():
                self.conn = mysql.connector.connect(
                    host=self.host, 
                    user=self.user, 
                    passwd=self.passwd, 
                    database=self.database
                )
                logging.info("Database connection established.")
                self.execute_query("SET time_zone = '+05:30';")
                self.set_session_timeouts()
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            print(e)

    def set_session_timeouts(self):
        """Set session-specific timeout values for the MySQL connection."""
        query = "SET SESSION wait_timeout = %s, SESSION interactive_timeout = %s"
        params = (self.wait_timeout, self.interactive_timeout)
        self.execute_query(query, params)

    def fetch_data(self, query, params=()):
        """Fetch data from the database using a SELECT query."""
        try:
            if not self.conn or not self.conn.is_connected():
                self.connect()
            with self.conn.cursor() as cursor:
                cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;")
                cursor.execute(query, params)
                result = cursor.fetchall()
            return result
        except Exception as e:
            logging.error(f"Fetch data error: {e}")
            return []

    def execute_query(self, query, params=()):
        """Execute a given SQL query (INSERT, UPDATE, DELETE) and return True if successful."""
        if self.conn and self.conn.is_connected():
            try:
                with self.conn.cursor() as cursor:
                    cursor.execute(query, params)
                self.conn.commit()
                return True
            except Exception as e:
                logging.error(f"Execute query error: {e}")
                if self.conn and self.conn.is_connected():
                    self.conn.rollback()
                return False
        self.connect()
        return False
        
    def close(self):
        """Close the database connection."""
        if self.conn and self.conn.is_connected():
            self.conn.close()
            logging.info("Database connection closed.")

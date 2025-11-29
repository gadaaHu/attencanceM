import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime, date
import logging

class MySQLDatabase:
    def __init__(self, host='localhost', user='root', password='', database='attendance_system'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.logger = logging.getLogger(__name__)
        self.connect()

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            if self.connection.is_connected():
                self.logger.info("Successfully connected to MySQL database")
                return True
        except Error as e:
            self.logger.error(f"Error connecting to MySQL: {e}")
            return False

    def execute_query(self, query, params=None, fetch=False):
        """Execute SQL query with optional parameters"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                self.connection.commit()
                cursor.close()
                return True
                
        except Error as e:
            self.logger.error(f"Query execution error: {e}")
            self.connection.rollback()
            return False

    def execute_many(self, query, data):
        """Execute multiple insert/update operations"""
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, data)
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            self.logger.error(f"Bulk operation error: {e}")
            self.connection.rollback()
            return False

    def insert_attendance(self, user_id, user_name, clock_in=None, clock_out=None, status='present', confidence=0.0):
        """Insert or update attendance record"""
        clock_in = clock_in or datetime.now()
        
        # Check if attendance already exists for today
        check_query = """
        SELECT id, clock_in, clock_out FROM attendance 
        WHERE user_id = %s AND DATE(clock_in) = %s
        """
        existing = self.execute_query(check_query, (user_id, date.today()), fetch=True)
        
        if existing:
            record = existing[0]
            if not record['clock_out'] and clock_out:
                # Update clock_out time
                update_query = """
                UPDATE attendance SET clock_out = %s, status = %s 
                WHERE id = %s
                """
                return self.execute_query(update_query, (clock_out, status, record['id']))
            return True  # Record already exists
        else:
            # Insert new attendance record
            insert_query = """
            INSERT INTO attendance (user_id, user_name, clock_in, clock_out, status, confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            return self.execute_query(insert_query, 
                                   (user_id, user_name, clock_in, clock_out, status, confidence))

    def get_user_attendance(self, user_id, start_date=None, end_date=None):
        """Get attendance records for a specific user"""
        query = """
        SELECT * FROM attendance 
        WHERE user_id = %s
        """
        params = [user_id]
        
        if start_date and end_date:
            query += " AND DATE(clock_in) BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        
        query += " ORDER BY clock_in DESC"
        return self.execute_query(query, params, fetch=True)

    def get_all_attendance(self, start_date=None, end_date=None):
        """Get all attendance records with optional date filter"""
        query = "SELECT * FROM attendance WHERE 1=1"
        params = []
        
        if start_date and end_date:
            query += " AND DATE(clock_in) BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        
        query += " ORDER BY clock_in DESC"
        return self.execute_query(query, params, fetch=True)

    def get_today_attendance(self):
        """Get today's attendance records"""
        query = """
        SELECT * FROM attendance 
        WHERE DATE(clock_in) = %s 
        ORDER BY clock_in DESC
        """
        return self.execute_query(query, (date.today(),), fetch=True)

    def get_user_stats(self, user_id, month=None, year=None):
        """Get user attendance statistics"""
        current_month = month or datetime.now().month
        current_year = year or datetime.now().year
        
        query = """
        SELECT 
            COUNT(*) as total_days,
            SUM(TIMESTAMPDIFF(MINUTE, clock_in, clock_out)) as total_minutes,
            AVG(TIMESTAMPDIFF(MINUTE, clock_in, clock_out)) as avg_minutes
        FROM attendance 
        WHERE user_id = %s 
        AND MONTH(clock_in) = %s 
        AND YEAR(clock_in) = %s
        AND clock_out IS NOT NULL
        """
        return self.execute_query(query, (user_id, current_month, current_year), fetch=True)

    def register_user(self, user_id, user_name, email=None, department=None):
        """Register a new user in the system"""
        query = """
        INSERT INTO users (user_id, user_name, email, department, registered_at)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        user_name = VALUES(user_name), 
        email = VALUES(email), 
        department = VALUES(department)
        """
        return self.execute_query(query, (user_id, user_name, email, department, datetime.now()))

    def get_user_by_id(self, user_id):
        """Get user information by ID"""
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None

    def get_all_users(self):
        """Get all registered users"""
        query = "SELECT * FROM users ORDER BY user_name"
        return self.execute_query(query, fetch=True)

    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("MySQL connection closed")

    def __del__(self):
        self.close()
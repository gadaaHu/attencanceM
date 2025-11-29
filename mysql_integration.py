import os
import sys
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module.mysql_database import MySQLDatabase
from module.mysql_schema import MySQLSchema

class AttendanceMySQL:
    def __init__(self):
        self.db = MySQLDatabase()
        self.schema = MySQLSchema(self.db)
        
        # Initialize database
        self.initialize_database()

    def initialize_database(self):
        """Initialize database tables and sample data"""
        if self.db.connect():
            if self.schema.create_tables():
                print("MySQL tables created successfully")
                self.schema.initialize_sample_data()
                print("Sample data initialized")
            else:
                print("Error creating tables")
        else:
            print("Failed to connect to MySQL database")

    def log_attendance(self, user_id, user_name, confidence=0.0):
        """Log attendance for face recognition system"""
        return self.db.insert_attendance(user_id, user_name, confidence=confidence)

    def clock_out_user(self, user_id):
        """Clock out a specific user"""
        today = datetime.now().date()
        
        # Find today's attendance record
        query = """
        SELECT id FROM attendance 
        WHERE user_id = %s AND DATE(clock_in) = %s AND clock_out IS NULL
        """
        result = self.db.execute_query(query, (user_id, today), fetch=True)
        
        if result:
            record_id = result[0]['id']
            update_query = "UPDATE attendance SET clock_out = %s WHERE id = %s"
            return self.db.execute_query(update_query, (datetime.now(), record_id))
        
        return False

    def get_daily_report(self, target_date=None):
        """Generate daily attendance report"""
        target_date = target_date or datetime.now().date()
        
        query = """
        SELECT 
            u.user_id,
            u.user_name,
            u.department,
            a.clock_in,
            a.clock_out,
            TIMESTAMPDIFF(MINUTE, a.clock_in, a.clock_out) as minutes_worked,
            a.status,
            a.confidence
        FROM users u
        LEFT JOIN attendance a ON u.user_id = a.user_id AND DATE(a.clock_in) = %s
        ORDER BY u.department, u.user_name
        """
        
        return self.db.execute_query(query, (target_date,), fetch=True)

    def get_monthly_report(self, year=None, month=None):
        """Generate monthly attendance report"""
        current_date = datetime.now()
        year = year or current_date.year
        month = month or current_date.month
        
        query = """
        SELECT 
            u.user_id,
            u.user_name,
            u.department,
            COUNT(a.id) as days_present,
            AVG(TIMESTAMPDIFF(MINUTE, a.clock_in, a.clock_out)) as avg_minutes_per_day,
            SUM(TIMESTAMPDIFF(MINUTE, a.clock_in, a.clock_out)) as total_minutes
        FROM users u
        LEFT JOIN attendance a ON u.user_id = a.user_id 
            AND YEAR(a.clock_in) = %s 
            AND MONTH(a.clock_in) = %s
            AND a.clock_out IS NOT NULL
        GROUP BY u.user_id, u.user_name, u.department
        ORDER BY u.department, u.user_name
        """
        
        return self.db.execute_query(query, (year, month), fetch=True)

    def export_to_csv(self, start_date, end_date, filename=None):
        """Export attendance data to CSV"""
        query = """
        SELECT 
            u.user_id,
            u.user_name,
            u.department,
            a.clock_in,
            a.clock_out,
            TIMESTAMPDIFF(MINUTE, a.clock_in, a.clock_out) as minutes_worked,
            a.status,
            a.confidence
        FROM attendance a
        JOIN users u ON a.user_id = u.user_id
        WHERE DATE(a.clock_in) BETWEEN %s AND %s
        ORDER BY a.clock_in DESC
        """
        
        data = self.db.execute_query(query, (start_date, end_date), fetch=True)
        
        if data:
            df = pd.DataFrame(data)
            filename = filename or f"attendance_export_{start_date}_to_{end_date}.csv"
            df.to_csv(filename, index=False)
            return filename
        
        return None

    def backup_database(self):
        """Create a database backup"""
        try:
            backup_file = f"attendance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            os.system(f"mysqldump -u {self.db.user} -p{self.db.password} {self.db.database} > {backup_file}")
            return backup_file
        except Exception as e:
            print(f"Backup failed: {e}")
            return None
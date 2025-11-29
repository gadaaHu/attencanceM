class MySQLSchema:
    def __init__(self, database):
        self.db = database

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        
        # Users table
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(100) UNIQUE NOT NULL,
            user_name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            department VARCHAR(100),
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_user_name (user_name)
        )
        """

        # Attendance table
        attendance_table = """
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            user_name VARCHAR(255) NOT NULL,
            clock_in TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            clock_out TIMESTAMP NULL,
            status ENUM('present', 'absent', 'late', 'half_day') DEFAULT 'present',
            confidence FLOAT DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            INDEX idx_user_date (user_id, DATE(clock_in)),
            INDEX idx_clock_in (clock_in),
            INDEX idx_clock_out (clock_out)
        )
        """

        # Attendance summary table for reporting
        summary_table = """
        CREATE TABLE IF NOT EXISTS attendance_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            summary_date DATE NOT NULL,
            total_hours DECIMAL(5,2) DEFAULT 0,
            status ENUM('present', 'absent', 'late') DEFAULT 'present',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_summary (user_id, summary_date),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """

        tables = [users_table, attendance_table, summary_table]
        
        for table_sql in tables:
            if not self.db.execute_query(table_sql):
                return False
                
        return True

    def initialize_sample_data(self):
        """Initialize with sample data for testing"""
        
        # Sample users
        sample_users = [
            ('EMP001', 'John Doe', 'john.doe@company.com', 'IT'),
            ('EMP002', 'Jane Smith', 'jane.smith@company.com', 'HR'),
            ('EMP003', 'Mike Johnson', 'mike.johnson@company.com', 'Finance'),
            ('EMP004', 'Sarah Wilson', 'sarah.wilson@company.com', 'Marketing'),
            ('EMP005', 'David Brown', 'david.brown@company.com', 'Operations')
        ]

        insert_user = """
        INSERT IGNORE INTO users (user_id, user_name, email, department) 
        VALUES (%s, %s, %s, %s)
        """

        return self.db.execute_many(insert_user, sample_users)
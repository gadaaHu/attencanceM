import mysql.connector
from mysql.connector import Error
import config
from datetime import date

def get_db_connection():
    """Create and return a MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=config.Config.DB_HOST,
            database=config.Config.DB_NAME,
            user=config.Config.DB_USER,
            password=config.Config.DB_PASSWORD,
            port=config.Config.DB_PORT
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    """Initialize MySQL database tables"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to MySQL database")
        return
    
    cursor = conn.cursor()
    
    try:
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS membership_system")
        cursor.execute("USE membership_system")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                fullname VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fullname VARCHAR(255) NOT NULL,
                membership_number VARCHAR(100) UNIQUE,
                email VARCHAR(255),
                phone VARCHAR(50),
                address TEXT,
                date_of_birth DATE,
                emergency_contact TEXT,
                membership_type VARCHAR(50),
                status VARCHAR(20) DEFAULT 'pending',
                join_date DATE,
                profile_image VARCHAR(500),
                face_encoding_path TEXT,
                approved_by INT,
                approved_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        """)
        
        # Create events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                event_date DATE NOT NULL,
                start_time TIME,
                end_time TIME,
                location VARCHAR(500),
                description TEXT,
                event_type VARCHAR(100),
                created_by INT,
                status VARCHAR(20) DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # Create attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                member_id INT,
                event_id INT,
                status VARCHAR(50) NOT NULL DEFAULT 'present',
                recognized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence DECIMAL(5,4),
                marked_by INT,
                UNIQUE(member_id, event_id),
                FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                FOREIGN KEY (marked_by) REFERENCES users(id)
            )
        """)
        
        # Create annual_plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS annual_plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                plan_type VARCHAR(50),
                year INT,
                file_path VARCHAR(500) NOT NULL,
                analysis_data JSON,
                uploaded_by INT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                analyzed_at TIMESTAMP NULL,
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        """)
        
        # Create member_activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS member_activities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                member_id INT,
                activity_type VARCHAR(100),
                description TEXT,
                points_earned INT DEFAULT 0,
                activity_date DATE DEFAULT (CURRENT_DATE),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
            )
        """)
        
        # Insert default users
        cursor.execute("""
            INSERT IGNORE INTO users (username, password, fullname, role, email) 
            VALUES 
            ('admin', 'admin123', 'System Administrator', 'admin', 'admin@system.com'),
            ('manager', 'manager123', 'Event Manager', 'manager', 'manager@system.com'),
            ('user', 'user123', 'Regular User', 'user', 'user@system.com')
        """)
        
        # Insert sample members if table is empty
        cursor.execute("SELECT COUNT(*) FROM members")
        if cursor.fetchone()[0] == 0:
            sample_members = [
                ('John Doe', 'john@example.com', '123-456-7890', '123 Main St', '1990-01-15', 'Jane Doe - 123-456-7891', 'premium', 'active', date.today()),
                ('Jane Smith', 'jane@example.com', '123-456-7892', '456 Oak Ave', '1985-05-20', 'John Smith - 123-456-7893', 'standard', 'active', date.today()),
                ('Bob Johnson', 'bob@example.com', '123-456-7894', '789 Pine Rd', '1992-11-30', 'Alice Johnson - 123-456-7895', 'basic', 'pending', date.today()),
            ]
            
            for member in sample_members:
                cursor.execute("""
                    INSERT INTO members (fullname, email, phone, address, date_of_birth, emergency_contact, membership_type, status, join_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, member)
        
        conn.commit()
        print("✅ MySQL database initialized successfully!")
        
    except Error as e:
        print(f"Error initializing MySQL database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def test_connection():
    """Test MySQL connection"""
    conn = get_db_connection()
    if conn:
        print("✅ MySQL connection successful!")
        conn.close()
        return True
    else:
        print("❌ MySQL connection failed!")
        return False

if __name__ == "__main__":
    if test_connection():
        init_db()
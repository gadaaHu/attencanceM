import mysql.connector
from mysql.connector import Error
import os
import time

class DatabaseSetup:
    def __init__(self, host='localhost', user='root', password=''):
        self.host = host
        self.user = user
        self.password = password
        self.database = 'membership_system'
        
    def execute_sql_file(self, cursor, filename):
        """Execute SQL commands from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                sql_commands = file.read().split(';')
                
                for command in sql_commands:
                    command = command.strip()
                    if command and not command.startswith('--'):
                        try:
                            cursor.execute(command)
                            print(f"✅ Executed: {command[:50]}..." if len(command) > 50 else f"✅ Executed: {command}")
                        except Error as e:
                            print(f"❌ Error in command: {e}")
                            # Continue with next command
            return True
        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
            return False
    
    def setup_database(self):
        """Main method to set up the entire database"""
        try:
            # Connect to MySQL server (without database)
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()
            
            print("🚀 Starting database setup...")
            
            # Create database and tables
            print("\n📦 Creating database and tables...")
            self.execute_sql_file(cursor, 'database/schema.sql')
            
            # Insert sample data
            print("\n📊 Inserting sample data...")
            self.execute_sql_file(cursor, 'database/sample_data.sql')
            
            conn.commit()
            print("\n🎉 Database setup completed successfully!")
            
            # Display summary
            cursor.execute("USE membership_system")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"\n📋 Created {len(tables)} tables:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"   - {table[0]}: {count} records")
            
        except Error as e:
            print(f"❌ Database connection failed: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
                print("\n🔒 Database connection closed.")

def main():
    print("=" * 50)
    print("      MEMBERSHIP SYSTEM DATABASE SETUP")
    print("=" * 50)
    
    # Get database credentials
    host = input("Enter MySQL host [localhost]: ") or "localhost"
    user = input("Enter MySQL username [root]: ") or "root"
    password = input("Enter MySQL password: ")
    
    # Create setup instance
    db_setup = DatabaseSetup(host, user, password)
    
    # Run setup
    db_setup.setup_database()
    
    print("\n✅ Setup complete! You can now run the application.")
    print("💡 Run: python run.py")

if __name__ == "__main__":
    main()
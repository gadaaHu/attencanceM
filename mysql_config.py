import os
from dotenv import load_dotenv

load_dotenv()

class MySQLConfig:
    HOST = os.getenv('MYSQL_HOST', 'localhost')
    USER = os.getenv('MYSQL_USER', 'root')
    PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    DATABASE = os.getenv('MYSQL_DATABASE', 'attendance_system')
    PORT = os.getenv('MYSQL_PORT', 3306)
    
    @classmethod
    def get_connection_string(cls):
        return {
            'host': cls.HOST,
            'user': cls.USER,
            'password': cls.PASSWORD,
            'database': cls.DATABASE,
            'port': cls.PORT
        }
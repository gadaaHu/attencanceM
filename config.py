import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'membership-system-secret-key-2024'
    
    # MySQL configuration (XAMPP)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'membership_system')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    
    # File upload settings
    MAX_FILE_SIZE = 16 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xlsx', 'xls'}
    
    # Face recognition
    FACE_RECOGNITION_TOLERANCE = 0.6
    FACE_DETECTION_MODEL = 'hog'
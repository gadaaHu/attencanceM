import sys
import os

# Add your project directory to the Python path
project_dir = r'C:\xampp\htdocs\attendance'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Set environment variables
os.environ['PYTHONPATH'] = project_dir

from app import app as application

if __name__ == "__main__":
    application.run()
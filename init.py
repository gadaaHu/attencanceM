from flask import Flask
import os

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Ensure upload directories exist
    os.makedirs('uploads/profiles', exist_ok=True)
    os.makedirs('uploads/face_encodings', exist_ok=True)
    os.makedirs('uploads/plans', exist_ok=True)
    
    # Register blueprints/routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
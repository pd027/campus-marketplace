import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = 'your-secret-key-here'  # Change this in production
    
    # Database configuration
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'  # Change to your MySQL username
    MYSQL_PASSWORD = 'root@123'  # Change to your MySQL password
    MYSQL_DB = 'campus_marketplace'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

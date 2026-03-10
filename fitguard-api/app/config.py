import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    # Fallback to sqlite if MYSQL_URL is not set (for safety, though user provided MySQL creds)
    SQLALCHEMY_DATABASE_URI = os.getenv("MYSQL_URL", "mysql+pymysql://root:Ksksuriya1826@localhost/fitguard")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-dev")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-jwt-secret-key-for-dev")
    
    # Claude API
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

    # File uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.getcwd(), "uploads"))

    # Injury model dataset override
    INJURY_DATASET_PATH = os.getenv("INJURY_DATASET_PATH", os.path.join(os.getcwd(), "..", "datasets", "athelete_injury_dataset.csv"))

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "fitguard.db"

class Config:
    # Database Configuration
    # Prefer Railway-style database URLs, then fall back to a local SQLite file.
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL")
        or os.getenv("MYSQL_URL")
        or f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-dev")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-jwt-secret-key-for-dev")
    
    # Claude API
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

    # File uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))

    # Injury model dataset override
    INJURY_DATASET_PATH = os.getenv(
        "INJURY_DATASET_PATH",
        str(REPO_ROOT / "datasets" / "athelete_injury_dataset.csv"),
    )

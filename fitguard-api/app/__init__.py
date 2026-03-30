import logging
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    # Allow requests from the React frontend (usually port 5173 for Vite)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from app import models
        from app.schema_sync import ensure_schema_compatibility

        db.create_all()
        # Apply lightweight legacy schema patches to avoid runtime crashes on old DBs.
        result = ensure_schema_compatibility()
        if result.get("applied"):
            logger.warning("Applied schema compatibility patches: %s", ", ".join(result["applied"]))
        os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    # Register blueprints 
    from .routes.auth import auth_bp
    from .routes.training import training_bp
    from .routes.athletes import athletes_bp
    from .routes.fatigue import fatigue_bp
    from .routes.prediction import prediction_bp
    from .routes.coach import coach_bp
    from .routes.recovery import recovery_bp
    from .routes.profile import profile_bp
    from .routes.planning import planning_bp
    from .routes.analytics import analytics_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(training_bp, url_prefix="/api/training")
    app.register_blueprint(athletes_bp, url_prefix="/api/athletes")
    app.register_blueprint(fatigue_bp, url_prefix="/api/fatigue")
    app.register_blueprint(prediction_bp, url_prefix="/api/predict")
    app.register_blueprint(coach_bp, url_prefix="/api/coach")
    app.register_blueprint(recovery_bp, url_prefix="/api/recovery")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(planning_bp, url_prefix="/api/planning")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}

    return app

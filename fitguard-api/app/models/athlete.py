from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class Athlete(db.Model):
    __tablename__ = 'athletes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sport = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Float, nullable=False) # kg
    height = db.Column(db.Float, nullable=False) # cm
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    training_logs = db.relationship('TrainingLog', backref='athlete', lazy=True)
    fatigue_scores = db.relationship('FatigueScore', backref='athlete', lazy=True)
    injury_predictions = db.relationship('InjuryPrediction', backref='athlete', lazy=True)
    recovery_history = db.relationship('RecoveryHistory', backref='athlete', lazy=True)
    coach_recommendations = db.relationship('CoachRecommendation', backref='athlete', lazy=True)
    profile = db.relationship('AthleteProfile', backref='athlete', uselist=False, lazy=True)
    hydration_logs = db.relationship('HydrationLog', backref='athlete', lazy=True)
    personal_records = db.relationship('PersonalRecord', backref='athlete', lazy=True)
    sport_setting = db.relationship('SportSetting', backref='athlete', uselist=False, lazy=True)
    goals = db.relationship('AthleteGoal', backref='athlete', lazy=True)
    training_plans = db.relationship('WeeklyTrainingPlan', foreign_keys='WeeklyTrainingPlan.athlete_id', backref='planned_athlete', lazy=True)
    coach_assignments = db.relationship('CoachAssignment', foreign_keys='CoachAssignment.coach_id', backref='coach', lazy=True)
    alert_notifications = db.relationship('AlertNotification', backref='athlete', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'age': self.age,
            'sport': self.sport,
            'weight': self.weight,
            'height': self.height,
            'created_at': self.created_at.isoformat()
        }

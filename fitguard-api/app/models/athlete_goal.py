from datetime import datetime
from app import db


class AthleteGoal(db.Model):
    __tablename__ = "athlete_goals"

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False)
    goal_type = db.Column(db.String(100), nullable=False)
    target_value = db.Column(db.Float, nullable=True)
    target_sessions_per_week = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "goal_type": self.goal_type,
            "target_value": self.target_value,
            "target_sessions_per_week": self.target_sessions_per_week,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


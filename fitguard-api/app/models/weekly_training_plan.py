from datetime import datetime
from app import db


class WeeklyTrainingPlan(db.Model):
    __tablename__ = "weekly_training_plans"

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=True)
    week_start = db.Column(db.Date, nullable=False)
    plan_date = db.Column(db.Date, nullable=False)
    session_name = db.Column(db.String(120), nullable=False, default="Training")
    duration_hrs = db.Column(db.Float, nullable=True)
    intensity_target = db.Column(db.Float, nullable=True)
    distance_target_km = db.Column(db.Float, nullable=True)
    is_rest_day = db.Column(db.Boolean, nullable=False, default=False)
    source = db.Column(db.String(30), nullable=False, default="rule")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("athlete_id", "plan_date", "session_name", name="uq_plan_session"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "coach_id": self.coach_id,
            "week_start": self.week_start.isoformat(),
            "plan_date": self.plan_date.isoformat(),
            "session_name": self.session_name,
            "duration_hrs": self.duration_hrs,
            "intensity_target": self.intensity_target,
            "distance_target_km": self.distance_target_km,
            "is_rest_day": self.is_rest_day,
            "source": self.source,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


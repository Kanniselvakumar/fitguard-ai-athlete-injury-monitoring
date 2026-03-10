from datetime import datetime
from app import db


class CoachAssignment(db.Model):
    __tablename__ = "coach_assignments"

    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False)
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("coach_id", "athlete_id", name="uq_coach_athlete"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "coach_id": self.coach_id,
            "athlete_id": self.athlete_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


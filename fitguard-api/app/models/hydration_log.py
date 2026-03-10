from datetime import datetime
from app import db


class HydrationLog(db.Model):
    __tablename__ = "hydration_logs"

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False)
    log_date = db.Column(db.Date, nullable=False)
    liters = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "log_date": self.log_date.isoformat(),
            "liters": self.liters,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


from datetime import datetime
from app import db


class PersonalRecord(db.Model):
    __tablename__ = "personal_records"

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(30), nullable=True)
    achieved_on = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "unit": self.unit,
            "achieved_on": self.achieved_on.isoformat(),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


from datetime import datetime
from app import db


class AlertNotification(db.Model):
    __tablename__ = "alert_notifications"

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False)
    alert_type = db.Column(db.String(60), nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="info")
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


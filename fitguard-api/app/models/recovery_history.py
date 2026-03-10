from datetime import datetime
from app import db

class RecoveryHistory(db.Model):
    __tablename__ = 'recovery_history'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    sleep_hrs = db.Column(db.Float, nullable=False)
    rest_days = db.Column(db.Integer, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'athlete_id': self.athlete_id,
            'sleep_hrs': self.sleep_hrs,
            'rest_days': self.rest_days,
            'recorded_at': self.recorded_at.isoformat()
        }

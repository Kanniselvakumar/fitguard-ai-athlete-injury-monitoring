from datetime import datetime
from app import db

class TrainingLog(db.Model):
    __tablename__ = 'training_logs'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration_hrs = db.Column(db.Float, nullable=False)
    intensity = db.Column(db.Float, nullable=False) # 1-10 string
    distance_km = db.Column(db.Float, nullable=True) # Optional depending on sport
    heart_rate = db.Column(db.Integer, nullable=True) # Average HR
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'athlete_id': self.athlete_id,
            'date': self.date.isoformat(),
            'duration_hrs': self.duration_hrs,
            'intensity': self.intensity,
            'distance_km': self.distance_km,
            'heart_rate': self.heart_rate,
            'created_at': self.created_at.isoformat()
        }

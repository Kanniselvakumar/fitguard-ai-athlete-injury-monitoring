from datetime import datetime
from app import db

class FatigueScore(db.Model):
    __tablename__ = 'fatigue_scores'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    log_id = db.Column(db.Integer, db.ForeignKey('training_logs.id'), nullable=True) # Can be tied to a specific log or daily summary
    score = db.Column(db.Float, nullable=False)
    level = db.Column(db.Integer, nullable=False) # 0 = Low, 1 = Medium, 2 = High
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'athlete_id': self.athlete_id,
            'log_id': self.log_id,
            'score': self.score,
            'level': self.level,
            'calculated_at': self.calculated_at.isoformat()
        }

from datetime import datetime
from app import db

class CoachRecommendation(db.Model):
    __tablename__ = 'coach_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    prediction_id = db.Column(db.Integer, db.ForeignKey('injury_predictions.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'athlete_id': self.athlete_id,
            'prediction_id': self.prediction_id,
            'message': self.message,
            'created_at': self.created_at.isoformat()
        }

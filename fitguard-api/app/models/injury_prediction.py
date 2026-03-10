from datetime import datetime
from app import db

class InjuryPrediction(db.Model):
    __tablename__ = 'injury_predictions'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.id'), nullable=False)
    risk_score = db.Column(db.Float, nullable=False) # E.g., probability %
    risk_level = db.Column(db.String(20), nullable=False) # e.g., 'Low', 'Medium', 'High'
    algorithm_used = db.Column(db.String(50), default='Random Forest')
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to recommendation if needed
    recommendation = db.relationship('CoachRecommendation', uselist=False, backref='prediction')
    insight = db.relationship('PredictionInsight', uselist=False, backref='prediction')

    def to_dict(self):
        insight = self.insight.to_dict() if self.insight else None
        return {
            'id': self.id,
            'athlete_id': self.athlete_id,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'algorithm_used': self.algorithm_used,
            'predicted_at': self.predicted_at.isoformat(),
            'insight': insight
        }

from datetime import datetime
from app import db


class PredictionInsight(db.Model):
    __tablename__ = "prediction_insights"

    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("injury_predictions.id"), nullable=False, unique=True)
    confidence_lower = db.Column(db.Float, nullable=False)
    confidence_upper = db.Column(db.Float, nullable=False)
    probability = db.Column(db.Float, nullable=False)
    feature_importance = db.Column(db.Text, nullable=False)
    model_version = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "prediction_id": self.prediction_id,
            "confidence_lower": self.confidence_lower,
            "confidence_upper": self.confidence_upper,
            "probability": self.probability,
            "feature_importance": self.feature_importance,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


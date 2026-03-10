from datetime import datetime
from app import db


class ModelTrainingRun(db.Model):
    __tablename__ = "model_training_runs"

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(80), nullable=False, default="injury_random_forest")
    model_version = db.Column(db.String(40), nullable=False)
    precision = db.Column(db.Float, nullable=False)
    recall = db.Column(db.Float, nullable=False)
    f1_score = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    training_rows = db.Column(db.Integer, nullable=False)
    feature_importance = db.Column(db.Text, nullable=False)
    trained_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "accuracy": self.accuracy,
            "training_rows": self.training_rows,
            "feature_importance": self.feature_importance,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
        }


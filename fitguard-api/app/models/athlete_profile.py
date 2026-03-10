from datetime import datetime
from app import db


class AthleteProfile(db.Model):
    __tablename__ = "athlete_profiles"

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False, unique=True)
    account_type = db.Column(db.String(20), nullable=False, default="athlete")
    injury_history = db.Column(db.Text, nullable=True)
    previous_injuries_count = db.Column(db.Integer, nullable=False, default=0)
    avatar_path = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "account_type": self.account_type,
            "injury_history": self.injury_history,
            "previous_injuries_count": self.previous_injuries_count,
            "avatar_path": self.avatar_path,
            "bio": self.bio,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

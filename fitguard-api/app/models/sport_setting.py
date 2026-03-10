from datetime import datetime
from app import db


class SportSetting(db.Model):
    __tablename__ = "sport_settings"

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey("athletes.id"), nullable=False, unique=True)
    sport = db.Column(db.String(50), nullable=False, default="General Fitness")
    intensity_low_threshold = db.Column(db.Float, nullable=False, default=4.0)
    intensity_high_threshold = db.Column(db.Float, nullable=False, default=7.5)
    hr_zone_easy_max = db.Column(db.Integer, nullable=False, default=130)
    hr_zone_moderate_max = db.Column(db.Integer, nullable=False, default=160)
    hr_zone_hard_max = db.Column(db.Integer, nullable=False, default=185)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "athlete_id": self.athlete_id,
            "sport": self.sport,
            "intensity_low_threshold": self.intensity_low_threshold,
            "intensity_high_threshold": self.intensity_high_threshold,
            "hr_zone_easy_max": self.hr_zone_easy_max,
            "hr_zone_moderate_max": self.hr_zone_moderate_max,
            "hr_zone_hard_max": self.hr_zone_hard_max,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


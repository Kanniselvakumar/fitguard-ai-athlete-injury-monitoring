from datetime import date, datetime, timedelta

from app import db
from app.models.alert_notification import AlertNotification
from app.models.fatigue_score import FatigueScore
from app.models.injury_prediction import InjuryPrediction
from app.models.training_log import TrainingLog


def _create_alert_if_needed(athlete_id: int, alert_type: str, severity: str, message: str) -> AlertNotification | None:
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    existing = (
        AlertNotification.query.filter_by(athlete_id=athlete_id, alert_type=alert_type)
        .filter(AlertNotification.created_at >= recent_cutoff)
        .first()
    )
    if existing:
        return None

    alert = AlertNotification(
        athlete_id=athlete_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
    )
    db.session.add(alert)
    return alert


def _overtraining_high_risk_streak(athlete_id: int) -> int:
    predictions = (
        InjuryPrediction.query.filter_by(athlete_id=athlete_id)
        .order_by(InjuryPrediction.predicted_at.desc())
        .limit(7)
        .all()
    )
    seen_dates = set()
    streak = 0
    for pred in predictions:
        pred_day = pred.predicted_at.date()
        if pred_day in seen_dates:
            continue
        seen_dates.add(pred_day)
        if pred.risk_level == "High":
            streak += 1
        else:
            break
    return streak


def generate_alerts(athlete_id: int):
    created = []

    latest_prediction = (
        InjuryPrediction.query.filter_by(athlete_id=athlete_id)
        .order_by(InjuryPrediction.predicted_at.desc())
        .first()
    )
    if latest_prediction and latest_prediction.risk_level == "High":
        alert = _create_alert_if_needed(
            athlete_id,
            "high_risk_banner",
            "high",
            f"Injury risk is High ({round(latest_prediction.risk_score, 1)}%). Reduce load and prioritize recovery.",
        )
        if alert:
            created.append(alert)

    latest_log = (
        TrainingLog.query.filter_by(athlete_id=athlete_id)
        .order_by(TrainingLog.date.desc())
        .first()
    )
    if not latest_log or (date.today() - latest_log.date).days >= 3:
        alert = _create_alert_if_needed(
            athlete_id,
            "missing_training_reminder",
            "medium",
            "You haven't logged training in 3+ days. Add your latest session to keep risk predictions accurate.",
        )
        if alert:
            created.append(alert)

    latest_fatigue = (
        FatigueScore.query.filter_by(athlete_id=athlete_id)
        .order_by(FatigueScore.calculated_at.desc())
        .first()
    )
    if latest_fatigue and latest_fatigue.level == 2:
        alert = _create_alert_if_needed(
            athlete_id,
            "pre_session_fatigue_warning",
            "high",
            "Fatigue is High before session start. Consider active recovery or reducing intensity.",
        )
        if alert:
            created.append(alert)

    streak = _overtraining_high_risk_streak(athlete_id)
    if streak >= 3:
        alert = _create_alert_if_needed(
            athlete_id,
            "overtraining_alert",
            "high",
            f"Overtraining risk flagged: High injury risk persisted for {streak} consecutive logged days.",
        )
        if alert:
            created.append(alert)

    if created:
        db.session.commit()

    return [item.to_dict() for item in created]

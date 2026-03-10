from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.ml.fatigue_engine import calculate_fatigue
from app.models.fatigue_score import FatigueScore
from app.models.recovery_history import RecoveryHistory
from app.models.training_log import TrainingLog
from app.services.alert_service import generate_alerts


fatigue_bp = Blueprint("fatigue", __name__)


def _latest_recovery_inputs(athlete_id: int) -> tuple[float, int]:
    recovery = (
        RecoveryHistory.query.filter_by(athlete_id=athlete_id)
        .order_by(RecoveryHistory.recorded_at.desc())
        .first()
    )
    if not recovery:
        return 7.0, 0
    return float(recovery.sleep_hrs), int(recovery.rest_days)


@fatigue_bp.route("/calculate", methods=["POST"])
@jwt_required()
def calculate():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    log_id = data.get("log_id")
    if log_id:
        log = TrainingLog.query.get(log_id)
        if not log or log.athlete_id != current_user_id:
            return jsonify({"message": "Log not found or unauthorized"}), 404
        duration_hrs = float(log.duration_hrs)
        intensity = float(log.intensity)
        heart_rate = float(log.heart_rate) if log.heart_rate else 0.0
    else:
        duration_hrs = float(data.get("duration_hrs", 1.0))
        intensity = float(data.get("intensity", 5.0))
        heart_rate = float(data.get("heart_rate", 140))

    sleep_hrs, rest_days = _latest_recovery_inputs(current_user_id)
    score, level = calculate_fatigue(duration_hrs * (intensity / 5.0), heart_rate, sleep_hrs, rest_days)

    fatigue_entry = FatigueScore(
        athlete_id=current_user_id,
        log_id=log_id,
        score=score,
        level=level,
    )
    db.session.add(fatigue_entry)
    db.session.commit()

    generate_alerts(current_user_id)

    return jsonify({"message": "Fatigue calculated successfully", "fatigue_score": fatigue_entry.to_dict()}), 201


@fatigue_bp.route("/latest/<int:athlete_id>", methods=["GET"])
@jwt_required()
def latest(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    latest_score = (
        FatigueScore.query.filter_by(athlete_id=athlete_id)
        .order_by(FatigueScore.calculated_at.desc())
        .first()
    )
    return jsonify({"fatigue_score": latest_score.to_dict() if latest_score else None}), 200


@fatigue_bp.route("/history/<int:athlete_id>", methods=["GET"])
@jwt_required()
def history(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    rows = (
        FatigueScore.query.filter_by(athlete_id=athlete_id)
        .order_by(FatigueScore.calculated_at.desc())
        .all()
    )
    return jsonify([row.to_dict() for row in rows]), 200


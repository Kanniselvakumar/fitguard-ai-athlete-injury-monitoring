from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.hydration_log import HydrationLog
from app.models.recovery_history import RecoveryHistory
from app.models.training_log import TrainingLog
from app.services.alert_service import generate_alerts
from app.services.analytics_service import build_recovery_trend, build_rest_day_tracker


recovery_bp = Blueprint("recovery", __name__)


@recovery_bp.route("/log", methods=["POST"])
@jwt_required()
def log_recovery():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    sleep_hrs = float(data.get("sleep_hrs", 0))
    rest_days = int(data.get("rest_days", 0))
    if sleep_hrs <= 0:
        return jsonify({"message": "sleep_hrs must be greater than 0"}), 400

    recorded_at = datetime.utcnow()
    date_text = data.get("date")
    if date_text:
        try:
            recorded_at = datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

    row = RecoveryHistory(
        athlete_id=current_user_id,
        sleep_hrs=sleep_hrs,
        rest_days=rest_days,
        recorded_at=recorded_at,
    )
    db.session.add(row)
    db.session.commit()

    generate_alerts(current_user_id)
    return jsonify({"message": "Recovery data logged", "recovery": row.to_dict()}), 201


@recovery_bp.route("/history/<int:athlete_id>", methods=["GET"])
@jwt_required()
def get_recovery_history(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    rows = (
        RecoveryHistory.query.filter_by(athlete_id=athlete_id)
        .order_by(RecoveryHistory.recorded_at.desc())
        .all()
    )
    return jsonify([row.to_dict() for row in rows]), 200


@recovery_bp.route("/hydration/log", methods=["POST"])
@jwt_required()
def log_hydration():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    liters = float(data.get("liters", 0))
    if liters <= 0:
        return jsonify({"message": "liters must be greater than 0"}), 400

    log_date = datetime.utcnow().date()
    date_text = data.get("date")
    if date_text:
        try:
            log_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

    existing = HydrationLog.query.filter_by(athlete_id=current_user_id, log_date=log_date).first()
    if existing:
        existing.liters = liters
        db.session.commit()
        return jsonify({"message": "Hydration updated", "hydration": existing.to_dict()}), 200

    row = HydrationLog(athlete_id=current_user_id, log_date=log_date, liters=liters)
    db.session.add(row)
    db.session.commit()
    return jsonify({"message": "Hydration logged", "hydration": row.to_dict()}), 201


@recovery_bp.route("/hydration/history/<int:athlete_id>", methods=["GET"])
@jwt_required()
def hydration_history(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    rows = HydrationLog.query.filter_by(athlete_id=athlete_id).order_by(HydrationLog.log_date.desc()).all()
    return jsonify([row.to_dict() for row in rows]), 200


@recovery_bp.route("/score-trend/<int:athlete_id>", methods=["GET"])
@jwt_required()
def recovery_score_trend(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403
    return jsonify({"trend": build_recovery_trend(athlete_id)}), 200


@recovery_bp.route("/rest-days/<int:athlete_id>", methods=["GET"])
@jwt_required()
def rest_days(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    logs = TrainingLog.query.filter_by(athlete_id=athlete_id).order_by(TrainingLog.date.asc()).all()
    return jsonify(build_rest_day_tracker(logs, days=14)), 200


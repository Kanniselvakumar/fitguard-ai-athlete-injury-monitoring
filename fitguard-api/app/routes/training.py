from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.training_log import TrainingLog
from app.services.alert_service import generate_alerts


training_bp = Blueprint("training", __name__)


@training_bp.route("/log", methods=["POST"])
@jwt_required()
def log_training():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    if not data:
        return jsonify({"message": "No input data provided"}), 400

    date_str = data.get("date")
    try:
        log_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.utcnow().date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

    duration_hrs = float(data.get("duration_hrs", 0))
    intensity = float(data.get("intensity", 0))
    distance_km = data.get("distance_km")
    heart_rate = data.get("heart_rate")

    if duration_hrs <= 0 or intensity <= 0:
        return jsonify({"message": "Duration and intensity must be positive values"}), 400

    log = TrainingLog(
        athlete_id=current_user_id,
        date=log_date,
        duration_hrs=duration_hrs,
        intensity=intensity,
        distance_km=float(distance_km) if distance_km is not None else None,
        heart_rate=int(heart_rate) if heart_rate is not None else None,
    )
    db.session.add(log)
    db.session.commit()

    generate_alerts(current_user_id)
    return jsonify({"message": "Training logged successfully", "log": log.to_dict()}), 201


@training_bp.route("/history/<int:athlete_id>", methods=["GET"])
@jwt_required()
def get_history(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized to view this history"}), 403

    logs = TrainingLog.query.filter_by(athlete_id=athlete_id).order_by(TrainingLog.date.desc()).all()
    return jsonify([log.to_dict() for log in logs]), 200


@training_bp.route("/latest/<int:athlete_id>", methods=["GET"])
@jwt_required()
def get_latest_log(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    log = TrainingLog.query.filter_by(athlete_id=athlete_id).order_by(TrainingLog.date.desc()).first()
    return jsonify({"log": log.to_dict() if log else None}), 200


@training_bp.route("/by-date/<int:athlete_id>/<string:log_date>", methods=["GET"])
@jwt_required()
def get_logs_for_date(athlete_id, log_date):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    try:
        parsed = datetime.strptime(log_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

    logs = TrainingLog.query.filter_by(athlete_id=athlete_id, date=parsed).all()
    return jsonify([log.to_dict() for log in logs]), 200


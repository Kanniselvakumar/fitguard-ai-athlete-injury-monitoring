from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.alert_notification import AlertNotification
from app.services.alert_service import generate_alerts
from app.services.analytics_service import build_dashboard_payload, latest_alerts


analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard/<int:athlete_id>", methods=["GET"])
@jwt_required()
def dashboard(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    generate_alerts(athlete_id)
    payload = build_dashboard_payload(athlete_id)
    payload["alerts"] = latest_alerts(athlete_id, limit=20)
    return jsonify(payload), 200


@analytics_bp.route("/alerts/<int:athlete_id>", methods=["GET"])
@jwt_required()
def get_alerts(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403
    return jsonify({"alerts": latest_alerts(athlete_id, limit=50)}), 200


@analytics_bp.route("/alerts/read/<int:alert_id>", methods=["PUT"])
@jwt_required()
def mark_alert_read(alert_id):
    current_user_id = int(get_jwt_identity())
    alert = AlertNotification.query.get(alert_id)
    if not alert or alert.athlete_id != current_user_id:
        return jsonify({"message": "Alert not found"}), 404
    alert.is_read = True
    db.session.commit()
    return jsonify({"message": "Alert marked as read"}), 200


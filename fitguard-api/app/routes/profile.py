import os
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app import db
from app.models.athlete import Athlete
from app.models.athlete_profile import AthleteProfile
from app.models.personal_record import PersonalRecord
from app.models.sport_setting import SportSetting


profile_bp = Blueprint("profile", __name__)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _get_or_create_profile(athlete_id: int) -> AthleteProfile:
    profile = AthleteProfile.query.filter_by(athlete_id=athlete_id).first()
    if profile:
        return profile
    profile = AthleteProfile(athlete_id=athlete_id)
    db.session.add(profile)
    db.session.flush()
    return profile


def _get_or_create_sport_setting(athlete_id: int, sport_name: str) -> SportSetting:
    setting = SportSetting.query.filter_by(athlete_id=athlete_id).first()
    if setting:
        return setting
    setting = SportSetting(athlete_id=athlete_id, sport=sport_name or "General Fitness")
    db.session.add(setting)
    db.session.flush()
    return setting


@profile_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    current_user_id = int(get_jwt_identity())
    athlete = Athlete.query.get(current_user_id)
    if not athlete:
        return jsonify({"message": "Athlete not found"}), 404

    profile = _get_or_create_profile(current_user_id)
    sport_setting = _get_or_create_sport_setting(current_user_id, athlete.sport)
    db.session.commit()

    records = (
        PersonalRecord.query.filter_by(athlete_id=current_user_id)
        .order_by(PersonalRecord.achieved_on.desc())
        .all()
    )

    payload = athlete.to_dict()
    payload["profile"] = profile.to_dict()
    payload["sport_settings"] = sport_setting.to_dict()
    payload["personal_records"] = [r.to_dict() for r in records]
    return jsonify(payload), 200


@profile_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    current_user_id = int(get_jwt_identity())
    athlete = Athlete.query.get(current_user_id)
    if not athlete:
        return jsonify({"message": "Athlete not found"}), 404

    data = request.get_json() or {}
    profile = _get_or_create_profile(current_user_id)

    editable_athlete_fields = ["name", "age", "sport", "weight", "height"]
    for field in editable_athlete_fields:
        if field in data:
            setattr(athlete, field, data[field])

    if "injury_history" in data:
        profile.injury_history = data.get("injury_history")
    if "previous_injuries_count" in data:
        profile.previous_injuries_count = int(data.get("previous_injuries_count") or 0)
    if "bio" in data:
        profile.bio = data.get("bio")
    if "account_type" in data and data.get("account_type") in {"athlete", "coach"}:
        profile.account_type = data.get("account_type")

    setting = _get_or_create_sport_setting(current_user_id, athlete.sport)
    setting.sport = athlete.sport or setting.sport
    for field in [
        "intensity_low_threshold",
        "intensity_high_threshold",
        "hr_zone_easy_max",
        "hr_zone_moderate_max",
        "hr_zone_hard_max",
    ]:
        if field in data:
            setattr(setting, field, data[field])

    db.session.commit()

    payload = athlete.to_dict()
    payload["profile"] = profile.to_dict()
    payload["sport_settings"] = setting.to_dict()
    return jsonify(payload), 200


@profile_bp.route("/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    current_user_id = int(get_jwt_identity())
    athlete = Athlete.query.get(current_user_id)
    if not athlete:
        return jsonify({"message": "Athlete not found"}), 404

    if "avatar" not in request.files:
        return jsonify({"message": "No avatar file provided"}), 400

    file = request.files["avatar"]
    if not file.filename:
        return jsonify({"message": "Invalid file"}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"message": "Unsupported file type"}), 400

    uploads_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(uploads_dir, exist_ok=True)
    saved_name = f"avatar_{current_user_id}_{uuid4().hex}.{ext}"
    saved_path = os.path.join(uploads_dir, saved_name)
    file.save(saved_path)

    profile = _get_or_create_profile(current_user_id)
    profile.avatar_path = f"/api/profile/avatar/{saved_name}"
    db.session.commit()
    return jsonify({"message": "Avatar uploaded", "avatar_path": profile.avatar_path}), 200


@profile_bp.route("/avatar/<path:filename>", methods=["GET"])
def serve_avatar(filename):
    uploads_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(uploads_dir, filename)


@profile_bp.route("/records", methods=["GET"])
@jwt_required()
def list_records():
    current_user_id = int(get_jwt_identity())
    records = (
        PersonalRecord.query.filter_by(athlete_id=current_user_id)
        .order_by(PersonalRecord.achieved_on.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in records]), 200


@profile_bp.route("/records", methods=["POST"])
@jwt_required()
def create_record():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not data.get("metric_name") or data.get("value") is None:
        return jsonify({"message": "metric_name and value are required"}), 400

    achieved_on = datetime.utcnow().date()
    if data.get("achieved_on"):
        try:
            achieved_on = datetime.strptime(data["achieved_on"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid achieved_on format. Use YYYY-MM-DD"}), 400

    record = PersonalRecord(
        athlete_id=current_user_id,
        metric_name=data["metric_name"],
        value=float(data["value"]),
        unit=data.get("unit"),
        achieved_on=achieved_on,
        notes=data.get("notes"),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


@profile_bp.route("/records/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_record(record_id):
    current_user_id = int(get_jwt_identity())
    record = PersonalRecord.query.get(record_id)
    if not record or record.athlete_id != current_user_id:
        return jsonify({"message": "Record not found"}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Record deleted"}), 200


@profile_bp.route("/sport-settings", methods=["GET"])
@jwt_required()
def get_sport_settings():
    current_user_id = int(get_jwt_identity())
    athlete = Athlete.query.get(current_user_id)
    if not athlete:
        return jsonify({"message": "Athlete not found"}), 404
    settings = _get_or_create_sport_setting(current_user_id, athlete.sport)
    db.session.commit()
    return jsonify(settings.to_dict()), 200


@profile_bp.route("/sport-settings", methods=["PUT"])
@jwt_required()
def update_sport_settings():
    current_user_id = int(get_jwt_identity())
    athlete = Athlete.query.get(current_user_id)
    if not athlete:
        return jsonify({"message": "Athlete not found"}), 404

    data = request.get_json() or {}
    settings = _get_or_create_sport_setting(current_user_id, athlete.sport)
    for field in [
        "sport",
        "intensity_low_threshold",
        "intensity_high_threshold",
        "hr_zone_easy_max",
        "hr_zone_moderate_max",
        "hr_zone_hard_max",
    ]:
        if field in data:
            setattr(settings, field, data[field])

    db.session.commit()
    return jsonify(settings.to_dict()), 200


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.athlete import Athlete
from app.models.athlete_profile import AthleteProfile
from app.models.coach_assignment import CoachAssignment


athletes_bp = Blueprint("athletes", __name__)


def _is_coach(user_id: int) -> bool:
    profile = AthleteProfile.query.filter_by(athlete_id=user_id).first()
    return bool(profile and profile.account_type == "coach")


@athletes_bp.route("", methods=["GET"])
@jwt_required()
def get_athletes():
    current_user_id = int(get_jwt_identity())

    if _is_coach(current_user_id):
        assigned_ids = [row.athlete_id for row in CoachAssignment.query.filter_by(coach_id=current_user_id).all()]
        athletes = Athlete.query.filter(Athlete.id.in_(assigned_ids)).all() if assigned_ids else []
        return jsonify([a.to_dict() for a in athletes]), 200

    athlete = Athlete.query.get(current_user_id)
    return jsonify([athlete.to_dict()] if athlete else []), 200


@athletes_bp.route("/all", methods=["GET"])
@jwt_required()
def get_all_athletes():
    current_user_id = int(get_jwt_identity())
    if not _is_coach(current_user_id):
        return jsonify({"message": "Coach account required"}), 403
    athletes = Athlete.query.filter(Athlete.id != current_user_id).order_by(Athlete.name.asc()).all()
    return jsonify([athlete.to_dict() for athlete in athletes]), 200


@athletes_bp.route("", methods=["POST"])
@jwt_required()
def create_athlete():
    current_user_id = int(get_jwt_identity())
    if not _is_coach(current_user_id):
        return jsonify({"message": "Only coach accounts can create athletes from this endpoint"}), 403

    data = request.get_json() or {}
    if not data.get("email") or not data.get("password") or not data.get("name"):
        return jsonify({"message": "name, email and password are required"}), 400

    if Athlete.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already registered"}), 400

    athlete = Athlete(
        name=data["name"],
        email=data["email"],
        age=int(data.get("age", 25)),
        sport=data.get("sport", "General Fitness"),
        weight=float(data.get("weight", 70)),
        height=float(data.get("height", 175)),
    )
    athlete.set_password(data["password"])
    db.session.add(athlete)
    db.session.flush()

    profile = AthleteProfile(
        athlete_id=athlete.id,
        injury_history=data.get("injury_history"),
        previous_injuries_count=int(data.get("previous_injuries_count", 0) or 0),
    )
    db.session.add(profile)

    assignment = CoachAssignment(coach_id=current_user_id, athlete_id=athlete.id)
    db.session.add(assignment)
    db.session.commit()

    return jsonify(athlete.to_dict()), 201


@athletes_bp.route("/<int:athlete_id>", methods=["GET"])
@jwt_required()
def get_athlete(athlete_id):
    current_user_id = int(get_jwt_identity())
    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({"message": "Not found"}), 404

    if current_user_id != athlete_id:
        if not _is_coach(current_user_id):
            return jsonify({"message": "Unauthorized"}), 403
        assignment = CoachAssignment.query.filter_by(coach_id=current_user_id, athlete_id=athlete_id).first()
        if not assignment:
            return jsonify({"message": "Unauthorized"}), 403

    profile = AthleteProfile.query.filter_by(athlete_id=athlete_id).first()
    payload = athlete.to_dict()
    payload["profile"] = profile.to_dict() if profile else None
    return jsonify(payload), 200

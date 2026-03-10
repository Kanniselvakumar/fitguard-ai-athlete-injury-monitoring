from datetime import date, datetime, timedelta

from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.athlete import Athlete
from app.models.athlete_profile import AthleteProfile
from app.models.coach_assignment import CoachAssignment
from app.models.coach_recommendation import CoachRecommendation
from app.models.fatigue_score import FatigueScore
from app.models.injury_prediction import InjuryPrediction
from app.models.training_log import TrainingLog
from app.models.weekly_training_plan import WeeklyTrainingPlan


coach_bp = Blueprint("coach", __name__)


def _get_or_create_profile(user_id: int) -> AthleteProfile:
    profile = AthleteProfile.query.filter_by(athlete_id=user_id).first()
    if profile:
        return profile
    profile = AthleteProfile(athlete_id=user_id)
    db.session.add(profile)
    db.session.flush()
    return profile


def _is_coach(user_id: int) -> bool:
    profile = AthleteProfile.query.filter_by(athlete_id=user_id).first()
    return bool(profile and profile.account_type == "coach")


def _assigned_athletes(coach_id: int) -> list[int]:
    rows = CoachAssignment.query.filter_by(coach_id=coach_id).all()
    return [row.athlete_id for row in rows]


def _can_access_athlete(user_id: int, athlete_id: int) -> bool:
    if user_id == athlete_id:
        return True
    if not _is_coach(user_id):
        return False
    return athlete_id in _assigned_athletes(user_id)


def _fallback_weekly_recommendation(log: TrainingLog | None, prediction: InjuryPrediction | None) -> str:
    risk = prediction.risk_level if prediction else "Low"
    score = round(prediction.risk_score, 1) if prediction else 20
    base_intensity = log.intensity if log else 6

    lines = [f"Injury risk today: {risk} ({score}%). 7-day plan:"]
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for idx, day_label in enumerate(day_labels):
        if idx in {2, 6} and risk != "Low":
            lines.append(f"{day_label}: Recovery day, mobility + low-impact cardio 30-40 min.")
            continue
        shift = [-1, 0, 1, -2, 1, 0, -2][idx]
        intensity = max(3, min(9, base_intensity + shift))
        duration = round(0.9 + intensity / 8.0, 1)
        lines.append(f"{day_label}: {duration}h session, intensity {intensity}/10, finish with 10 min cooldown.")
    lines.append("Sleep 7.5-9h, hydrate 2.5L+, and lower load if pain signals increase.")
    return "\n".join(lines)


def _claude_weekly_recommendation(athlete: Athlete, log: TrainingLog | None, prediction: InjuryPrediction | None) -> str:
    api_key = current_app.config.get("CLAUDE_API_KEY")
    if not api_key:
        return _fallback_weekly_recommendation(log, prediction)

    risk = prediction.risk_level if prediction else "Unknown"
    score = prediction.risk_score if prediction else 0
    summary = "No recent log."
    if log:
        summary = (
            f"date={log.date}, duration={log.duration_hrs}h, intensity={log.intensity}/10, "
            f"distance={log.distance_km if log.distance_km is not None else 'N/A'}km, "
            f"hr={log.heart_rate if log.heart_rate is not None else 'N/A'}"
        )

    prompt = (
        "You are an expert sports performance coach. "
        "Return a practical 7-day training microcycle with daily bullet points. "
        "Include: session focus, duration, intensity target, recovery notes, and one rest/recovery day. "
        f"Athlete sport={athlete.sport}, age={athlete.age}, latest log: {summary}, injury risk={risk} ({score}%). "
        "Keep it concise and action-focused."
    )
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=900,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception:
        return _fallback_weekly_recommendation(log, prediction)


def _escape_pdf(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf(lines: list[str]) -> bytes:
    content = "BT\n/F1 12 Tf\n72 760 Td\n"
    for line in lines:
        content += f"({_escape_pdf(line)}) Tj\n0 -16 Td\n"
    content += "ET\n"
    content_bytes = content.encode("latin-1", errors="ignore")

    objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
        "4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        f"5 0 obj\n<< /Length {len(content_bytes)} >>\nstream\n{content}endstream\nendobj\n",
    ]

    header = "%PDF-1.4\n".encode("latin-1")
    offsets = [0]
    body = b""
    position = len(header)
    for obj in objects:
        encoded = obj.encode("latin-1")
        offsets.append(position)
        body += encoded
        position += len(encoded)

    xref_start = len(header) + len(body)
    xref = f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("latin-1")
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode("latin-1")
    trailer = f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("latin-1")
    return header + body + xref + trailer


@coach_bp.route("/account/upgrade", methods=["POST"])
@jwt_required()
def upgrade_coach_account():
    current_user_id = int(get_jwt_identity())
    profile = _get_or_create_profile(current_user_id)
    profile.account_type = "coach"
    db.session.commit()
    return jsonify({"message": "Account upgraded to coach", "profile": profile.to_dict()}), 200


@coach_bp.route("/assignments", methods=["POST"])
@jwt_required()
def assign_athletes():
    current_user_id = int(get_jwt_identity())
    if not _is_coach(current_user_id):
        return jsonify({"message": "Coach account required"}), 403

    data = request.get_json() or {}
    athlete_ids = data.get("athlete_ids", [])
    if not athlete_ids:
        return jsonify({"message": "athlete_ids is required"}), 400

    created = []
    for athlete_id in athlete_ids:
        athlete = Athlete.query.get(int(athlete_id))
        if not athlete:
            continue
        exists = CoachAssignment.query.filter_by(coach_id=current_user_id, athlete_id=athlete.id).first()
        if exists:
            continue
        row = CoachAssignment(coach_id=current_user_id, athlete_id=athlete.id)
        db.session.add(row)
        created.append(row)
    db.session.commit()
    return jsonify({"message": "Assignments updated", "created": [row.to_dict() for row in created]}), 200


@coach_bp.route("/assignments", methods=["GET"])
@jwt_required()
def list_assignments():
    current_user_id = int(get_jwt_identity())
    if not _is_coach(current_user_id):
        return jsonify({"message": "Coach account required"}), 403
    athlete_ids = _assigned_athletes(current_user_id)
    athletes = Athlete.query.filter(Athlete.id.in_(athlete_ids)).all() if athlete_ids else []
    return jsonify([athlete.to_dict() for athlete in athletes]), 200


@coach_bp.route("/team/risk", methods=["GET"])
@jwt_required()
def compare_team_risk():
    current_user_id = int(get_jwt_identity())
    if not _is_coach(current_user_id):
        return jsonify({"message": "Coach account required"}), 403

    athlete_ids = _assigned_athletes(current_user_id)
    rows = []
    for athlete_id in athlete_ids:
        athlete = Athlete.query.get(athlete_id)
        latest_prediction = (
            InjuryPrediction.query.filter_by(athlete_id=athlete_id)
            .order_by(InjuryPrediction.predicted_at.desc())
            .first()
        )
        latest_fatigue = (
            FatigueScore.query.filter_by(athlete_id=athlete_id)
            .order_by(FatigueScore.calculated_at.desc())
            .first()
        )
        rows.append(
            {
                "athlete_id": athlete_id,
                "athlete_name": athlete.name if athlete else f"Athlete {athlete_id}",
                "risk_score": round(latest_prediction.risk_score, 2) if latest_prediction else None,
                "risk_level": latest_prediction.risk_level if latest_prediction else "Unknown",
                "fatigue_level": latest_fatigue.level if latest_fatigue else None,
                "updated_at": latest_prediction.predicted_at.isoformat() if latest_prediction else None,
            }
        )
    rows.sort(key=lambda item: item["risk_score"] if item["risk_score"] is not None else -1, reverse=True)
    return jsonify(rows), 200


@coach_bp.route("/recommend/<int:athlete_id>", methods=["GET"])
@jwt_required()
def get_recommendation(athlete_id):
    current_user_id = int(get_jwt_identity())
    if not _can_access_athlete(current_user_id, athlete_id):
        return jsonify({"message": "Unauthorized"}), 403

    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({"message": "Athlete not found"}), 404

    recent_pred = (
        InjuryPrediction.query.filter_by(athlete_id=athlete_id)
        .order_by(InjuryPrediction.predicted_at.desc())
        .first()
    )
    prediction_id = recent_pred.id if recent_pred else None
    existing_rec = None
    if prediction_id:
        existing_rec = CoachRecommendation.query.filter_by(athlete_id=athlete_id, prediction_id=prediction_id).first()
    else:
        existing_rec = (
            CoachRecommendation.query.filter_by(athlete_id=athlete_id, prediction_id=None)
            .order_by(CoachRecommendation.created_at.desc())
            .first()
        )
    if existing_rec:
        return jsonify({"message": "Recommendation retrieved", "recommendation": existing_rec.to_dict()}), 200

    latest_log = TrainingLog.query.filter_by(athlete_id=athlete_id).order_by(TrainingLog.date.desc()).first()
    message = _claude_weekly_recommendation(athlete, latest_log, recent_pred)

    recommendation = CoachRecommendation(
        athlete_id=athlete_id,
        prediction_id=prediction_id,
        message=message,
    )
    db.session.add(recommendation)
    db.session.commit()

    return jsonify({"message": "Recommendation generated", "recommendation": recommendation.to_dict()}), 200


@coach_bp.route("/report/<int:athlete_id>/pdf", methods=["GET"])
@jwt_required()
def export_athlete_report(athlete_id):
    current_user_id = int(get_jwt_identity())
    if not _can_access_athlete(current_user_id, athlete_id):
        return jsonify({"message": "Unauthorized"}), 403

    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify({"message": "Athlete not found"}), 404

    latest_prediction = (
        InjuryPrediction.query.filter_by(athlete_id=athlete_id)
        .order_by(InjuryPrediction.predicted_at.desc())
        .first()
    )
    recent_logs = (
        TrainingLog.query.filter_by(athlete_id=athlete_id)
        .order_by(TrainingLog.date.desc())
        .limit(7)
        .all()
    )
    total_hours = round(sum(log.duration_hrs for log in recent_logs), 2)
    avg_intensity = round(sum(log.intensity for log in recent_logs) / len(recent_logs), 2) if recent_logs else 0

    lines = [
        "FitGuard Athlete Report",
        f"Generated: {datetime.utcnow().isoformat()}",
        "",
        f"Athlete: {athlete.name} (ID: {athlete.id})",
        f"Sport: {athlete.sport} | Age: {athlete.age}",
        f"Weight: {athlete.weight} kg | Height: {athlete.height} cm",
        "",
        f"Last 7 sessions total hours: {total_hours}",
        f"Last 7 sessions avg intensity: {avg_intensity}",
        f"Latest injury risk: {latest_prediction.risk_level if latest_prediction else 'N/A'}",
        f"Latest risk score: {round(latest_prediction.risk_score, 2) if latest_prediction else 'N/A'}",
    ]
    pdf_data = _build_simple_pdf(lines)
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=fitguard_report_{athlete_id}.pdf"},
    )


@coach_bp.route("/plans/bulk-assign", methods=["POST"])
@jwt_required()
def bulk_assign_plan():
    current_user_id = int(get_jwt_identity())
    if not _is_coach(current_user_id):
        return jsonify({"message": "Coach account required"}), 403

    data = request.get_json() or {}
    athlete_ids = [int(item) for item in data.get("athlete_ids", [])]
    week_start_text = data.get("week_start")
    sessions = data.get("sessions", [])
    if not athlete_ids or not week_start_text or not sessions:
        return jsonify({"message": "athlete_ids, week_start and sessions are required"}), 400

    try:
        week_start = datetime.strptime(week_start_text, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid week_start format. Use YYYY-MM-DD"}), 400

    assigned_ids = set(_assigned_athletes(current_user_id))
    created_count = 0
    for athlete_id in athlete_ids:
        if athlete_id not in assigned_ids:
            continue
        week_end = week_start + timedelta(days=6)
        WeeklyTrainingPlan.query.filter(
            WeeklyTrainingPlan.athlete_id == athlete_id,
            WeeklyTrainingPlan.plan_date >= week_start,
            WeeklyTrainingPlan.plan_date <= week_end,
        ).delete(synchronize_session=False)

        for session in sessions:
            day_offset = int(session.get("day_offset", 0))
            day = week_start + timedelta(days=max(0, min(day_offset, 6)))
            row = WeeklyTrainingPlan(
                athlete_id=athlete_id,
                coach_id=current_user_id,
                week_start=week_start,
                plan_date=day,
                session_name=session.get("session_name", "Coach Session"),
                duration_hrs=float(session.get("duration_hrs", 1.0)),
                intensity_target=float(session.get("intensity_target", 6.0)),
                distance_target_km=float(session.get("distance_target_km", 0.0)),
                is_rest_day=bool(session.get("is_rest_day", False)),
                source="coach",
                notes=session.get("notes"),
            )
            db.session.add(row)
            created_count += 1

    db.session.commit()
    return jsonify({"message": "Bulk plan assignment completed", "sessions_created": created_count}), 200

from datetime import date, datetime, timedelta
import json

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.athlete_goal import AthleteGoal
from app.models.fatigue_score import FatigueScore
from app.models.training_log import TrainingLog
from app.models.weekly_training_plan import WeeklyTrainingPlan


planning_bp = Blueprint("planning", __name__)


def _parse_week_start(raw: str | None) -> date | None:
    if raw:
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return None
    today = date.today()
    return today - timedelta(days=today.weekday())


def _rule_based_week(week_start: date, base_intensity: float, rest_day: int, source: str) -> list[dict]:
    sessions = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        if i == rest_day:
            sessions.append(
                {
                    "plan_date": day,
                    "session_name": "Rest / Mobility",
                    "duration_hrs": 0.5,
                    "intensity_target": 2.5,
                    "distance_target_km": 0,
                    "is_rest_day": True,
                    "notes": "Mobility + hydration + sleep focus.",
                    "source": source,
                }
            )
            continue

        periodized_shift = [-1.0, 0.0, 0.5, -1.5, 1.0, 0.0, -2.0][i]
        intensity = max(3.0, min(9.0, base_intensity + periodized_shift))
        duration = round(0.9 + (intensity / 10.0) * 1.4, 2)
        session_name = "Aerobic + Strength" if i in {1, 3, 5} else "Sport-Specific Session"
        sessions.append(
            {
                "plan_date": day,
                "session_name": session_name,
                "duration_hrs": duration,
                "intensity_target": round(intensity, 2),
                "distance_target_km": round(max(0.0, intensity - 2.0), 2),
                "is_rest_day": False,
                "notes": "Warm up 15 min, cool down 10 min.",
                "source": source,
            }
        )
    return sessions


def _generate_claude_week_plan(athlete_id: int, week_start: date, base_intensity: float) -> tuple[list[dict], str]:
    api_key = current_app.config.get("CLAUDE_API_KEY")
    if not api_key:
        sessions = _rule_based_week(week_start, base_intensity, rest_day=3, source="rule")
        return sessions, "Claude key not set. Returned rule-based plan."

    prompt = (
        "You are an elite sports performance coach. "
        "Generate a 7-day periodization plan in strict JSON array format only. "
        "Each item keys: day_offset (0-6), session_name, duration_hrs, intensity_target (1-10), "
        "distance_target_km, is_rest_day, notes. "
        f"Week start is {week_start.isoformat()}. Base intensity={base_intensity}. "
        "Balance load, include at least one rest/recovery day."
    )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        parsed = json.loads(text)
        sessions = []
        for item in parsed:
            offset = int(item.get("day_offset", 0))
            plan_date = week_start + timedelta(days=max(0, min(offset, 6)))
            sessions.append(
                {
                    "plan_date": plan_date,
                    "session_name": item.get("session_name", "Training"),
                    "duration_hrs": float(item.get("duration_hrs", 1.0)),
                    "intensity_target": float(item.get("intensity_target", base_intensity)),
                    "distance_target_km": float(item.get("distance_target_km", 0.0)),
                    "is_rest_day": bool(item.get("is_rest_day", False)),
                    "notes": item.get("notes", ""),
                    "source": "claude",
                }
            )
        if len(sessions) != 7:
            raise ValueError("Claude response did not contain 7 sessions")
        return sessions, "Claude-generated periodization plan."
    except Exception as exc:
        sessions = _rule_based_week(week_start, base_intensity, rest_day=3, source="rule")
        return sessions, f"Claude generation failed ({exc}). Returned rule-based plan."


def _replace_week_plan(athlete_id: int, week_start: date, sessions: list[dict], coach_id: int | None = None):
    week_end = week_start + timedelta(days=6)
    WeeklyTrainingPlan.query.filter(
        WeeklyTrainingPlan.athlete_id == athlete_id,
        WeeklyTrainingPlan.plan_date >= week_start,
        WeeklyTrainingPlan.plan_date <= week_end,
    ).delete(synchronize_session=False)

    created = []
    for session in sessions:
        row = WeeklyTrainingPlan(
            athlete_id=athlete_id,
            coach_id=coach_id,
            week_start=week_start,
            plan_date=session["plan_date"],
            session_name=session["session_name"],
            duration_hrs=session.get("duration_hrs"),
            intensity_target=session.get("intensity_target"),
            distance_target_km=session.get("distance_target_km"),
            is_rest_day=session.get("is_rest_day", False),
            source=session.get("source", "rule"),
            notes=session.get("notes"),
        )
        db.session.add(row)
        created.append(row)
    db.session.commit()
    return created


@planning_bp.route("/goals", methods=["GET"])
@jwt_required()
def list_goals():
    current_user_id = int(get_jwt_identity())
    rows = AthleteGoal.query.filter_by(athlete_id=current_user_id).order_by(AthleteGoal.created_at.desc()).all()
    return jsonify([row.to_dict() for row in rows]), 200


@planning_bp.route("/goals", methods=["POST"])
@jwt_required()
def create_goal():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not data.get("goal_type") or not data.get("end_date"):
        return jsonify({"message": "goal_type and end_date are required"}), 400

    start = date.today()
    if data.get("start_date"):
        try:
            start = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    try:
        end = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid end_date format. Use YYYY-MM-DD"}), 400

    goal = AthleteGoal(
        athlete_id=current_user_id,
        goal_type=data["goal_type"],
        target_value=float(data["target_value"]) if data.get("target_value") is not None else None,
        target_sessions_per_week=int(data["target_sessions_per_week"]) if data.get("target_sessions_per_week") is not None else None,
        start_date=start,
        end_date=end,
        status=data.get("status", "active"),
        notes=data.get("notes"),
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify(goal.to_dict()), 201


@planning_bp.route("/goals/<int:goal_id>", methods=["PUT"])
@jwt_required()
def update_goal(goal_id):
    current_user_id = int(get_jwt_identity())
    goal = AthleteGoal.query.get(goal_id)
    if not goal or goal.athlete_id != current_user_id:
        return jsonify({"message": "Goal not found"}), 404

    data = request.get_json() or {}
    for field in ["goal_type", "status", "notes"]:
        if field in data:
            setattr(goal, field, data[field])
    for field in ["target_value", "target_sessions_per_week"]:
        if field in data:
            setattr(goal, field, data[field])
    for field in ["start_date", "end_date"]:
        if field in data:
            try:
                setattr(goal, field, datetime.strptime(data[field], "%Y-%m-%d").date())
            except ValueError:
                return jsonify({"message": f"Invalid {field} format. Use YYYY-MM-DD"}), 400
    db.session.commit()
    return jsonify(goal.to_dict()), 200


@planning_bp.route("/week/<int:athlete_id>", methods=["GET"])
@jwt_required()
def get_week_plan(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    week_start = _parse_week_start(request.args.get("week_start"))
    if not week_start:
        return jsonify({"message": "Invalid week_start format. Use YYYY-MM-DD"}), 400
    week_end = week_start + timedelta(days=6)
    rows = (
        WeeklyTrainingPlan.query.filter(
            WeeklyTrainingPlan.athlete_id == athlete_id,
            WeeklyTrainingPlan.plan_date >= week_start,
            WeeklyTrainingPlan.plan_date <= week_end,
        )
        .order_by(WeeklyTrainingPlan.plan_date.asc())
        .all()
    )
    return jsonify(
        {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "sessions": [row.to_dict() for row in rows],
        }
    ), 200


@planning_bp.route("/recommend-rest-day/<int:athlete_id>", methods=["GET"])
@jwt_required()
def recommend_rest_day(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    latest_fatigue = (
        FatigueScore.query.filter_by(athlete_id=athlete_id)
        .order_by(FatigueScore.calculated_at.desc())
        .first()
    )
    recent_logs = (
        TrainingLog.query.filter_by(athlete_id=athlete_id)
        .order_by(TrainingLog.date.desc())
        .limit(5)
        .all()
    )
    heavy_sessions = sum(1 for log in recent_logs if log.intensity >= 7 or log.duration_hrs >= 2)
    rest_day_offset = 1 if (latest_fatigue and latest_fatigue.level == 2) or heavy_sessions >= 3 else 3

    suggested = date.today() + timedelta(days=rest_day_offset)
    return jsonify(
        {
            "recommended_rest_day": suggested.isoformat(),
            "reason": "High fatigue trend" if latest_fatigue and latest_fatigue.level == 2 else "Load balancing for the week",
        }
    ), 200


@planning_bp.route("/generate-weekly", methods=["POST"])
@jwt_required()
def generate_weekly_plan():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    week_start = _parse_week_start(data.get("week_start"))
    if not week_start:
        return jsonify({"message": "Invalid week_start format. Use YYYY-MM-DD"}), 400
    use_claude = bool(data.get("use_claude", False))

    latest_log = TrainingLog.query.filter_by(athlete_id=current_user_id).order_by(TrainingLog.date.desc()).first()
    base_intensity = float(data.get("base_intensity") or (latest_log.intensity if latest_log else 6.0))
    latest_fatigue = (
        FatigueScore.query.filter_by(athlete_id=current_user_id)
        .order_by(FatigueScore.calculated_at.desc())
        .first()
    )
    rest_day = 2 if latest_fatigue and latest_fatigue.level == 2 else 4

    if use_claude:
        sessions, info = _generate_claude_week_plan(current_user_id, week_start, base_intensity)
    else:
        sessions = _rule_based_week(week_start, base_intensity, rest_day=rest_day, source="rule")
        info = "Rule-based weekly plan generated."

    rows = _replace_week_plan(current_user_id, week_start, sessions, coach_id=None)
    return jsonify({"message": info, "sessions": [row.to_dict() for row in rows]}), 200

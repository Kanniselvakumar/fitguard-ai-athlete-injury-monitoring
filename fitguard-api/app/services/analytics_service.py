from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean, pstdev

from app.models.alert_notification import AlertNotification
from app.models.fatigue_score import FatigueScore
from app.models.hydration_log import HydrationLog
from app.models.injury_prediction import InjuryPrediction
from app.models.model_training_run import ModelTrainingRun
from app.models.recovery_history import RecoveryHistory
from app.models.sport_setting import SportSetting
from app.models.training_log import TrainingLog


def _date_to_week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _date_to_month_label(value: date) -> str:
    return value.strftime("%Y-%m")


def _safe_float(value, default=0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_value(log: TrainingLog) -> float:
    return _safe_float(log.duration_hrs) * _safe_float(log.intensity)


def _map_level(level: int) -> str:
    if level == 2:
        return "High"
    if level == 1:
        return "Medium"
    return "Low"


def build_training_load_trends(logs: list[TrainingLog]) -> dict:
    weekly = defaultdict(float)
    monthly = defaultdict(float)

    for log in logs:
        weekly[_date_to_week_start(log.date)] += _load_value(log)
        monthly[_date_to_month_label(log.date)] += _load_value(log)

    weekly_trend = [
        {"week_start": week.isoformat(), "training_load": round(load, 2)}
        for week, load in sorted(weekly.items())
    ]
    monthly_trend = [
        {"month": month, "training_load": round(load, 2)}
        for month, load in sorted(monthly.items())
    ]

    return {"weekly": weekly_trend, "monthly": monthly_trend}


def build_fatigue_data(athlete_id: int) -> dict:
    fatigue_scores = (
        FatigueScore.query.filter_by(athlete_id=athlete_id)
        .order_by(FatigueScore.calculated_at.asc())
        .all()
    )
    history = [
        {
            "date": entry.calculated_at.date().isoformat(),
            "score": round(entry.score, 2),
            "level": entry.level,
            "level_label": _map_level(entry.level),
        }
        for entry in fatigue_scores
    ]
    latest = history[-1] if history else {"score": 0, "level": 0, "level_label": "Low", "date": None}
    return {"latest": latest, "history": history}


def build_injury_risk_progression(athlete_id: int) -> list[dict]:
    predictions = (
        InjuryPrediction.query.filter_by(athlete_id=athlete_id)
        .order_by(InjuryPrediction.predicted_at.asc())
        .all()
    )
    progression = []
    for pred in predictions:
        progression.append(
            {
                "date": pred.predicted_at.date().isoformat(),
                "risk_score": round(pred.risk_score, 2),
                "risk_level": pred.risk_level,
                "confidence_lower": round(pred.insight.confidence_lower, 2) if pred.insight else None,
                "confidence_upper": round(pred.insight.confidence_upper, 2) if pred.insight else None,
            }
        )
    return progression


def build_hr_zone_breakdown(athlete_id: int, logs: list[TrainingLog]) -> dict:
    setting = SportSetting.query.filter_by(athlete_id=athlete_id).first()
    easy_max = setting.hr_zone_easy_max if setting else 130
    moderate_max = setting.hr_zone_moderate_max if setting else 160
    hard_max = setting.hr_zone_hard_max if setting else 185

    zones = {"easy": 0.0, "moderate": 0.0, "hard": 0.0, "max": 0.0}
    for log in logs:
        if not log.heart_rate:
            continue
        duration = max(_safe_float(log.duration_hrs), 0.0)
        hr = log.heart_rate
        if hr <= easy_max:
            zones["easy"] += duration
        elif hr <= moderate_max:
            zones["moderate"] += duration
        elif hr <= hard_max:
            zones["hard"] += duration
        else:
            zones["max"] += duration

    total = sum(zones.values()) or 1
    breakdown = [
        {"zone": "Easy", "hours": round(zones["easy"], 2), "percentage": round((zones["easy"] / total) * 100, 2)},
        {"zone": "Moderate", "hours": round(zones["moderate"], 2), "percentage": round((zones["moderate"] / total) * 100, 2)},
        {"zone": "Hard", "hours": round(zones["hard"], 2), "percentage": round((zones["hard"] / total) * 100, 2)},
        {"zone": "Max", "hours": round(zones["max"], 2), "percentage": round((zones["max"] / total) * 100, 2)},
    ]
    return {
        "thresholds": {
            "easy_max": easy_max,
            "moderate_max": moderate_max,
            "hard_max": hard_max,
        },
        "breakdown": breakdown,
    }


def build_heatmap_data(logs: list[TrainingLog], days: int = 120) -> list[dict]:
    cutoff = date.today() - timedelta(days=days)
    recent_logs = [log for log in logs if log.date >= cutoff]
    by_date = defaultdict(lambda: {"distance_km": 0.0, "duration_hrs": 0.0, "training_load": 0.0})

    for log in recent_logs:
        row = by_date[log.date]
        row["distance_km"] += _safe_float(log.distance_km)
        row["duration_hrs"] += _safe_float(log.duration_hrs)
        row["training_load"] += _load_value(log)

    return [
        {
            "date": key.isoformat(),
            "distance_km": round(value["distance_km"], 2),
            "duration_hrs": round(value["duration_hrs"], 2),
            "training_load": round(value["training_load"], 2),
        }
        for key, value in sorted(by_date.items())
    ]


def _recovery_score(sleep_hrs: float, rest_days: int, hydration_liters: float) -> float:
    sleep_component = min(max(sleep_hrs, 0), 10) / 8.0 * 50
    rest_component = min(max(rest_days, 0), 2) / 2.0 * 30
    hydration_component = min(max(hydration_liters, 0), 3.5) / 3.5 * 20
    return round(min(100.0, sleep_component + rest_component + hydration_component), 2)


def build_recovery_training_balance(athlete_id: int, logs: list[TrainingLog]) -> list[dict]:
    training_by_date = defaultdict(float)
    for log in logs:
        training_by_date[log.date] += _load_value(log)

    recovery_entries = RecoveryHistory.query.filter_by(athlete_id=athlete_id).all()
    recovery_by_date = defaultdict(list)
    for entry in recovery_entries:
        recovery_by_date[entry.recorded_at.date()].append(entry)

    hydration_entries = HydrationLog.query.filter_by(athlete_id=athlete_id).all()
    hydration_by_date = defaultdict(float)
    for hydration in hydration_entries:
        hydration_by_date[hydration.log_date] += _safe_float(hydration.liters)

    all_dates = sorted(set(training_by_date.keys()) | set(recovery_by_date.keys()) | set(hydration_by_date.keys()))
    data = []
    for day in all_dates:
        day_recovery = recovery_by_date.get(day, [])
        if day_recovery:
            avg_sleep = mean([_safe_float(entry.sleep_hrs) for entry in day_recovery])
            avg_rest_days = round(mean([_safe_float(entry.rest_days) for entry in day_recovery]))
        else:
            avg_sleep = 0.0
            avg_rest_days = 0
        hydration = hydration_by_date.get(day, 0.0)
        data.append(
            {
                "date": day.isoformat(),
                "training_load": round(training_by_date.get(day, 0.0), 2),
                "recovery_score": _recovery_score(avg_sleep, avg_rest_days, hydration),
                "sleep_hrs": round(avg_sleep, 2),
                "rest_days": avg_rest_days,
                "hydration_liters": round(hydration, 2),
            }
        )
    return data


def _daily_load_map(logs: list[TrainingLog], days: int = 60) -> dict[date, float]:
    cutoff = date.today() - timedelta(days=days)
    values = defaultdict(float)
    for log in logs:
        if log.date >= cutoff:
            values[log.date] += _load_value(log)
    return values


def build_advanced_metrics(logs: list[TrainingLog], athlete_id: int) -> dict:
    daily_load = _daily_load_map(logs, days=90)
    today = date.today()
    acute_window = [today - timedelta(days=i) for i in range(7)]
    chronic_window = [today - timedelta(days=i) for i in range(28)]

    acute_load = sum(daily_load.get(day, 0.0) for day in acute_window)
    chronic_load = sum(daily_load.get(day, 0.0) for day in chronic_window)
    chronic_weekly = chronic_load / 4 if chronic_load > 0 else 0
    acwr = round((acute_load / chronic_weekly), 2) if chronic_weekly else 0.0

    weekly_daily = [daily_load.get(day, 0.0) for day in acute_window]
    weekly_mean = mean(weekly_daily) if weekly_daily else 0.0
    weekly_std = pstdev(weekly_daily) if len(weekly_daily) > 1 else 0.0
    monotony = round((weekly_mean / weekly_std), 2) if weekly_std > 0 else 0.0
    strain = round(acute_load * monotony, 2)

    predictions = (
        InjuryPrediction.query.filter_by(athlete_id=athlete_id)
        .order_by(InjuryPrediction.predicted_at.asc())
        .all()
    )
    scatter_points = []
    logs_by_date = defaultdict(list)
    for log in logs:
        logs_by_date[log.date].append(log)

    for pred in predictions:
        pred_day = pred.predicted_at.date()
        day_logs = logs_by_date.get(pred_day, [])
        if not day_logs:
            day_logs = logs_by_date.get(pred_day - timedelta(days=1), [])
        performance_proxy = 0.0
        if day_logs:
            performance_proxy = mean(
                [
                    (_safe_float(l.distance_km) * 2.5) + (_safe_float(l.duration_hrs) * 4) + (_safe_float(l.intensity) * 1.5)
                    for l in day_logs
                ]
            )
        scatter_points.append(
            {
                "date": pred_day.isoformat(),
                "risk_score": round(pred.risk_score, 2),
                "performance_score": round(performance_proxy, 2),
            }
        )

    return {
        "acwr": acwr,
        "monotony": monotony,
        "strain": strain,
        "risk_performance_scatter": scatter_points,
    }


def build_weekly_summary(logs: list[TrainingLog], athlete_id: int) -> dict:
    cutoff = date.today() - timedelta(days=7)
    week_logs = [log for log in logs if log.date >= cutoff]
    total_hours = sum(_safe_float(log.duration_hrs) for log in week_logs)
    avg_intensity = mean([_safe_float(log.intensity) for log in week_logs]) if week_logs else 0.0

    predictions = (
        InjuryPrediction.query.filter_by(athlete_id=athlete_id)
        .order_by(InjuryPrediction.predicted_at.desc())
        .limit(2)
        .all()
    )
    risk_trend = "stable"
    if len(predictions) == 2:
        if predictions[0].risk_score > predictions[1].risk_score + 3:
            risk_trend = "up"
        elif predictions[0].risk_score < predictions[1].risk_score - 3:
            risk_trend = "down"

    return {
        "total_hours": round(total_hours, 2),
        "avg_intensity": round(avg_intensity, 2),
        "sessions": len(week_logs),
        "risk_trend": risk_trend,
    }


def build_recovery_trend(athlete_id: int) -> list[dict]:
    entries = RecoveryHistory.query.filter_by(athlete_id=athlete_id).order_by(RecoveryHistory.recorded_at.asc()).all()
    hydration_entries = HydrationLog.query.filter_by(athlete_id=athlete_id).all()
    hydration_by_date = defaultdict(float)
    for hydration in hydration_entries:
        hydration_by_date[hydration.log_date] += _safe_float(hydration.liters)

    trend = []
    for entry in entries:
        day = entry.recorded_at.date()
        trend.append(
            {
                "date": day.isoformat(),
                "score": _recovery_score(_safe_float(entry.sleep_hrs), int(_safe_float(entry.rest_days)), hydration_by_date.get(day, 0.0)),
                "sleep_hrs": round(_safe_float(entry.sleep_hrs), 2),
                "rest_days": int(_safe_float(entry.rest_days)),
                "hydration_liters": round(hydration_by_date.get(day, 0.0), 2),
            }
        )
    return trend


def build_rest_day_tracker(logs: list[TrainingLog], days: int = 14) -> dict:
    cutoff = date.today() - timedelta(days=days - 1)
    log_days = {log.date for log in logs if log.date >= cutoff}
    missing_days = []
    for i in range(days):
        day = cutoff + timedelta(days=i)
        if day not in log_days:
            missing_days.append(day.isoformat())
    return {
        "window_days": days,
        "rest_days": len(missing_days),
        "rest_day_dates": missing_days,
    }


def build_dashboard_payload(athlete_id: int) -> dict:
    logs = TrainingLog.query.filter_by(athlete_id=athlete_id).order_by(TrainingLog.date.asc()).all()

    model_run = ModelTrainingRun.query.order_by(ModelTrainingRun.trained_at.desc()).first()
    latest_model_metrics = model_run.to_dict() if model_run else None

    payload = {
        "training_load_trends": build_training_load_trends(logs),
        "fatigue": build_fatigue_data(athlete_id),
        "injury_risk_progression": build_injury_risk_progression(athlete_id),
        "heart_rate_zones": build_hr_zone_breakdown(athlete_id, logs),
        "heatmap_calendar": build_heatmap_data(logs),
        "recovery_training_balance": build_recovery_training_balance(athlete_id, logs),
        "advanced_metrics": build_advanced_metrics(logs, athlete_id),
        "recovery_score_trend": build_recovery_trend(athlete_id),
        "rest_day_tracker": build_rest_day_tracker(logs),
        "weekly_summary": build_weekly_summary(logs, athlete_id),
        "latest_model_metrics": latest_model_metrics,
    }

    return payload


def latest_alerts(athlete_id: int, limit: int = 15) -> list[dict]:
    rows = (
        AlertNotification.query.filter_by(athlete_id=athlete_id)
        .order_by(AlertNotification.created_at.desc())
        .limit(limit)
        .all()
    )
    return [row.to_dict() for row in rows]

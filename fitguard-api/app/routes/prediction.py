import json

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.ml.injury_model import model_dashboard, predict_injury_risk, train_model
from app.models.athlete import Athlete
from app.models.athlete_profile import AthleteProfile
from app.models.injury_prediction import InjuryPrediction
from app.models.model_training_run import ModelTrainingRun
from app.models.prediction_insight import PredictionInsight
from app.models.recovery_history import RecoveryHistory
from app.models.training_log import TrainingLog
from app.services.alert_service import generate_alerts


prediction_bp = Blueprint("prediction", __name__)


def _build_default_features(user_id: int) -> dict:
    athlete = Athlete.query.get(user_id)
    profile = AthleteProfile.query.filter_by(athlete_id=user_id).first()
    latest_log = TrainingLog.query.filter_by(athlete_id=user_id).order_by(TrainingLog.date.desc()).first()
    latest_recovery = (
        RecoveryHistory.query.filter_by(athlete_id=user_id)
        .order_by(RecoveryHistory.recorded_at.desc())
        .first()
    )

    return {
        "Player_Age": athlete.age if athlete else 25,
        "Player_Weight": athlete.weight if athlete else 70,
        "Player_Height": athlete.height if athlete else 175,
        "Previous_Injuries": profile.previous_injuries_count if profile else 0,
        "Training_Intensity": latest_log.intensity if latest_log else 5,
        "Recovery_Time": latest_recovery.sleep_hrs if latest_recovery else 3,
    }


@prediction_bp.route("/injury", methods=["POST"])
@jwt_required()
def predict_injury():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    incoming_features = data.get("features", {})
    features = _build_default_features(current_user_id)
    features.update(incoming_features)

    prediction_data = predict_injury_risk(features)
    prediction = InjuryPrediction(
        athlete_id=current_user_id,
        risk_score=prediction_data["risk_score"],
        risk_level=prediction_data["risk_level"],
        algorithm_used="Random Forest",
    )
    db.session.add(prediction)
    db.session.flush()

    insight = PredictionInsight(
        prediction_id=prediction.id,
        confidence_lower=prediction_data["confidence_interval"][0],
        confidence_upper=prediction_data["confidence_interval"][1],
        probability=prediction_data["probability"],
        feature_importance=json.dumps(prediction_data["feature_importance"]),
        model_version=prediction_data["model_version"],
    )
    db.session.add(insight)
    db.session.commit()

    generate_alerts(current_user_id)

    return jsonify(
        {
            "message": "Prediction generated",
            "prediction": prediction.to_dict(),
            "model_metrics": prediction_data.get("metrics", {}),
            "feature_importance": prediction_data.get("feature_importance", {}),
        }
    ), 201


@prediction_bp.route("/injury/latest/<int:athlete_id>", methods=["GET"])
@jwt_required()
def get_latest_prediction(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    latest = (
        InjuryPrediction.query.filter_by(athlete_id=athlete_id)
        .order_by(InjuryPrediction.predicted_at.desc())
        .first()
    )
    return jsonify({"prediction": latest.to_dict() if latest else None}), 200


@prediction_bp.route("/history/<int:athlete_id>", methods=["GET"])
@jwt_required()
def get_prediction_history(athlete_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id != athlete_id:
        return jsonify({"message": "Unauthorized"}), 403

    predictions = (
        InjuryPrediction.query.filter_by(athlete_id=athlete_id)
        .order_by(InjuryPrediction.predicted_at.desc())
        .all()
    )
    return jsonify([p.to_dict() for p in predictions]), 200


@prediction_bp.route("/model/metrics", methods=["GET"])
@jwt_required()
def get_model_metrics():
    dashboard = model_dashboard()
    latest_run = ModelTrainingRun.query.order_by(ModelTrainingRun.trained_at.desc()).first()
    db_metrics = latest_run.to_dict() if latest_run else None

    feature_importance = dashboard.get("feature_importance", {})
    sortable_importance = sorted(
        [{"feature": key, "importance": value} for key, value in feature_importance.items()],
        key=lambda item: item["importance"],
        reverse=True,
    )

    return jsonify(
        {
            "dashboard": dashboard,
            "latest_training_run": db_metrics,
            "feature_importance_ranked": sortable_importance,
        }
    ), 200


@prediction_bp.route("/model/retrain", methods=["POST"])
@jwt_required()
def retrain_model():
    data = request.get_json() or {}
    csv_path = data.get("dataset_path")
    bundle = train_model(csv_path=csv_path)
    metrics = bundle.get("metrics", {})

    training_run = ModelTrainingRun(
        model_name="injury_random_forest",
        model_version=bundle.get("model_version", "unknown"),
        precision=metrics.get("precision", 0.0),
        recall=metrics.get("recall", 0.0),
        f1_score=metrics.get("f1_score", 0.0),
        accuracy=metrics.get("accuracy", 0.0),
        training_rows=bundle.get("trained_rows", 0),
        feature_importance=json.dumps(bundle.get("feature_importance", {})),
    )
    db.session.add(training_run)
    db.session.commit()

    return jsonify(
        {
            "message": "Model retrained successfully",
            "training_run": training_run.to_dict(),
            "dashboard": model_dashboard(),
        }
    ), 200


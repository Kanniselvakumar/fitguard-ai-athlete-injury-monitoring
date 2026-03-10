from __future__ import annotations

from datetime import datetime
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split


FEATURE_COLUMNS = [
    "Player_Age",
    "Player_Weight",
    "Player_Height",
    "Previous_Injuries",
    "Training_Intensity",
    "Recovery_Time",
]
TARGET_COLUMN = "Likelihood_of_Injury"

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "injury_rf_model.pkl")


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _default_dataset_path() -> str:
    env_path = os.getenv("INJURY_DATASET_PATH")
    if env_path:
        return env_path
    return os.path.join(_repo_root(), "datasets", "athelete_injury_dataset.csv")


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_intensity(value: float) -> float:
    v = _safe_float(value, 0.5)
    if v > 1.0:
        v = v / 10.0
    return max(0.0, min(v, 1.0))


def _normalize_recovery_time(value: float) -> float:
    return max(0.0, min(_safe_float(value, 3.0), 12.0))


def prepare_feature_row(features: dict) -> dict:
    return {
        "Player_Age": max(12.0, min(_safe_float(features.get("Player_Age"), 25.0), 80.0)),
        "Player_Weight": max(35.0, min(_safe_float(features.get("Player_Weight"), 70.0), 180.0)),
        "Player_Height": max(120.0, min(_safe_float(features.get("Player_Height"), 175.0), 230.0)),
        "Previous_Injuries": max(0.0, min(_safe_float(features.get("Previous_Injuries"), 0.0), 20.0)),
        "Training_Intensity": _normalize_intensity(features.get("Training_Intensity")),
        "Recovery_Time": _normalize_recovery_time(features.get("Recovery_Time")),
    }


def _load_training_df(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    df = pd.read_csv(csv_path)
    missing = [column for column in FEATURE_COLUMNS + [TARGET_COLUMN] if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")

    clean = df[FEATURE_COLUMNS + [TARGET_COLUMN]].copy()
    clean = clean.dropna(subset=[TARGET_COLUMN])

    clean["Training_Intensity"] = clean["Training_Intensity"].apply(_normalize_intensity)
    clean["Recovery_Time"] = clean["Recovery_Time"].apply(_normalize_recovery_time)
    for col in ["Player_Age", "Player_Weight", "Player_Height", "Previous_Injuries"]:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")
    clean = clean.dropna()
    clean[TARGET_COLUMN] = clean[TARGET_COLUMN].astype(int)
    return clean


def train_model(csv_path: str | None = None, random_state: int = 42) -> dict:
    dataset_path = csv_path or _default_dataset_path()
    df = _load_training_df(dataset_path)

    if len(df) < 20:
        raise ValueError("Not enough rows to train model. Need at least 20 samples.")

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=random_state,
        stratify=y if y.nunique() > 1 else None,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=random_state,
        max_depth=10,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
    }
    importances = {
        col: round(float(importance), 6)
        for col, importance in zip(FEATURE_COLUMNS, model.feature_importances_)
    }

    version = f"rf-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    bundle = {
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "metrics": metrics,
        "feature_importance": importances,
        "trained_rows": int(len(df)),
        "dataset_path": dataset_path,
        "model_version": version,
        "trained_at": datetime.utcnow().isoformat(),
    }

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(bundle, MODEL_PATH)
    return bundle


def load_model_bundle(auto_train: bool = True) -> dict:
    if os.path.exists(MODEL_PATH):
        loaded = joblib.load(MODEL_PATH)
        if isinstance(loaded, dict):
            if "model" in loaded:
                if auto_train and (
                    loaded.get("model_version") == "legacy-rf" or int(loaded.get("trained_rows", 0)) == 0
                ):
                    return train_model()
                return loaded
        if isinstance(loaded, RandomForestClassifier):
            # Legacy single-model artifact detected: retrain to generate full metadata bundle.
            return train_model()
    if auto_train:
        return train_model()
    raise FileNotFoundError("Model not found. Train the model first.")


def _tree_probabilities(model: RandomForestClassifier, row: pd.DataFrame) -> np.ndarray:
    probs = []
    for tree in model.estimators_:
        tree_probs = tree.predict_proba(row)[0]
        class_to_prob = {int(label): float(value) for label, value in zip(tree.classes_, tree_probs)}
        probs.append(class_to_prob.get(1, 0.0))
    return np.array(probs, dtype=float)


def predict_injury_risk(features: dict) -> dict:
    bundle = load_model_bundle(auto_train=True)
    model: RandomForestClassifier = bundle["model"]
    row = prepare_feature_row(features)
    feature_df = pd.DataFrame([row], columns=FEATURE_COLUMNS)

    probabilities = model.predict_proba(feature_df)[0]
    class_to_prob = {int(label): float(value) for label, value in zip(model.classes_, probabilities)}
    injury_probability = class_to_prob.get(1, 0.0)

    tree_probs = _tree_probabilities(model, feature_df)
    lower = float(np.percentile(tree_probs, 10) * 100) if len(tree_probs) else injury_probability * 100
    upper = float(np.percentile(tree_probs, 90) * 100) if len(tree_probs) else injury_probability * 100
    risk_score = injury_probability * 100

    if risk_score >= 70:
        risk_level = "High"
    elif risk_score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "probability": round(risk_score, 2),
        "confidence_interval": [round(lower, 2), round(upper, 2)],
        "feature_importance": bundle.get("feature_importance", {}),
        "model_version": bundle.get("model_version", "unknown"),
        "metrics": bundle.get("metrics", {}),
        "normalized_features": row,
    }


def model_dashboard() -> dict:
    bundle = load_model_bundle(auto_train=True)
    dataset_path = bundle.get("dataset_path") or _default_dataset_path()
    new_rows = None
    needs_retraining = False
    if os.path.exists(dataset_path):
        current_rows = len(pd.read_csv(dataset_path))
        new_rows = max(0, current_rows - int(bundle.get("trained_rows", 0)))
        needs_retraining = new_rows >= 25

    return {
        "model_version": bundle.get("model_version"),
        "trained_at": bundle.get("trained_at"),
        "training_rows": bundle.get("trained_rows"),
        "feature_importance": bundle.get("feature_importance", {}),
        "metrics": bundle.get("metrics", {}),
        "new_data_rows": new_rows,
        "needs_retraining": needs_retraining,
    }

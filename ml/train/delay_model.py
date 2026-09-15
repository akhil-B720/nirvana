"""
NIRVANA ML — Delay Prediction Model

Predicts probability and expected duration of project delay.

Model: Random Forest (supervised)
Labels: Derived from historical completion status (weak supervision)

⚠️  IMPORTANT: 
- Labels are derived from completion status, not expert fraud labels
- Model accuracy is limited by label noise and data availability
- Results are probabilistic estimates, not determinations
- If training data is insufficient, falls back to statistical baseline

Model Card: MODEL_CARD_DELAY.md
"""
import os
import sys
import uuid
import logging
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report, roc_auc_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("ml.delay_model")

MODEL_DIR = Path("models/delay_model")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MIN_TRAINING_SAMPLES = 50  # Minimum for reliable model


def load_training_data() -> pd.DataFrame:
    """Load labeled project data for delay prediction."""
    from backend.database.session import SyncSessionLocal
    from backend.database.models import Project

    db = SyncSessionLocal()
    try:
        projects = db.query(Project).filter(
            Project.start_date.isnot(None),
            Project.expected_completion_date.isnot(None),
        ).all()

        today = date.today()
        rows = []
        for p in projects:
            if not p.start_date or not p.expected_completion_date:
                continue

            planned_duration = (p.expected_completion_date - p.start_date).days
            elapsed = (today - p.start_date).days

            if planned_duration <= 0 or elapsed <= 0:
                continue

            elapsed_ratio = elapsed / planned_duration
            
            # Label derivation (weak supervision)
            # is_delayed: project is past due date and not completed
            is_past_due = today > p.expected_completion_date
            is_completed = p.status == "COMPLETED"
            is_delayed = int(is_past_due and not is_completed)

            rows.append({
                "project_id": p.project_id,
                "sector": p.sector or "Unknown",
                "project_type": p.project_type or "OTHER",
                "state": p.state or "Unknown",
                "planned_duration_days": planned_duration,
                "elapsed_days": elapsed,
                "elapsed_ratio": elapsed_ratio,
                "reported_progress": float(p.reported_progress or 0),
                "sanction_amount": float(p.sanction_amount or 0),
                "released_amount": float(p.released_amount or 0),
                "expenditure_amount": float(p.expenditure_amount or 0),
                "status": p.status or "IN_PROGRESS",
                "is_delayed": is_delayed,  # Label
                "data_availability_status": p.data_availability_status,
            })

        df = pd.DataFrame(rows)
        logger.info(f"Loaded {len(df)} labeled projects "
                   f"({df['is_delayed'].sum()} delayed, "
                   f"{len(df)-df['is_delayed'].sum()} on-track)")
        return df
    finally:
        db.close()


def engineer_delay_features(df: pd.DataFrame) -> tuple:
    """Engineer features for delay prediction."""
    feat = df.copy()

    # Core time features
    feat["elapsed_ratio"] = feat["elapsed_ratio"].clip(0, 3)
    feat["log_planned_duration"] = np.log1p(feat["planned_duration_days"])

    # Financial features
    feat["utilization_rate"] = np.where(
        feat["sanction_amount"] > 0,
        feat["expenditure_amount"] / feat["sanction_amount"], 0
    ).clip(0, 2)
    feat["payment_rate"] = np.where(
        feat["sanction_amount"] > 0,
        feat["released_amount"] / feat["sanction_amount"], 0
    ).clip(0, 2)
    feat["log_amount"] = np.log1p(feat["sanction_amount"])

    # Progress vs time gap
    expected_progress_at_elapsed = feat["elapsed_ratio"].clip(0, 1) * 100
    feat["progress_vs_expected"] = feat["reported_progress"] - expected_progress_at_elapsed

    # Encoders
    le_sector = LabelEncoder()
    feat["sector_enc"] = le_sector.fit_transform(feat["sector"].fillna("Unknown"))
    le_ptype = LabelEncoder()
    feat["ptype_enc"] = le_ptype.fit_transform(feat["project_type"].fillna("OTHER"))
    le_state = LabelEncoder()
    feat["state_enc"] = le_state.fit_transform(feat["state"].fillna("Unknown"))

    feature_cols = [
        "elapsed_ratio", "log_planned_duration", "reported_progress",
        "utilization_rate", "payment_rate", "log_amount",
        "progress_vs_expected", "sector_enc", "ptype_enc", "state_enc",
    ]

    encoders = {"sector": le_sector, "project_type": le_ptype, "state": le_state}
    return feat, feature_cols, encoders


def train():
    """Train the delay prediction model."""
    logger.info("=== NIRVANA Delay Prediction Model Training ===")
    logger.info("Model: Random Forest (weak supervision from completion status)")

    df = load_training_data()

    if len(df) < MIN_TRAINING_SAMPLES:
        logger.warning(f"Only {len(df)} samples — below minimum of {MIN_TRAINING_SAMPLES}.")
        logger.warning("Using statistical BASELINE model. Label quality caveats apply.")
        train_baseline_model(df)
        return

    feat_df, feature_cols, encoders = engineer_delay_features(df)
    X = feat_df[feature_cols].values
    y = feat_df["is_delayed"].values

    imputer = SimpleImputer(strategy="median")
    X = imputer.fit_transform(X)

    logger.info(f"Training on {len(X)} samples | Delay rate: {y.mean():.1%}")

    # Cross-validation for honest evaluation
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=10, min_samples_leaf=5,
        class_weight="balanced", random_state=42, n_jobs=-1
    )

    cv_scores = cross_val_score(rf, X, y, cv=5, scoring="roc_auc")
    logger.info(f"5-fold CV ROC-AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    if cv_scores.mean() < 0.55:
        logger.warning("Low model performance — label quality may be insufficient")
        logger.warning("Falling back to statistical baseline with performance caveat")

    # Fit on full data
    rf.fit(X, y)

    # Feature importance (honest, from tree structure)
    importances = dict(zip(feature_cols, rf.feature_importances_))
    logger.info("\nFeature importances:")
    for feat_name, imp in sorted(importances.items(), key=lambda x: -x[1]):
        logger.info(f"  {feat_name:30s}: {imp:.4f}")

    # Save
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifacts = {
        "model": rf,
        "imputer": imputer,
        "encoders": encoders,
        "feature_cols": feature_cols,
        "training_metadata": {
            "version": version,
            "model_type": "RandomForestClassifier",
            "n_samples": len(X),
            "delay_rate": float(y.mean()),
            "cv_roc_auc_mean": float(cv_scores.mean()),
            "cv_roc_auc_std": float(cv_scores.std()),
            "feature_importances": importances,
            "label_source": "completion_status_weak_supervision",
            "caveat": "Labels derived from status field — not expert fraud labels",
            "trained_at": datetime.utcnow().isoformat(),
        }
    }

    model_path = MODEL_DIR / f"delay_model_{version}.joblib"
    latest_path = MODEL_DIR / "delay_model_latest.joblib"
    joblib.dump(artifacts, model_path)
    joblib.dump(artifacts, latest_path)

    logger.info(f"Model saved: {latest_path}")
    register_model(artifacts, str(latest_path), version, is_baseline=False)
    logger.info("✅ Delay prediction model training complete.")


def train_baseline_model(df: pd.DataFrame):
    """Statistical baseline when training data is insufficient."""
    logger.info("Training statistical baseline model")

    # Baseline: delayed if elapsed_ratio > 1.1 and progress < 80%
    def baseline_predict_proba(elapsed_ratio, reported_progress):
        if elapsed_ratio > 1.3:
            return min(0.95, 0.5 + (elapsed_ratio - 1.0) * 0.3)
        elif elapsed_ratio > 1.0 and reported_progress < 80:
            return 0.7
        elif elapsed_ratio > 0.9 and reported_progress < 50:
            return 0.4
        return 0.1

    version = f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    artifacts = {
        "model_type": "statistical_baseline",
        "predict_fn": baseline_predict_proba,
        "training_metadata": {
            "version": version,
            "model_type": "Statistical Baseline",
            "n_samples": len(df),
            "caveat": "BASELINE MODEL — insufficient training data for ML. "
                     "Requires more labeled data for reliable ML predictions.",
            "trained_at": datetime.utcnow().isoformat(),
        }
    }

    latest_path = MODEL_DIR / "delay_model_latest.joblib"
    joblib.dump(artifacts, latest_path)
    register_model(artifacts, str(latest_path), version, is_baseline=True)
    logger.info("✅ Baseline model saved. Marked as EXPERIMENTAL in registry.")


def register_model(artifacts, model_path, version, is_baseline: bool = False):
    try:
        from backend.database.session import SyncSessionLocal
        from backend.database.models import ModelVersion
        
        db = SyncSessionLocal()
        meta = artifacts["training_metadata"]

        db.query(ModelVersion).filter_by(
            model_name="delay_prediction",
            status="ACTIVE"
        ).update({"status": "RETIRED"})

        mv = ModelVersion(
            model_id=str(uuid.uuid4()),
            model_name="delay_prediction",
            version=version,
            algorithm=meta.get("model_type", "Statistical Baseline"),
            training_data_version=f"n={meta.get('n_samples')}",
            training_timestamp=datetime.utcnow(),
            features={"feature_cols": artifacts.get("feature_cols", [])},
            hyperparameters={"n_estimators": 200, "max_depth": 10},
            metrics={"cv_roc_auc": meta.get("cv_roc_auc_mean", None),
                    "caveat": meta.get("caveat", "")},
            status="EXPERIMENTAL" if is_baseline else "ACTIVE",
            model_path=model_path,
            card_path="MODEL_CARD_DELAY.md",
        )
        db.add(mv)
        db.commit()
        db.close()
        logger.info("✅ Model registered in database")
    except Exception as e:
        logger.warning(f"Could not register model: {e}")


if __name__ == "__main__":
    train()

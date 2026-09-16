"""
NIRVANA ML — Cost Anomaly Detection (Isolation Forest)

This is an UNSUPERVISED anomaly detection model.
There are no fraud labels — we detect statistical outliers.

Output: anomaly_score (0-100), where higher = more anomalous
        is_anomaly (bool) — based on configurable threshold
        
Model Cards: MODEL_CARD_COST.md
Training data: GODL-licensed MPLADS project data + synthetic data
"""
import os
import sys
import json
import uuid
import logging
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
warnings.filterwarnings("ignore")

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("ml.cost_anomaly")

MODEL_DIR = Path("models/cost_anomaly")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_training_data() -> pd.DataFrame:
    """Load project data from database for training."""
    from backend.database.session import SyncSessionLocal
    from backend.database.models import Project

    db = SyncSessionLocal()
    try:
        projects = db.query(Project).filter(
            Project.sanction_amount.isnot(None),
        ).all()

        rows = []
        for p in projects:
            rows.append({
                "project_id": p.project_id,
                "sanction_amount": float(p.sanction_amount or 0),
                "released_amount": float(p.released_amount or 0),
                "expenditure_amount": float(p.expenditure_amount or 0),
                "sector": p.sector or "Unknown",
                "project_type": p.project_type or "OTHER",
                "state": p.state or "Unknown",
                "status": p.status or "IN_PROGRESS",
                "reported_progress": float(p.reported_progress or 0),
                "data_availability_status": p.data_availability_status,
                "start_date": p.start_date,
                "expected_completion_date": p.expected_completion_date,
                "actual_completion_date": p.actual_completion_date,
            })

        df = pd.DataFrame(rows)
        if df.empty:
            logger.info("Loaded 0 projects for training.")
            return df

        logger.info(f"Loaded {len(df)} projects for training "
                   f"({(df['data_availability_status'] == 'SYNTHETIC').sum()} synthetic)")
        return df
    finally:
        db.close()


def engineer_cost_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering for cost anomaly detection.
    
    Features:
    - sanction_amount (raw INR)
    - log_sanction_amount (log-transformed)
    - utilization_rate: expenditure / sanction_amount
    - payment_rate: released / sanction_amount
    - progress_financial_gap: |reported_progress/100 - utilization_rate|
    - project_duration_days
    - elapsed_days
    - elapsed_ratio
    - cost_per_day
    - sector_encoded
    """
    feat = df.copy()

    # Log-transform amount (handles right-skewed distribution)
    feat["log_sanction"] = np.log1p(feat["sanction_amount"])

    # Utilization
    feat["utilization_rate"] = np.where(
        feat["sanction_amount"] > 0,
        feat["expenditure_amount"] / feat["sanction_amount"],
        0.0
    ).clip(0, 2)  # Cap at 2x to handle data errors

    # Payment rate
    feat["payment_rate"] = np.where(
        feat["sanction_amount"] > 0,
        feat["released_amount"] / feat["sanction_amount"],
        0.0
    ).clip(0, 2)

    # Progress-financial gap (key anomaly signal)
    feat["progress_financial_gap"] = np.abs(
        feat["reported_progress"] / 100.0 - feat["utilization_rate"]
    )

    # Duration features
    today = pd.Timestamp.today().normalize()
    feat["start_date"] = pd.to_datetime(feat["start_date"], errors="coerce")
    feat["expected_completion_date"] = pd.to_datetime(feat["expected_completion_date"], errors="coerce")

    feat["planned_duration_days"] = (
        feat["expected_completion_date"] - feat["start_date"]
    ).dt.days.clip(1, 3650)

    feat["elapsed_days"] = (
        today - feat["start_date"]
    ).dt.days.clip(0, 5000)

    feat["elapsed_ratio"] = np.where(
        feat["planned_duration_days"] > 0,
        feat["elapsed_days"] / feat["planned_duration_days"],
        1.0
    ).clip(0, 3)

    feat["cost_per_day"] = np.where(
        feat["elapsed_days"] > 0,
        feat["sanction_amount"] / feat["elapsed_days"],
        feat["sanction_amount"]
    )
    feat["log_cost_per_day"] = np.log1p(feat["cost_per_day"])

    # Sector-relative cost (within sector, how expensive is this project?)
    sector_medians = feat.groupby("sector")["sanction_amount"].transform("median")
    feat["sector_relative_cost"] = feat["sanction_amount"] / (sector_medians + 1)

    # Sector encoding
    le_sector = LabelEncoder()
    feat["sector_encoded"] = le_sector.fit_transform(feat["sector"].fillna("Unknown"))
    le_ptype = LabelEncoder()
    feat["ptype_encoded"] = le_ptype.fit_transform(feat["project_type"].fillna("OTHER"))
    le_status = LabelEncoder()
    feat["status_encoded"] = le_status.fit_transform(feat["status"].fillna("IN_PROGRESS"))

    # Select final feature columns
    feature_cols = [
        "log_sanction",
        "utilization_rate",
        "payment_rate",
        "progress_financial_gap",
        "elapsed_ratio",
        "log_cost_per_day",
        "sector_relative_cost",
        "sector_encoded",
        "ptype_encoded",
    ]

    return feat, feature_cols, {
        "sector": le_sector,
        "project_type": le_ptype,
        "status": le_status,
    }


def train():
    """Train the Isolation Forest cost anomaly model."""
    logger.info("=== NIRVANA Cost Anomaly Model Training ===")
    logger.info("Model: Isolation Forest (unsupervised)")
    logger.info("NOTE: Detects statistical outliers, NOT confirmed fraud")

    # Load data
    df = load_training_data()

    if len(df) < 10:
        logger.error(f"Insufficient training data ({len(df)} records). Run data_pipeline first.")
        logger.error("python -m data_pipeline.run --synthetic")
        sys.exit(1)

    logger.info(f"Training on {len(df)} projects")

    # Feature engineering
    feat_df, feature_cols, encoders = engineer_cost_features(df)

    X = feat_df[feature_cols].values

    # Impute any remaining NaNs (unavailable fields → median)
    imputer = SimpleImputer(strategy="median")
    X = imputer.fit_transform(X)

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Isolation Forest
    # contamination=0.1: ~10% expected anomaly rate (conservative)
    iforest = IsolationForest(
        n_estimators=200,
        max_samples="auto",
        contamination=0.10,
        random_state=42,
        n_jobs=-1,
    )
    iforest.fit(X_scaled)

    # Raw scores (negative = more anomalous in sklearn)
    raw_scores = iforest.score_samples(X_scaled)
    # Normalize to 0-100 (higher = more anomalous)
    score_min, score_max = raw_scores.min(), raw_scores.max()
    anomaly_scores = 100 * (1 - (raw_scores - score_min) / (score_max - score_min + 1e-9))
    predictions = iforest.predict(X_scaled)  # -1 = anomaly, 1 = normal
    is_anomaly = predictions == -1

    n_anomalies = is_anomaly.sum()
    logger.info(f"Detected {n_anomalies}/{len(df)} projects as anomalous "
               f"({n_anomalies/len(df):.1%})")

    # Save artifacts
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifacts = {
        "model": iforest,
        "scaler": scaler,
        "imputer": imputer,
        "encoders": encoders,
        "feature_cols": feature_cols,
        "training_metadata": {
            "version": version,
            "n_training_samples": len(df),
            "n_synthetic": int((df["data_availability_status"] == "SYNTHETIC").sum()),
            "n_real": int((df["data_availability_status"] == "PUBLIC_VERIFIED").sum()),
            "contamination": 0.10,
            "n_anomalies": int(n_anomalies),
            "anomaly_rate": float(n_anomalies / len(df)),
            "score_min": float(score_min),
            "score_max": float(score_max),
            "trained_at": datetime.utcnow().isoformat(),
        }
    }

    model_path = MODEL_DIR / f"cost_anomaly_{version}.joblib"
    latest_path = MODEL_DIR / "cost_anomaly_latest.joblib"
    joblib.dump(artifacts, model_path)
    joblib.dump(artifacts, latest_path)

    logger.info(f"Model saved to: {model_path}")
    logger.info(f"Latest model: {latest_path}")

    # Register in DB
    register_model(artifacts, str(latest_path), version)

    # Print feature importance (via contamination impact)
    logger.info("\nFeature means for anomalous vs. normal projects:")
    feat_array = feat_df[feature_cols].fillna(0).values
    for i, col in enumerate(feature_cols):
        anom_mean = feat_array[is_anomaly, i].mean()
        norm_mean = feat_array[~is_anomaly, i].mean()
        logger.info(f"  {col:30s}: anomalous={anom_mean:.3f}, normal={norm_mean:.3f}")

    logger.info("\n✅ Cost anomaly model training complete.")
    logger.info("NOTE: This model detects statistical outliers.")
    logger.info("      Results do NOT constitute evidence of fraud.")


def register_model(artifacts, model_path, version):
    """Register model in the database model registry."""
    try:
        from backend.database.session import SyncSessionLocal
        from backend.database.models import ModelVersion

        db = SyncSessionLocal()
        meta = artifacts["training_metadata"]

        # Retire previous active version
        db.query(ModelVersion).filter_by(
            model_name="cost_anomaly_isolation_forest",
            status="ACTIVE"
        ).update({"status": "RETIRED"})

        mv = ModelVersion(
            model_id=str(uuid.uuid4()),
            model_name="cost_anomaly_isolation_forest",
            version=version,
            algorithm="Isolation Forest",
            training_data_version=f"n={meta['n_training_samples']}",
            training_timestamp=datetime.utcnow(),
            features={"feature_cols": artifacts["feature_cols"]},
            hyperparameters={"contamination": 0.10, "n_estimators": 200},
            metrics={
                "n_anomalies": meta["n_anomalies"],
                "anomaly_rate": meta["anomaly_rate"],
                "note": "Unsupervised — no precision/recall without labels",
            },
            status="ACTIVE",
            model_path=model_path,
            card_path="MODEL_CARD_COST.md",
        )
        db.add(mv)
        db.commit()
        db.close()
        logger.info("✅ Model registered in database")
    except Exception as e:
        logger.warning(f"Could not register model in DB: {e}")


if __name__ == "__main__":
    train()

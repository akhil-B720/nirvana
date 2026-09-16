import os
import sys
import uuid
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
import logging

from backend.database.session import SyncSessionLocal
from backend.database.models import Project, ProjectAnomaly, ModelPrediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml.inference.engine")

MODEL_DIR = Path(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
COST_MODEL_PATH = MODEL_DIR / "cost_anomaly" / "cost_anomaly_latest.joblib"
DELAY_MODEL_PATH = MODEL_DIR / "delay_model" / "delay_model_latest.joblib"

_cost_model = None
_delay_model = None

def load_models():
    global _cost_model, _delay_model
    if _cost_model is None and COST_MODEL_PATH.exists():
        _cost_model = joblib.load(COST_MODEL_PATH)
    if _delay_model is None and DELAY_MODEL_PATH.exists():
        _delay_model = joblib.load(DELAY_MODEL_PATH)

def run_project_inference(project_id: str):
    """Run all ML models for a single project and generate anomalies if needed."""
    load_models()
    db = SyncSessionLocal()
    try:
        project = db.query(Project).filter_by(project_id=project_id).first()
        if not project:
            return

        # 1. Cost Anomaly Inference
        if _cost_model:
            _run_cost_inference(db, project, _cost_model)

        # 2. Delay Model Inference
        if _delay_model:
            _run_delay_inference(db, project, _delay_model)

        # Note: Similarity generates anomalies offline/batch since it needs N^2 pairs.
        
        db.commit()
    except Exception as e:
        logger.error(f"Inference error for {project_id}: {e}")
        db.rollback()
    finally:
        db.close()

def _run_cost_inference(db, project, model_artifacts):
    meta = model_artifacts["training_metadata"]
    model_version = meta["version"]

    sanction = float(project.sanction_amount or 0)
    if sanction == 0:
        return

    exp = float(project.expenditure_amount or 0)
    rel = float(project.released_amount or 0)
    utilization_rate = exp / sanction if sanction > 0 else 0.0
    utilization_rate = min(u, 2.0) if (u:=utilization_rate) else 0.0
    payment_rate = rel / sanction if sanction > 0 else 0.0
    payment_rate = min(p, 2.0) if (p:=payment_rate) else 0.0
    progress = float(project.reported_progress or 0) / 100.0
    progress_financial_gap = abs(progress - utilization_rate)

    start = project.start_date
    end = project.expected_completion_date
    today = date.today()
    planned_duration = (end - start).days if start and end else 0
    planned_duration = max(min(planned_duration, 3650), 1)

    elapsed = (today - start).days if start else 0
    elapsed = max(min(elapsed, 5000), 0)

    elapsed_ratio = elapsed / planned_duration if planned_duration > 0 else 1.0
    elapsed_ratio = min(elapsed_ratio, 3.0)

    cost_per_day = sanction / elapsed if elapsed > 0 else sanction
    log_cost_per_day = np.log1p(cost_per_day)

    sector = project.sector or "Unknown"
    ptype = project.project_type or "OTHER"
    
    le_sector = model_artifacts["encoders"]["sector"]
    le_ptype = model_artifacts["encoders"]["project_type"]
    
    sec_enc = le_sector.transform([sector])[0] if sector in le_sector.classes_ else 0
    ptype_enc = le_ptype.transform([ptype])[0] if ptype in le_ptype.classes_ else 0
    
    features = [
        np.log1p(sanction), utilization_rate, payment_rate, progress_financial_gap,
        elapsed_ratio, log_cost_per_day, sanction / 1.0, sec_enc, ptype_enc
    ]

    imputer = model_artifacts["imputer"]
    scaler = model_artifacts["scaler"]
    iforest = model_artifacts["model"]

    X = np.array([features])
    X = imputer.transform(X)
    X = scaler.transform(X)

    raw_score = iforest.score_samples(X)[0]
    pred = iforest.predict(X)[0]
    
    score_min, score_max = meta["score_min"], meta["score_max"]
    normalized_score = 100 * (1 - (raw_score - score_min) / (score_max - score_min + 1e-9))
    normalized_score = max(min(normalized_score, 100.0), 0.0)

    if pred == -1 or normalized_score > 70:
        _store_anomaly(db, project.project_id, "COST", normalized_score, 
            normalized_score, 0.75, {"utilization": utilization_rate, "gap": progress_financial_gap})

def _run_delay_inference(db, project, model_artifacts):
    start = project.start_date
    end = project.expected_completion_date
    if not (start and end):
        return

    today = date.today()
    planned_duration = (end - start).days
    elapsed = (today - start).days
    if planned_duration <= 0 or elapsed <= 0:
        return
    
    elapsed_ratio = min(elapsed / planned_duration, 3.0)
    reported_progress = float(project.reported_progress or 0)

    is_baseline = model_artifacts.get("model_type") == "statistical_baseline"
    
    if is_baseline:
        prob = model_artifacts["predict_fn"](elapsed_ratio, reported_progress)
    else:
        sanction = float(project.sanction_amount or 0)
        exp = float(project.expenditure_amount or 0)
        rel = float(project.released_amount or 0)
        
        log_planned = np.log1p(planned_duration)
        utilization = min(exp/sanction, 2.0) if sanction > 0 else 0
        payment = min(rel/sanction, 2.0) if sanction > 0 else 0
        log_amount = np.log1p(sanction)
        expected_prog = min(elapsed_ratio, 1.0) * 100
        prog_diff = reported_progress - expected_prog
        
        encoders = model_artifacts["encoders"]
        le_sector = encoders["sector"]
        le_ptype = encoders["project_type"]
        le_state = encoders["state"]
        
        sector = project.sector or "Unknown"
        sec_enc = le_sector.transform([sector])[0] if sector in le_sector.classes_ else 0
        ptype = project.project_type or "OTHER"
        ptype_enc = le_ptype.transform([ptype])[0] if ptype in le_ptype.classes_ else 0
        state = project.state or "Unknown"
        state_enc = le_state.transform([state])[0] if state in le_state.classes_ else 0

        features = [
            elapsed_ratio, log_planned, reported_progress, utilization, payment,
            log_amount, prog_diff, sec_enc, ptype_enc, state_enc
        ]
        X = np.array([features])
        X = model_artifacts["imputer"].transform(X)
        prob = float(model_artifacts["model"].predict_proba(X)[0][1])

    if prob > 0.6:
        _store_anomaly(db, project.project_id, "DELAY", prob, prob * 100, 0.8,
            {"prob": prob, "elapsed_ratio": elapsed_ratio})

def _store_anomaly(db, project_id, type_, raw, norm, conf, feats):
    # clear open anomaly of same type
    db.query(ProjectAnomaly).filter_by(project_id=project_id, anomaly_type=type_, status="OPEN").delete()
    
    anom = ProjectAnomaly(
        anomaly_id=str(uuid.uuid4()),
        project_id=project_id,
        anomaly_type=type_,
        signal_value=raw,
        normalized_score=norm,
        confidence=conf,
        contributing_features=feats,
        status="OPEN"
    )
    db.add(anom)

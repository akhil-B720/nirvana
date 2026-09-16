from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.session import get_db
from backend.database.models import Project, ProjectAnomaly, RiskScore
from backend.engines.risk_fusion import RiskFusionEngine, RiskSignals

router = APIRouter(prefix="/projects/{project_id}/risk", tags=["Risk"])
risk_engine = RiskFusionEngine()

@router.get("/")
async def get_project_risk(project_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the fused risk score for a project.
    Aggregates anomalies and computes the final score.
    """
    # Fetch project
    query = select(Project).where(Project.project_id == project_id)
    result = await db.execute(query)
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch anomalies
    anom_query = select(ProjectAnomaly).where(ProjectAnomaly.project_id == project_id)
    anom_result = await db.execute(anom_query)
    anomalies = anom_result.scalars().all()
    
    # We map anomalies to RiskSignals
    signals = RiskSignals(project_id=project_id)
    for a in anomalies:
        if a.anomaly_type == "COST":
            signals.cost_anomaly_score = a.normalized_score
            signals.cost_anomaly_confidence = a.confidence
        elif a.anomaly_type == "PAYMENT_PROGRESS":
            signals.payment_progress_gap = a.normalized_score
        elif a.anomaly_type == "DELAY":
            signals.delay_probability = a.signal_value
        elif a.anomaly_type == "DUPLICATE":
            signals.similarity_score = a.signal_value

    # Evaluate reality gap as well if available (placeholder - reality gap engine runs this)
    # signals.reality_gap_score = compute_or_fetch_reality_gap(project_id)
    
    # Compute fusion
    risk_result = risk_engine.compute(signals)
    
    # Save the risk result to the database
    risk_engine.save_to_db(risk_result, db)
    
    return risk_result

